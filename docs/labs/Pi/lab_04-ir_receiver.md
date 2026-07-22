## Lab 4: IR Receiver

[ir_receiver.py](../../../pi-controller/src/ir_receiver.py)

**Goal:** wire a 38 kHz IR receiver module to the Pi and decode incoming
infrared pulses (from any standard NEC-protocol remote, or from the
killbot ESP32 transmitter - see [ESP32 Lab 2: IR
Transmitter](../Esp32/lab_02-ir_transmitter.md)) into a command byte.

<a href="https://images2.imgbox.com/b4/25/Iuw2LyrT_o.png" target="_new"><img src="https://images2.imgbox.com/b4/25/Iuw2LyrT_o.png" alt="Raspberry Pi 40-pin GPIO pinout" width="400">

**Parts needed**

- Raspberry Pi (powered off while wiring)
- Breadboard
- 1x IR receiver module (TSOP38238 or VS1838B, 3-pin: VCC/GND/OUT)
- 3x jumper wires
- Something to test with: a 38 kHz NEC-protocol remote (e.g. a
  cheap TV/AC remote), or the killbot ESP32 transmitter

**Step 1 - Power off before wiring**

Shut the Pi down (`sudo shutdown now`) or unplug it before touching the
GPIO header. Wiring a live board risks shorting a pin.

**Step 2 - Identify the pins**

Using the reference pinout above, find:

- **Physical pin 1** - `3V3` - receiver `VCC`
- **Physical pin 6** - `Ground` - receiver `GND`
- **Physical pin 18** - `GPIO24` - receiver `OUT`

**Step 3 - Build the circuit**

1.  Check your module's silkscreen for the order of its three legs -
    it varies between breakout boards.
2.  Connect `VCC` to physical pin 1 (`3V3`). Use 3.3V, not 5V - the
    receiver's logic-level output needs to match the Pi's GPIO
    directly, with no level shifter in between.
3.  Connect `GND` to physical pin 6 (`Ground`).
4.  Connect `OUT` to physical pin 18 (`GPIO24`).

**Step 4 - Double-check before powering on**

- `VCC` is on `3V3`, not `5V`.
- `OUT` lands on `GPIO24`, not `VCC` or `GND`.
- No bare wires are bridging adjacent pins.

**Step 5 - Power on and connect**

