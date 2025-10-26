#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sqlite3
from pathlib import Path
from collections import Counter, defaultdict, deque
import threading

import cv2
import numpy as np
import torch
from ultralytics import YOLO

# =========================
# Quick health checks (optional; run manually)
# -------------------------
# # Temperature:
# #   vcgencmd measure_temp
# # Throttle flags:
# #   vcgencmd get_throttled  (should be 0x0)
# # Governor:
# #   cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
# =========================

# =========================
# Tunables
# =========================
STREAM_URL = "http://127.0.0.1:8090/?action=stream"
IMGSZ = 384
CONF, IOU = 0.25, 0.45
MAX_DET = 12

# Commit to SQLite every N frames to reduce I/O stalls
BATCH_COMMIT_N = 15  # try 10–30

# Drop pacing unless you’re comfortably > target
TARGET_FPS = 10      # soft target; we won't sleep if we’re behind

# Optional: limit OpenCV & torch threads on ARM
cv2.setNumThreads(1)
torch.set_num_threads(4)
torch.set_num_interop_threads(1)

# =========================
# Load models (CPU on Pi)
# =========================
light_model = YOLO("/home/sarsa/Traffic_lights_detection.pt")
sign_model  = YOLO("/home/sarsa/new_traffic_signs.pt")
ped_model   = YOLO("/home/sarsa/pedestrian_detection.pt")

CLASSES_LIGHT = None
CLASSES_SIGN  = None
CLASSES_PED   = None

# =========================
# DB setup (WAL + batched commits)
# =========================
base_dir = Path(__file__).parent.resolve()
db_path = base_dir / "dashtest_new/dashtest/backend_server/dashboard.db"
conn = sqlite3.connect(str(db_path), check_same_thread=False)
cur = conn.cursor()
cur.execute("PRAGMA journal_mode=WAL;")
cur.execute("PRAGMA synchronous=NORMAL;")
cur.execute("DELETE FROM traffic_signs;")
conn.commit()

pending_rows = []  # we’ll batch INSERTs into this and commit periodically

# =========================
# Utilities
# =========================
def letterbox(img: np.ndarray, size: int) -> np.ndarray:
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
    per_type = defaultdict(Counter)
    detected_any = False
    for det_type, res in results_dict.items():
        if res is None or res.boxes is None or len(res.boxes) == 0:
            continue
        names = res.names
        for cls_id in res.boxes.cls.tolist():
            per_type[det_type][names[int(cls_id)]] += 1
            detected_any = True
    if not detected_any:
        return False, "none"
    segments = []
    for det_type, counter in per_type.items():
        parts = [f"{cls}({n})" for cls, n in counter.most_common()]
        segments.append(f"{det_type}:" + ",".join(parts))
    return True, " | ".join(segments)

# =========================
# Threaded frame grabber (drop old frames)
# =========================
class FrameGrabber:
    def __init__(self, src):
        self.cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
        # reduce internal buffer if supported (no-op if not)
        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open stream (check URL/FFMPEG/OpenCV).")
        self.q = deque(maxlen=1)  # keep only the latest
        self.running = True
        self.th = threading.Thread(target=self._loop, daemon=True)
        self.th.start()

    def _loop(self):
        while self.running:
            ok, frame = self.cap.read()
            if not ok or frame is None:
                # brief pause on hiccup to avoid tight spin
                time.sleep(0.005)
                continue
            if frame.ndim == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            self.q.append(frame)

    def read(self):
        return self.q[-1] if self.q else None

    def release(self):
        self.running = False
        try:
            self.th.join(timeout=1.0)
        except Exception:
            pass
        self.cap.release()

# =========================
# Main
# =========================
def main():
    grab = FrameGrabber(STREAM_URL)
    print("Stream opened successfully.")
    frame_idx = 0
    k = 0
    last_print = 0.0

    last_results = {"light": None, "sign": None, "pedestrian": None}

    try:
        while True:
            loop_start = time.perf_counter()

            frame = grab.read()
            if frame is None:
                time.sleep(0.002)
                continue  # no frame yet; keep spinning

            # ---- Round-robin: ONE model per iteration ----
            sel = k % 3
            t0 = time.perf_counter()
            if sel == 0:
                last_results["light"] = yolo_infer(light_model, frame, CLASSES_LIGHT)
            elif sel == 1:
                last_results["sign"] = yolo_infer(sign_model, frame, CLASSES_SIGN)
            else:
                last_results["pedestrian"] = yolo_infer(ped_model, frame, CLASSES_PED)
            infer_ms = (time.perf_counter() - t0) * 1000.0

            # ---- Build DB rows from ALL cached results (latest view) ----
            detected_any = False
            for key, res in last_results.items():
                if res is None or res.boxes is None or len(res.boxes) == 0:
                    continue
                names = res.names
                for cls_id in res.boxes.cls.tolist():
                    cls_name = names[int(cls_id)]
                    pending_rows.append(
                        (f"{key}:{cls_name}", "50", frame_idx, 1)
                    )
                    detected_any = True

            if not detected_any:
                pending_rows.append(("none", "50", frame_idx, 0))

            # ---- Commit batched rows every N frames ----
            if frame_idx % BATCH_COMMIT_N == 0 and pending_rows:
                cur.executemany(
                    "INSERT INTO traffic_signs (type, value, distance, active) VALUES (?,?,?,?)",
                    pending_rows
                )
                conn.commit()
                pending_rows.clear()

            # ---- Telemetry & adaptive pacing ----
            frame_idx += 1
            k += 1

            loop_ms = (time.perf_counter() - loop_start) * 1000.0
            now = time.time()
            if now - last_print > 1.0:
                det_flag, det_summary = summarize_detections(last_results)
                eff_fps = 1000.0 / max(loop_ms, 1.0)
                print(
                    f"Frame {frame_idx} | this model {infer_ms:.0f} ms | "
                    f"loop {loop_ms:.0f} ms | eff FPS={eff_fps:.1f} | "
                    f"detected={det_flag} | {('Detected: ' + det_summary) if det_flag else 'Detected: none'}"
                )
                last_print = now

            # Pace only if we’re *ahead* of target; never sleep when behind
            if TARGET_FPS:
                budget = 1.0 / TARGET_FPS
                spent = (time.perf_counter() - loop_start)
                if spent < budget:
                    time.sleep(budget - spent)

    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        # Final flush of any pending rows
        if pending_rows:
            cur.executemany(
                "INSERT INTO traffic_signs (type, value, distance, active) VALUES (?,?,?,?)",
                pending_rows
            )
            conn.commit()
            pending_rows.clear()

        grab.release()
        cv2.destroyAllWindows()
        conn.close()
        print("Clean shutdown.")

if __name__ == "__main__":
    main()
