from ultralytics import YOLO
import cv2, sqlite3, time

# Load all three models
light_model = YOLO("runs/detect/train7/weights/Traffic_lights_detection.pt")
sign_model = YOLO("Traffic_signs_training/experiment_2/weights/Traffic_sign_detection.pt")
pedestrian_model = YOLO("pedestrian_detection1.pt")

# Open the video capture
cap = cv2.VideoCapture(0)

# db file
conn = sqlite3.connect("dashboard.db")
cur = conn.cursor()
cur.execute("DELETE FROM traffic_signs;")
cur.execute("DELETE FROM traffic_signs WHERE id;")
conn.commit()

frame_idx = 0
if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run all three models
    light_results = light_model(frame)[0]
    sign_results = sign_model(frame)[0]
    pedestrian_results = pedestrian_model(frame)[0]

    # Annotate frame step by step
    annotated_frame = light_results.plot()
    sign_results.orig_img = annotated_frame
    annotated_frame = sign_results.plot()
    pedestrian_results.orig_img = annotated_frame
    annotated_frame = pedestrian_results.plot()

    # Log detections
    detected = False
    for r, model_type in [(light_results, "light"), (sign_results, "sign"), (pedestrian_results, "pedestrian")]:
        if len(r.boxes) > 0:
            for cls_id in r.boxes.cls.tolist():
                cls_name = r.names[int(cls_id)]
                cur.execute("""
                INSERT INTO traffic_signs (type, value, distance, active) 
                VALUES (?,?,?,?)""", (f"{model_type}:{cls_name}", "50", frame_idx, 1))
                detected = True

    if not detected:
        cur.execute("""
        INSERT INTO traffic_signs (type, value, distance, active)
        VALUES (?,?,?,?)""", ("none", "50", frame_idx, 0))

    conn.commit()

    # Show the annotated frame
    cv2.imshow("Traffic Detection", annotated_frame)
    frame_idx += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
conn.close()
