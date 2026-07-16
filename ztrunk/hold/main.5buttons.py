"""
ESP32 Button-Controlled IR Transmitter
=======================================

Hardware:
    ESP-WROOM-32 development board
    4x momentary push buttons (forward / backward / left / right)
    1x momentary push button (action - horn, lights, whatever you like)
    38 kHz IR transmitter module

Wiring:
    Forward button  -> ESP32 GPIO 26, other leg -> GND
    Backward button -> ESP32 GPIO 27, other leg -> GND
    Left button     -> ESP32 GPIO 14, other leg -> GND
    Right button    -> ESP32 GPIO 13, other leg -> GND
    Action button   -> ESP32 GPIO 32, other leg -> GND

    IR module GND -> ESP32 GND
    IR module VCC -> ESP32 3V3
    IR module SIG -> ESP32 GPIO 25

Each button uses the ESP32's internal pull-up resistor, so:

    Not pressed -> pin reads 1
    Pressed     -> pin reads 0 (button connects the pin to GND)

No external resistors are needed.

This program is intentionally kept in one file for teaching.

Later, its sections could be separated into:

    config.py      Pin numbers and adjustable settings
    commands.py    Command definitions
    buttons.py     Button reading and command classification
    ir_tx.py       Infrared transmission
    main.py        Main control loop

For now, keeping everything together makes the execution flow easier
to see and reduces the number of files students must mentally track.
"""

# =====================================================================
# SECTION 1: IMPORTS
# =====================================================================

from machine import Pin, PWM
from time import sleep_ms, sleep_us, ticks_diff, ticks_ms


# =====================================================================
# SECTION 2: PIN ASSIGNMENTS
#
# Possible future file:
#     config.py
#
# GPIO numbers correspond directly to the labels printed on the ESP32.
# =====================================================================

FORWARD_BUTTON_PIN = 26
BACKWARD_BUTTON_PIN = 27
LEFT_BUTTON_PIN = 14
RIGHT_BUTTON_PIN = 13
ACTION_BUTTON_PIN = 32

IR_TRANSMITTER_PIN = 25


# =====================================================================
# SECTION 3: COMMAND DEFINITIONS
#
# Possible future file:
#     commands.py
#
# Decimal values are used because they are easier for beginning students
# to read. Hexadecimal is not required.
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
ACTION_BUTTON = 9


# A dictionary is useful for debugging output.
#
# The robot does not receive these strings. It receives only the numeric
# command. The strings are printed for humans watching the serial console.

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
    ACTION_BUTTON: "ACTION_BUTTON",
}


# =====================================================================
# SECTION 4: ADJUSTABLE SETTINGS
#
# Possible future file:
#     config.py
# =====================================================================

# How frequently the current command is retransmitted.
#
# Repeating commands helps recover from an occasional missed IR frame.

SEND_INTERVAL_MS = 120


# Small delay in the main loop.
#
# Buttons are cheap to read (no ADC settling time like a joystick), so
# this can be shorter than it would be for analog input.

LOOP_DELAY_MS = 50


# Standard infrared remote-control carrier frequency.

IR_FREQUENCY_HZ = 38_000


# PWM duty cycle while the IR carrier is active.
#
# 32768 is approximately 50% of the full 16-bit duty range.

IR_DUTY_ON = 32768
IR_DUTY_OFF = 0


# =====================================================================
# SECTION 5: HARDWARE INITIALIZATION
#
# Possible future file:
#     hardware.py
# =====================================================================

# Each button's switch connects its pin to ground when pressed.
#
# PULL_UP keeps the pin HIGH while the button is not pressed:
#
#     Not pressed -> 1
#     Pressed     -> 0

forward_button = Pin(FORWARD_BUTTON_PIN, Pin.IN, Pin.PULL_UP)
backward_button = Pin(BACKWARD_BUTTON_PIN, Pin.IN, Pin.PULL_UP)
left_button = Pin(LEFT_BUTTON_PIN, Pin.IN, Pin.PULL_UP)
right_button = Pin(RIGHT_BUTTON_PIN, Pin.IN, Pin.PULL_UP)
action_button = Pin(ACTION_BUTTON_PIN, Pin.IN, Pin.PULL_UP)


