"""
OLED status display (SSD1306 128x64, I2C).

This module knows nothing about the joystick or its command constants.
Callers pass plain strings/numbers to display, so this file and
joystick.py can be developed, tested, and reasoned about separately -
joystick.py just calls the functions below.

Public API:
    show_lines(*lines) -> None
    show_status(label, x=None, y=None) -> None
    clear() -> None
"""

from machine import I2C, Pin

from ssd1306 import SSD1306_I2C

# =====================================================================
# HARDWARE PIN CONFIGURATION
# =====================================================================

SDA_PIN = 21
SCL_PIN = 22
I2C_FREQ = 400_000

WIDTH = 128
HEIGHT = 64

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
display = SSD1306_I2C(WIDTH, HEIGHT, i2c)


def clear():
    """Blank the display."""
    display.fill(0)
    display.show()


def show_lines(*lines):
    """Render each argument as its own row, top to bottom."""
    display.fill(0)
    for row, line in enumerate(lines):
        display.text(str(line), 0, row * 10)
    display.show()


def show_status(label, x=None, y=None):
    """Convenience wrapper: a status label plus optional raw axis values."""
    lines = [str(label)]
    if x is not None and y is not None:
        lines.append(f"x={x} y={y}")
    show_lines(*lines)
