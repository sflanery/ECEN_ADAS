from gpiozero import DistanceSensor
import tkinter as tk
from tkinter import font
import requests
import time

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
# Sensor setup (right ultrasonic)
# -----------------------------
sensor_right = DistanceSensor(echo=24, trigger=23, max_distance=2)

# -----------------------------
# GUI setup
# -----------------------------
window = tk.Tk()
window.title("Right Ultrasonic Sensor Test")
custom_font = font.Font(size=30)
window.geometry("800x400")

distance_label = tk.Label(window, text="Measuring right sensor...", anchor='center', font=custom_font)
distance_label.pack(expand=True)

# -----------------------------
# Distance measurement
# -----------------------------
last_alert_state = None

def measure_distance():
    global last_alert_state
    
    distance_right = int(sensor_right.distance * 100)  # Convert to cm

    if distance_right < 101:
        distance_label.config(
            fg="red",
            text=f"Right Blind Spot Warning:\nVehicle is {distance_right} cm away!\n"
        )
        # Only send update if state changed
        if last_alert_state != True:
            update_alert_via_api("blindSpot", True)
            last_alert_state = True
    else:
        distance_label.config(
            fg="blue",
            text=f"Right Side Clear\n{distance_right} cm"
        )
        # Only send update if state changed
        if last_alert_state != False:
            update_alert_via_api("blindSpot", False)
            last_alert_state = False

    window.after(500, measure_distance)  # Check every 0.5 sec

# -----------------------------
# Cleanup on exit
# -----------------------------
def on_closing():
    """Clear alert when closing window"""
    update_alert_via_api("blindSpot", False)
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)

# -----------------------------
# Start measuring
# -----------------------------
measure_distance()
window.mainloop()
