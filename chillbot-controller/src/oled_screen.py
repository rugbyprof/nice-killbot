"""
OLED status display (SSD1306 128x64, I2C, via luma.oled).

Mirrors the public API of killbot-controller's own oled_screen.py so
both boards' "controller" scripts follow the same shape, even though
the underlying driver differs (luma.oled here vs. a vendored
MicroPython ssd1306 driver on the ESP32 side).

This module knows nothing about IR or command decoding. Callers pass
plain strings to display.

Public API:
    show_lines(*lines) -> None
    show_status(label, extra=None) -> None
    clear() -> None
"""

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

I2C_PORT = 1
I2C_ADDRESS = 0x3C

WIDTH = 128
HEIGHT = 64

serial = i2c(port=I2C_PORT, address=I2C_ADDRESS)
device = ssd1306(serial, width=WIDTH, height=HEIGHT)


def clear():
    """Blank the display."""
    device.clear()


def show_lines(*lines):
    """Render each argument as its own row, top to bottom."""
    with canvas(device) as draw:
        for row, line in enumerate(lines):
            draw.text((0, row * 12), str(line), fill="white")


def show_status(label, extra=None):
    """Convenience wrapper: a status label plus an optional detail line."""
    lines = [str(label)]
    if extra is not None:
        lines.append(str(extra))
    show_lines(*lines)


if __name__ == "__main__":
    # Standalone demo: confirms the display is wired correctly without
    # needing the IR receiver hardware from ir_receiver.py.
    from time import sleep

    seconds = 0
    try:
        while True:
            show_status("chillbot", f"uptime: {seconds}s")
            sleep(1)
            seconds += 1
    except KeyboardInterrupt:
        clear()
