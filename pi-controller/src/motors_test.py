#!/usr/bin/env python3
"""
IR-controlled motor test for Raspberry Pi.

This script combines:

    ir_receiver_test.py  -> receives and decodes IR command integers
    motors.py            -> converts command integers into wheel movement

Required files in the same directory:

    motors_test.py
    motors.py
    ir_receiver_test.py
    commands.py

The ESP32 transmitter is expected to send these command numbers:

    0 = STOP
    1 = FORWARD
    2 = BACKWARD
    3 = LEFT
    4 = RIGHT
    5 = FORWARD_LEFT
    6 = FORWARD_RIGHT
    7 = BACKWARD_LEFT
    8 = BACKWARD_RIGHT
    9 = JOYSTICK_BUTTON

Safety behavior:

    If no valid IR command is received for DEADMAN_TIMEOUT seconds,
    the motors stop automatically.

Run:

    sudo systemctl start pigpiod
    python3 motors_test.py

Optional:

    python3 motors_test.py --pin 24
    python3 motors_test.py --raw
    python3 motors_test.py --timeout 0.75

IMPORTANT:
    Lift the wheels off the ground for the first test.
"""

from __future__ import annotations

import argparse
import signal
import sys
import time

import pigpio

import motors
from ir_receiver_test import (
    COMMAND_NAMES,
    decode_durations,
    edges_to_durations,
    format_durations,
)


VALID_COMMANDS = set(COMMAND_NAMES)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Control Raspberry Pi motors using decoded IR commands"
    )
    parser.add_argument(
        "--pin",
        type=int,
        default=24,
        help="BCM GPIO pin connected to the IR receiver (default: 24)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="print raw IR pulse durations",
    )
    parser.add_argument(
        "--idle-ms",
        type=float,
        default=20.0,
        help="idle gap that marks the end of an IR frame (default: 20 ms)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=0.75,
        help=(
            "stop motors after this many seconds without a valid command "
            "(default: 0.75)"
        ),
    )
    args = parser.parse_args()

    pi = pigpio.pi()

    if not pi.connected:
        print("ERROR: Could not connect to pigpiod.", file=sys.stderr)
        print("Start it with: sudo systemctl start pigpiod", file=sys.stderr)
        return 1

    pin = args.pin
    idle_us_required = int(args.idle_ms * 1_000)

    # Configure the IR receiver input.
    pi.set_mode(pin, pigpio.INPUT)
    pi.set_pull_up_down(pin, pigpio.PUD_UP)

    # Ignore tiny electrical glitches. Legitimate protocol pulses are
    # approximately 560 microseconds or longer.
    pi.set_glitch_filter(pin, 100)

    edge_ticks: list[int] = []

    def on_edge(gpio: int, level: int, tick: int) -> None:
        """Store the time of each rising or falling IR receiver edge."""
        del gpio, level
        edge_ticks.append(tick)

    callback = pi.callback(pin, pigpio.EITHER_EDGE, on_edge)

    running = True
    last_valid_command_time = time.monotonic()
    last_command: int | None = None
    timeout_stop_reported = False

    def request_shutdown(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)

    # Begin from a known safe state.
    motors.stop()

    print(f"Listening for IR commands on BCM GPIO {pin}.")
    print(f"Motor dead-man timeout: {args.timeout:.2f} seconds.")
    print("Lift the wheels for the first test.")
    print("Press Ctrl+C to stop.\n")

    try:
        while running:
            time.sleep(0.005)
            now = time.monotonic()

            # ----------------------------------------------------------
            # SAFETY TIMEOUT
            # ----------------------------------------------------------
            # If the transmitter disappears, the joystick loses power,
            # or an IR frame is missed for too long, stop the robot.
            if now - last_valid_command_time >= args.timeout:
                if last_command != 0:
                    motors.stop()
                    last_command = 0

                if not timeout_stop_reported:
                    print("TIMEOUT: no valid IR command; motors stopped")
                    timeout_stop_reported = True

            # Nothing has arrived from the IR receiver yet.
            if not edge_ticks:
                continue

            # Wait until the receiver has been idle long enough to indicate
            # that the complete IR frame has arrived.
            idle_us = pigpio.tickDiff(
                edge_ticks[-1],
                pi.get_current_tick(),
            )

            if idle_us < idle_us_required:
                # Avoid unlimited growth if the input is noisy.
                if len(edge_ticks) > 300:
                    print(
                        f"NOISE: discarded {len(edge_ticks)} edges "
                        "without a complete frame"
                    )
                    edge_ticks.clear()
                continue

            # Copy and clear the shared edge list before decoding.
            captured_edges = edge_ticks[:]
            edge_ticks.clear()

            durations = edges_to_durations(captured_edges)
            result = decode_durations(durations)

            if result.command is None:
                print(
                    f"UNDECODED: edges={len(captured_edges)}; "
                    f"{result.reason}"
                )

                if args.raw and durations:
                    print(
                        "  durations_us:",
                        format_durations(durations),
                    )

                continue

            command = result.command

            if command not in VALID_COMMANDS:
                # motors.drive() safely treats unknown commands as STOP,
                # but explicitly rejecting them makes debugging clearer.
                print(
                    f"UNKNOWN COMMAND: {command} (0x{command:02X}); "
                    "motors stopped"
                )
                motors.stop()
                last_command = 0
                continue

            # A valid frame refreshes the safety timer even if the command
            # is identical to the previous command.
            last_valid_command_time = now
            timeout_stop_reported = False

            # Repeated commands are expected as a transmitter heartbeat.
            # Only call drive() and print when the command changes.
            if command != last_command:
                name = COMMAND_NAMES.get(command, "UNKNOWN")
                print(
                    f"COMMAND: {command:2d}  "
                    f"hex=0x{command:02X}  "
                    f"name={name}"
                )

                motors.drive(command)
                last_command = command

            if args.raw:
                print(
                    "  durations_us:",
                    format_durations(durations),
                )

    finally:
        print("\nStopping motors and cleaning up GPIO...")
        motors.stop()
        callback.cancel()
        pi.set_glitch_filter(pin, 0)
        pi.stop()
        print("Motor test stopped.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
