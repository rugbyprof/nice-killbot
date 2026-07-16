# Standalone HC-SR04 ultrasonic distance test.
#
# Not part of the joystick/IR remote pipeline - this is just for
# bringing up and testing an HC-SR04 on the ESP32 by itself. Prints a
# distance reading a few times a second and flags anything closer than
# OBSTACLE_THRESHOLD_CM.
#
# Wiring:
#     HC-SR04 VCC  -> ESP32 5V / VIN (HC-SR04 needs 5V to work reliably)
#     HC-SR04 GND  -> ESP32 GND
#     HC-SR04 TRIG -> ESP32 GPIO26 (direct - ESP32's 3.3V output is a
#                     valid HIGH for the sensor's trigger input)
#     HC-SR04 ECHO -> voltage divider -> ESP32 GPIO27
#
# IMPORTANT: ECHO swings up to VCC (5V) when the sensor is powered
# from 5V, but ESP32 GPIO pins are only 3.3V-tolerant. Connecting ECHO
# straight to a GPIO can damage the pin. Use a voltage divider on the
# ECHO line: a 1k resistor from ECHO to the GPIO, and a 2k resistor
# from that same GPIO to GND. That brings the 5V signal down to
# roughly 3.3V.

from machine import Pin, time_pulse_us
from time import sleep_ms, sleep_us

TRIG_PIN = 26
ECHO_PIN = 27

OBSTACLE_THRESHOLD_CM = 15
MAX_ECHO_WAIT_US = 30_000  # ~5m round trip - anything longer is "no echo"
SPEED_OF_SOUND_CM_PER_US = 0.0343

trig = Pin(TRIG_PIN, Pin.OUT)
trig.value(0)

echo = Pin(ECHO_PIN, Pin.IN)


def measure_distance_cm():
    """
    Trigger one ping and measure the echo's round-trip time.

    Returns:
        Distance in cm, or None if no echo came back in time (nothing
        in range, or the sensor isn't wired up).
    """
    trig.value(0)
    sleep_us(2)
    trig.value(1)
    sleep_us(10)  # HC-SR04 datasheet: trigger pulse must be >= 10us
    trig.value(0)

    duration_us = time_pulse_us(echo, 1, MAX_ECHO_WAIT_US)

    if duration_us < 0:
        # time_pulse_us returns a negative value on timeout.
        return None

    return (duration_us * SPEED_OF_SOUND_CM_PER_US) / 2


print("HC-SR04 obstacle test. Press Ctrl+C to stop.")
print()

try:
    while True:
        distance_cm = measure_distance_cm()

        if distance_cm is None:
            print("no echo (nothing in range, or check wiring)")
        elif distance_cm < OBSTACLE_THRESHOLD_CM:
            print(f"{distance_cm:6.1f} cm  *** OBSTACLE ***")
        else:
            print(f"{distance_cm:6.1f} cm")

        sleep_ms(200)  # HC-SR04 needs time to settle between pings
except KeyboardInterrupt:
    print()
    print("Stopped.")