# PWM creates the 38 kHz infrared carrier.
#
# The carrier begins disabled because duty_u16 is initially zero.

ir_pwm = PWM(
    Pin(IR_TRANSMITTER_PIN),
    freq=IR_FREQUENCY_HZ,
    duty_u16=IR_DUTY_OFF,
)


# =====================================================================
# SECTION 6: BUTTON READING AND CLASSIFICATION
#
# Possible future file:
#     buttons.py
# =====================================================================


def is_pressed(pin):
    """
    Return True when a button's pin reads LOW (pressed).
    """

    return pin.value() == 0


def read_buttons():
    """
    Read the four directional buttons.

    Returns:
        tuple: (forward, backward, left, right), each True or False
    """

    return (
        is_pressed(forward_button),
        is_pressed(backward_button),
        is_pressed(left_button),
        is_pressed(right_button),
    )


def get_button_command(forward, backward, left, right):
    """
    Convert directional button states into one numeric command.

    Args:
        forward, backward, left, right: True if that button is pressed

    Returns:
        One of the numeric command constants.
    """

    # Holding two opposite buttons on the same axis cancels out, rather
    # than picking one arbitrarily.

    if forward and backward:
        forward = False
        backward = False

    if left and right:
        left = False
        right = False

    # Check diagonals first.
    #
    # If we checked FORWARD first, a forward+left combination would be
    # classified only as FORWARD and the LEFT press would be ignored.

    if forward and left:
        return FORWARD_LEFT

    if forward and right:
        return FORWARD_RIGHT

    if backward and left:
        return BACKWARD_LEFT

    if backward and right:
        return BACKWARD_RIGHT

    # Check the four basic directions.

    if forward:
        return FORWARD

    if backward:
        return BACKWARD

    if left:
        return LEFT

    if right:
        return RIGHT

    # No directional button is pressed.

    return STOP


# =====================================================================
# SECTION 7: INFRARED CARRIER CONTROL
#
# Possible future file:
#     ir_tx.py
#
# Terminology:
#
#     mark  = transmit the 38 kHz infrared carrier
#     space = stop transmitting the carrier
#
# The receiver sees a timed pattern of marks and spaces.
# =====================================================================


def ir_mark(duration_us):
    """
    Transmit the 38 kHz carrier for a specified number of microseconds.
    """

    ir_pwm.duty_u16(IR_DUTY_ON)
    sleep_us(duration_us)
    ir_pwm.duty_u16(IR_DUTY_OFF)


def ir_space(duration_us):
    """
    Leave the infrared carrier off for a specified number of microseconds.
    """

    ir_pwm.duty_u16(IR_DUTY_OFF)

    if duration_us > 0:
        sleep_us(duration_us)


# =====================================================================
# SECTION 8: INFRARED BIT ENCODING
#
# Possible future file:
#     ir_tx.py
#
# This uses pulse-distance encoding:
#
#     Binary 0:
#         short mark + short space
#
#     Binary 1:
#         short mark + long space
#
# This resembles common consumer IR protocols and works well with a
# typical demodulating 38 kHz receiver.
# =====================================================================


def send_ir_bit(bit_value):
    """
    Send one binary bit through the IR transmitter.

    Args:
        bit_value: 0 or 1
    """

    # Every bit begins with the same 560 microsecond mark.

    ir_mark(560)

    if bit_value == 0:
        ir_space(560)
    else:
        ir_space(1690)


def send_ir_byte(value):
    """
    Send one 8-bit value, least-significant bit first.

    Args:
        value: Integer from 0 through 255
    """

    for bit_position in range(8):
        bit_value = (value >> bit_position) & 1
        send_ir_bit(bit_value)


