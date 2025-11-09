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
import re  # for speed limit extraction

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
    except Exception:
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
    try:
        state = requests.get(f"{BASE_URL}/get_state", timeout=API_TIMEOUT).json()
    except Exception:
        print("⚠️ Could not reach state API to update speed limit")
        return False

    for sign in state.get('signs', []):
        if sign.get('type') == 'speed_limit':
            try:
                requests.post(
                    f"{BASE_URL}/update_sign",
                    json={
                        "id": sign['id'],
                        "type": "speed_limit",
                        "value": str(new_limit),
                        "distance": "50m"
                    },
                    timeout=API_TIMEOUT
                )
                print(f"🔄 Speed limit set to {new_limit} MPH")
                return True
            except Exception:
                print("⚠️ Failed to update sign through API")
                return False

    print("⚠️ Could not find speed limit sign")
    return False


# =========================
# Tunables
# =========================
STREAM_URL = "http://127.0.0.1:8090/?action=stream"
IMGSZ = 384
CONF_DEFAULT, IOU = 0.25, 0.45
MAX_DET = 12

# False-positive controls
TH_CONF = {
    "light": 0.40,
    "sign": 0.45,
    "pedestrian": 0.35,
}
MIN_AREA = {
    "light": 900,
    "sign": 1200,
    "pedestrian": 1600,
}
ASPECT_LIMITS = {
    "light": (0.5, 3.0),
    "sign": (0.5, 2.5),
    "pedestrian": (1.3, 4.5),
}

# Temporal smoothing
WINDOW = 5
PERSIST_HITS = 2
IOU_MATCH = 0.30


