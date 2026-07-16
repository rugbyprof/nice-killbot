"""
38 kHz IR transmitter (NEC-style pulse-distance protocol over PWM).

This module knows nothing about joystick commands or command names -
callers pass a plain 0-255 byte to send_ir_command(). Keeping it free
of COMMAND_NAMES/joystick-specific constants keeps this file reusable
by any project that just needs to put a byte on the air over IR.

Public API:
    send_ir_command(command) -> None
    ir_off() -> None
"""

import machine
import time

# Standard infrared remote-control carrier frequency. PWM drives the
# transmitter LED on/off at this rate; demodulating IR receivers are
# tuned to expect exactly this.
IR_TRANSMITTER_PIN = 25
IR_FREQUENCY_HZ = 38_000

# PWM duty cycle while the IR carrier is active.
# 32768 is approximately 50% of the full 16-bit duty range.
IR_DUTY_ON = 32768
IR_DUTY_OFF = 0

ir_pwm = machine.PWM(
    machine.Pin(IR_TRANSMITTER_PIN),
    freq=IR_FREQUENCY_HZ,
    duty_u16=IR_DUTY_OFF,
)


def ir_mark(duration_us):
    """Transmit the 38 kHz carrier for a specified number of microseconds."""
    ir_pwm.duty_u16(IR_DUTY_ON)
    time.sleep_us(duration_us)
    ir_pwm.duty_u16(IR_DUTY_OFF)


def ir_space(duration_us):
    """Leave the infrared carrier off for a specified number of microseconds."""
    ir_pwm.duty_u16(IR_DUTY_OFF)
    if duration_us > 0:
        time.sleep_us(duration_us)


def send_ir_bit(bit_value):
    """
    Send one binary bit through the IR transmitter.

    Pulse-distance encoding:
        Binary 0: short mark + short space
        Binary 1: short mark + long space
    """
    ir_mark(560)
    if bit_value == 0:
        ir_space(560)
    else:
        ir_space(1690)


def send_ir_byte(value):
    """Send one 8-bit value, least-significant bit first."""
    for bit_position in range(8):
        bit_value = (value >> bit_position) & 1
        send_ir_bit(bit_value)


def send_ir_command(command):
    """
    Transmit one command byte (0-255) over IR.

    Frame format: header, command byte, inverted command byte (for
    error detection), ending mark. The receiver can verify:
        command + inverted_command == 255
    """
    ir_mark(9000)
    ir_space(4500)

    send_ir_byte(command)
    send_ir_byte(command ^ 255)

    ir_mark(560)
    ir_space(0)


def ir_off():
    """Force the IR carrier off. Call this on shutdown/error."""
    ir_pwm.duty_u16(IR_DUTY_OFF)
