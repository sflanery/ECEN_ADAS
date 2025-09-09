from gpiozero import DistanceSensor  # Import DistanceSensor class
import tkinter as tk  # Import tkinter for GUI
from tkinter import font  # Import font module from tkinter
import sqlite3 # to read database

# -----------------------------
# Database setup
# -----------------------------
conn = sqlite3.connect("dashboard.db")
cursor = conn.cursor()

# Ensure the blindSpot and collision columns exist
try:
    cursor.execute("ALTER TABLE alerts ADD COLUMN collision INTEGER DEFAULT 0;")
    cursor.execute("ALTER TABLE alerts ADD COLUMN blindSpot INTEGER DEFAULT 0;")
except sqlite3.OperationalError:
    pass  # Columns already exist

conn.commit()

# -----------------------------
# Logging functions
# -----------------------------
def log_collision_detection(detected: bool):
    """Logs collision detection as 1 (detected) or 0 (not detected)."""
    cursor.execute(
        "INSERT INTO alerts (type, collision) VALUES (?, ?)",
        ("collision", 1 if detected else 0)
    )
    conn.commit()

def log_blindspot_detection(detected: bool):
    """Logs blindspot detection as 1 (detected) or 0 (not detected)."""
    cursor.execute(
        "INSERT INTO alerts (type, blindSpot) VALUES (?, ?)",
        ("blindspot", 1 if detected else 0)
    )
    conn.commit()

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
custom_font = font.Font(size=30)  # Set font size
window.geometry("800x400")  # Set window size

distance_label = tk.Label(window, text="Distance: ", anchor='center', font=custom_font)
distance_label.pack()  # Add the label to the window

# -----------------------------
# Distance measurement
# -----------------------------
def measure_distance():
    """Measures distances and updates the label accordingly."""
    distance_left = int(sensor_left.distance * 100)
    distance_right = int(sensor_right.distance * 100)
    distance_back = int(sensor_back.distance * 100)
    distance_front = int(sensor_front.distance * 100)

    if distance_left < 101:
        distance_label.config(fg="red", text=f"Left Blindspot Warning:\nVehicle is {distance_left} cm away!\n")
        log_blindspot_detection(True)

    elif distance_right < 101:
        distance_label.config(fg="red", text=f"Right Blind Spot Warning:\nVehicle is {distance_right} cm away!\n")
        log_blindspot_detection(True)

    elif distance_back < 101:
        distance_label.config(fg="red", text=f"Warning: Object Behind \nVehicle {distance_back} cm away\n")
        log_collision_detection(True)

    elif distance_front < 201:
        distance_label.config(fg="red", text=f"Warning: Object In Front \nVehicle {distance_front} cm away")
        log_collision_detection(True)

    else:
        distance_label.config(fg="blue", text="Nothing Detected")
        # Log "not detected" events too
        log_blindspot_detection(False)
        log_collision_detection(False)

    # Schedule next measurement
    window.after(500, measure_distance)

# Start measuring distance
measure_distance()

# Run the Tkinter event loop
window.mainloop()
