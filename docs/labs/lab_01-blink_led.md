## Lab 1: Blink LED

**Goal:** wire an LED to the Pi's GPIO header and blink it on/off from a
Python script.

<a href="https://images2.imgbox.com/74/6e/oFYXUW8F_o.png"><img src="https://images2.imgbox.com/74/6e/oFYXUW8F_o.png" width="400px"></a>

**Parts needed**

- Raspberry Pi (powered off while wiring)
- Breadboard
- 1x LED
- 1x 220-330 Ω resistor
- 2x jumper wires (male-to-male, or male-to-female depending on your
  breadboard)

**Step 1 - Power off before wiring**

Shut the Pi down (`sudo shutdown now`) or unplug it before touching the
GPIO header. Wiring a live board risks shorting a pin.

**Step 2 - Identify the pins**

Using the reference pinout below (`images/pinout.png`), find:

- **Physical pin 11** - `GPIO17`
- **Physical pin 6** - `Ground`

<img src="https://images2.imgbox.com/b4/25/Iuw2LyrT_o.png" alt="Raspberry Pi 40-pin GPIO pinout">

**Step 3 - Build the circuit**

1.  Place the LED on the breadboard, straddling the center gap.
2.  Note the long leg (anode, +) and short leg (cathode, -).
3.  Connect physical pin 11 (`GPIO17`) -\> resistor -\> LED long leg
    (anode).
4.  Connect LED short leg (cathode) -\> physical pin 6 (`Ground`).

The resistor can sit on either leg of the LED as long as it's
somewhere in the loop - its job is just to limit current.

**Step 4 - Double-check before powering on**

- LED and resistor are in series between GPIO17 and Ground.
- No bare wires are bridging adjacent pins.
- If the LED is backwards it simply won't light (it won't damage
  anything).

**Step 5 - Power on and connect**

Boot the Pi and connect over VS Code Remote SSH (see [section
3](#3-vs-code-remote-ssh)).

**Step 6 - Set up the environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install gpiozero
```

**Step 7 - Write the script**

Create `blink.py`:

```python
from gpiozero import LED
from time import sleep

led = LED(17)

try:
    while True:
        led.on()
        sleep(1)
        led.off()
        sleep(1)
except KeyboardInterrupt:
    led.off()
```

**Step 8 - Run it**

```bash
python blink.py
```

The LED should turn on and off once per second. Press `Ctrl+C` to stop

- the `except` block turns the LED off cleanly on exit.

**Troubleshooting**

- **Nothing lights up:** check the LED orientation (flip it around),
  and confirm the resistor and jumpers are seated firmly.
- **`GPIO busy` or permission errors:** make sure no other script is
  already using GPIO17, and that you're in the virtual environment
  where `gpiozero` is installed.
- **Still nothing:** verify pin 11 and pin 6 against the pinout image
  again - it's easy to be off by one row.