def make_road_roi(size):
    """Define lower 2/3 of frame as ROI mask."""
    m = np.zeros((size, size), np.uint8)
    m[size // 3:, :] = 1
    return m


ROI_MASK = make_road_roi(IMGSZ)
TARGET_FPS = 10

# Optimize threading on Pi
cv2.setNumThreads(1)
torch.set_num_threads(4)
torch.set_num_interop_threads(1)

# =========================
# Load models
# =========================
merged_ls_model = YOLO("/home/sarsa/Traffic_Lights_Signs_Merged.pt")
ped_model = YOLO("/home/sarsa/pedestrian_detection.pt")

# =========================
# State tracking
# =========================
pedestrian_active = False
last_sign_update = 0


# =========================
# Helper functions
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
    if inter <= 0:
        return 0.0
    area_a = (xa2 - xa1) * (ya2 - ya1)
    area_b = (xb2 - xb1) * (yb2 - yb1)
    return inter / max(area_a + area_b - inter, 1e-6)


def box_ok(det_type, box, conf):
    x1, y1, x2, y2 = map(int, box)
    w, h = max(1, x2 - x1), max(1, y2 - y1)
    area = w * h
    if conf < TH_CONF[det_type]:
        return False
    if area < MIN_AREA[det_type]:
        return False
    ratio = h / float(w)
    rmin, rmax = ASPECT_LIMITS[det_type]
    if not (rmin <= ratio <= rmax):
        return False
    if ROI_MASK is not None:
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        if not (0 <= cx < ROI_MASK.shape[1] and 0 <= cy < ROI_MASK.shape[0] and ROI_MASK[cy, cx] == 1):
            return False
    return True


def extract_speed_limit(cls_name: str, mph_min: int = 5, mph_max: int = 90):
    s = cls_name.lower()
    m = re.search(r'(\d{2,3})\s*mph', s)
    if not m:
        m = re.search(r'(\d{2,3})', s)
    if not m:
        return None
    val = int(m.group(1))
    if mph_min <= val <= mph_max:
        return val
    return None


def is_light_class(name: str) -> bool:
    s = name.lower()
    if "traffic_light" in s or "tl_" in s:
        return True
    if "light" in s and any(col in s for col in ("red", "green", "yellow", "amber")):
        return True
    light_tokens = {
        "red", "green", "yellow", "amber",
        "light_red", "light_green", "light_yellow",
        "trafficlight", "traffic_light"
    }
    return s in light_tokens


def effective_type_for(name: str) -> str:
    return "light" if is_light_class(name) else "sign"


class TemporalSmoother:
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
    for det_key, res in results_dict.items():
        if res is None or res.boxes is None or len(res.boxes) == 0:
            continue
        names = res.names
        cls_list = res.boxes.cls.tolist() if hasattr(res.boxes.cls, "tolist") else list(res.boxes.cls)
        for cls_id in cls_list:
            cls_name = names[int(cls_id)]
            det_type = effective_type_for(cls_name) if det_key == "merged" else "pedestrian"
            per_type[det_type][cls_name] += 1
            detected_any = True
    if not detected_any:
        return False, "none"
    segments = []
    for det_type, counter in per_type.items():
        parts = [f"{cls}({n})" for cls, n in counter.most_common()]
        segments.append(f"{det_type}:" + ",".join(parts))
    return True, " | ".join(segments)


# =========================
# Frame grabber
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
    last_results = {"merged": None, "pedestrian": None}

    try:
        while True:
            loop_start = time.perf_counter()
            frame = grab.read()
            if frame is None:
                time.sleep(0.002)
                continue

            # Round-robin: 2 models
            sel = k % 2
            t0 = time.perf_counter()
            if sel == 0:
                last_results["merged"] = yolo_infer(merged_ls_model, frame)
            else:
                last_results["pedestrian"] = yolo_infer(ped_model, frame)
            infer_ms = (time.perf_counter() - t0) * 1000.0

            pedestrian_detected = False

            for det_key, res in last_results.items():
                if res is None or res.boxes is None or len(res.boxes) == 0:
                    continue

                names = res.names
                xyxy = res.boxes.xyxy
                conf = res.boxes.conf
                cls = res.boxes.cls

                if hasattr(xyxy, "cpu"): xyxy = xyxy.cpu().numpy()
                if hasattr(conf, "cpu"): conf = conf.cpu().numpy()
                if hasattr(cls, "cpu"): cls = cls.cpu().numpy()

                if det_key == "merged":
                    buckets = defaultdict(lambda: defaultdict(list))
                    for i in range(len(cls)):
                        cls_name = names[int(cls[i])]
                        eff_type = effective_type_for(cls_name)
                        box = xyxy[i].tolist()
                        c = float(conf[i])
                        if box_ok(eff_type, box, c):
                            buckets[eff_type][cls_name].append(box + [c])

                    for eff_type, cls_map in buckets.items():
                        for cls_name, boxes in cls_map.items():
                            stable = smoother.update_and_accept(eff_type, cls_name, boxes)
                            if not stable:
                                continue
                            if eff_type == "sign":
                                now = time.time()
                                if now - last_sign_update > 2.0:
                                    cls_lower = cls_name.lower()
                                    if "speed" in cls_lower or "limit" in cls_lower:
                                        limit_val = extract_speed_limit(cls_lower) or 50
                                        update_traffic_sign_via_api("speed_limit", str(limit_val), f"{frame_idx}m")
                                        update_speed_limit(limit_val)
                                        print(f"[SIGN] speed_limit {limit_val} MPH detected & updated")
                                    else:
                                        update_traffic_sign_via_api(cls_lower, "", f"{frame_idx}m")
                                        print(f"[SIGN] {cls_lower} detected (generic)")
                                    last_sign_update = now

                else:  # pedestrian
                    cls_to_boxes = defaultdict(list)
                    for i in range(len(cls)):
                        cls_name = names[int(cls[i])]
                        box = xyxy[i].tolist()
                        c = float(conf[i])
                        if box_ok("pedestrian", box, c):
                            cls_to_boxes[cls_name].append(box + [c])

                    for cls_name, boxes in cls_to_boxes.items():
                        stable = smoother.update_and_accept("pedestrian", cls_name, boxes)
                        if stable:
                            pedestrian_detected = True

            if pedestrian_detected and not pedestrian_active:
                update_alert_via_api("pedestrian", 1)
                pedestrian_active = True
                print("[ALERT] Pedestrian detected!")
            elif not pedestrian_detected and pedestrian_active:
                update_alert_via_api("pedestrian", 0)
                pedestrian_active = False
                print("[CLEAR] Pedestrian cleared")

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

            if TARGET_FPS:
                budget = 1.0 / TARGET_FPS
                spent = (time.perf_counter() - loop_start)
                if spent < budget:
                    time.sleep(budget - spent)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        if pedestrian_active:
            update_alert_via_api("pedestrian", 0)
        grab.release()
        cv2.destroyAllWindows()
        print("Clean shutdown.")


if __name__ == "__main__":
    main()