Boot the Pi and connect over VS Code Remote SSH (see [section
3](../Raspberry_Pi_Robotics_Handbook_v0.1.md#3-vs-code-remote-ssh)).

**Step 6 - Set up the environment**

This lab needs microsecond-accurate pulse timing, which `gpiozero`
alone doesn't provide - it uses the `pigpio` library and its
background daemon instead.

```bash
sudo apt install -y python3-pigpio
```

`pigpio` (the daemon itself) isn't packaged for Raspberry Pi OS
Bookworm onward - see [First
Setup](../Raspberry-pi-first-setup.md#create-a-project) for building
it from source and registering it as a systemd service. Once
`sudo systemctl status pigpiod` shows active (running):

```bash
cd pi-controller
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The `--system-site-packages` flag matters here for the same reason it
does for `gpiozero` (see [First Setup](../Raspberry-pi-first-setup.md)):
`python3-pigpio`, installed via `apt`, needs to be visible from inside
the venv.

**Step 7 - Bring-up test**

Wiring bring-up is easier with a script that tells you *why* a frame
failed instead of just staying silent. That's what
[`pi-controller/src/ir_receiver_test.py`](../../../pi-controller/src/ir_receiver_test.py)
is for - it decodes the same NEC-style frames as the production
`ir_receiver.py`, but:

- searches for the header anywhere in the captured edges instead of
  assuming it starts at the very first one, so a stray noise edge
  before a real frame doesn't throw off the whole decode
- adds a pull-up (`PUD_UP`) and a 100 us glitch filter on the input,
  which cuts down on false triggers
- prints the specific reason a frame didn't decode (bad header, bad
  bit timing, checksum mismatch) rather than dropping it silently

It has no dependency on `commands.py`, so it can be copied to the Pi
and run entirely on its own - clone/pull the repo (or `scp` just that
file over) so it's alongside this lab's venv.

**Step 8 - Run it**

```bash
python3 src/ir_receiver_test.py
```

Point a remote at the receiver and press a button. A good frame looks
like:

```text
RECEIVED: command=  1  hex=0x01  name=FORWARD  edges=36
```

A bad one tells you why, instead of just staying silent:

```text
UNDECODED: edges=30 intervals=29; too few pulse intervals (29; need at least 34)
UNDECODED: edges=36 intervals=35; bit 4: invalid space 2400 us
UNDECODED: edges=36 intervals=35; complement check failed: command=1 (0x01), inverse=1 (0x01)
```

Useful flags:

```bash
python3 src/ir_receiver_test.py --pin 24      # non-default wiring
python3 src/ir_receiver_test.py --raw         # also print every decoded frame's raw durations
python3 src/ir_receiver_test.py --idle-ms 30  # widen the gap that ends a frame
```

**One inversion to keep in mind:** the receiver module flips what it
demodulates - its `OUT` pin reads LOW while the 38 kHz carrier is
present ("mark") and HIGH while it's absent ("space"), the opposite of
what's actually being transmitted. The decoder only cares about
durations between edges, so this doesn't need special-casing in code -
just don't be surprised if you ever probe the pin directly.

**Troubleshooting**

- **Nothing prints, ever:** confirm `pigpiod` is running
  (`sudo systemctl status pigpiod`), and that `OUT` is on `GPIO24`
  (physical pin 18), not swapped with `VCC`/`GND`.
- **`Could not connect to pigpiod`:** the daemon isn't running -
  `sudo systemctl enable --now pigpiod`, then try again.
- **`too few pulse intervals`:** the frame got cut off partway through
  - weak/dying remote battery, receiver too far from the transmitter,
  or something interrupting line of sight.
- **`no 9 ms / 4.5 ms NEC-style header found`:** either the remote uses
  a different protocol, or what's arriving is noise with no real frame
  in it at all - add `--raw` to see the actual durations.
- **`bit N: invalid mark/space`:** a timing fell outside the expected
  window - move closer, check for interference (sunlight, some
  fluorescent/LED lighting), and confirm the receiver is on 3.3V, not
  5V.
- **`complement check failed`:** the frame's shape decoded fine but the
  checksum doesn't match - usually a marginal signal (partial dropout
  mid-frame) rather than the wrong protocol.
- **Sporadic/garbage frames with no button pressed:** ambient IR noise
  landing between valid frames. Expected - a real remote or the
  killbot ESP32 transmitter (see [ESP32 Lab 2: IR
  Transmitter](../Esp32/lab_02-ir_transmitter.md)) will still decode
  correctly.
- **`GPIO busy` or permission errors:** make sure no other script is
  already using GPIO24, and that `python3-pigpio` is visible from your
  venv (`--system-site-packages`).

**Step 9 - Full integration test (motors + IR)**

With this lab and [Lab 3: Motors](./lab_03-motors.md) both wired, you
can test the whole car end-to-end before wiring anything into
`main.py`:
[`pi-controller/src/motors_test.py`](../../../pi-controller/src/motors_test.py)
combines `ir_receiver_test.py`'s decoder with the real `motors.py`, so
every decoded IR command actually drives the wheels.

**Lift the wheels off the ground before running this** - it drives all
four wheels at full speed, the same wiring `main.py` will eventually
use.

```bash
python3 src/motors_test.py
```

It expects the ESP32 transmitter's command numbers (`0`=`STOP` through
`9`=`JOYSTICK_BUTTON` - see
[esp32-controller/docs/protocol.md](../../../esp32-controller/docs/protocol.md)),
prints each command as it changes, and stops the motors automatically
if no valid command arrives for 0.75 seconds (transmitter switched
off, out of range, etc.) - a dead-man safety timeout:

```bash
python3 src/motors_test.py --timeout 1.5   # more forgiving timeout
python3 src/motors_test.py --raw           # also print raw pulse durations
```

Ctrl+C stops the motors and releases the GPIO pins before exiting,
same as `ir_receiver_test.py`.

---

**Next step:** everything through Step 9 has been standalone bring-up
and diagnostic scripts. The production pieces they stand in for -
[`ir_receiver.py`](../../../pi-controller/src/ir_receiver.py)'s
`decode()`/`listen()`/`close()` and
[`motors.py`](../../../pi-controller/src/motors.py)'s
`drive()`/`stop()` - are wired together by
[`main.py`](../../../pi-controller/src/main.py), which also mirrors
the current command on the OLED (see [Pi Lab 5: OLED
Screen](./lab_05-oled_screen.md)).
