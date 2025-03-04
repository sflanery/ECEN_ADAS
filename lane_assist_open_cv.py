import cv2
import numpy as np
from picamera2 import Picamera2

# Initialize cameras
camera1 = Picamera2(0)  # IMX219
camera2 = Picamera2(1)  # OV5647

# Configure cameras
camera1.configure(camera1.create_preview_configuration(main={"size": (640, 480)}))
camera2.configure(camera2.create_preview_configuration(main={"size": (640, 480)}))

camera1.start()
camera2.start()

def detect_vertical_lines(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=50, maxLineGap=10)
    
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            if abs(angle) > 80 and abs(angle) < 100:  # Near vertical
                return True, lines
    return False, None

while True:
    frame1 = camera1.capture_array()  # Get frame from camera 1
    frame2 = camera2.capture_array()  # Get frame from camera 2
    
    detected1, lines1 = detect_vertical_lines(frame1)
    detected2, lines2 = detect_vertical_lines(frame2)
    
    if detected1 or detected2:
        alert_text = "Vertical Line Detected!"
    else:
        alert_text = "Nothing Detected"
    
    # Display alert text on frames
    cv2.putText(frame1, alert_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(frame2, alert_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # Show frames
    cv2.imshow("Camera 1", frame1)
    cv2.imshow("Camera 2", frame2)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cv2.destroyAllWindows()
thread2.join()

cv2.destroyAllWindows()
