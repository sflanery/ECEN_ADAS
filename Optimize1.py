import cv2, time, threading, numpy as np
from collections import deque
from ultralytics import YOLO

# --- Settings you can play with ---
STREAM_URL = "http://127.0.0.1:8090/?action=stream"
IMGSZ      = 416     # try 384/416/512
CONF       = 0.25
IOU        = 0.45
MAX_DET    = 10
TARGET_FPS = 10      # budget your loop for ~10 fps

# Optional: limit OpenCV threads on Pi to avoid contention
cv2.setNumThreads(1)

# --- Load models (use your actual paths) ---
light_model = YOLO("/home/sarsa/Traffic_lights_detection.pt")
sign_model  = YOLO("/home/sarsa/new_traffic_signs.pt")
ped_model   = YOLO("/home/sarsa/pedestrian_detection.pt")

# If you only need some classes, you can predefine them (example; adjust to your model's class indices)
CLASSES_SIGN = None  # e.g., [0, 1, 2]  # set to None to keep all

# --- Threaded frame grabber: always keep only the latest frame ---
class FrameGrabber:
    def __init__(self, src):
        self.cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open stream")
        self.q = deque(maxlen=1)
        self.running = True
        self.t = threading.Thread(target=self._loop, daemon=True)
        self.t.start()

    def _loop(self):
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.02)
                continue
            # Some MJPEG feeds are gray; normalize to 3-ch
            if frame.ndim == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            self.q.append(frame)

    def read(self):
        return self.q[-1] if self.q else None

    def release(self):
        self.running = False
        self.t.join(timeout=1.0)
        self.cap.release()

def letterbox_resize(image, size):
    """Resize & pad to (size, size) while keeping aspect ratio."""
    h, w = image.shape[:2]
    scale = min(size / h, size / w)
    nh, nw = int(h * scale), int(w * scale)
    resized = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_LINEAR)
    canvas = np.zeros((size, size, 3), dtype=np.uint8)
    top = (size - nh) // 2
    left = (size - nw) // 2
    canvas[top:top+nh, left:left+nw] = resized
    return canvas

def run_once(model, frame, classes=None):
    # Pre-resize to reduce model’s work; Ultralytics accepts BGR uint8
    inp = letterbox_resize(frame, IMGSZ)
    r = model.predict(
        inp,
        device="cpu",
        imgsz=IMGSZ,
        conf=CONF,
        iou=IOU,
        max_det=MAX_DET,
        classes=classes,
        verbose=False
    )[0]
    return r

def main():
    grab = FrameGrabber(STREAM_URL)
    print("Stream opened. Press Ctrl+C to stop.")
    last_print = 0
    frame_count = 0

    try:
        while True:
            start = time.perf_counter()
            frame = grab.read()
            if frame is None:
                time.sleep(0.01)
                continue

            t0 = time.perf_counter()
            # --- Run the three models (you can stagger or skip to save time) ---
            # Option A: run all three every frame (heavier)
            light_r = run_once(light_model, frame, classes=None)
            sign_r  = run_once(sign_model,  frame, classes=CLASSES_SIGN)
            ped_r   = run_once(ped_model,   frame, classes=None)
            t1 = time.perf_counter()

            # Example: if too slow, only run pedestrians every 2nd frame:
            # if frame_count % 2 == 0: ped_r = run_once(ped_model, frame)

            # ---- Example stats to see where time goes ----
            loop_ms = (time.perf_counter() - start) * 1000
            infer_ms = (t1 - t0) * 1000
            if time.time() - last_print > 1.0:
                print(f"Loop: {loop_ms:.1f} ms  (Inference: {infer_ms:.1f} ms)  FPS≈{1000.0/max(loop_ms,1):.1f}")
                last_print = time.time()

            frame_count += 1

            # --- simple pacing to avoid thrashing CPU (optional) ---
            budget = 1.0 / TARGET_FPS
            spent = time.perf_counter() - start
            if spent < budget:
                time.sleep(budget - spent)

    except KeyboardInterrupt:
        pass
    finally:
        grab.release()

if __name__ == "__main__":
    main()
