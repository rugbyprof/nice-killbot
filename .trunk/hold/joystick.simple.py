import machine
import time

# 1. Hardware Pin Configurations
# Use ADC1 pins (32-39) to avoid conflicts if Wi-Fi is used later
pin_x = machine.Pin(34, machine.Pin.IN)
pin_y = machine.Pin(35, machine.Pin.IN)

# Initialize ADC
adc_x = machine.ADC(pin_x)
adc_y = machine.ADC(pin_y)

# Configure ADC for full 3.3V range (12-bit resolution: 0 to 4095)
adc_x.atten(machine.ADC.ATTN_11DB)
adc_y.atten(machine.ADC.ATTN_11DB)

# 2. Calibration Constants
CENTER_X = 2048
CENTER_Y = 2048
DEADZONE = 500  # Ignore movements within this window
SAMPLES = 16  # Number of reads for oversampling
# SAMPLES = 1  # Number of reads for oversampling

# Number of joystick samples used during startup calibration.
#
# The joystick must remain untouched while these samples are collected.

CALIBRATION_SAMPLES = 25

# State Management variables
last_direction = "CENTER"
last_transmit_time = 0
DEBOUNCE_DELAY = 300  # Milliseconds between allowed IR transmissions


def calibrate_joystick():
    """
    Measure the joystick's resting center position.

    The user should leave the joystick untouched during calibration.

    Returns:
        tuple: (center_x, center_y)
    """
    global CENTER_X
    global CENTER_Y

    print("Leave the joystick centered.")
    print("Calibrating...")

    total_x = 0
    total_y = 0

    for _ in range(CALIBRATION_SAMPLES):
        total_x += adc_x.read()
        total_y += adc_y.read()
        print(f"{adc_x.read()},{adc_y.read()}")
        time.sleep_ms(20)

    CENTER_X = total_x // CALIBRATION_SAMPLES
    CENTER_Y = total_y // CALIBRATION_SAMPLES

    print("Calibration complete.")
    print("Center X:", CENTER_X)
    print("Center Y:", CENTER_Y)
    print()


def read_joystick():
    """Oversamples the ADC to eliminate random noise spikes."""
    sum_x = 0
    sum_y = 0
    for _ in range(SAMPLES):
        sum_x += adc_x.read()
        sum_y += adc_y.read()
    # print(f"{sum_x},{sum_y}")
    return sum_x // SAMPLES, sum_y // SAMPLES


def get_direction(x, y):
    """Maps raw coordinate math to a clean directional output."""
    dev_x = x - CENTER_X
    dev_y = y - CENTER_Y

    # print(f"CENTER = {CENTER_X},{CENTER_Y}")
    # print(f"x:{x} abs(x):{abs(dev_x)}  y:{y} abs(y):{abs(dev_y)}")
    # time.sleep_ms(200)

    # Check if movement exceeds the deadzone threshold
    if abs(dev_x) < DEADZONE and abs(dev_y) < DEADZONE:
        return "CENTER"

    # print(f"if {abs(dev_x)} > {abs(dev_y)}")
    # Determine the dominant axis of movement
    if abs(dev_x) > abs(dev_y):
        return "RIGHT" if dev_x > 0 else "LEFT"
    else:
        return "DOWN" if dev_y > 0 else "UP"


def transmit_ir(direction):
    """Stub function where you place your MicroPython IR library code."""
    print(f"TRANSMITTING IR CODE FOR: {direction}")
    # Example: ir_tx.transmit(NEC_CODES[direction])


# calibrate_joystick()

# Main Application Loop
i = 1
while True:

    current_time = time.ticks_ms()
    raw_x, raw_y = read_joystick()
    current_direction = get_direction(raw_x, raw_y)

    # State change logic + debounce protection
    # if current_direction != last_direction:
    # if current_direction != "CENTER":
    if time.ticks_diff(current_time, last_transmit_time) > DEBOUNCE_DELAY:
        transmit_ir(current_direction)
        last_transmit_time = current_time

        last_direction = current_direction

    time.sleep_ms(200)  # Prevents CPU core throttling
