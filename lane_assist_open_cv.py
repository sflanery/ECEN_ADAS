import cv2
import numpy as np
from picamera2 import Picamera2

# Initialize cameras
camera1 = Picamera2(0)  # IMX219
camera2 = Picamera2(1)  # OV5647

# Configure cameras
camera1.configure(camera1.create_preview_configuration(main={"size": (640, 480)}))
camera2.configure(camera2.create_preview_configuration(main={"size": (640, 480)}))

# start the threads
camera1.start()
camera2.start()

#detect the vertical lines using cv2 image recognition
def detect_vertical_lines(frame):
#configuration stuff
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # convert to gray scale to limit external variables
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    # HoughLines detects lines in cv2
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=50, maxLineGap=10)
    
    # if there is a line present
    if lines is not None:
        for line in lines:
            # use polar coordinates to find the angle of the line relative to the frame
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            if abs(angle) > 80 and abs(angle) < 100:  # Near vertical
                # check if the angle conditions are true, adjust for margain of error
                return True, lines
    return False, None

while True:
    frame1 = camera1.capture_array()  # Get frame from camera 1
    frame2 = camera2.capture_array()  # Get frame from camera 2
  
    detected1, lines1 = detect_vertical_lines(frame1)
    detected2, lines2 = detect_vertical_lines(frame2)
    
# If a vertical line is detected
    if detected1:
        # eventually alert the user - robert's subsystem
        alert_text = "Vertical Line Detected! - OV5647"
    elif detected2:
        alert_text = "Vertical Line Detected! - IMX219"
    else:
        alert_text = "Nothing Detected"
    
    # Display alert text on frames
    # debugging windows
    cv2.putText(frame1, alert_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(frame2, alert_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # Show frames
    cv2.imshow("Camera 1", frame1)
    cv2.imshow("Camera 2", frame2)
    
    # when q is entered in the terminal, exit the program
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cv2.destroyAllWindows()
