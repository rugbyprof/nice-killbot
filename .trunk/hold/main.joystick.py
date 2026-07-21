"""
ESP32 Joystick-Controlled IR Transmitter
========================================

Hardware:
    ESP-WROOM-32 development board
    KY-023 dual-axis joystick
    38 kHz IR transmitter module

Wiring:
    KY-023 GND  -> ESP32 GND
    KY-023 VCC  -> ESP32 3V3
    KY-023 VRx  -> ESP32 GPIO 34
    KY-023 VRy  -> ESP32 GPIO 35
    KY-023 SW   -> ESP32 GPIO 32

    IR module GND -> ESP32 GND
    IR module VCC -> ESP32 3V3
    IR module SIG -> ESP32 GPIO 25

This program is intentionally kept in one file for teaching.

Later, its sections could be separated into:

    config.py      Pin numbers and adjustable settings
    commands.py    Command definitions
    joystick.py    Joystick reading and direction logic
    ir_tx.py       Infrared transmission
    main.py        Main control loop

For now, keeping everything together makes the execution flow easier
to see and reduces the number of files students must mentally track.
"""

# =====================================================================
# SECTION 1: IMPORTS
#
# Future location:
#     These imports would remain in the modules that use them.
#
# Why this section exists:
#     Imports give the program access to ESP32 hardware and timing tools.
# =====================================================================

from machine import ADC, Pin, PWM
from time import sleep_ms, sleep_us, ticks_diff, ticks_ms

# =====================================================================
# SECTION 2: PIN ASSIGNMENTS
#
# Possible future file:
#     config.py or pins.py
#
# Why separate these later:
#     If the hardware wiring changes, we should only need to update pin
#     numbers in one location.
#
# GPIO numbers correspond directly to the labels printed on the ESP32.
# For example, Pin(25) means GPIO25.
# =====================================================================

JOYSTICK_X_PIN = 34
JOYSTICK_Y_PIN = 33
JOYSTICK_BUTTON_PIN = 32

IR_TRANSMITTER_PIN = 25


# =====================================================================
# SECTION 3: COMMAND DEFINITIONS
#
# Possible future file:
#     commands.py
#
# Why separate these later:
#     Other parts of the program can use names such as FORWARD rather
#     than unexplained numbers such as 1 or 4.
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
JOYSTICK_BUTTON = 9


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
    JOYSTICK_BUTTON: "JOYSTICK_BUTTON",
}


# =====================================================================
# SECTION 4: ADJUSTABLE SETTINGS
#
# Possible future file:
#     config.py
#
# Why separate these later:
#     These values alter behavior without changing the program logic.
# =====================================================================

# The ESP32 ADC normally returns values from approximately 0 through 4095.
#
# A KY-023 joystick should rest near the middle, approximately 2048,
# although inexpensive joystick modules are rarely perfectly centered.

DEFAULT_CENTER_X = 2048
DEFAULT_CENTER_Y = 2048


# Ignore small movements around the center.
#
# Without a dead zone, tiny electrical variations could cause the robot
# to twitch while the joystick appears centered.

DEAD_ZONE = 500


# Number of joystick samples used during startup calibration.
#
# The joystick must remain untouched while these samples are collected.

CALIBRATION_SAMPLES = 25


# How frequently the current command is retransmitted.
#
# Repeating commands helps recover from an occasional missed IR frame.

SEND_INTERVAL_MS = 120


# Small delay in the main loop.
#
# This prevents the ESP32 from reading and printing values thousands of
# times per second for absolutely no useful reason.

LOOP_DELAY_MS = 200


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
#
# Why separate this later:
#     It gathers the physical hardware setup into one predictable place.
# =====================================================================

# Create analog input objects for the joystick axes.

joystick_x = ADC(Pin(JOYSTICK_X_PIN))
joystick_y = ADC(Pin(JOYSTICK_Y_PIN))


# Allow the ADC pins to measure most of the ESP32's 3.3 V range.
#
# This setting is specific to the ESP32 MicroPython implementation.

joystick_x.atten(ADC.ATTN_11DB)
joystick_y.atten(ADC.ATTN_11DB)


# The KY-023 switch connects its output to ground when pressed.
#
# PULL_UP keeps the pin HIGH while the button is not pressed:
#
#     Not pressed -> 1
#     Pressed     -> 0

joystick_button = Pin(
    JOYSTICK_BUTTON_PIN,
    Pin.IN,
    Pin.PULL_UP,
)


# PWM creates the 38 kHz infrared carrier.
#
# The carrier begins disabled because duty_u16 is initially zero.

ir_pwm = PWM(
    Pin(IR_TRANSMITTER_PIN),
    freq=IR_FREQUENCY_HZ,
    duty_u16=IR_DUTY_OFF,
)


