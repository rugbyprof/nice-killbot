## Lab 2: Button

**Goal:** wire a momentary push button to the Pi's GPIO header and read
button presses from a Python script.

<a href="https://images2.imgbox.com/1d/59/WJPeeFfg_o.png" target="_new"><img src="https://images2.imgbox.com/1d/59/WJPeeFfg_o.png" alt="Raspberry Pi Button Led Diagram" width="400">

<a href="https://images2.imgbox.com/b4/25/Iuw2LyrT_o.png" target="_new"><img src="https://images2.imgbox.com/b4/25/Iuw2LyrT_o.png" alt="Raspberry Pi 40-pin GPIO pinout" width="400">

**Parts needed**

- Raspberry Pi (powered off while wiring)
- Breadboard
- 1x momentary push button
- 2x jumper wires (male-to-male, or male-to-female depending on your
  breadboard)

**Step 1 - Power off before wiring**

Shut the Pi down (`sudo shutdown now`) or unplug it before touching the
GPIO header. Wiring a live board risks shorting a pin.

**Step 2 - Identify the pins**

Using the reference pinout above, find:

- **Physical pin 13** - `GPIO27`
- **Physical pin 14** - `Ground`

**Step 3 - Build the circuit**

1.  Place the button on the breadboard, straddling the center gap.
    Push buttons have 4 legs: the two legs on each side are already
    connected to each other internally, and pressing the button
    bridges the two sides together.
2.  Connect physical pin 13 (`GPIO27`) to one leg on one side of the
    button.
3.  Connect physical pin 14 (`Ground`) to the diagonally opposite leg,
    on the other side of the button.

No resistor is needed - `gpiozero` enables the Pi's internal pull-up
resistor by default, so the pin reads HIGH when the button is
untouched and LOW when it's pressed.

**Step 4 - Double-check before powering on**

- The two jumper wires land on opposite sides of the button, not the
  same side (same-side legs are always connected, so the button would
  never register as "unpressed").
- `Ground` is wired to pin 14, not a 3V3 or 5V pin.
- No bare wires are bridging adjacent pins.

**Step 5 - Power on and connect**

Boot the Pi and connect over VS Code Remote SSH (see [section
3](../Raspberry_Pi_Robotics_Handbook_v0.1.md#3-vs-code-remote-ssh)).

**Step 6 - Set up the environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install gpiozero
```

**Step 7 - Write the script**

Create `button.py`:

```python
from gpiozero import Button
from signal import pause

button = Button(27)

button.when_pressed = lambda: print("Button pressed")
button.when_released = lambda: print("Button released")

pause()
```

**Step 8 - Run it**

```bash
python button.py
```

Press the button - you should see "Button pressed" and "Button
released" printed as you press and let go. Press `Ctrl+C` to stop.

**Troubleshooting**

- **No output when pressed:** confirm the two jumpers land on
  diagonally opposite legs of the button, not the same side.
- **Stuck on "pressed" or never changes:** double-check `Ground` is on
  pin 14 and not accidentally on a 3V3/5V pin.
- **`GPIO busy` or permission errors:** make sure no other script is
  already using GPIO27, and that you're in the virtual environment
  where `gpiozero` is installed.
