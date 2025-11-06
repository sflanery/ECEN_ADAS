#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import requests
import threading
from pathlib import Path
from collections import Counter, defaultdict, deque

import cv2
import numpy as np
import torch
from ultralytics import YOLO

# =========================
# API Configuration
# =========================
BASE_URL = "http://localhost:8080"
API_TIMEOUT = 0.5  # shorter timeout to avoid blocking

def update_alert_via_api(alert_type, status):
    """Update alert via Flask API (non-blocking)."""
    try:
        requests.post(
            f"{BASE_URL}/update_alert",
            json={"type": alert_type, "status": status},
            timeout=API_TIMEOUT
        )
    except Exception as e:
        pass  # Silent fail to avoid spam

def update_traffic_sign_via_api(sign_type, value, distance):
    """Update traffic sign via Flask API (non-blocking)."""
    try:
        requests.post(
            f"{BASE_URL}/add_sign",
            json={"type": sign_type, "value": value, "distance": distance},
            timeout=API_TIMEOUT
        )
    except Exception:
        pass  # Silent fail

def update_speed_limit(new_limit):
    """Update speed limit sign."""
    state = requests.get(f"{BASE_URL}/get_state").json()
    for sign in state['signs']:
        if sign['type'] == 'speed_limit':
            requests.post(f"{BASE_URL}/update_sign", json={
                "id": sign['id'],
                "type": "speed_limit",
                "value": str(new_limit),
                "distance": "50m"
            })
            print(f"🔄 Speed limit set to {new_limit} MPH")
            return True
    print("⚠️ Could not find speed limit sign")
    return False
# =========================
# Tunables
# =========================
STREAM_URL = "http://127.0.0.1:8090/?action=stream"
IMGSZ = 384
CONF_DEFAULT, IOU = 0.25, 0.45
MAX_DET = 12

# False-positive controls (per-detector thresholds)
TH_CONF = {
    "light": 0.40,
    "sign":  0.45,
    "pedestrian": 0.35,
}
MIN_AREA = {
    "light": 900,
    "sign":  1200,
    "pedestrian": 1600,
}
ASPECT_LIMITS = {
    "light": (0.5, 3.0),
    "sign":  (0.5, 2.5),
    "pedestrian": (1.3, 4.5),
}

# Temporal smoothing: require persistence across frames
WINDOW = 5
PERSIST_HITS = 2
IOU_MATCH = 0.30

