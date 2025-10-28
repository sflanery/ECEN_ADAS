from gpiozero import DistanceSensor
import tkinter as tk
from tkinter import font
import requests

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
sensor_back = DistanceSensor(echo=17, trigger=27, max_distance=2)
sensor_front = DistanceSensor(echo=6, trigger=13, max_distance=2)

# -----------------------------
# GUI setup
# -----------------------------
window = tk.Tk()
window.title("Distance Measurement")
custom_font = font.Font(size=30)
window.geometry("800x400")

distance_label = tk.Label(window, text="Distance: ", anchor='center', font=custom_font)
distance_label.pack()

# -----------------------------
# State tracking to avoid redundant API calls
# -----------------------------
last_blindspot_state = None
last_collision_state = None

# -----------------------------
# Distance measurement
# -----------------------------
def measure_distance():
    """Measures distances and updates the label accordingly."""
    global last_blindspot_state, last_collision_state
    
    distance_left = int(sensor_left.distance * 100)
    distance_right = int(sensor_right.distance * 100)
    distance_back = int(sensor_back.distance * 100)
    distance_front = int(sensor_front.distance * 100)

    blindspot_detected = False
    collision_detected = False

    if distance_left < 101:
        distance_label.config(fg="red", text=f"Left Blindspot Warning:\nVehicle is {distance_left} cm away!\n")
        blindspot_detected = True

    elif distance_right < 101:
        distance_label.config(fg="red", text=f"Right Blind Spot Warning:\nVehicle is {distance_right} cm away!\n")
        blindspot_detected = True

    elif distance_back < 101:
        distance_label.config(fg="red", text=f"Warning: Object Behind\nVehicle {distance_back} cm away\n")
        collision_detected = True

    elif distance_front < 201:
        distance_label.config(fg="red", text=f"Warning: Object In Front\nVehicle {distance_front} cm away")
        collision_detected = True

    else:
        distance_label.config(fg="blue", text="Nothing Detected")

    # Edge-triggered updates: only send API calls when state changes
    if blindspot_detected != last_blindspot_state:
        update_alert_via_api("blindSpot", blindspot_detected)
        last_blindspot_state = blindspot_detected

    if collision_detected != last_collision_state:
        update_alert_via_api("collision", collision_detected)
        last_
