"""
ESP32 Joystick-to-command driver for a KY-023-style dual-axis joystick.

Reads the joystick's X/Y ADC lines and SW (button) line, applies
calibration and a dead zone, and classifies the result into one of the
numeric command constants defined below (STOP, FORWARD, ..., diagonals,
JOYSTICK_BUTTON).

Each transmitted command is mirrored to an OLED status display via the
oled_screen module (see oled_screen.py), and sent over IR via the
ir_transmitter module (see ir_transmitter.py). This file only calls
their public functions and does not depend on their internals.

Public API for callers importing this as a module:
    Constants:
        STOP, FORWARD, BACKWARD, LEFT, RIGHT,
        FORWARD_LEFT, FORWARD_RIGHT, BACKWARD_LEFT, BACKWARD_RIGHT,
        JOYSTICK_BUTTON, COMMAND_NAMES
    Functions:
        calibrate_joystick() -> None
        read_joystick() -> (x, y)
        button_is_pressed() -> bool
        get_direction(x, y) -> command constant
        transmit_ir(command) -> None

Note: importing this module initializes the ADC/Pin hardware objects
(pin_x, pin_y, pin_sw) as a side effect, since MicroPython has no
separate hardware-init step. The blocking read loop itself only runs
under `if __name__ == "__main__"`, so importing this module for its
constants/functions (e.g. from a test) will not start it.
"""

import machine
import time

import ir_transmitter

import oled_screen

# =====================================================================
# HARDWARE PIN CONFIGURATION
#
# Use ADC1 pins (32-39) to avoid conflicts if Wi-Fi is used later.
# GPIO numbers correspond directly to the labels printed on the ESP32.
# =====================================================================

pin_x = machine.Pin(34, machine.Pin.IN)
pin_y = machine.Pin(35, machine.Pin.IN)

# The joystick's SW (button) line connects to ground when pressed.
# PULL_UP keeps the pin HIGH while the button is not pressed:
#     Not pressed -> 1
#     Pressed     -> 0
pin_sw = machine.Pin(32, machine.Pin.IN, machine.Pin.PULL_UP)

# Initialize ADC
adc_x = machine.ADC(pin_x)
adc_y = machine.ADC(pin_y)

# Configure ADC for full 3.3V range (12-bit resolution: 0 to 4095)
adc_x.atten(machine.ADC.ATTN_11DB)
adc_y.atten(machine.ADC.ATTN_11DB)


# =====================================================================
# COMMAND DEFINITIONS
#
# Named constants let other parts of the program use names such as
# FORWARD rather than unexplained numbers such as 1 or 4.
#
# Decimal values are used because they are easier for beginning
# students to read. Hexadecimal is not required.
# =====================================================================

STOP = 0
FORWARD = 1
BACKWARD = 2
LEFT = 3
RIGHT = 4
FORWARD_LEFT = 5
FORWARD_RIGHT = 6
BACKWARD_LEFT = 7
BACKWARD_RIGHT = 8
JOYSTICK_BUTTON = 9


# A dictionary is useful for debugging output.
#
# The robot does not receive these strings. It receives only the
# numeric command. The strings are printed for humans watching the
# serial console.

COMMAND_NAMES = {
    STOP: "STOP",
    FORWARD: "FORWARD",
    BACKWARD: "BACKWARD",
    LEFT: "LEFT",
    RIGHT: "RIGHT",
    FORWARD_LEFT: "FORWARD_LEFT",
    FORWARD_RIGHT: "FORWARD_RIGHT",
    BACKWARD_LEFT: "BACKWARD_LEFT",
    BACKWARD_RIGHT: "BACKWARD_RIGHT",
    JOYSTICK_BUTTON: "JOYSTICK_BUTTON",
}


# =====================================================================
# CALIBRATION / ADJUSTABLE SETTINGS
# =====================================================================

# The ESP32 ADC normally returns values from approximately 0 through
# 4095. A joystick should rest near the middle, approximately 2048,
# although inexpensive joystick modules are rarely perfectly centered.
CENTER_X = 2048
CENTER_Y = 2048

# Ignore small movements around the center.
#
# Without a dead zone, tiny electrical variations could cause the
# robot to twitch while the joystick appears centered.
DEADZONE = 500  # Ignore movements within this window

SAMPLES = 16  # Number of reads for oversampling
# SAMPLES = 1  # Number of reads for oversampling

# Number of joystick samples used during startup calibration.
#
# The joystick must remain untouched while these samples are collected.

CALIBRATION_SAMPLES = 25

# State Management variables
last_direction = STOP
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


def button_is_pressed():
    """Return True when the joystick's built-in switch (SW) is pressed."""
    return pin_sw.value() == 0


def get_direction(x, y):
    """
    Convert analog joystick values into one numeric command.

    Unlike a dominant-axis check, each axis is evaluated independently
    so diagonal positions (e.g. FORWARD_LEFT) can be detected instead
    of being collapsed into a single cardinal direction.

    The joystick's physical orientation may reverse one or both axes.
    If FORWARD/BACKWARD or LEFT/RIGHT appear swapped, swap those
    comparisons below.

    Returns:
        One of the numeric command constants.
    """
    dev_x = x - CENTER_X
    dev_y = y - CENTER_Y

    moving_left = dev_x < -DEADZONE
    moving_right = dev_x > DEADZONE

    moving_forward = dev_y < -DEADZONE
    moving_backward = dev_y > DEADZONE

    # Check diagonals first.
    #
    # If we checked FORWARD first, a forward-left position would be
    # classified only as FORWARD and the horizontal movement would be
    # ignored.

    if moving_forward and moving_left:
        return FORWARD_LEFT

    if moving_forward and moving_right:
        return FORWARD_RIGHT

    if moving_backward and moving_left:
        return BACKWARD_LEFT

    if moving_backward and moving_right:
        return BACKWARD_RIGHT

    # Check the four basic directions.

    if moving_forward:
        return FORWARD

    if moving_backward:
        return BACKWARD

    if moving_left:
        return LEFT

    if moving_right:
        return RIGHT

    # Neither axis moved outside the dead zone.

    return STOP


def transmit_ir(command):
    """Send `command` over IR and print it for debugging."""
    print(f"TRANSMITTING IR CODE FOR: {COMMAND_NAMES.get(command, 'UNKNOWN')}")
    ir_transmitter.send_ir_command(command)


def main():
    """Run the joystick read/transmit loop. Blocks forever."""
    global last_direction, last_transmit_time

    calibrate_joystick()

    while True:

        current_time = time.ticks_ms()
        raw_x, raw_y = read_joystick()

        # The button takes priority over directional movement.
        if button_is_pressed():
            current_direction = JOYSTICK_BUTTON
        else:
            current_direction = get_direction(raw_x, raw_y)

        # State change logic + debounce protection
        # if current_direction != last_direction:
        # if current_direction != STOP:
        if time.ticks_diff(current_time, last_transmit_time) > DEBOUNCE_DELAY:
            transmit_ir(current_direction)
            oled_screen.show_status(
                COMMAND_NAMES.get(current_direction, "UNKNOWN"),
                raw_x,
                raw_y,
            )
            last_transmit_time = current_time

            last_direction = current_direction

        time.sleep_ms(200)  # Prevents CPU core throttling


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Controller stopped.")
    finally:
        # Make absolutely sure the IR transmitter is disabled when the
        # program exits or encounters an error.
        ir_transmitter.ir_off()
