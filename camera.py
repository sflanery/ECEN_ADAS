from ultralytics import YOLO
import cv2

# path to model
model = YOLO("Pedestrian_models/pedestrian1/weights/pedestrian_detection.pt")

#default camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # if window resize is needed
    # frame = cv2.resize(frame, (640, 640))

    # perform inference with the model on the current frame
    results = model(frame)

    # annotate the frame with detection results
    annotated_frame = results[0].plot()

    # display the frame
    cv2.imshow("person", annotated_frame)

    # close camera if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()