# =====================================================================
# SECTION 6: JOYSTICK CALIBRATION
#
# Possible future file:
#     joystick.py
#
# Why calibrate:
#     A real joystick may rest at x=2150 and y=1930 rather than exactly
#     2048. Measuring its resting position gives more reliable behavior.
# =====================================================================


def calibrate_joystick():
    """
    Measure the joystick's resting center position.

    The user should leave the joystick untouched during calibration.

    Returns:
        tuple: (center_x, center_y)
    """

    print("Leave the joystick centered.")
    print("Calibrating...")

    total_x = 0
    total_y = 0

    for _ in range(CALIBRATION_SAMPLES):
        total_x += joystick_x.read()
        total_y += joystick_y.read()
        sleep_ms(20)

    center_x = total_x // CALIBRATION_SAMPLES
    center_y = total_y // CALIBRATION_SAMPLES

    print("Calibration complete.")
    print("Center X:", center_x)
    print("Center Y:", center_y)
    print()

    return center_x, center_y


# =====================================================================
# SECTION 7: JOYSTICK READING AND CLASSIFICATION
#
# Possible future file:
#     joystick.py
#
# Why this is its own logical section:
#     Reading hardware and deciding what a joystick position means are
#     separate responsibilities from transmitting infrared data.
# =====================================================================


def button_is_pressed():
    """
    Return True when the joystick's built-in switch is pressed.
    """

    return joystick_button.value() == 0


def read_joystick():
    """
    Read the current analog joystick values.

    Returns:
        tuple: (x_value, y_value)
    """
    return joystick_x.read(), joystick_y.read()


def get_joystick_command(x_value, y_value, center_x, center_y):
    """
    Convert analog joystick values into one numeric command.

    The joystick's physical orientation may reverse one or both axes.
    If FORWARD and BACKWARD appear reversed, swap those comparisons.
    The same applies to LEFT and RIGHT.

    Args:
        x_value: Current horizontal ADC reading
        y_value: Current vertical ADC reading
        center_x: Calibrated horizontal center
        center_y: Calibrated vertical center

    Returns:
        One of the numeric command constants.
    """

    # Determine whether each axis is outside its dead zone.

    moving_left = x_value < center_x - DEAD_ZONE
    moving_right = x_value > center_x + DEAD_ZONE

    moving_forward = y_value < center_y - DEAD_ZONE
    moving_backward = y_value > center_y + DEAD_ZONE

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


# =====================================================================
# SECTION 8: INFRARED CARRIER CONTROL
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
# SECTION 9: INFRARED BIT ENCODING
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
# SECTION 10: COMPLETE COMMAND TRANSMISSION
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
# Example:
#
#     Command:
#         1
#
#     Inverted command:
#         254
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
    Transmit one joystick command.

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
# SECTION 11: DEBUG OUTPUT
#
# Possible future file:
#     utils.py
#
# Why isolate this conceptually:
#     Debug output is useful during development but may be disabled later.
# =====================================================================


def print_command(command, x_value, y_value):
    """
    Print readable controller information to the serial console.
    """

    command_name = COMMAND_NAMES.get(command, "UNKNOWN")

    print(
        "x={:4d}  y={:4d}  command={:2d}  {}".format(
            x_value,
            y_value,
            command,
            command_name,
        )
    )


# =====================================================================
# SECTION 12: MAIN PROGRAM
#
# This section should remain in:
#     main.py
#
# Why:
#     main.py should show the overall behavior of the application.
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
    Run the joystick-controlled IR transmitter.
    """

    center_x, center_y = calibrate_joystick()

    import sys

    # sys.exit(0)

    previous_command = None
    last_send_time = ticks_ms()

    print("Controller ready.")
    print("Move the joystick or press its button.")
    print()

    while True:
        # -------------------------------------------------------------
        # Step 1: Read the joystick hardware.
        # -------------------------------------------------------------

        x_value, y_value = read_joystick()

        # -------------------------------------------------------------
        # Step 2: Convert the input into a named command.
        #
        # The joystick button takes priority over directional movement.
        # -------------------------------------------------------------

        if button_is_pressed():
            current_command = JOYSTICK_BUTTON
        else:
            current_command = get_joystick_command(
                x_value,
                y_value,
                center_x,
                center_y,
            )

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
                x_value,
                y_value,
            )

            previous_command = current_command
            last_send_time = current_time

        # -------------------------------------------------------------
        # Step 4: Pause briefly and repeat.
        # -------------------------------------------------------------

        sleep_ms(LOOP_DELAY_MS)


# =====================================================================
# SECTION 13: PROGRAM ENTRY POINT
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
