"""
ESP32 Button + Rotary Encoder IR Transmitter
=============================================

Hardware:
    ESP-WROOM-32 development board
    Forward button  (momentary push button)
    Backward button (momentary push button)
    Action button   (momentary push button - spare, "just in case")
    Rotary encoder (KY-040 style: CLK + DT, quadrature)
    38 kHz IR transmitter module

Wiring:
    Forward button  -> ESP32 GPIO 26, other leg -> GND
    Backward button -> ESP32 GPIO 27, other leg -> GND
    Action button   -> ESP32 GPIO 32, other leg -> GND

    Encoder CLK -> ESP32 GPIO 18
    Encoder DT  -> ESP32 GPIO 19
    Encoder SW  -> ESP32 GPIO 23
    Encoder GND -> ESP32 GND
    Encoder +   -> ESP32 3V3

    IR module GND -> ESP32 GND
    IR module VCC -> ESP32 3V3
    IR module SIG -> ESP32 GPIO 25

Buttons use the ESP32's internal pull-up resistor, so:

    Not pressed -> pin reads 1
    Pressed     -> pin reads 0 (button connects the pin to GND)

Steering model:
    Forward/backward are simple on/off, like a button.
    Steering is continuous: turning the knob adds or subtracts from a
    "steering" value on every detent (click) of the encoder. That value
    is meant to become either a servo angle or a left/right wheel speed
    differential once a receiver exists - this transmitter just reports
    the number, it doesn't decide what it means.

    A rotary encoder only reports movement, not absolute position, so
    steering can drift off-center over many turns with no way back
    except manually counter-turning. Pressing the encoder's SW button
    snaps steering back to STEERING_CENTER.

Because steering is now a value instead of a single command, the IR
frame carries two fields instead of one - see SECTION 9.

This program is intentionally kept in one file for teaching.

Later, its sections could be separated into:

    config.py      Pin numbers and adjustable settings
    commands.py    Command definitions
    buttons.py     Button reading
    encoder.py     Rotary encoder reading
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
ACTION_BUTTON_PIN = 32

ENCODER_CLK_PIN = 18
ENCODER_DT_PIN = 19
ENCODER_SW_PIN = 23

IR_TRANSMITTER_PIN = 25


# =====================================================================
# SECTION 3: COMMAND DEFINITIONS
#
# Possible future file:
#     commands.py
#
# There is no LEFT/RIGHT/diagonal command anymore - steering is a
# continuous value sent alongside the movement command instead.
# =====================================================================

STOP = 0
FORWARD = 1
BACKWARD = 2
ACTION_BUTTON = 3

COMMAND_NAMES = {
    STOP: "STOP",
    FORWARD: "FORWARD",
    BACKWARD: "BACKWARD",
    ACTION_BUTTON: "ACTION_BUTTON",
}


# =====================================================================
# SECTION 4: ADJUSTABLE SETTINGS
#
# Possible future file:
#     config.py
# =====================================================================

# Steering is sent as a single byte (0-255) so it fits the same
# byte + inverted-byte framing already used for the movement command.
#
# 128 means "centered / straight ahead."

STEERING_MIN = 0
STEERING_MAX = 255
STEERING_CENTER = 128

# How much the steering value changes per encoder detent (click).

STEERING_STEP = 8

# Ignore encoder interrupts that fire faster than this. Mechanical
# encoders are prone to contact bounce, which can otherwise register
# one physical click as several steps.

ENCODER_DEBOUNCE_MS = 2


# How frequently the current command is retransmitted.
#
# Repeating commands helps recover from an occasional missed IR frame.

SEND_INTERVAL_MS = 120


# Small delay in the main loop.
#
# Buttons are cheap to read (no ADC settling time like a joystick), so
# this can be short. Encoder turns are handled separately by an
# interrupt, not by this loop, so they aren't affected by this delay.

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

forward_button = Pin(FORWARD_BUTTON_PIN, Pin.IN, Pin.PULL_UP)
backward_button = Pin(BACKWARD_BUTTON_PIN, Pin.IN, Pin.PULL_UP)
action_button = Pin(ACTION_BUTTON_PIN, Pin.IN, Pin.PULL_UP)

encoder_clk = Pin(ENCODER_CLK_PIN, Pin.IN, Pin.PULL_UP)
encoder_dt = Pin(ENCODER_DT_PIN, Pin.IN, Pin.PULL_UP)
encoder_sw = Pin(ENCODER_SW_PIN, Pin.IN, Pin.PULL_UP)


# PWM creates the 38 kHz infrared carrier.
#
# The carrier begins disabled because duty_u16 is initially zero.

ir_pwm = PWM(
    Pin(IR_TRANSMITTER_PIN),
    freq=IR_FREQUENCY_HZ,
    duty_u16=IR_DUTY_OFF,
)


# =====================================================================
# SECTION 6: BUTTON READING
#
# Possible future file:
#     buttons.py
# =====================================================================


def is_pressed(pin):
    """
    Return True when a button's pin reads LOW (pressed).
    """

    return pin.value() == 0


# =====================================================================
# SECTION 7: ROTARY ENCODER READING
#
# Possible future file:
#     encoder.py
#
# Encoder turns are handled with an interrupt rather than polling in
# the main loop, because a quick flick of the knob can produce pulses
# faster than a 50ms polling loop would reliably catch.
#
# How direction is determined:
#     CLK and DT are two switches, slightly out of phase with each
#     other. When CLK transitions, comparing it to DT's current value
#     tells us which direction the knob turned:
#
#         DT != CLK  ->  one direction
#         DT == CLK  ->  the other direction
# =====================================================================

steering = STEERING_CENTER
_last_encoder_event_ms = 0


def _handle_encoder_turn(pin):
    """
    Interrupt handler: adjust `steering` by one step in the direction
    the encoder was turned, clamped to STEERING_MIN..STEERING_MAX.
    """

    global steering, _last_encoder_event_ms

    now = ticks_ms()

    if ticks_diff(now, _last_encoder_event_ms) < ENCODER_DEBOUNCE_MS:
        return

    _last_encoder_event_ms = now

    if encoder_dt.value() != encoder_clk.value():
        steering = min(STEERING_MAX, steering + STEERING_STEP)
    else:
        steering = max(STEERING_MIN, steering - STEERING_STEP)


encoder_clk.irq(
    trigger=Pin.IRQ_FALLING,
    handler=_handle_encoder_turn,
)


def recenter_steering():
    """
    Reset `steering` back to STEERING_CENTER.

    Called when the encoder's SW button is pressed, since an
    incremental encoder has no way to report "straight ahead" on its
    own.
    """

    global steering

    steering = STEERING_CENTER


# =====================================================================
# SECTION 8: INFRARED CARRIER CONTROL AND BIT ENCODING
#
# Possible future file:
#     ir_tx.py
#
# Terminology:
#
#     mark  = transmit the 38 kHz infrared carrier
#     space = stop transmitting the carrier
#
# This uses pulse-distance encoding:
#
#     Binary 0:
#         short mark + short space
#
#     Binary 1:
#         short mark + long space
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


def send_ir_field(value):
    """
    Send one byte plus its inverted copy, for error detection.

    The receiver can verify:

        value + inverted_value == 255
    """

    send_ir_byte(value)
    send_ir_byte(value ^ 255)


# =====================================================================
# SECTION 9: COMPLETE FRAME TRANSMISSION
#
# Possible future file:
#     ir_tx.py
#
# Frame format:
#
#     Header
#     Movement field   (byte + inverted byte)
#     Steering field    (byte + inverted byte)
#     Ending mark
#
# Movement and steering are sent as two separate self-checked fields
# in the same frame, rather than packed into one byte, so each can be
# validated independently on the receiving end.
# =====================================================================


def send_ir_command(movement, steering_value):
    """
    Transmit one movement command and the current steering value.

    Args:
        movement: One of the movement command constants (0-255)
        steering_value: Current steering byte (0-255)
    """

    # Start/header pattern tells the receiver that a new frame is coming.

    ir_mark(9000)
    ir_space(4500)

    send_ir_field(movement)
    send_ir_field(steering_value)

    print(f"Sending: movement:{movement}, steering:{steering_value}")

    # Final mark completes the transmission.

    ir_mark(560)
    ir_space(0)


# =====================================================================
# SECTION 10: DEBUG OUTPUT
#
# Possible future file:
#     utils.py
# =====================================================================


def print_command(movement, steering_value, forward, backward, action, sw):
    """
    Print readable controller information to the serial console.
    """

    movement_name = COMMAND_NAMES.get(movement, "UNKNOWN")

    print(
        "F={} B={} A={} SW={}  movement={}  {}  steering={:3d} ({:+d})".format(
            int(forward),
            int(backward),
            int(action),
            int(sw),
            movement,
            movement_name,
            steering_value,
            steering_value - STEERING_CENTER,
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
    Run the button + rotary encoder IR transmitter.
    """

    previous_movement = None
    previous_steering = None
    last_send_time = ticks_ms()

    print("Controller ready.")
    print("Hold forward/backward to drive. Turn the knob to steer.")
    print()

    while True:
        # -------------------------------------------------------------
        # Step 1: Read the button hardware.
        #
        # (Turning the encoder updates `steering` on its own via
        # interrupt - there's nothing to read for that here. Pressing
        # it, however, is a plain button read like the others.)
        # -------------------------------------------------------------

        forward = is_pressed(forward_button)
        backward = is_pressed(backward_button)
        action = is_pressed(action_button)
        sw = is_pressed(encoder_sw)

        if sw:
            recenter_steering()

        # -------------------------------------------------------------
        # Step 2: Convert the input into a movement command.
        #
        # The action button takes priority over driving.
        # Holding both forward and backward cancels out to STOP rather
        # than picking one arbitrarily.
        # -------------------------------------------------------------

        if action:
            current_movement = ACTION_BUTTON
        elif forward and backward:
            current_movement = STOP
        elif forward:
            current_movement = FORWARD
        elif backward:
            current_movement = BACKWARD
        else:
            current_movement = STOP

        current_steering = steering

        # -------------------------------------------------------------
        # Step 3: Decide whether the command should be transmitted.
        #
        # Send when:
        #
        #     The movement command changed
        #
        # or:
        #
        #     The steering value changed
        #
        # or:
        #
        #     Enough time has passed since the previous transmission
        #
        # Periodic repetition helps if one IR frame is missed.
        # -------------------------------------------------------------

        current_time = ticks_ms()

        state_changed = (
            current_movement != previous_movement
            or current_steering != previous_steering
        )

        repeat_due = ticks_diff(current_time, last_send_time) >= SEND_INTERVAL_MS

        if state_changed or repeat_due:
            send_ir_command(current_movement, current_steering)

            print_command(
                current_movement,
                current_steering,
                forward,
                backward,
                action,
                sw,
            )

            previous_movement = current_movement
            previous_steering = current_steering
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
