# IR Protocol

The wire format spoken between `esp32-controller` (ESP32 transmitter)
and `pi-controller` (Raspberry Pi receiver). Both sides implement
this independently, so this document is the single source of truth -
if you change one side's timing or command IDs, update this file and
the other side to match.

Implementations:

- Transmitter: [`esp32-controller/src/lib/ir_transmitter.py`](../src/lib/ir_transmitter.py)
- Receiver: [`pi-controller/src/ir_receiver.py`](../../pi-controller/src/ir_receiver.py)

## Framing

Standard NEC-style pulse-distance encoding, carried on a 38 kHz IR
carrier. A "mark" is carrier-on, a "space" is carrier-off.

| Segment     | Mark    | Space                          |
| ----------- | ------- | ------------------------------- |
| Header      | 9000 µs | 4500 µs                         |
| Bit `0`     | 560 µs  | 560 µs                          |
| Bit `1`     | 560 µs  | 1690 µs                         |
| Final mark  | 560 µs  | (none - ends the frame)         |

A full frame is: header, command byte (LSB-first), inverted command
byte (`command ^ 0xFF`, LSB-first), final mark. 16 data bits total.

The receiver validates `command ^ inverted_command == 0xFF` and drops
anything that doesn't check out - this is the only error detection;
there's no retry/ack, so `esp32-controller` just retransmits the
current command periodically (`DEBOUNCE_DELAY` in `joystick.py`)
rather than confirming delivery.

**Receiver note:** a demodulating IR receiver module (TSOP38238 /
VS1838B) inverts what it demodulates - its output pin reads LOW during
a mark and HIGH during a space, the opposite of what's transmitted.
Timing math only cares about durations between edges, so this doesn't
affect decoding logic, only direct oscilloscope/logic-analyzer
probing.

## Command IDs

| ID  | Name              |
| --- | ----------------- |
| 0   | `STOP`            |
| 1   | `FORWARD`         |
| 2   | `BACKWARD`        |
| 3   | `LEFT`            |
| 4   | `RIGHT`           |
| 5   | `FORWARD_LEFT`    |
| 6   | `FORWARD_RIGHT`   |
| 7   | `BACKWARD_LEFT`   |
| 8   | `BACKWARD_RIGHT`  |
| 9   | `JOYSTICK_BUTTON` |

This table is duplicated as a plain dict (`COMMAND_NAMES`) in both
`joystick.py` and `ir_receiver.py`, since the two projects run on
different runtimes (MicroPython vs. CPython) with no shared import
path between them.

## Related labs

- [ESP32 Lab 2: IR Transmitter](../../docs/labs/Esp32/lab_02-ir_transmitter.md)
- [Pi Lab 4: IR Receiver](../../docs/labs/Pi/lab_04-ir_receiver.md)
