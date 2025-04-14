import cv2
import numpy as np
from picamera2 import Picamera2

# Initialize cameras
camera1 = Picamera2(0)  # OV5647 (right side)
camera2 = Picamera2(1)  # IMX219 (left side) 

# Configure cameras
camera1.configure(camera1.create_preview_configuration(main={"size": (640, 480)}))
camera2.configure(camera2.create_preview_configuration(main={"size": (640, 480)}))

# Start the cameras
camera1.start()
camera2.start()

def preprocess_for_ov5647(frame):
    # Increase contrast and brightness
    alpha = 1.8  # Contrast control (1.0-3.0)
    beta = 20    # Brightness control (0-100)

    enhanced = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

    # Optional: apply sharpening
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)

    return sharpened

def detect_vertical_lines(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=50, maxLineGap=10)

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            if 45 < abs(angle) < 150:
                return True, lines
    return False, None

while True:
    frame1 = camera1.capture_array()  # Left camera (IMX219)
    frame2 = camera2.capture_array()  # Right camera (OV5647)

    # Preprocess OV5647 frame to boost its clarity
    frame2_processed = preprocess_for_ov5647(frame2)

    # Detect lines
    detected1, lines1 = detect_vertical_lines(frame1)
    detected2, lines2 = detect_vertical_lines(frame2_processed)

    # Decide alert text
    if detected1:
        alert_text = "Lane Detected! - Right Side"
    elif detected2:
        alert_text = "Lane Detected! - Left Side"
    else:
        alert_text = "Nothing Detected"

    # Display the text
    cv2.putText(frame1, alert_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(frame2, alert_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Show frames
    cv2.imshow("Camera 1 (Right - OV5647)", frame1)
    cv2.imshow("Camera 2 (Left - IMX219)", frame2)

    # Exit condition
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()

