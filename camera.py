from ultralytics import YOLO
import cv2
import threading

# Load YOLOv8n model for speed on Raspberry Pi
model = YOLO("Traffic_lights_detection.pt")  # tiny model

# MJPG-Streamer URL
stream_url = "http://127.0.0.1:8080/?action=stream"
cap = cv2.VideoCapture(stream_url)

if not cap.isOpened():
    print("Error: Cannot open video stream.")
    exit()

# Shared frame and lock
frame = None
lock = threading.Lock()
running = True

# Thread to continuously grab frames
def grab_frames():
    global frame, running
    while running:
        ret, f = cap.read()
        if not ret:
            continue
        with lock:
            frame = cv2.resize(f, (320, 240))  # resize for speed

# Start frame grabbing thread
thread = threading.Thread(target=grab_frames)
thread.start()

# Main loop: run YOLO inference
last_annotated = None
while True:
    with lock:
        if frame is None:
            continue
        current_frame = frame.copy()

    # Run YOLO inference
    results = model.predict(current_frame, conf=0.3, verbose=False)
    annotated = results[0].plot()
    last_annotated = annotated

    # Display annotated frame
    cv2.imshow("YOLO Detection", last_annotated)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        running = False
        break

# Cleanup
thread.join()
cap.release()
cv2.destroyAllWindows()

