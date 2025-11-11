from gpiozero import DistanceSensor
import tkinter as tk
from tkinter import font
import requests
import time
import gpiod
import time

# -----------------------------
# GPIO lines (BCM numbering)
RELAY_LINE = 25
STEERING_LINE = 18
THROTTLE_LINE = 19

CHIP = "/dev/gpiochip0"  # default GPIO chip

# Initialize chip and lines
chip = gpiod.Chip(CHIP)

relay = chip.get_line(RELAY_LINE)
steering = chip.get_line(STEERING_LINE)
throttle = chip.get_line(THROTTLE_LINE)

# Request lines as output
relay.request(consumer="relay", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
steering.request(consumer="steering", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
throttle.request(consumer="throttle", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

# Helper to generate a single PWM pulse
def pwm_pulse(line, pulse_ms):
    line.set_value(1)
    time.sleep(pulse_ms / 1000.0)
    line.set_value(0)

# Helper for neutral pulse (~1.5 ms)
def send_neutral():
    for _ in range(50):  # 50 pulses = ~1 second at 50Hz
        pwm_pulse(steering, 1.5)
        pwm_pulse(throttle, 1.5)
        time.sleep(0.0185)  # remaining time in 20ms period

# -----------------------------
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
sensor_left = DistanceSensor(echo=16, trigger=12, max_distance=2)
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
# Distance measurement
# -----------------------------
def measure_distance():
    global last_blindspot_state, last_collision_state
    
    distance_left = int(sensor_left.distance * 100)  # Convert to cm
    distance_right = int(sensor_right.distance * 100)
    distance_back = int(sensor_back.distance * 100)
    distance_front = int(sensor_front.distance * 100)

    blindspot_detected = False
    collision_detected = False

    # Check sensors in priority order
    if distance_front < 101:
        distance_label.config(
            fg="red",
            text=f"Warning: Object In Front\nVehicle {distance_front} cm away"
        )
        collision_detected = True
        relay.set_value(0)
        relay.set_value(1)
        time.sleep(0.018)
        send_neutral()
        relay.set_value(0)

    elif distance_left < 101:
        distance_label.config(
            fg="red",
            text=f"Left Blindspot Warning:\nVehicle is {distance_left} cm away!\n"
        )
        blindspot_detected = True

    elif distance_right < 101:
        distance_label.config(
            fg="red",
            text=f"Right Blind Spot Warning:\nVehicle is {distance_right} cm away!\n"
        )
        blindspot_detected = True

    elif distance_back < 101:
        distance_label.config(
            fg="red",
            text=f"Warning: Object Behind\nVehicle {distance_back} cm away\n"
        )
        collision_detected = True

    else:
        distance_label.config(
            fg="blue",
            text="All Sides Clear\nNo Obstacles Detected"
        )

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
