import cv2
import numpy as np
from picamera2 import Picamera2
import requests
import gpiod
import time

# -----------------------------
# GPIO Setup - Request only when needed
# -----------------------------
CHIP = "/dev/gpiochip0"
RELAY_LINE = 25
STEERING_RIGHT = 18
STEERING_LEFT = 12

def get_gpio_lines():
    """Request GPIO lines - call this only when needed"""
    chip = gpiod.Chip(CHIP)
    relay = chip.get_line(RELAY_LINE)
    right = chip.get_line(STEERING_RIGHT)
    left = chip.get_line(STEERING_LEFT)
    
    relay.request(consumer="lane_relay", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
    right.request(consumer="lane_right", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
    left.request(consumer="lane_left", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
    
    return chip, relay, right, left

def release_gpio_lines(chip, relay, right, left):
    """Release GPIO lines after use"""
    try:
        relay.release()
        right.release()
        left.release()
        chip.close()
    except Exception:
        pass

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

def correct_steering_left():
    """Request GPIO, correct left, release GPIO"""
    try:
        chip, relay, right, left = get_gpio_lines()
        relay.set_value(1)
        #send_pwm(steering, 1.6, 0.35)
        time.sleep(0.028)
        relay.set_value(0)
        last_collision_trigger = False
        #steering.set_value(0)
        #throttle.set_value(0)
        time.sleep(0.028)
        release_gpio_lines(chip, relay, right, left)
    except Exception:
        pass  # GPIO in use by another process
         
def correct_steering_right():
    """Request GPIO, correct right, release GPIO"""
    try:
        chip, relay, right, left = get_gpio_lines()
        relay.set_value(1)
        #send_pwm(steering, 1.4, 0.35)
        time.sleep(0.028)
        relay.set_value(0)
        last_collision_trigger = False
        #steering.set_value(0)
        #throttle.set_value(0)
        time.sleep(0.028)
        release_gpio_lines(chip, relay, right, left)
    except Exception:
        pass  # GPIO in use by another process

# -----------------------------
# API Configuration
# -----------------------------
BASE_URL = "http://localhost:8080"

def update_lane_departure_via_api(detected):
    """Update laneDeparture alert via Flask API."""
    try:
        requests.post(
            f"{BASE_URL}/update_alert",
            json={"type": "laneDeparture", "status": 1 if detected else 0},
            timeout=1
        )
    except Exception:
        pass  # Silent fail

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

        # LEFT lane departure → correct with temporary GPIO access
        if detected_left:
            if not lane_correction_trigger:
                lane_correction_trigger = True
                correct_steering_left()

        # RIGHT lane departure → correct with temporary GPIO access
        elif detected_right:
            if not lane_correction_trigger:
                lane_correction_trigger = True
                correct_steering_right()

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

        # Display frames with simple 0/1 overlay
        text = f"Lane Detected: {int(detected)}"
        cv2.putText(frame1, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame2, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("Camera 1 (Right)", frame1)
        cv2.imshow("Camera 2 (Left)", frame2)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    pass
finally:
    update_lane_departure_via_api(False)
    cv2.destroyAllWindows()
    camera1.stop()
    camera2.stop()
