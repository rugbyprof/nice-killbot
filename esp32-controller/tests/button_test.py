# Standalone push-button test.
#
# Not part of the joystick/IR remote pipeline - just for confirming a
# momentary push button is wired correctly before using it in a real
# project.
#
# Wiring:
#     Button leg (one side)  -> ESP32 GPIO4
#     Button leg (other side, diagonally opposite) -> ESP32 GND
#
# Push buttons have 4 legs: the two legs on each side are already
# connected to each other internally, and pressing the button bridges
# the two sides together. Land the two wires on diagonally opposite
# legs, not the same side, or it'll always read as "pressed."
#
# No resistor needed - PULL_UP enables the ESP32's internal pull-up
# resistor, so the pin reads HIGH when the button is untouched and
# LOW when pressed (the button connects the pin to GND).

from machine import Pin
from time import sleep_ms

BUTTON_PIN = 4

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

last_pressed = False

print("Button test. Press Ctrl+C to stop.")
print()

try:
    while True:
        is_pressed = button.value() == 0

        if is_pressed and not last_pressed:
            print("Button pressed")
        elif not is_pressed and last_pressed:
            print("Button released")

        last_pressed = is_pressed

        sleep_ms(20)  # simple debounce
except KeyboardInterrupt:
    print()
    print("Stopped.")
