from gpiozero import Motor
from time import sleep

front_left = Motor(forward=5, backward=6)
front_right = Motor(forward=13, backward=19)
rear_left = Motor(forward=16, backward=26)
rear_right = Motor(forward=20, backward=21)

left = [front_left, rear_left]
right = [front_right, rear_right]
all_motors = left + right

try:
    for motor in all_motors:
        motor.forward()
    sleep(2)

    for motor in all_motors:
        motor.stop()
    sleep(1)

    for motor in all_motors:
        motor.backward()
    sleep(2)
finally:
    for motor in all_motors:
        motor.stop()
