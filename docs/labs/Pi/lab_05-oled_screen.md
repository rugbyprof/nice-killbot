## Lab 5: OLED Screen

[oled_screen.py](../../../pi-controller/src/oled_screen.py)

**Goal:** wire an SSD1306 128x64 I2C OLED display to the Pi and show
text on it from a Python script.

<a href="https://images2.imgbox.com/b4/25/Iuw2LyrT_o.png" target="_new"><img src="https://images2.imgbox.com/b4/25/Iuw2LyrT_o.png" alt="Raspberry Pi 40-pin GPIO pinout" width="400">

**Parts needed**

- Raspberry Pi (powered off while wiring)
- Breadboard
- 1x SSD1306 128x64 I2C OLED display module (4-pin: VCC/GND/SCL/SDA)
- 4x jumper wires

**Step 1 - Power off before wiring**

Shut the Pi down (`sudo shutdown now`) or unplug it before touching the
GPIO header. Wiring a live board risks shorting a pin.

**Step 2 - Identify the pins**

Using the reference pinout above, find:

- **Physical pin 1** - `3V3` - OLED `VCC`
- **Physical pin 3** - `GPIO2` (`SDA`) - OLED `SDA`
- **Physical pin 5** - `GPIO3` (`SCL`) - OLED `SCL`
- **Physical pin 9** - `Ground` - OLED `GND`

Pins 3 and 5 are the Pi's dedicated hardware I2C bus (I2C1) - unlike
the GPIO pins used in earlier labs, these two can't be swapped for
other GPIOs, since I2C needs the Pi's dedicated I2C controller.

**Step 3 - Build the circuit**

1.  Connect `VCC` to physical pin 1 (`3V3`). Do not use `5V` - most
    SSD1306 breakout boards run their logic at 3.3V (check your
    module's silkscreen if unsure).
2.  Connect `GND` to physical pin 9 (`Ground`).
3.  Connect `SDA` to physical pin 3 (`GPIO2` / `SDA`).
4.  Connect `SCL` to physical pin 5 (`GPIO3` / `SCL`).

**Step 4 - Double-check before powering on**

- `SDA` and `SCL` aren't swapped - double-check against the module's
  silkscreen labels.
- `VCC` is on `3V3`, not `5V`.
- No bare wires are bridging adjacent pins.

**Step 5 - Power on, enable I2C, and connect**

Boot the Pi and connect over VS Code Remote SSH (see [section
3](../Raspberry_Pi_Robotics_Handbook_v0.1.md#3-vs-code-remote-ssh)).

If I2C isn't already enabled (it is automatically if you ran
`chillbot_bootstrap.sh`):

```bash
sudo raspi-config
```

`Interface Options` -\> `I2C` -\> `Enable`, then reboot.

Verify the OLED is detected:

```bash
sudo apt install -y i2c-tools
i2cdetect -y 1
```

You should see a device listed at address `3c` (occasionally `3d` on
some modules) in the grid.

**Step 6 - Set up the environment**

```bash
cd pi-controller
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Step 7 - The script**

The driver already lives in the repo:
[`pi-controller/src/oled_screen.py`](../../../pi-controller/src/oled_screen.py) -
clone/pull the repo onto the Pi (or `scp` just that file over) rather
than writing it from scratch.

It exposes three functions, deliberately unaware of IR or anything
else - it only knows how to put text on the screen:

```text
show_lines(*lines)          render each argument as its own row
show_status(label, extra)   a status label plus an optional detail line
clear()                     blank the display
```

It also has its own `if __name__ == "__main__":` block: a small demo
that shows "chillbot" and an uptime counter, incrementing once per
second, so you can confirm the wiring works before hooking it up to
anything else.

**Step 8 - Run it**

```bash
python src/oled_screen.py
```

The screen should show "chillbot" and an uptime counter that increases
once per second. Press `Ctrl+C` to stop - the display clears on exit.

**Troubleshooting**

- **Nothing shows up:** run `i2cdetect -y 1` again to confirm the
  module appears at `3c`. If it doesn't appear at all, re-check
  `SDA`/`SCL` aren't swapped and that I2C is enabled (`raspi-config`,
  then reboot).
- **`OSError: [Errno 121] Remote I/O error`:** the OLED is at a
  different address than the script expects - check what `i2cdetect`
  showed and update `I2C_ADDRESS` near the top of `oled_screen.py` to
  match (commonly `0x3D` on some boards).
- **Display flickers or shows garbled pixels:** reseat the jumpers,
  especially `SDA`/`SCL` - I2C is sensitive to loose connections.
- **`ImportError` for `luma...` modules:** confirm you're inside
  `.venv` and `pip install -r requirements.txt` completed without
  errors.
