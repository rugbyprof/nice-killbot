# Raspberry Pi Robotics Handbook

## Version 0.1

This handbook is intended as a practical reference for students learning
robotics with the Raspberry Pi.

# Table of Contents

1.  [First Setup](raspberry-pi-first-setup.md)
2.  [Linux Essentials](linux-essentials.md)
3.  VS Code Remote SSH
4.  Project Organization
5.  Python Virtual Environments
6.  GPIO Basics
7.  Motors
8.  Sensors
9.  Communications
10. Camera
11. Services
12. Git
13. Troubleshooting
14. Suggested Lab Sequence

---

# 1. First Setup

See [raspberry-pi-first-setup.md](raspberry-pi-first-setup.md) for
the full walkthrough: flashing the SD card, first boot, updating the
system, and setting up VS Code Remote SSH.

# 2. Linux Essentials

See [linux-essentials.md](linux-essentials.md) for filesystem
navigation, SSH, SSH keys, and wireless/network debugging commands
(`nmap`, `nmcli`, `iw`, `rfkill`, etc.).

# 3. VS Code Remote SSH

Install the Remote - SSH extension and connect to:

```text
username@hostname.local
```

# 4. Project Organization

```text
~/projects/
  smartcar-ir/
  smartcar-obstacle/
  smartcar-camera/
```

# 5. Python Virtual Environments

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install gpiozero pigpio rich
```

# 6. GPIO Basics

```python
from gpiozero import LED
led = LED(17)
led.on()
```

# 7. Motors

Use a USB power bank for the Pi and a separate battery for the motors.
Tie the grounds together.

# 8. Sensors

Suggested order: LED, Button, Ultrasonic, IR, Line Sensor, IMU, Camera.

# 9. Communications

IR -\> Bluetooth -\> Wi-Fi/MQTT.

# 10. Camera

```bash
pip install opencv-python numpy
```

# 11. Services

Develop by running `python main.py`. Later use `systemd` for auto-start.

# 12. Git

```bash
git clone URL
git add .
git commit -m "message"
git push
```

# 13. Troubleshooting

- Check SSH
- Check Wi-Fi
- Check power
- Verify common ground

# 14. Suggested Labs

1.  Blink LED
2.  Button
3.  Motors
4.  PWM
5.  IR Remote
6.  Obstacle Avoidance
7.  Camera
8.  Autonomous Robot
