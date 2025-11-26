import cv2
import numpy as np
from picamera2 import Picamera2
import requests

# lane assist
import gpiod
import time

CHIP = "/dev/gpiochip0"
RELAY_LINE = 25
STEERING_RIGHT = 18
STEERING_LEFT = 12

chip = gpiod.Chip(CHIP)
relay = chip.get_line(RELAY_LINE)
right = chip.get_line(STEERING_RIGHT)
left = chip.get_line(STEERING_LEFT)
#throttle = chip.get_line(THROTTLE_LINE)

right.request(consumer="right", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
relay.request(consumer="relay", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
left.request(consumer="left", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
#throttle.request(consumer="throttle", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

def send_pwm(line, pulse_width_ms, duration_s):
    period = 0.02  # 20 ms = 50 Hz
    end_time = time.time() + duration_s
    while time.time() < end_time:
        line.set_value(1)
        time.sleep(pulse_width_ms / 1000.0)
        line.set_value(0)
        time.sleep(period - pulse_width_ms / 1000.0)
def send_pwm_inverted(line, pulse_width_ms, duration_s):
    period = 0.02
    end_time = time.time() + duration_s
    while time.time() < end_time:
        line.set_value(0)  # invert
        time.sleep(pulse_width_ms / 1000.0)
        line.set_value(1)
        time.sleep(period - pulse_width_ms / 1000.0)
def move_steering_left(pulse_width_ms, duration_s):
    relay.set_value(1)               # Turn on relay
    send_pwm_inverted(left, pulse_width_ms, duration_s)
    relay.set_value(0)               # Turn off relay
    left.set_value(0)
         
def move_steering_right(pulse_width_ms, duration_s):
    relay.set_value(1)               # Turn on relay
    send_pwm(right, pulse_width_ms, duration_s)
    relay.set_value(0)               # Turn off relay
    right.set_value(0)
       

# -----------------------------
# API Configuration
# -----------------------------
BASE_URL = "http://localhost:8080"

def update_lane_departure_via_api(detected):
    """Update laneDeparture alert via Flask API."""
    try:
        response = requests.post(
            f"{BASE_URL}/update_alert",
            json={"type": "laneDeparture", "status": 1 if detected else 0},
            timeout=1
        )
        if response.status_code == 200:
            print(f"[API] Lane departure → {detected}")
        else:
            print(f"[API] Error: {response.status_code}")
    except Exception as e:
        print(f"[API] Failed to update: {e}")

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

def detect_vertical_lines(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=50, maxLineGap=10)
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            if 45 < abs(angle) < 150:
                return True
    return False

# -----------------------------
# State variables
# -----------------------------
lane_logged = False
lane_correction_trigger = False

# -----------------------------
# Main loop
# -----------------------------
try:
    while True:
        frame1 = camera1.capture_array()
        frame2 = camera2.capture_array()
        frame2_processed = preprocess_for_ov5647(frame2)

        detected = detect_vertical_lines(frame1) or detect_vertical_lines(frame2_processed)
        detected_left = detect_vertical_lines(frame2)
        detected_right = detect_vertical_lines(frame1)

        # LEFT lane departure → invert direction
        if detected_left:
            if not lane_correction_trigger:
                lane_correction_trigger = True
                relay.set_value(1)
                send_pwm_inverted(left, 1.6, .3)  # now goes left
                #move_steering_left(1.8, 0.3)
                time.sleep(0.018)
                relay.set_value(0)
                left.set_value(0)
               # right.set_value(0)

        # RIGHT lane departure → keep correct PWM
        elif detected_right:
            if not lane_correction_trigger:
                lane_correction_trigger = True
                relay.set_value(1)
                send_pwm(right, 1.2, .3)  # correct
                time.sleep(0.018)
                relay.set_value(0)
                right.set_value(0)
              #  left.set_value(0)

        # Reset the lane correction once no detection
        if not detected:
            lane_correction_trigger = False

        # API notifications
        if detected and not lane_logged:
            update_lane_departure_via_api(True)
            lane_logged = True
        elif not detected and lane_logged:
            update_lane_departure_via_api(False)
            lane_logged = False

        # Display frames
        text = f"Lane Detected: {int(detected)}"
        cv2.putText(frame1, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame2, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("Camera 1 (Right)", frame1)
        cv2.imshow("Camera 2 (Left)", frame2)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\n[INFO] Stopping lane assist...")
finally:
    # -----------------------------
    # Cleanup
    # -----------------------------
    update_lane_departure_via_api(False)
    cv2.destroyAllWindows()
    print("[INFO] Cleanup complete")
