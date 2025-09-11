from ultralytics import YOLO
import cv2, sqlite3, time

# ---------- Load models ----------
light_model = YOLO("runs/detect/train7/weights/Traffic_lights_detection.pt")
sign_model  = YOLO("Traffic_signs_training/experiment_2/weights/Traffic_sign_detection.pt")
ped_model   = YOLO("pedestrian_detection1.pt")

# ---------- Video capture ----------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open video stream.")
    raise SystemExit

# ---------- Database ----------
conn = sqlite3.connect("dashboard.db")
cur  = conn.cursor()

# Clear table (and optionally reset AUTOINCREMENT counter)
cur.execute("DELETE FROM traffic_signs;")
# Optional: reset autoincrement (uncomment if needed)
# cur.execute("DELETE FROM sqlite_sequence WHERE name='traffic_signs';")
conn.commit()

frame_idx = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run all three models
        light_results = light_model(frame)[0]
        sign_results  = sign_model(frame)[0]
        ped_results   = ped_model(frame)[0]

        # Log detections
        detected = False
        for r, model_type in [
            (light_results, "light"),
            (sign_results, "sign"),
            (ped_results, "pedestrian")
        ]:
            if r.boxes is not None and len(r.boxes) > 0:
                for cls_id in r.boxes.cls.tolist():
                    cls_name = r.names[int(cls_id)]
                    cur.execute("""
                        INSERT INTO traffic_signs (type, value, distance, active)
                        VALUES (?,?,?,?)
                    """, (f"{model_type}:{cls_name}", "50", frame_idx, 1))
                detected = True

        if not detected:
            cur.execute("""
                INSERT INTO traffic_signs (type, value, distance, active)
                VALUES (?,?,?,?)
            """, ("none", "50", frame_idx, 0))

        conn.commit()
        frame_idx += 1

        # ---- Quit if 'q' is pressed ----
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    # Graceful exit on Ctrl+C
    pass
finally:
    cap.release()
    cv2.destroyAllWindows()  # needed for waitKey cleanup
    conn.close()
