"""
38 kHz IR receiver (NEC-style pulse-distance protocol via pigpio).

Decodes frames sent by esp32-controller's ir_transmitter.py (see
esp32-controller/docs/protocol.md for the shared wire format). This
module doesn't know about the OLED or any other output - callers
supply a callback to listen() and get invoked with each decoded
command byte.

Public API:
    COMMAND_NAMES (alias of commands.NAMES)
    decode(edge_ticks) -> command byte or None
    listen(on_command) -> None, blocks forever
    close() -> None

Note: importing this module connects to the pigpiod daemon and
configures the receiver pin as a side effect - the daemon must already
be running (see README.md). The blocking read loop itself only starts
when listen() is called.
"""

from time import sleep

import pigpio

import commands

IR_RECEIVER_PIN = 24

# Alias kept for backward compatibility with existing callers/docs -
# the actual table lives in commands.py, shared with motors.py.
COMMAND_NAMES = commands.NAMES

pi = pigpio.pi()
if not pi.connected:
    raise SystemExit(
        "Could not connect to pigpio daemon - is it running? "
        "(sudo systemctl start pigpiod)"
    )

pi.set_mode(IR_RECEIVER_PIN, pigpio.INPUT)


def decode(edge_ticks):
    """
    Convert a list of edge timestamps into a command byte, or None if
    the timing doesn't match a valid frame.

    This is the standard NEC IR protocol:
        Header:  ~9000us mark, ~4500us space
        Bit 0:   ~560us mark,  ~560us space
        Bit 1:   ~560us mark, ~1690us space
    Sent LSB-first, as a command byte followed by its bitwise
    complement for error checking.

    Note: the receiver module inverts what it demodulates - the pin
    reads LOW while the 38 kHz carrier is present ("mark") and HIGH
    while it's absent ("space"), the opposite of what's actually being
    transmitted. Timing math only cares about durations between edges,
    so this doesn't need special-casing here.
    """

    if len(edge_ticks) < 36:
        return None

    def duration(i):
        return pigpio.tickDiff(edge_ticks[i], edge_ticks[i + 1])

    if not (8000 < duration(0) < 10000):
        return None
    if not (3500 < duration(1) < 5500):
        return None

    bits = []
    i = 2
    while i + 1 < len(edge_ticks) and len(bits) < 16:
        mark = duration(i)
        space = duration(i + 1)

        if not (300 < mark < 900):
            return None

        if 300 < space < 900:
            bits.append(0)
        elif 1400 < space < 2000:
            bits.append(1)
        else:
            return None

        i += 2

    if len(bits) < 16:
        return None

    def bits_to_byte(bit_list):
        value = 0
        for position, bit in enumerate(bit_list):
            value |= bit << position
        return value

    command = bits_to_byte(bits[0:8])
    inverted = bits_to_byte(bits[8:16])

    if command ^ inverted != 0xFF:
        return None

    return command


def listen(on_command):
    """
    Block forever, calling on_command(command) for each valid frame
    received. Malformed frames (bad checksum or timing) are silently
    dropped rather than passed through.
    """
    edges = []

    def _on_edge(gpio, level, tick):
        edges.append(tick)

    callback = pi.callback(IR_RECEIVER_PIN, pigpio.EITHER_EDGE, _on_edge)

    try:
        while True:
            sleep(0.05)

            idle_us = (
                pigpio.tickDiff(edges[-1], pi.get_current_tick()) if edges else 0
            )

            if len(edges) >= 36 and idle_us > 20000:
                command = decode(edges)
                if command is not None:
                    on_command(command)
                edges.clear()
            elif len(edges) > 100:
                # Runaway noise with no valid frame - drop it and start over.
                edges.clear()
    finally:
        callback.cancel()


def close():
    """Release the connection to the pigpio daemon."""
    pi.stop()


if __name__ == "__main__":

    def _print_command(command):
        print(f"command={command:3d}  {COMMAND_NAMES.get(command, 'UNKNOWN')}")

    print("Listening for IR commands. Press Ctrl+C to stop.")
    print()

    try:
        listen(_print_command)
    except KeyboardInterrupt:
        print()
        print("Receiver stopped.")
    finally:
        close()
