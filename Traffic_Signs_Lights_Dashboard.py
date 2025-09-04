from ultralytics import YOLO
import cv2, sqlite3, time

model = YOLO("runs/detect/train7/weights/Traffic_lights_detection.pt")
# model = YOLO("Traffic_signs_training/experiment_2/weights/Traffic_sign_detection.pt")

# Open the video capture
cap = cv2.VideoCapture(1)

# db file
conn = sqlite3.connect("dashboard.db")
cur = conn.cursor()

# clear everything from the table
cur.execute("DELETE FROM traffic_signs;")
# reset the counter
cur.execute("DELETE FROM traffic_signs WHERE id;")
conn.commit()

# counter for identifying the frame
frame_idx = 0
# if camera does not open exit
if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

while True:
    # ret = True, frame grabbed successfully
    # frame - numpy array in BGR color
    ret, frame = cap.read()
    if not ret:
        break

    # resize
    # frame = cv2.resize(frame, (500, 640))

    # pass numpy array to YOLO
    results = model(frame)
    r = results[0]

    if len(r.boxes) > 0:
        for cls_id in r.boxes.cls.tolist():  # get all detected class IDs
            cls_name = model.names[int(cls_id)] #cls_name = name of what was detected

    # draw rectangle
    # annotated_frame = results[0].plot()
    annotated_frame = r.plot()
    ts = time.time()
    # check if anything was detected
    if len(r.boxes) > 0: # len() says how many detections there was
        cur.execute("""
        INSERT INTO traffic_signs (type, value, distance, active) 
        VALUES (?,?,?,?)""", (cls_name, "50",  frame_idx, 1)) # 1 means detection
    else: # if there were no detections
        cur.execute("""
        INSERT INTO traffic_signs (type, value, distance, active)
        VALUES (?,?,?,?)""", ("none" , "50",  frame_idx, 0))
    conn.commit()

    # display the annotated frame
    cv2.imshow("Traffic Light/Sign Detection", annotated_frame)
    frame_idx += 1

    # break the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# release resources
cap.release()
cv2.destroyAllWindows()
conn.close()