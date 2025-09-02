import cv2
import numpy as np
from picamera2 import Picamera2
import sqlite3

# -----------------------------
# Database setup
# -----------------------------
conn = sqlite3.connect("dashboard.db")
cursor = conn.cursor()

# Ensure the laneDeparture column exists
try:
    cursor.execute("ALTER TABLE alerts ADD COLUMN laneDeparture INTEGER DEFAULT 0;")
except sqlite3.OperationalError:
    pass  # Column already exists

conn.commit()

def log_lane_departure(detected):
    """Logs lane detection as 1 (detected) or 0 (not detected)."""
    #NOTE: this is only for debugging purposes, this feature will need to be removed during full scale integration
    cursor.execute(
        "INSERT INTO alerts (laneDeparture) VALUES (?)",
        (1 if detected else 0,)
    )
    conn.commit()

# -----------------------------
# Camera setup
# -----------------------------
camera1 = Picamera2(0)  # Right side
camera2 = Picamera2(1)  # Left side

camera1.configure(camera1.create_preview_configuration(main={"size": (640, 480)}))
camera2.configure(camera2.create_preview_configuration(main={"size": (640, 480)}))

camera1.start()
camera2.start()

# -----------------------------
# Preprocessing and detection
# -----------------------------
def preprocess_for_ov5647(frame):
    alpha = 1.8  # Contrast
    beta = 20    # Brightness
    enhanced = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    return cv2.filter2D(enhanced, -1, kernel)
    # this increases sensitivity to account for the car moving so quickly

def detect_vertical_lines(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # detacts vertical lines using cv2 - already trained model
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=50, maxLineGap=10)
    # specified thickness
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # accounts for the fact that the angle that the car sees the lane will not always be perfectly vertical
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            if 45 < abs(angle) < 150:
                return True
                # specific angle tolerance
    return False
def log_lane_departure(detected):
    """Logs lane detection as 1 (detected) or 0 (not detected)."""
    cursor.execute(
        "INSERT INTO alerts (type, laneDeparture) VALUES (?, ?)",
        ("laneDeparture", 1 if detected else 0)
    )
    conn.commit()
# -----------------------------
# State variable to prevent repeated logging
# -----------------------------
lane_logged = False

# -----------------------------
# Main loop
# -----------------------------
while True:
    frame1 = camera1.capture_array()
    frame2 = camera2.capture_array()
    frame2_processed = preprocess_for_ov5647(frame2)

    detected = detect_vertical_lines(frame1) or detect_vertical_lines(frame2_processed)

    # Edge-triggered logging: log only when detection state changes
    # capturing changes for the database
    if detected and not lane_logged:
        log_lane_departure(True)
        lane_logged = True
    elif not detected and lane_logged:
        log_lane_departure(False)
        lane_logged = False

    # Display frames with simple 0/1 overlay
    text = f"Lane Detected: {int(detected)}"
    cv2.putText(frame1, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
    cv2.putText(frame2, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

    cv2.imshow("Camera 1 (Right)", frame1)
    cv2.imshow("Camera 2 (Left)", frame2)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# -----------------------------
# Cleanup
# -----------------------------
conn.close()
cv2.destroyAllWindows()


