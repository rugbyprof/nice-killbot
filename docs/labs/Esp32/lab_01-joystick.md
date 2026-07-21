## Esp32 Joystick

<a href="https://images2.imgbox.com/b5/4e/Kk89lTeY_o.png"><img src="https://images2.imgbox.com/b5/4e/Kk89lTeY_o.png" width="400"></a>

[joystick.py](../../../esp32-controller/src/joystick.py)

---

# Goal

Read a KY-023 dual-axis joystick (X, Y, and its built-in push button),
turn its position into a movement command (`STOP`, `FORWARD`,
`BACKWARD`, `LEFT`, `RIGHT`, and the four diagonals), and mirror the
current command onto an attached OLED status display.

`transmit_ir()` already encodes and drives a real 38 kHz signal on
`GPIO25` (via the `ir_transmitter` module) - but this lab doesn't wire
up the transmitter hardware itself, so nothing is actually plugged
into that output yet. [Lab 2](./lab_02-ir_transmitter.md) adds the
transmitter module and verifies the signal end-to-end.

---

# Hardware

- ESP-WROOM-32 development board
- KY-023 dual-axis joystick module
- SSD1306 128x64 I2C OLED display
- Breadboard and jumper wires

---

# Wiring

| Joystick pin | ESP32 pin |
| ------------ | --------- |
| VRx          | GPIO34    |
| VRy          | GPIO35    |
| SW           | GPIO32    |
| +            | 3V3       |
| GND          | GND       |

| OLED pin | ESP32 pin |
| -------- | --------- |
| VCC      | 3V3       |
| GND      | GND       |
| SDA      | GPIO21    |
| SCL      | GPIO22    |

`VRx`/`VRy` use `GPIO34`/`GPIO35` specifically because those are
ADC1-only pins - using an ADC2 pin here can conflict with Wi-Fi later,
since the radio uses ADC2 internally.

`SW` uses the ESP32's internal pull-up, so it reads `1` when not
pressed and `0` when pressed - no external resistor needed.

**The OLED must be wired and powered before you run the script.**
`joystick.py` imports `oled_screen`, which initializes the display the
moment it's imported - if the OLED isn't connected, the script will
crash with an I2C error before it ever reads the joystick.

---

# Files needed on the ESP32

```text
joystick.py          (top-level script, in src/)
lib/oled_screen.py    (dependency)
lib/ssd1306.py         (dependency)
lib/ir_transmitter.py   (dependency)
```

`joystick.py` is the driver you'll be editing, living directly in
`esp32-controller/src/`. The other three are dependencies it
imports, living in `esp32-controller/src/lib/` - MicroPython
automatically searches a device's `/lib` folder for imports, so
`import oled_screen` in `joystick.py` doesn't need to know or care
that the file lives in a subfolder on your computer.

---

# Step 1 - Copy the dependency files

These rarely change, so copy the whole `lib/` folder once with
`mpremote` (adjust the port for your OS - see [Esp32 First Setup,
Step 4](./Esp32-first-setup.md#step-4--plug-in-the-esp32)):

```bash
cd esp32-controller
mpremote connect /dev/cu.SLAB_USBtoUART fs cp -r src/lib :lib
```

---

# Step 2 - Run the joystick script

For fast iteration, run it directly from your computer without
copying it to the board's filesystem:

```bash
mpremote connect /dev/cu.SLAB_USBtoUART run src/joystick.py
```

Move the joystick. The terminal should print a line like:

```text
TRANSMITTING IR CODE FOR: FORWARD
```

roughly every 300ms (`DEBOUNCE_DELAY`), and the OLED should show the
current command name plus the raw `x`/`y` ADC readings.

Press the joystick's button (`SW`) - the button takes priority over
directional movement, so the command should switch to
`JOYSTICK_BUTTON` regardless of joystick position.

Stop it with `Ctrl-C`.

---

# How it works

`joystick.py` breaks into four pieces:

1.  **Reading** (`read_joystick`) - oversamples the ADC (`SAMPLES`
    reads averaged together) to smooth out electrical noise.
2.  **Classifying** (`get_direction`) - compares the reading against a
    calibrated center (`CENTER_X`/`CENTER_Y`) and a dead zone
    (`DEADZONE`), checking diagonals first so a forward-left position
    isn't collapsed into just `FORWARD`.
3.  **Debouncing** (`main`) - only transmits/redraws at most once per
    `DEBOUNCE_DELAY` milliseconds, instead of flooding the IR
    transmitter and OLED on every loop iteration.
4.  **Output** (`transmit_ir`, `oled_screen.show_status`) -
    `transmit_ir` delegates to the `ir_transmitter` module (see [Lab
    2](./lab_02-ir_transmitter.md)) to drive the real IR signal, while
    `oled_screen.show_status` draws to the display. Both are called
    with the same numeric command constant, looked up in
    `COMMAND_NAMES` for a human-readable label.

---

# Calibration

Every joystick rests at a slightly different center position.
`calibrate_joystick()` measures it by averaging `CALIBRATION_SAMPLES`
readings - but it's commented out in `main()` by default:

```python
# calibrate_joystick()
```

If your joystick's resting position is far enough from `(2048, 2048)`
that it reports a direction while sitting still, uncomment that line
so `main()` calibrates on startup, and leave the joystick untouched
for the second or so it takes to run.

---

# Uploading permanently

Once the script works, `esp32-controller/upload.sh` copies `src/lib/`
to the board's `/lib` and every top-level `.py` in `src/` to the board's
root (edit the `PORT` variable inside it first to match your OS).

`esp32-controller/src/` also contains `button_encoder_remote.py`, a
different, unrelated project (button + rotary-encoder IR transmitter).
It won't auto-run or collide with `joystick.py` - MicroPython only
auto-runs a file specifically named `main.py`, and neither script uses
that name, so both can sit on the board at once without conflict.
Run whichever one you want with `mpremote run <file>`.

---

# Troubleshooting

- **Script crashes immediately with an I2C error:** the OLED isn't
  wired, isn't powered, or `SDA`/`SCL` are swapped. Double-check the
  wiring table above.
- **`ImportError` for `oled_screen`, `ssd1306`, or `ir_transmitter`:**
  `src/lib/` wasn't copied to the board's `/lib`. Run `mpremote fs ls
  :lib` to confirm all three are present there.
- **Joystick reports a direction while sitting still:** your
  joystick's resting position differs from the default `(2048,
  2048)`. Uncomment `calibrate_joystick()` in `main()` (see
  *Calibration* above).
- **Directions feel swapped or mirrored:** the joystick's physical
  orientation doesn't match the code's assumptions. Swap the
  comparisons inside `get_direction()` (see the docstring's note about
  this) rather than rewiring anything.
- **Nothing happens at all:** confirm `VRx`/`VRy` are on `GPIO34`/
  `GPIO35`, not swapped with each other or with `SW`.
