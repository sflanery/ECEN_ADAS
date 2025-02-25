from gpiozero import DistanceSensor  # Import the DistanceSensor class from the gpiozero library

import tkinter as tk  # Import the tkinter library for creating the GUI

from tkinter import font  # Import the font module from tkinter for customizing the font

from time import sleep  # Import the sleep function from the time module for delay

import threading

# threat checking
#threat_check = {left, right, back}

# Initialize the ultrasonic sensor
#Currently using GPIOs 24 and 23 for the right side blind spot, for the second ultrasonic, we will use GPIOs 12 and 16 for the left side blind spot

sensor_right = DistanceSensor(echo=24, trigger=23, max_distance=2)
sensor_left = DistanceSensor(echo=16, trigger=12, max_distance=2)
sensor_back = DistanceSensor(echo = 17, trigger = 27, max_distance = 2)

# Initialize the Tkinter window

window = tk.Tk()

window.title("Distance Measurement")

custom_font = font.Font(size=30)  # Create a custom font object with size 30

window.geometry("800x400")  # Set the dimensions of the window

distance_label = tk.Label(window, text="Distance: ", anchor='center', font=custom_font)

# Create a label to display the distance, centered text, and use the custom font

distance_label.pack()  # Add the label to the window

def measure_distance_left():

#defining both of the ultrasonic distances to be calculated
    # Measure the distance and convert it to an integer
   distance_left = int(sensor_left.distance * 100)
   

   #distance_label.config(text="Distance: {} cm".format(distance))  # Update the distance label with the new distance

       # If the distance is less than 1.01 meter, set the label text to display a blindspot detection warning
       # Each if statement is true for both sides
   if distance_left < 101:

       distance_label.config(fg = "red", text = "Left Blindspot Warning: \nVehicle is {} cm away\n!".format(distance_left))
       
   #elif distance_right > 101 and distance_left > 101:
    #      distance_label.config(fg="blue", text="No Vehicle detected in either blind spot.")

   
       # If the distance is greater than 1.01 meter, just indicate otherwise
 #  elif distance_left > 101:

     #         distance_label.config(fg = "blue", text = "Nothing detected in right blindspot \n")
     
       
   
   window.after(500, measure_distance_left)  # Schedule the next measurement after 0.5 second
  

def measure_distance_right():
   distance_right = int(sensor_right.distance * 100)
        #copy paste
   if distance_right < 101:
            
              distance_label.config(fg="red", text="Right Blind Spot Warning: \nVehicle is {} cm away!\n".format(distance_right))
              
  # elif distance_right > 101:
    #          distance_label.config(fg = "blue", text = "Nothing detected in left blindspot \n")
        
              
   window.after(500, measure_distance_right)  # Schedule the next measurement after 0.5 second
   

def measure_distance_back():
   distance_back = int(sensor_back.distance * 100)
       
   if distance_back < 101:
     
       distance_label.config(fg = "red", text = "Warning: Object Detected Behind Vehicle {} cm away\n".format(distance_back))
       
  # elif distance_back > 101:
  #     distance_label.config(fg = "blue", text = "Nothing detected behind the vehicle \n")
      
   
   window.after(500, measure_distance_back)  # Schedule the next measurement after 0.5 second


              

thread_left = threading.Thread(target = measure_distance_left)
thread_right = threading.Thread(target = measure_distance_right)
thread_back = threading.Thread(target = measure_distance_back)



thread_left.start()
thread_right.start()
thread_back.start()



# Run the Tkinter event loop

window.mainloop()

