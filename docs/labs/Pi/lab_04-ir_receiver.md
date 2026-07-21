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
sudo apt install -y pigpio python3-pigpio
sudo systemctl enable --now pigpiod

cd pi-controller
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The `--system-site-packages` flag matters here for the same reason it
does for `gpiozero` (see [First Setup](../Raspberry-pi-first-setup.md)):
`python3-pigpio`, installed via `apt`, needs to be visible from inside
the venv.

**Step 7 - The script**

The decoder already lives in the repo:
[`pi-controller/src/ir_receiver.py`](../../../pi-controller/src/ir_receiver.py).
No need to write it from scratch - clone/pull the repo onto the Pi (or
`scp` just that file over) so it's alongside this lab's venv.

It's built from a few pieces:

```text
decode(edge_ticks)   turn a list of edge timestamps into a command byte, or None
listen(on_command)   block forever; call on_command(command) for each valid frame
close()              release the pigpio connection
```

`decode()` implements the standard NEC IR protocol - a `~9000us` mark
+ `~4500us` space header, then 16 bits (`~560us` mark + `~560us` or
`~1690us` space, LSB-first) forming a command byte and its bitwise
complement. Frames that don't check out (`command ^ inverted != 0xFF`,
or timings outside the expected windows) are silently discarded rather
than passed to `on_command`.

**One inversion to keep in mind:** the receiver module flips what it
demodulates - its `OUT` pin reads LOW while the 38 kHz carrier is
present ("mark") and HIGH while it's absent ("space"), the opposite of
what's actually being transmitted. `decode()` only cares about
durations between edges, so this doesn't need special-casing in code -
just don't be surprised if you ever probe the pin directly.

`ir_receiver.py` also has its own `if __name__ == "__main__":` block,
so it can be run standalone (just prints decoded commands) before
wiring it into anything else - see Step 8.

**Step 8 - Run it**

```bash
python src/ir_receiver.py
```

Point a remote at the receiver and press a button - you should see a
`command=` line printed. Frames with a bad checksum or malformed
timing are silently dropped rather than printed as garbage.

**Troubleshooting**

- **Nothing prints, ever:** confirm `pigpiod` is running
  (`sudo systemctl status pigpiod`), and that `OUT` is on `GPIO24`
  (physical pin 18), not swapped with `VCC`/`GND`.
- **`Could not connect to pigpio daemon`:** the daemon isn't running -
  `sudo systemctl enable --now pigpiod`, then try again.
- **Sporadic/garbage frames with no button pressed:** these receivers
  pick up ambient IR noise (sunlight, some fluorescent/LED lighting).
  This is expected - the checksum check in `decode()` filters most of
  it out.
- **Frames never decode even with a known-good remote:** some remotes
  use a different protocol (not NEC). Try a different remote, or the
  killbot ESP32 transmitter (see [ESP32 Lab 2: IR
  Transmitter](../Esp32/lab_02-ir_transmitter.md)).
- **`GPIO busy` or permission errors:** make sure no other script is
  already using GPIO24, and that `python3-pigpio` is visible from your
  venv (`--system-site-packages`).