# Optional ROI mask: only accept detections within this region
def make_road_roi(size):
    m = np.zeros((size, size), np.uint8)
    m[size // 3:, :] = 1  # lower 2/3 of the frame
    return m
ROI_MASK = make_road_roi(IMGSZ)  # set to None to disable

TARGET_FPS = 10

# Limit threading on ARM
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
# State tracking for alerts
# =========================
pedestrian_active = False
last_sign_update = 0  # timestamp to rate-limit sign updates

# =========================
# Helpers
# =========================
def letterbox(img: np.ndarray, size: int) -> np.ndarray:
    h, w = img.shape[:2]
    r = min(size / h, size / w)
    nh, nw = int(h * r), int(w * r)
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    canvas = np.zeros((size, size, 3), dtype=np.uint8)
    top = (size - nh) // 2
    left = (size - nw) // 2
    canvas[top:top+nh, left:left+nw] = resized
    return canvas

def yolo_infer(model: YOLO, frame: np.ndarray, classes=None):
    """Run YOLO with fixed size; returns Ultralytics result object."""
    inp = letterbox(frame, IMGSZ)
    return model.predict(
        inp,
        device="cpu",
        imgsz=IMGSZ,
        conf=CONF_DEFAULT,
        iou=IOU,
        max_det=MAX_DET,
        classes=classes,
        verbose=False
    )[0]

def iou(box_a, box_b):
    xa1, ya1, xa2, ya2 = box_a
    xb1, yb1, xb2, yb2 = box_b
    inter_w = max(0, min(xa2, xb2) - max(xa1, xb1))
    inter_h = max(0, min(ya2, yb2) - max(ya1, yb1))
    inter = inter_w * inter_h
    if inter <= 0: return 0.0
    area_a = (xa2 - xa1) * (ya2 - ya1)
    area_b = (xb2 - xb1) * (yb2 - yb1)
    return inter / max(area_a + area_b - inter, 1e-6)

def box_ok(det_type, box, conf):
    """Apply per-detector confidence, size, aspect, and ROI filters."""
    x1, y1, x2, y2 = map(int, box)
    w, h = max(1, x2 - x1), max(1, y2 - y1)
    area = w * h
    if conf < TH_CONF[det_type]: return False
    if area < MIN_AREA[det_type]: return False
    ratio = h / float(w)
    rmin, rmax = ASPECT_LIMITS[det_type]
    if not (rmin <= ratio <= rmax): return False
    if ROI_MASK is not None:
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        if not (0 <= cx < ROI_MASK.shape[1] and 0 <= cy < ROI_MASK.shape[0] and ROI_MASK[cy, cx] == 1):
            return False
    return True

class TemporalSmoother:
    """Require persistence: a box must match across >=PERSIST_HITS of last WINDOW frames."""
    def __init__(self, window=WINDOW, hits=PERSIST_HITS, iou_match=IOU_MATCH):
        self.window = window
        self.hits = hits
        self.iou_match = iou_match
        self.history = defaultdict(lambda: defaultdict(lambda: deque(maxlen=window)))

    def update_and_accept(self, det_type, class_name, boxes):
        dq = self.history[det_type][class_name]
        dq.append(boxes)
        accepted = []
        for b in boxes:
            count = 1
            for past in list(dq)[:-1]:
                if any(iou(b[:4], pb[:4]) >= self.iou_match for pb in past):
                    count += 1
            if count >= self.hits:
                accepted.append(b)
        return accepted

smoother = TemporalSmoother()

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
# Threaded frame grabber
# =========================
class FrameGrabber:
    def __init__(self, src):
        self.cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open stream (URL/FFmpeg/OpenCV).")
        self.q = deque(maxlen=1)
        self.running = True
        self.th = threading.Thread(target=self._loop, daemon=True)
        self.th.start()

    def _loop(self):
        while self.running:
            ok, frame = self.cap.read()
            if not ok or frame is None:
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
    global pedestrian_active, last_sign_update
    
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
                continue

            # Round-robin: ONE model per loop
            sel = k % 3
            t0 = time.perf_counter()
            if sel == 0:
                last_results["light"] = yolo_infer(light_model, frame, CLASSES_LIGHT)
            elif sel == 1:
                last_results["sign"] = yolo_infer(sign_model, frame, CLASSES_SIGN)
            else:
                last_results["pedestrian"] = yolo_infer(ped_model, frame, CLASSES_PED)
            infer_ms = (time.perf_counter() - t0) * 1000.0

            # -------- Filter + temporal smoothing + API updates --------
            pedestrian_detected = False
            sign_detected = None

            for det_type, res in last_results.items():
                if res is None or res.boxes is None or len(res.boxes) == 0:
                    continue

                names = res.names
                xyxy = res.boxes.xyxy
                conf = res.boxes.conf
                cls  = res.boxes.cls

                # Handle torch tensors vs numpy
                if hasattr(xyxy, "cpu"): xyxy = xyxy.cpu().numpy()
                if hasattr(conf, "cpu"):  conf  =  conf.cpu().numpy()
                if hasattr(cls, "cpu"):   cls   =   cls.cpu().numpy()

                # Collect filtered boxes per class
                cls_to_boxes = defaultdict(list)
                for i in range(len(cls)):
                    cls_name = names[int(cls[i])]
                    box = xyxy[i].tolist()
                    c = float(conf[i])
                    if box_ok(det_type, box, c):
                        cls_to_boxes[cls_name].append(box + [c])

                # Temporal smoothing
                for cls_name, boxes in cls_to_boxes.items():
                    stable = smoother.update_and_accept(det_type, cls_name, boxes)
                    if stable:
                        # Handle pedestrian alerts
                        if det_type == "pedestrian":
                            pedestrian_detected = True
                        
                        # Handle traffic signs (rate-limited)
                        elif det_type == "sign":
                            now = time.time()
                            if now - last_sign_update > 2.0:  # Update max every 2 seconds
                                if "speed" in cls_name.lower() or "limit" in cls_name.lower():
                                    sign_detected = ("speed_limit", "50", f"{frame_idx}m")
                                elif "stop" in cls_name.lower():
                                    sign_detected = ("stop", "", f"{frame_idx}m")
                                elif "yield" in cls_name.lower():
                                    sign_detected = ("yield", "", f"{frame_idx}m")
                                last_sign_update = now

            # Update pedestrian alert (edge-triggered)
            if pedestrian_detected and not pedestrian_active:
                update_alert_via_api("pedestrian", 1)
                pedestrian_active = True
                print("[ALERT] Pedestrian detected!")
            elif not pedestrian_detected and pedestrian_active:
                update_alert_via_api("pedestrian", 0)
                pedestrian_active = False
                print("[CLEAR] Pedestrian cleared")

            # Update traffic sign (if detected)
            if sign_detected:
                # if statements for new speed limit
                update_traffic_sign_via_api(*sign_detected)
                print(f"[SIGN] {sign_detected[0]} detected")

            # Telemetry
            frame_idx += 1
            k += 1

            loop_ms = (time.perf_counter() - loop_start) * 1000.0
            now = time.time()
            if now - last_print > 1.0:
                det_flag, det_summary = summarize_detections(last_results)
                eff_fps = 1000.0 / max(loop_ms, 1.0)
                print(
                    f"Frame {frame_idx} | model {infer_ms:.0f}ms | "
                    f"loop {loop_ms:.0f}ms | FPS={eff_fps:.1f} | "
                    f"{('Detected: ' + det_summary) if det_flag else 'Detected: none'}"
                )
                last_print = now

            # Pace only if ahead of target
            if TARGET_FPS:
                budget = 1.0 / TARGET_FPS
                spent = (time.perf_counter() - loop_start)
                if spent < budget:
                    time.sleep(budget - spent)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        # Clear alerts on exit
        if pedestrian_active:
            update_alert_via_api("pedestrian", 0)
        grab.release()
        cv2.destroyAllWindows()
        print("Clean shutdown.")

if __name__ == "__main__":
    main()