# =====================================================================
# SECTION 9: COMPLETE COMMAND TRANSMISSION
#
# Possible future file:
#     ir_tx.py
#
# Frame format:
#
#     Header
#     Command byte
#     Inverted command byte
#     Ending mark
#
# The receiver can verify:
#
#     command + inverted_command == 255
#
# This provides a small amount of error detection without introducing
# addresses, packet classes, checksums, or other ceremonial complexity.
# =====================================================================


def send_ir_command(command):
    """
    Transmit one button command.

    Args:
        command: Integer from 0 through 255
    """

    # Start/header pattern tells the receiver that a new frame is coming.

    ir_mark(9000)
    ir_space(4500)

    # Send the actual command.

    send_ir_byte(command)

    # Send the one's complement of the command for error checking.
    #
    # XOR with 255 flips all eight bits:
    #
    #     command 1   -> inverted value 254
    #     command 2   -> inverted value 253
    #     command 255 -> inverted value 0

    inverted_command = command ^ 255
    send_ir_byte(inverted_command)

    # Final mark completes the transmission.

    ir_mark(560)
    ir_space(0)


# =====================================================================
# SECTION 10: DEBUG OUTPUT
#
# Possible future file:
#     utils.py
#
# Why isolate this conceptually:
#     Debug output is useful during development but may be disabled later.
# =====================================================================


def print_command(command, forward, backward, left, right, action):
    """
    Print readable controller information to the serial console.
    """

    command_name = COMMAND_NAMES.get(command, "UNKNOWN")

    print(
        "F={} B={} L={} R={} A={}  command={:2d}  {}".format(
            int(forward),
            int(backward),
            int(left),
            int(right),
            int(action),
            command,
            command_name,
        )
    )


# =====================================================================
# SECTION 11: MAIN PROGRAM
#
# This section should remain in:
#     main.py
#
# Ideally, it reads like an outline:
#
#     1. Read inputs
#     2. Decide on a command
#     3. Send the command
#     4. Repeat
# =====================================================================


def main():
    """
    Run the button-controlled IR transmitter.
    """

    previous_command = None
    last_send_time = ticks_ms()

    print("Controller ready.")
    print("Press a direction button, or the action button.")
    print()

    while True:
        # -------------------------------------------------------------
        # Step 1: Read the button hardware.
        # -------------------------------------------------------------

        forward, backward, left, right = read_buttons()
        action = is_pressed(action_button)

        # -------------------------------------------------------------
        # Step 2: Convert the input into a named command.
        #
        # The action button takes priority over directional movement.
        # -------------------------------------------------------------

        if action:
            current_command = ACTION_BUTTON
        else:
            current_command = get_button_command(forward, backward, left, right)

        # -------------------------------------------------------------
        # Step 3: Decide whether the command should be transmitted.
        #
        # Send when:
        #
        #     The command changed
        #
        # or:
        #
        #     Enough time has passed since the previous transmission
        #
        # Periodic repetition helps if one IR frame is missed.
        # -------------------------------------------------------------

        current_time = ticks_ms()

        command_changed = current_command != previous_command

        repeat_due = ticks_diff(current_time, last_send_time) >= SEND_INTERVAL_MS

        if command_changed or repeat_due:
            send_ir_command(current_command)

            print_command(
                current_command,
                forward,
                backward,
                left,
                right,
                action,
            )

            previous_command = current_command
            last_send_time = current_time

        # -------------------------------------------------------------
        # Step 4: Pause briefly and repeat.
        # -------------------------------------------------------------

        sleep_ms(LOOP_DELAY_MS)


# =====================================================================
# SECTION 12: PROGRAM ENTRY POINT
#
# This pattern makes the program's starting point explicit.
# =====================================================================

try:
    main()

except KeyboardInterrupt:
    # Ctrl-C from the MicroPython REPL stops the program cleanly.

    print()
    print("Controller stopped.")

finally:
    # Make absolutely sure the IR transmitter is disabled when the
    # program exits or encounters an error.

    ir_pwm.duty_u16(IR_DUTY_OFF)
