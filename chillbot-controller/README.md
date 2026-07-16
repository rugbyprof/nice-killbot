# Chillbot Controller

Raspberry Pi-based IR receiver for the car itself. Decodes the
commands sent by [killbot-controller](../killbot-controller/), the
ESP32 handheld remote, and mirrors the current command on an OLED
status display.

Hardware

- Raspberry Pi 4
- TSOP38238 / VS1838B 38 kHz IR receiver
- SSD1306 128x64 I2C OLED display

Language

- Python 3 (CPython)

See the lab write-ups for full wiring and setup walkthroughs:

- [Pi Lab 4: IR Receiver](../docs/labs/Pi/lab_04-ir_receiver.md)
- [Pi Lab 5: OLED Screen](../docs/labs/Pi/lab_05-oled_screen.md)

The wire protocol these two projects speak to each other is documented
in [killbot-controller/docs/protocol.md](../killbot-controller/docs/protocol.md).

## Setup

```bash
sudo apt install -y pigpio python3-pigpio i2c-tools
sudo systemctl enable --now pigpiod

python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`--system-site-packages` is required so the venv can see
`python3-pigpio`, which is installed via `apt` rather than `pip` (it
needs to talk to the `pigpiod` daemon).

## Running

```bash
source .venv/bin/activate
python src/main.py
```
