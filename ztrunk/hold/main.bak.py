from joystick import Joystick
from protocol import build_packet
from ir_tx import IRTransmitter

joystick = Joystick()
ir = IRTransmitter()

while True:

    direction = joystick.direction()

    packet = build_packet(direction)

    ir.send(packet)
