from picamera2 import Picamera2
#installation complete
import cv2
#installation complete
import numpy as np
import threading

# Initialize both cameras
picam1 = Picamera2(0)  # IMX219
picam2 = Picamera2(1)  # OV5647

# Configure both cameras
picam1.configure(picam1.create_preview_configuration(main={"size": (640, 480)}))
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))

# Start both cameras
picam1.start()
picam2.start()

def detect_vertical_lines(camera, window_name):
    while True:
        # Capture frame
        frame = camera.capture_array()

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Detect lines using Hough Transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)

        vertical_line_detected = False


    # 3/4/25: Refine this algorithm right here, understand how it works and perfect it based off of the lane
        if lines is not None:
            for rho, theta in lines[:, 0]:
                if 85 < np.degrees(theta) < 95:  # Filter vertical lines
                    vertical_line_detected = True
                    a, b = np.cos(theta), np.sin(theta)
                    x0, y0 = a * rho, b * rho
                    x1, y1 = int(x0 + 1000 * (-b)), int(y0 + 1000 * (a))
                    x2, y2 = int(x0 - 1000 * (-b)), int(y0 - 1000 * (a))
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    #deep dive

        # Display detection status
        if vertical_line_detected:
            cv2.putText(frame, "Vertical Line Detected", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
# Add conditionals for when the car is not detecting anything, keep looking until something is found

        # Show output
        cv2.imshow(window_name, frame)
    #figure out why this is messing up, camera one is sometimes a back screen. Not the biggest deal in the world as long as it can detect lines
        cv2.imshow(f'Edges {window_name}', edges)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

#Testing once perfected: try horizontal and diagnoal lines to make sure it is perfected
# all packages are installed as is, please do not corrupt the pi by trying to add more

# Run both cameras in separate threads
thread1 = threading.Thread(target=detect_vertical_lines, args=(picam1, "Camera 1 (OV5647)"))
thread2 = threading.Thread(target=detect_vertical_lines, args=(picam2, "Camera 2 (IMX219)"))

thread1.start()
thread2.start()

# This will eventually be an infinite loop, for now it is here purely for debugging purposes
thread1.join()
thread2.join()

cv2.destroyAllWindows()
