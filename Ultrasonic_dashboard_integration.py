from gpiozero import DistanceSensor
import tkinter as tk
from tkinter import font
import requests
import time
import gpiod
import time

import gpiod
import time

CHIP = "/dev/gpiochip0"
RELAY_LINE = 25
STEERING_LINE = 18
THROTTLE_LINE = 19

chip = gpiod.Chip(CHIP)
relay = chip.get_line(RELAY_LINE)
steering = chip.get_line(STEERING_LINE)
throttle = chip.get_line(THROTTLE_LINE)

relay.request(consumer="relay", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
steering.request(consumer="steering", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
throttle.request(consumer="throttle", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

def send_pwm(line, pulse_width_ms, duration_s):
    """
    Continuously send PWM to a line.
    pulse_width_ms: 1.0 = full reverse, 1.5 = neutral, 2.0 = full forward
    duration_s: total duration to send PWM
    """
    period = 0.02  # 20 ms = 50 Hz
    end_time = time.time() + duration_s
    while time.time() < end_time:
        line.set_value(1)
        time.sleep(pulse_width_ms / 1000.0)
        line.set_value(0)
        time.sleep(period - pulse_width_ms / 1000.0)

# -----------------------------
# API Configuration
# -----------------------------
BASE_URL = "http://localhost:8080"

def update_alert_via_api(alert_type, status):
    """Update alert status via Flask API."""
    try:
        response = requests.post(
            f"{BASE_URL}/update_alert",
            json={"type": alert_type, "status": 1 if status else 0},
            timeout=1
        )
        if response.status_code == 200:
            print(f"[API] Updated {alert_type} → {status}")
        else:
            print(f"[API] Error: {response.status_code}")
    except Exception as e:
        print(f"[API] Failed to update: {e}")

# -----------------------------
# Sensor setup
# -----------------------------
sensor_right = DistanceSensor(echo=24, trigger=23, max_distance=2)
sensor_left = DistanceSensor(echo=16, trigger=26, max_distance=2)
sensor_back = DistanceSensor(echo=6, trigger=13, max_distance=2)
sensor_front = DistanceSensor(echo=17, trigger=27, max_distance=2)

# -----------------------------
# GUI setup
# -----------------------------
window = tk.Tk()
window.title("Vehicle Distance Monitoring System")
custom_font = font.Font(size=30)
window.geometry("800x400")

distance_label = tk.Label(window, text="Monitoring all sensors...", anchor='center', font=custom_font)
distance_label.pack(expand=True)

# -----------------------------
# State tracking to avoid redundant API calls
# -----------------------------
last_blindspot_state = None
last_collision_state = None

# -----------------------------
# NEW: Track if braking has already happened
# -----------------------------
last_collision_trigger = False

# -----------------------------
# Distance measurement
# -----------------------------
def measure_distance():
    global last_blindspot_state, last_collision_state
    global last_collision_trigger
    
    distance_left = int(sensor_left.distance * 100)  # Convert to cm
    distance_right = int(sensor_right.distance * 100)
    distance_back = int(sensor_back.distance * 100)
    distance_front = int(sensor_front.distance * 100)

    blindspot_detected = False
    collision_detected = False

    # FRONT COLLISION
    if distance_front < 101:
        distance_label.config(
            fg="red",
            text=f"Warning: Object In Front\nVehicle {distance_front} cm away"
        )
        collision_detected = True

        # ---- AUTOMATIC BRAKING (only once) ----
        if not last_collision_trigger:
            last_collision_trigger = True
            relay.set_value(1)
            send_pwm(steering, 1.5, .3)
            time.sleep(0.018)
            relay.set_value(0)
            steering.set_value(0)
            throttle.set_value(0)

    # BACK COLLISION
    elif distance_back < 51:
        distance_label.config(
            fg="red",
            text=f"Warning: Object Behind\nVehicle {distance_back} cm away\n"
        )
        collision_detected = True

        # ---- AUTOMATIC BRAKING (only once) ----
        if not last_collision_trigger:
            last_collision_trigger = True
            relay.set_value(1)
            send_pwm(steering, 1.5, 0.35)
            time.sleep(0.018)
            relay.set_value(0)
            steering.set_value(0)
            throttle.set_value(0)

    # LEFT BLINDSPOT
    elif distance_left < 101:
        distance_label.config(
            fg="red",
            text=f"Left Blindspot Warning:\nVehicle is {distance_left} cm away!\n"
        )
        blindspot_detected = True

    # RIGHT BLINDSPOT
    elif distance_right < 101:
        distance_label.config(
            fg="red",
            text=f"Right Blind Spot Warning:\nVehicle is {distance_right} cm away!\n"
        )
        blindspot_detected = True

    # ALL CLEAR → reset braking trigger
    else:
        distance_label.config(
            fg="blue",
            text="All Sides Clear\nNo Obstacles Detected"
        )
        last_collision_trigger = False   # <---- reset when object is gone

    # Only send API updates when state changes
    if blindspot_detected != last_blindspot_state:
        update_alert_via_api("blindSpot", blindspot_detected)
        last_blindspot_state = blindspot_detected

    if collision_detected != last_collision_state:
        update_alert_via_api("collision", collision_detected)
        last_collision_state = collision_detected

    window.after(500, measure_distance)  # Check every 0.5 sec

# -----------------------------
# Cleanup on exit
# -----------------------------
def on_closing():
    """Clear all alerts when closing window"""
    update_alert_via_api("blindSpot", False)
    update_alert_via_api("collision", False)
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)

# -----------------------------
# Start measuring
# -----------------------------
measure_distance()
window.mainloop()
