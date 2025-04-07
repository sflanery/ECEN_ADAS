from gpiozero import DistanceSensor  # Import DistanceSensor class
import tkinter as tk  # Import tkinter for GUI
from tkinter import font  # Import font module from tkinter

# Initialize the ultrasonic sensors
sensor_right = DistanceSensor(echo=24, trigger=23, max_distance=2)
sensor_left = DistanceSensor(echo=16, trigger=12, max_distance=2)
sensor_back = DistanceSensor(echo=17, trigger=27, max_distance=2)
sensor_front = DistanceSensor(echo = 6, trigger = 13, max_distance = 2)

# Initialize Tkinter window
window = tk.Tk()
window.title("Distance Measurement")
custom_font = font.Font(size=30)  # Set font size
window.geometry("800x400")  # Set window size

distance_label = tk.Label(window, text="Distance: ", anchor='center', font=custom_font)
distance_label.pack()  # Add the label to the window

def measure_distance():
    """Measures distances and updates the label accordingly."""
    
    distance_left = int(sensor_left.distance * 100)
    distance_right = int(sensor_right.distance * 100)
    distance_back = int(sensor_back.distance * 100)
    distance_front = int(sensor_front.distance*100)

    if distance_left < 101:
        distance_label.config(fg="red", text="Left Blindspot Warning:\nVehicle is {} cm away!\n".format(distance_left))
    elif distance_right < 101:
        distance_label.config(fg="red", text="Right Blind Spot Warning:\nVehicle is {} cm away!\n".format(distance_right))
    elif distance_back < 101:
        distance_label.config(fg="red", text="Warning: Object Behind \n Vehicle {} cm away\n".format(distance_back))
    elif distance_front < 301:
        disatance_label.config(fg = "red", text ="Warning: Object In front \n Vehicle {} cm away".format(distance_front))
    else:
        distance_label.config(fg="blue", text="Nothing Detected")  # Display "bye" when nothing is detected

    window.after(500, measure_distance)  # Schedule next measurement

# Start measuring distance
measure_distance()

# Run the Tkinter event loop
window.mainloop()
