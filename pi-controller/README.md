# Chillbot Controller

Raspberry Pi-based IR receiver for the car itself. Decodes the
commands sent by [esp32-controller](../esp32-controller/), the
ESP32 handheld remote, drives the 4 wheels accordingly, and mirrors
the current command on an OLED status display.

Hardware

- Raspberry Pi 4
- TSOP38238 / VS1838B 38 kHz IR receiver
- SSD1306 128x64 I2C OLED display
- 2x L9110S dual motor driver, 4x DC gear motors

Language

- Python 3 (CPython)

See the lab write-ups for full wiring and setup walkthroughs:

- [Pi Lab 3: Motors](../docs/labs/Pi/lab_03-motors.md)
- [Pi Lab 4: IR Receiver](../docs/labs/Pi/lab_04-ir_receiver.md)
- [Pi Lab 5: OLED Screen](../docs/labs/Pi/lab_05-oled_screen.md)

The wire protocol these two projects speak to each other is documented
in [esp32-controller/docs/protocol.md](../esp32-controller/docs/protocol.md).

## Project layout

```text
src/
    main.py          entry point - listens for IR, drives, mirrors to the OLED
    commands.py       command IDs shared by ir_receiver.py, motors.py, main.py
    ir_receiver.py    IR decoding - also runnable standalone (Lab 4)
    motors.py         4-wheel drive - also runnable standalone (Lab 3)
    oled_screen.py    OLED driver - also runnable standalone (Lab 5)
```

Everything lives flat in `src/` - no separate `lib/` folder here.
Unlike the ESP32 side, a plain CPython script can `import` a sibling
file in the same directory with no extra setup, so there's no
deployment-tooling reason to split "runnable" from "imported" the way
`esp32-controller` does with its `lib/` folder.

`ir_receiver.py`, `motors.py`, and `oled_screen.py` are each both:
importable by `main.py`, and directly runnable on their own for
hardware bring-up (each has its own `if __name__ == "__main__":` block
- see the Lab 3/4/5 write-ups). None of the three import each other -
`main.py` is the only file that ties them together, deciding what an
IR command actually *does* (drive + display) rather than that logic
living inside any one module.

`commands.py` exists because three different files ended up needing
the same command-ID table - unlike the ESP32/Pi split (genuinely
different runtimes, so `esp32-controller/src/joystick.py` and
`ir_receiver.py` each keep their own copy, kept in sync via
`esp32-controller/docs/protocol.md`), there's no reason for
`ir_receiver.py` and `motors.py` to duplicate it too when they're
already plain CPython files that can just import a shared module.

## Setup

```bash
sudo apt install -y python3-pigpio i2c-tools
```

`pigpio` (the daemon itself, as opposed to `python3-pigpio`'s Python
bindings) is no longer packaged for Raspberry Pi OS as of Bookworm -
upstream has been unmaintained since 2021 and doesn't support the Pi
5's GPIO chip, so it was dropped from the repos entirely. On a Pi 4 the
daemon still works fine, it just has to be built from source, and the
build doesn't install a systemd unit, so that has to be created by
hand too:

```bash
sudo apt install -y build-essential
git clone https://github.com/joan2937/pigpio
cd pigpio
make -j4
sudo make install

sudo tee /etc/systemd/system/pigpiod.service > /dev/null <<'EOF'
[Unit]
Description=pigpio daemon
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/bin/pigpiod
ExecStop=/bin/systemctl kill pigpiod

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now pigpiod
```

Then set up the venv:

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`--system-site-packages` is required so the venv can see
`python3-pigpio`, which is installed via `apt` rather than `pip` (it
needs to talk to the `pigpiod` daemon). It also happens to be what
`motors.py`'s `gpiozero` needs for its GPIO backend (`python3-rpi-lgpio`,
also `apt`-installed - see [Raspberry Pi First
Setup](../docs/labs/Pi/Raspberry-pi-first-setup.md)), so one venv flag
covers both.

## Running

```bash
source .venv/bin/activate
python src/main.py
```
