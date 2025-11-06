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
try:
    print("Manual RC mode active (relay LOW)")
    relay.set_value(0)
    send_neutral()
    time.sleep(1)

    print("Switching relay ON: Pi controls car")
    relay.set_value(1)

    print("Autonomous movement: forward & left")
    for _ in range(50):  # 50 cycles (~1 second)
        pwm_pulse(throttle, 1.6)  # forward
        pwm_pulse(steering, 1.4)  # left
        time.sleep(0.018)

    print("Stop and return to neutral")
    send_neutral()
    relay.set_value(0)
    print("Autonomous test finished. Back to manual RC")

finally:
    relay.set_value(0)
    steering.set_value(0)
    throttle.set_value(0)
    chip.close()
    print("Cleanup done. Safe exit.")
