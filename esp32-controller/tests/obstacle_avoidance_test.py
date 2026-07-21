# Standalone FC-51 IR obstacle sensor test.
#
# Not part of the joystick/IR remote pipeline - this is just for
# bringing up and testing an FC-51 on the ESP32 by itself.
#
# The FC-51 is a digital IR obstacle sensor: an IR LED + photodiode
# pair with an onboard LM393 comparator. It only reports
# obstacle-or-not, not a distance - there's no pulse timing involved,
# unlike an HC-SR04. Detection range (roughly 2-80cm) is set by the
# potentiometer on the module itself, not in software.
#
# Wiring (3 pins):
#     FC-51 VCC -> ESP32 3V3
#     FC-51 GND -> ESP32 GND
#     FC-51 OUT -> ESP32 GPIO26
#
# The comparator actively drives OUT itself, so no internal pull
# resistor is needed. Most FC-51 boards drive OUT LOW when an obstacle
# is detected and HIGH when clear - if yours reads backwards, flip the
# comparison in `obstacle_detected()` below rather than rewiring.

from machine import Pin
from time import sleep_ms

SENSOR_PIN = 26

sensor = Pin(SENSOR_PIN, Pin.IN)


def obstacle_detected():
    """True when the FC-51 reports something in range."""
    return sensor.value() == 0


print("FC-51 obstacle test. Press Ctrl+C to stop.")
print()

last_detected = None

try:
    while True:
        detected = obstacle_detected()

        if detected != last_detected:
            print("*** OBSTACLE ***" if detected else "clear")
            last_detected = detected

        sleep_ms(50)
except KeyboardInterrupt:
    print()
    print("Stopped.")
