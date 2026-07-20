## Lab 3: Motors

**Goal:** wire four DC motors (one per wheel) to two L9110S dual motor
drivers and drive them forward and backward from a Python script.

Each L9110S only has two independent channels, so one board can't
reach all four motors - this lab pairs one driver with the front axle
and one with the rear axle, giving each of the four wheels its own
independently-controlled channel.

![Raspberry Pi 40-pin GPIO pinout](../images/pinout.png)

**Parts needed**

- Raspberry Pi (powered off while wiring)
- 2x L9110S dual motor driver module
- 4x DC gear motors
- Separate battery pack for the motors (matching your motors' voltage
  rating - do **not** power motors from the Pi's 5V pin)
- Breadboard (to fan out a shared ground rail to both drivers)
- 9x jumper wires (8 for control signals, 1 from the Pi to the shared
  ground rail)

**Step 1 - Power off before wiring**

Shut the Pi down (`sudo shutdown now`) or unplug it, and make sure the
motor battery is disconnected, before wiring anything.

**Step 2 - Identify the pins**

Using the reference pinout above, find:

Front driver (L9110S #1):

- **Physical pin 29** - `GPIO5` - Front-left forward (`A-IA`)
- **Physical pin 31** - `GPIO6` - Front-left backward (`A-IB`)
- **Physical pin 33** - `GPIO13` - Front-right forward (`B-IA`)
- **Physical pin 35** - `GPIO19` - Front-right backward (`B-IB`)

Rear driver (L9110S #2):

- **Physical pin 36** - `GPIO16` - Rear-left forward (`A-IA`)
- **Physical pin 37** - `GPIO26` - Rear-left backward (`A-IB`)
- **Physical pin 38** - `GPIO20` - Rear-right forward (`B-IA`)
- **Physical pin 40** - `GPIO21` - Rear-right backward (`B-IB`)

Shared ground:

- **Physical pin 39** - `Ground` - common ground for both drivers

**Step 3 - Build the circuit**

1.  Connect the front-left motor to L9110S #1's `MA` terminal, and the
    front-right motor to its `MB` terminal.
2.  Connect the rear-left motor to L9110S #2's `MA` terminal, and the
    rear-right motor to its `MB` terminal.
3.  Wire the motor battery pack's positive lead to `VCC` and negative
    lead to `GND` on **both** L9110S boards - they can share the same
    battery pack, just double up the connections (a small terminal
    block or a couple of extra jumpers works).
4.  Run a ground rail across the breadboard and connect both L9110S
    boards' `GND` to it, then connect the Pi's physical pin 39
    (`Ground`) to the same rail. The Pi and the motor battery **must**
    share a common ground (see [section
    7](../Raspberry_Pi_Robotics_Handbook_v0.1.md#7-motors)) - routing
    both drivers' ground through one shared rail keeps that true for
    both boards without needing two GPIO ground pins.
5.  On L9110S #1: connect `A-IA` to physical pin 29 (`GPIO5`), `A-IB`
    to pin 31 (`GPIO6`), `B-IA` to pin 33 (`GPIO13`), `B-IB` to pin 35
    (`GPIO19`).
6.  On L9110S #2: connect `A-IA` to physical pin 36 (`GPIO16`), `A-IB`
    to pin 37 (`GPIO26`), `B-IA` to pin 38 (`GPIO20`), `B-IB` to pin 40
    (`GPIO21`).

**Step 4 - Double-check before powering on**

- The Pi is powered from its own USB supply, and the motors are
  powered from the separate battery pack - never from the Pi's 5V
  pin.
- Every ground (Pi, both drivers, battery) is tied to the same rail.
- Both L9110S boards are getting `VCC`/`GND` from the battery pack.
- No bare wires are bridging adjacent pins.
- Four motors pull noticeably more current than two, especially at
  stall (wheels blocked) - make sure the battery pack and its wiring
  are rated for that, not just sized for two motors.
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
```

Grouping the motors into `left`/`right` lists (rather than four
separate calls) keeps the drive logic identical to the two-motor
version - `for motor in left: motor.forward()` reads the same whether
`left` has one motor or two. Because each wheel still has its own
channel, nothing stops you from addressing `rear_left` by itself later
(e.g. to tune out one wheel spinning faster than its pair).

**Step 8 - Run it**

Connect the motor battery, then run:

```bash
python motors.py
```

All four motors should spin forward for 2 seconds, pause, then spin
backward for 2 seconds. If a motor spins the wrong direction relative
to "forward," power everything off and swap that motor's two wires at
its `MA`/`MB` terminal - it's simpler than changing the code.

**Troubleshooting**

- **No motors spin:** check the battery is connected to `VCC`/`GND` on
  **both** drivers, and that both drivers' `GND` is tied to the Pi's
  ground rail.
- **All of one driver's motors are dead, the other driver's are
  fine:** re-check that driver's `VCC`/`GND` connections to the
  battery pack specifically - with two boards sharing one battery,
  it's easy to wire the second board's power and forget it.
- **One motor spins, its pair on the same driver doesn't:** re-check
  that motor's control wires (`A-IA`/`A-IB` or `B-IA`/`B-IB`) against
  the GPIO pins in the script, and that its screw terminal is seated
  firmly.
- **A motor spins the wrong direction:** swap its two wires at the
  `MA`/`MB` terminal.
- **Motors run weaker/slower than they did with just two:** the
  battery pack or its wiring may not be rated for four motors' worth
  of current, especially under load - voltage sags under the higher
  draw. Try a higher-capacity pack or heavier-gauge wiring before
  suspecting the code or the drivers.
- **`GPIO busy` or permission errors:** make sure no other script is
  already using GPIO5, 6, 13, 19, 16, 26, 20, or 21, and that you're
  in the virtual environment where `gpiozero` is installed.
