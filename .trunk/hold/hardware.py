from machine import ADC
from machine import Pin

from config import *

x_axis = ADC(Pin(JOYSTICK_X))
y_axis = ADC(Pin(JOYSTICK_Y))

button = Pin(
    JOYSTICK_SW,
    Pin.IN,
    Pin.PULL_UP,
)

status_led = Pin(
    STATUS_LED,
    Pin.OUT,
)
