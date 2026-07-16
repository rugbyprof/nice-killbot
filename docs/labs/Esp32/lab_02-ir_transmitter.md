## Esp32 IR Transmitter

[joystick.py](../../../killbot-controller/src/joystick.py) ·
[ir_transmitter.py](../../../killbot-controller/src/ir_transmitter.py)

---

# Goal

Wire a 38 kHz IR transmitter to the ESP32 and send real infrared
commands - not just print statements - every time the joystick's
direction changes. This builds directly on [Lab
1](./lab_01-joystick.md): same `joystick.py`, but `transmit_ir()` now
actually transmits.

The frame format matches what `chillbot`'s IR receiver lab expects
(see [Raspberry Pi Lab 4: IR
Receiver](../Pi/lab_04-ir_receiver.md)), so once both sides are
wired up, moving the joystick should print matching `command=` lines
on the Pi.

---

# Hardware

- Everything from [Lab 1](./lab_01-joystick.md) (joystick + OLED),
  already wired and working
- 38 kHz IR transmitter module (or a plain IR LED + current-limiting
  resistor, if your module doesn't have one built in)
- 2 more jumper wires

---

# Wiring

| IR transmitter pin | ESP32 pin |
| ------------------- | --------- |
| SIG                  | GPIO25    |
| VCC                  | 3V3       |
| GND                  | GND       |

If you're using a bare IR LED instead of a breakout module, put a
220-330 Ω resistor in series and make sure the LED's polarity is
correct (flat side / short leg -\> `GND`).

---

# How the protocol works

The wire protocol itself lives in its own file, `ir_transmitter.py` -
it doesn't know anything about joysticks or command names, only how to
put a byte on the air. `joystick.py` imports it and calls
`ir_transmitter.send_ir_command(command)`, the same way it already
calls `oled_screen.show_status(...)` for the display.

`ir_transmitter.py` defines a `PWM` object on `GPIO25` at 38 kHz
(`ir_pwm`). Sending a command means turning that carrier on and off in
specific, timed patterns - "marks" (carrier on) and "spaces" (carrier
off):

- **Header** - a 9000 µs mark, then a 4500 µs space. This tells the
  receiver "a new frame is starting."
- **Each bit** - a 560 µs mark, followed by either a 560 µs space
  (binary `0`) or a 1690 µs space (binary `1`). This is called
  pulse-distance encoding: every bit has the same mark length, and
  only the space length carries information.
- **Two bytes per frame** - the command byte, least-significant bit
  first, followed by its bitwise complement (`command ^ 255`). The
  receiver checks `command + inverted_command == 255` and throws away
  anything that doesn't match - cheap error detection without a full
  checksum.
- **Final mark** - one more 560 µs mark to close out the frame.

`send_ir_command()` in `ir_transmitter.py` implements exactly this,
built from three smaller pieces:

```text
ir_mark(duration_us)     turn the carrier on for duration_us
ir_space(duration_us)    turn the carrier off for duration_us
send_ir_bit(bit_value)   one mark + one space, choosing the space length
send_ir_byte(value)      8 calls to send_ir_bit, LSB first
send_ir_command(command) header + command byte + inverted byte + final mark
```

Back in `joystick.py`, `transmit_ir()` - the function `main()` actually
calls every time the debounce timer allows it - does two things:
prints the command name for you to watch over serial, and calls
`ir_transmitter.send_ir_command()` to put it on the air.

---

# Step 1 - Run it

```bash
cd killbot-controller
mpremote connect /dev/cu.SLAB_USBtoUART fs cp src/ir_transmitter.py :
mpremote connect /dev/cu.SLAB_USBtoUART run src/joystick.py
```

(`oled_screen.py` and `ssd1306.py` still need to already be on the
board from Lab 1, and `ir_transmitter.py` now needs to be there too -
`joystick.py` imports all three.)

Move the joystick. You should see the same `TRANSMITTING IR CODE
FOR: ...` lines as Lab 1, but now an actual 38 kHz signal goes out on
`GPIO25` each time.

---

# Step 2 - Check it without a receiver yet

Most phone cameras can see infrared light that's invisible to your
eyes. Point the transmitter at a phone camera (not a DSLR/mirrorless -
many have IR filters) and move the joystick - you should see the LED
flicker/glow on screen when a command fires.

---

# Step 3 - Test against chillbot

Once the Raspberry Pi's IR receiver from [Pi Lab 4: IR
Receiver](../Pi/lab_04-ir_receiver.md) is wired and running
(`python src/ir_receiver.py`, or `python src/main.py` if [Pi Lab 5:
OLED Screen](../Pi/lab_05-oled_screen.md) is done too), point the
ESP32's transmitter at the Pi's receiver module (a few centimeters to
a meter away, depending on your parts) and move the joystick. The
Pi's terminal should print lines like:

```text
command=  1  FORWARD
```

matching the direction you're holding. Both `COMMAND_NAMES` tables
were written to agree, so the numbers line up without any translation
step.

---

# Troubleshooting

- **No IR at all (checked with a phone camera):** confirm `SIG` is on
  `GPIO25`, and that the module has power (`VCC`/`GND`). If using a
  bare LED, check its polarity.
- **Phone camera sees a flicker, but the Pi never decodes anything:**
  distance/angle - IR is fairly directional and loses range fast in
  bright ambient light. Move the two closer together and point them
  straight at each other.
- **Pi decodes frames, but the command name is wrong or `UNKNOWN`:**
  double check `killbot-controller/src/joystick.py`'s `COMMAND_NAMES`
  still matches the table in `chillbot-controller/src/ir_receiver.py`
  - both were written to agree, but if either file gets edited
  independently they can drift apart. The full protocol is documented
  once, in
  [killbot-controller/docs/protocol.md](../../../killbot-controller/docs/protocol.md).
- **OLED stops updating / script crashes:** this is unrelated to IR -
  see Lab 1's troubleshooting section for OLED/joystick issues.
- **Script exits but the transmitter LED stays lit:** shouldn't
  happen - `finally: ir_transmitter.ir_off()` at the bottom of
  `joystick.py` turns the carrier off on any exit, including
  `Ctrl-C`. If it does happen, power-cycle the board.
- **`ImportError` for `ir_transmitter`:** it wasn't copied to the
  board. Run `mpremote fs ls` to confirm it's present alongside
  `oled_screen.py` and `ssd1306.py`.
