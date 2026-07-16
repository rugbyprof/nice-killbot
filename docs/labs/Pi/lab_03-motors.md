## Lab 3: Motors

**Goal:** wire two DC motors to an L9110S dual motor driver and drive
them forward and backward from a Python script.

![Raspberry Pi 40-pin GPIO pinout](../images/pinout.png)

**Parts needed**

- Raspberry Pi (powered off while wiring)
- L9110S dual motor driver module
- 2x DC gear motors
- Separate battery pack for the motors (matching your motors' voltage
  rating - do **not** power motors from the Pi's 5V pin)
- 5x jumper wires (4 for control signals, 1 for common ground)

**Step 1 - Power off before wiring**

Shut the Pi down (`sudo shutdown now`) or unplug it, and make sure the
motor battery is disconnected, before wiring anything.

**Step 2 - Identify the pins**

Using the reference pinout above, find:

- **Physical pin 29** - `GPIO5` - Motor A forward (`A-IA`)
- **Physical pin 31** - `GPIO6` - Motor A backward (`A-IB`)
- **Physical pin 33** - `GPIO13` - Motor B forward (`B-IA`)
- **Physical pin 35** - `GPIO19` - Motor B backward (`B-IB`)
- **Physical pin 39** - `Ground` - common ground with the driver

**Step 3 - Build the circuit**

1.  Connect one DC motor to the L9110S `MA` terminal, and the other
    to the `MB` terminal.
2.  Connect the motor battery pack's positive lead to `VCC` and
    negative lead to `GND` on the L9110S.
3.  Connect the L9110S `GND` to the Pi's physical pin 39 (`Ground`) -
    the Pi and the motor battery **must** share a common ground (see
    [section 7](../Raspberry_Pi_Robotics_Handbook_v0.1.md#7-motors)).
4.  Connect `A-IA` to physical pin 29 (`GPIO5`).
5.  Connect `A-IB` to physical pin 31 (`GPIO6`).
6.  Connect `B-IA` to physical pin 33 (`GPIO13`).
7.  Connect `B-IB` to physical pin 35 (`GPIO19`).

**Step 4 - Double-check before powering on**

- The Pi is powered from its own USB supply, and the motors are
  powered from the separate battery pack - never from the Pi's 5V
  pin.
- Every ground (Pi, driver, battery) is tied together.
- No bare wires are bridging adjacent pins.
- Prop the robot up on a block so the wheels are off the ground for
  the first test - if a motor spins the "wrong" way you'll fix it in
  Step 8, and you don't want it driving off the table in the meantime.

**Step 5 - Power on and connect**

Boot the Pi and connect over VS Code Remote SSH (see [section
3](../Raspberry_Pi_Robotics_Handbook_v0.1.md#3-vs-code-remote-ssh)).
Leave the motor battery disconnected until your script is ready to
run.

**Step 6 - Set up the environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install gpiozero
```

**Step 7 - Write the script**

Create `motors.py`:

```python
from gpiozero import Motor
from time import sleep

left = Motor(forward=5, backward=6)
right = Motor(forward=13, backward=19)

try:
    left.forward()
    right.forward()
    sleep(2)

    left.stop()
    right.stop()
    sleep(1)

    left.backward()
    right.backward()
    sleep(2)
finally:
    left.stop()
    right.stop()
```

**Step 8 - Run it**

Connect the motor battery, then run:

```bash
python motors.py
```

Both motors should spin forward for 2 seconds, pause, then spin
backward for 2 seconds. If a motor spins the wrong direction relative
to "forward," power everything off and swap that motor's two wires at
the `MA`/`MB` terminal - it's simpler than changing the code.

**Troubleshooting**

- **Neither motor spins:** check the battery is connected to `VCC`/
  `GND` on the driver, and that the driver's `GND` is tied to the
  Pi's ground.
- **One motor spins, the other doesn't:** re-check that motor's
  control wires (`A-IA`/`A-IB` or `B-IA`/`B-IB`) against the GPIO pins
  in the script, and that its screw terminal is seated firmly.
- **A motor spins the wrong direction:** swap its two wires at the
  `MA`/`MB` terminal.
- **`GPIO busy` or permission errors:** make sure no other script is
  already using GPIO5, GPIO6, GPIO13, or GPIO19, and that you're in
  the virtual environment where `gpiozero` is installed.
