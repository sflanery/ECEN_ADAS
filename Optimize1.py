#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sqlite3
from pathlib import Path
from collections import Counter, defaultdict

import cv2
import numpy as np
import torch
from ultralytics import YOLO

# =========================
# Tunables (adjust as needed)
# =========================
STREAM_URL = "http://127.0.0.1:8090/?action=stream"  # your stream
IMGSZ = 384                 # try 320 / 384 / 416; smaller = faster
CONF, IOU = 0.25, 0.45
MAX_DET = 12
TARGET_FPS = 10             # pacing target, prevents thrash (not a guarantee)

# Optional: limit OpenCV threads on ARM
cv2.setNumThreads(1)

# Optional: limit torch threading on ARM (Pi 5: 4 big cores)
torch.set_num_threads(4)
torch.set_num_interop_threads(1)

# =========================
# Load models (CPU on Pi)
# =========================
light_model = YOLO("/home/sarsa/Traffic_lights_detection.pt")
sign_model  = YOLO("/home/sarsa/new_traffic_signs.pt")  # keep the newer one
ped_model   = YOLO("/home/sarsa/pedestrian_detection.pt")

# If you only care about specific classes in a model, set indices here (else None)
CLASSES_LIGHT = None  # e.g., [0,1,2]
CLASSES_SIGN  = None
CLASSES_PED   = None

# =========================
# DB setup
# =========================
base_dir = Path(__file__).parent.resolve()
db_path = base_dir / "dashtest_new/dashtest/backend_server/dashboard.db"
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

# Clear table (and optionally reset autoincrement sequence)
cur.execute("DELETE FROM traffic_signs;")
# cur.execute("DELETE FROM sqlite_sequence WHERE name='traffic_signs';")
conn.commit()

# =========================
# Utility functions
# =========================
def letterbox(img: np.ndarray, size: int) -> np.ndarray:
    """Resize & pad to (size, size) keeping aspect ratio (BGR uint8 in, out)."""
    h, w = img.shape[:2]
    r = min(size / h, size / w)
    nh, nw = int(h * r), int(w * r)
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    canvas = np.zeros((size, size, 3), dtype=np.uint8)
    top = (size - nh) // 2
    left = (size - nw) // 2
    canvas[top:top + nh, left:left + nw] = resized
    return canvas

def yolo_infer(model: YOLO, frame: np.ndarray, classes=None):
    """Run one YOLO model on a frame with fixed settings."""
    inp = letterbox(frame, IMGSZ)
    return model.predict(
        inp,
        device="cpu",
        imgsz=IMGSZ,
        conf=CONF,
        iou=IOU,
        max_det=MAX_DET,
        classes=classes,
        verbose=False
    )[0]

def summarize_detections(results_dict):
    """
    Build a human-readable summary string and a boolean flag.
    results_dict: {"light": r, "sign": r, "pedestrian": r}
    Returns: detected_any(bool), summary_str(str)
    """
    per_type_counts = defaultdict(Counter)
    detected_any = False

    for det_type, res in results_dict.items():
        if res is None or res.boxes is None or len(res.boxes) == 0:
            continue
        names = res.names
        for cls_id in res.boxes.cls.tolist():
            per_type_counts[det_type][names[int(cls_id)]] += 1
            detected_any = True

    if not detected_any:
        return False, "none"

    # Build compact "type:class1(n),class2(m)" segments
    segments = []
    for det_type, counter in per_type_counts.items():
        parts = [f"{cls}({n})" for cls, n in counter.most_common()]
        segments.append(f"{det_type}:" + ",".join(parts))
    return True, " | ".join(segments)

# =========================
# Video Capture
# =========================
cap = cv2.VideoCapture(STREAM_URL, cv2.CAP_FFMPEG)
if not cap.isOpened():
    raise RuntimeError("Failed to open stream. Verify the URL/FFMPEG/OpenCV build.")

print("Stream opened successfully.")
frame_idx = 0
k = 0
last_print = 0.0

# cached latest results (we update only one each frame)
last_results = {"light": None, "sign": None, "pedestrian": None}

# =========================
# Main loop
# =========================
try:
    while True:
        loop_start = time.perf_counter()

        ok, frame = cap.read()
        if not ok or frame is None:
            # Stream hiccup—sleep briefly and continue
            time.sleep(0.01)
            continue

        # Normalize to 3-channel if stream is grayscale
        if frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        # -------- round-robin: one model per frame --------
        sel = k % 3
        t0 = time.perf_counter()

        if sel == 0:
            # Traffic lights this frame
            last_results["light"] = yolo_infer(light_model, frame, CLASSES_LIGHT)
        elif sel == 1:
            # Traffic signs this frame
            last_results["sign"] = yolo_infer(sign_model, frame, CLASSES_SIGN)
        else:
            # Pedestrians this frame
            last_results["pedestrian"] = yolo_infer(ped_model, frame, CLASSES_PED)

        infer_ms = (time.perf_counter() - t0) * 1000.0

        # -------- Consolidated DB write per frame --------
        detected_any = False
        for key, res in last_results.items():
            if res is None or res.boxes is None or len(res.boxes) == 0:
                continue
            names = res.names
            for cls_id in res.boxes.cls.tolist():
                cls_name = names[int(cls_id)]
                cur.execute(
                    """
                    INSERT INTO traffic_signs (type, value, distance, active)
                    VALUES (?,?,?,?)
                    """,
                    (f"{key}:{cls_name}", "50", frame_idx, 1)
                )
                detected_any = True

        if not detected_any:
            cur.execute(
                """
                INSERT INTO traffic_signs (type, value, distance, active)
                VALUES (?,?,?,?)
                """,
                ("none", "50", frame_idx, 0)
            )

        conn.commit()

        # -------- Telemetry & pacing --------
        # Build a readable summary for the console
        det_flag, det_summary = summarize_detections(last_results)

        frame_idx += 1
        k += 1

        loop_ms = (time.perf_counter() - loop_start) * 1000.0
        now = time.time()
        if now - last_print > 1.0:
            eff_fps = 1000.0 / max(loop_ms, 1.0)
            print(
                f"Frame {frame_idx} | this model {infer_ms:.0f} ms | "
                f"loop {loop_ms:.0f} ms | eff FPS={eff_fps:.1f} | "
                f"detected={det_flag} | {('Detected: ' + det_summary) if det_flag else 'Detected: none'}"
            )
            last_print = now

        # soft pacing to avoid pegging CPU; reduces jitter
        budget = 1.0 / TARGET_FPS
        spent = (time.perf_counter() - loop_start)
        if spent < budget:
            time.sleep(budget - spent)

except KeyboardInterrupt:
    print("Interrupted by user.")
finally:
    cap.release()
    cv2.destroyAllWindows()
    conn.close()
    print("Clean shutdown.")



