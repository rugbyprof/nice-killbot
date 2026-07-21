"""
Command IDs shared across pi-controller's modules.

Matches the numeric command IDs defined in
esp32-controller/docs/protocol.md - keep both in sync.
"""

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

NAMES = {
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
