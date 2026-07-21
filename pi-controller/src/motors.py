"""
4-wheel differential (skid-steer) drive over two L9110S dual motor
drivers - see docs/labs/Pi/lab_03-motors.md for wiring.

Maps the command IDs from commands.py directly to wheel speeds. This
module knows nothing about IR or the OLED - callers just pass a
command byte to drive(), the same shape as oled_screen.show_status()
and what ir_receiver.listen()'s callback receives.

Public API:
    drive(command) -> None
    stop() -> None
"""

from gpiozero import Motor

import commands

front_left = Motor(forward=5, backward=6)
front_right = Motor(forward=13, backward=19)
rear_left = Motor(forward=16, backward=26)
rear_right = Motor(forward=20, backward=21)

left_motors = [front_left, rear_left]
right_motors = [front_right, rear_right]

FULL_SPEED = 1.0

# Speed of the "inside" side during a diagonal turn (FORWARD_LEFT,
# etc). Lower = tighter turn. The named side (LEFT in FORWARD_LEFT) is
# always the one that slows down, whether moving forward or backward -
# if your robot curves the "wrong" way specifically on the backward
# diagonals, that's a chassis/wiring quirk, not a bug: swap the two
# BACKWARD_LEFT/BACKWARD_RIGHT entries in _DRIVE_TABLE below.
TURN_SPEED = 0.4

# Skid-steer: turning slows or stops one side rather than reversing it.
# (Reversing one side while driving the other forward - a "tank
# pivot" - spins in place but is harder on the motors/gearboxes.)
#
# Each entry is (left_speed, right_speed): positive = forward,
# negative = backward, magnitude = fraction of full speed.
_DRIVE_TABLE = {
    commands.STOP: (0.0, 0.0),
    commands.FORWARD: (FULL_SPEED, FULL_SPEED),
    commands.BACKWARD: (-FULL_SPEED, -FULL_SPEED),
    commands.LEFT: (0.0, FULL_SPEED),
    commands.RIGHT: (FULL_SPEED, 0.0),
    commands.FORWARD_LEFT: (TURN_SPEED, FULL_SPEED),
    commands.FORWARD_RIGHT: (FULL_SPEED, TURN_SPEED),
    commands.BACKWARD_LEFT: (-TURN_SPEED, -FULL_SPEED),
    commands.BACKWARD_RIGHT: (-FULL_SPEED, -TURN_SPEED),
    commands.JOYSTICK_BUTTON: (0.0, 0.0),  # acts as an e-brake
}


def _set_side(motors, speed):
    if speed > 0:
        for motor in motors:
            motor.forward(speed)
    elif speed < 0:
        for motor in motors:
            motor.backward(-speed)
    else:
        for motor in motors:
            motor.stop()


def drive(command):
    """Drive all four wheels according to one of commands.py's IDs."""
    left_speed, right_speed = _DRIVE_TABLE.get(command, (0.0, 0.0))
    _set_side(left_motors, left_speed)
    _set_side(right_motors, right_speed)


def stop():
    """Immediately stop all four wheels."""
    drive(commands.STOP)


if __name__ == "__main__":
    # Standalone demo, matching Lab 3: confirms the wiring without
    # needing IR or the OLED.
    from time import sleep

    try:
        drive(commands.FORWARD)
        sleep(2)

        stop()
        sleep(1)

        drive(commands.BACKWARD)
        sleep(2)
    finally:
        stop()
