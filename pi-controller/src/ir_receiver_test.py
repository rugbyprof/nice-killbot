#!/usr/bin/env python3
"""
Diagnostic IR receiver for Raspberry Pi using pigpio.

Designed to test an ESP32 transmitter that sends an NEC-style frame:
    9 ms mark + 4.5 ms space
    8 command bits, LSB first
    8 inverted-command bits, LSB first
    optional trailing 560 us mark

Unlike a production receiver, this script prints useful diagnostics when a
frame cannot be decoded. It has no dependency on commands.py.

Wiring (BCM numbering):
    Receiver OUT -> GPIO 24 (physical pin 18)
    Receiver GND -> Pi GND
    Receiver VCC -> 3.3 V unless the module documentation explicitly says
                    its output is 3.3-V-safe when powered from 5 V

Run:
    sudo systemctl start pigpiod
    python3 ir_receiver_test.py

Optional:
    python3 ir_receiver_test.py --pin 24 --raw
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from dataclasses import dataclass

import pigpio


COMMAND_NAMES = {
    0: "STOP",
    1: "FORWARD",
    2: "BACKWARD",
    3: "LEFT",
    4: "RIGHT",
    5: "FORWARD_LEFT",
    6: "FORWARD_RIGHT",
    7: "BACKWARD_LEFT",
    8: "BACKWARD_RIGHT",
    9: "JOYSTICK_BUTTON",
}


@dataclass
class DecodeResult:
    command: int | None
    reason: str
    start_index: int | None = None


def in_range(value: int, low: int, high: int) -> bool:
    return low <= value <= high


def bits_to_byte(bits: list[int]) -> int:
    value = 0
    for position, bit in enumerate(bits):
        value |= bit << position
    return value


def decode_durations(durations: list[int]) -> DecodeResult:
    """Find and decode a 16-bit command/complement frame.

    Searching for the header rather than assuming it begins at durations[0]
    makes the test script more tolerant of an extra noise edge before a frame.
    """

    if len(durations) < 34:
        return DecodeResult(None, f"too few pulse intervals ({len(durations)}; need at least 34)")

    # A complete compact frame needs:
    #   header mark + header space + 16 * (bit mark + bit space)
    # = 34 durations. A trailing mark may add one more duration.
    for start in range(0, len(durations) - 33):
        header_mark = durations[start]
        header_space = durations[start + 1]

        if not in_range(header_mark, 8_000, 10_000):
            continue
        if not in_range(header_space, 3_500, 5_500):
            continue

        bits: list[int] = []
        index = start + 2

        for bit_number in range(16):
            mark = durations[index]
            space = durations[index + 1]

            if not in_range(mark, 300, 900):
                return DecodeResult(
                    None,
                    f"bit {bit_number}: invalid mark {mark} us",
                    start,
                )

            if in_range(space, 300, 900):
                bits.append(0)
            elif in_range(space, 1_300, 2_100):
                bits.append(1)
            else:
                return DecodeResult(
                    None,
                    f"bit {bit_number}: invalid space {space} us",
                    start,
                )

            index += 2

        command = bits_to_byte(bits[:8])
        inverted = bits_to_byte(bits[8:16])

        if (command ^ inverted) != 0xFF:
            return DecodeResult(
                None,
                f"complement check failed: command={command} (0x{command:02X}), "
                f"inverse={inverted} (0x{inverted:02X})",
                start,
            )

        return DecodeResult(command, "valid frame", start)

    return DecodeResult(None, "no 9 ms / 4.5 ms NEC-style header found")


def edges_to_durations(edge_ticks: list[int]) -> list[int]:
    return [
        pigpio.tickDiff(edge_ticks[i], edge_ticks[i + 1])
        for i in range(len(edge_ticks) - 1)
    ]


def format_durations(durations: list[int]) -> str:
    return " ".join(str(value) for value in durations)


def main() -> int:
    parser = argparse.ArgumentParser(description="Test an NEC-style IR receiver on Raspberry Pi")
    parser.add_argument("--pin", type=int, default=24, help="BCM GPIO pin (default: 24)")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="print all captured edge-to-edge durations, including valid frames",
    )
    parser.add_argument(
        "--idle-ms",
        type=float,
        default=20.0,
        help="idle gap that ends a frame (default: 20 ms)",
    )
    args = parser.parse_args()

    pi = pigpio.pi()
    if not pi.connected:
        print("ERROR: Could not connect to pigpiod.", file=sys.stderr)
        print("Start it with: sudo systemctl start pigpiod", file=sys.stderr)
        return 1

    pin = args.pin
    idle_us_required = int(args.idle_ms * 1_000)

    pi.set_mode(pin, pigpio.INPUT)
    pi.set_pull_up_down(pin, pigpio.PUD_UP)
    pi.set_glitch_filter(pin, 100)  # Ignore edges shorter than 100 us.

    edges: list[int] = []

    def on_edge(gpio: int, level: int, tick: int) -> None:
        del gpio, level
        edges.append(tick)

    callback = pi.callback(pin, pigpio.EITHER_EDGE, on_edge)
    running = True

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    print(f"Listening on BCM GPIO {pin} (physical pin 18 when pin=24).")
    print("Point the transmitter at the receiver and move the joystick.")
    print("Press Ctrl+C to stop.\n")

    try:
        while running:
            time.sleep(0.005)

            if not edges:
                continue

            idle_us = pigpio.tickDiff(edges[-1], pi.get_current_tick())
            if idle_us < idle_us_required:
                # Prevent unbounded growth if the input is noisy.
                if len(edges) > 300:
                    print(f"NOISE: discarded {len(edges)} edges without an idle gap")
                    edges.clear()
                continue

            captured = edges[:]
            edges.clear()

            durations = edges_to_durations(captured)
            result = decode_durations(durations)

            if result.command is not None:
                command = result.command
                name = COMMAND_NAMES.get(command, "UNKNOWN")
                print(
                    f"RECEIVED: command={command:3d}  hex=0x{command:02X}  "
                    f"name={name}  edges={len(captured)}"
                )
                if args.raw:
                    print(f"  durations_us: {format_durations(durations)}")
            else:
                print(
                    f"UNDECODED: edges={len(captured)} intervals={len(durations)}; "
                    f"{result.reason}"
                )
                if durations:
                    print(f"  durations_us: {format_durations(durations)}")

    finally:
        callback.cancel()
        pi.set_glitch_filter(pin, 0)
        pi.stop()
        print("\nReceiver stopped.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
