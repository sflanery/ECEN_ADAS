from ultralytics import YOLO
import cv2, sqlite3, time

# ---------- Load models ----------
light_model = YOLO("/home/sarsa/Traffic_lights_detection.pt")
sign_model  = YOLO("/home/sarsa/Traffic_sign_detection.pt")
sign_model = YOLO("/home/sarsa/new_traffic_signs.pt")
ped_model   = YOLO("/home/sarsa/pedestrian_detection.pt")

# ---------- Video capture ----------
#cap = cv2.VideoCapture(0) #for some reason this must be 0 or 8
# tryin something
cap = cv2.VideoCapture("http://127.0.0.1:8090/?action=stream", cv2.CAP_FFMPEG)
if not cap.isOpened():
    print("Failed to open stream!")
else:
    print("Stream opened successfully!")

# ---------- Database ----------
from pathlib import Path

# Assuming your Python script is located somewhere relative to the dashboard.db file
# This gets the directory of the current Python file (__file__)
base_dir = Path(__file__).parent.resolve()

# Append relative path to your database file from this script's directory
db_path = base_dir / 'dashtest_new/dashtest/backend_server/dashboard.db'

# Connect to the SQLite database by converting Path to str
conn = sqlite3.connect(str(db_path))

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