# Raspberry Pi First Setup

## Hardware

- Raspberry Pi 4 Model B
- microSD card (32 GB recommended)
- USB-C power supply or USB power bank (5V, 3A recommended)
- Wi-Fi network
- Laptop with VS Code

---

# Install Raspberry Pi Imager

Install **Raspberry Pi Imager** on your computer.

- [Generic Downloads](https://www.raspberrypi.com/software/)
- - [Windows](https://downloads.raspberrypi.com/imager/imager_latest.exe)
  - [Mac](https://downloads.raspberrypi.com/imager/imager_latest.dmg)
  - [Linux](https://downloads.raspberrypi.com/imager/imager_latest_amd64.AppImage)

---

# Flash Raspberry Pi OS

1.  Insert the microSD card.
2.  Open Raspberry Pi Imager.
3.  Choose:
    - **Device:** Raspberry Pi 4
    - **Operating System:** Raspberry Pi OS (64-bit)
    - **Storage:** Your microSD card
4.  Open **Advanced Options** (gear icon) and configure:

    Hostname: chillbot (this will be the name of your raspberry pi)
    Username: chillbot (this is the name you use to login)
    Password: chillbot2026 (password that goes with your username)

    Enable SSH
    Configure Wi-Fi
    Set Wi-Fi country
    Set locale
    Set keyboard layout

**Important:** You must set the Wi-Fi _country_, not just the SSID and
password. Without it, the Wi-Fi radio may not turn on at all.

1.  Click **Write**.

2.  Insert the microSD into the Raspberry Pi.

3.  Power on the Raspberry Pi.

**Wait 1-2 minutes** before trying to connect. On first boot, the Pi
resizes its filesystem and initializes networking — SSH won't respond
right away. If you try too soon and it fails, just wait and try again
rather than reflashing.

---

# First Connection

From a terminal:

```bash
ssh griffin@chillbot.local
```

Accept the host key if prompted.

**If `chillbot.local` doesn't resolve** (common on Windows without
Bonjour installed), find the Pi's IP address from your router's
connected-devices list, or run a network scan, then connect with:

```bash
ssh griffin@<ip-address>
$ username: chillbot
$ password:
```

> Note: When you type a password on linux, the cursor does NOT move. But it's listening!

---

# Update the System

```bash
$ sudo apt update
$ sudo apt upgrade -y
```

---

# Install Common Packages

```bash
$ sudo apt install -y git python3 python3-pip python3-venv python3-gpiozero python3-rpi-lgpio
```

Verify Python:

```bash
$ python3 --version
```

---

# VS Code Remote SSH Setup

## Install Extension

Install the Microsoft **Remote - SSH** extension.

1.  Open VS Code.
2.  Open extensions.
3.  Search for `remote ssh` and install the extension.

## Connect

1.  After it's installed press: **ctrl-shift p** on windows or **cmd-shift p** on Mac to get a "run command" text box at the top of VScodes's window.
2.  Type `ssh` in the box. You should see lots of commands that "match" with `ssh`.
3.  Select:

```
    Remote-SSH: Connect to Host...
```

4.  Enter:

```
    yourusername@yourcomputername.local
```

or like in the example

```
    chillbot@chillbot.local
```

5.  Open a folder on the Raspberry Pi.

---

# Typical Project Layout

```text
~/projects/
├── smartcar-ir/
│   ├── main.py
│   ├── requirements.txt
│   └── .venv/
├── smartcar-obstacle/
├── smartcar-light/
└── test-motors/
```

---

# Create a Project

```bash
mkdir -p ~/projects/smartcar-ir
cd ~/projects/smartcar-ir

python3 -m venv --system-site-packages .venv
source .venv/bin/activate

pip install gpiozero pigpio rich
pip freeze > requirements.txt
```

**Note the `--system-site-packages` flag.** A normal venv is isolated
from the system Python, but `gpiozero` needs a GPIO "pin factory"
backend (`python3-rpi-lgpio`, installed earlier via `apt`) to actually
talk to the pins. Without this flag, GPIO code will fail with an error
like `no pin factory could be determined`, even though `pip install
gpiozero` succeeded.

If a project uses `pigpio`, the daemon must also be installed and
running (once, system-wide — not inside the venv):

```bash
$ sudo apt install -y pigpio python3-pigpio
$ sudo systemctl enable --now pigpiod
```

---

# Running a Project

```bash
cd ~/projects/smartcar-ir
source .venv/bin/activate
python main.py
```

Stop with:

```text
Ctrl+C
```

---

# Useful Commands

Update packages:

```bash
$ sudo apt update
$ sudo apt upgrade -y
```

System information:

```bash
hostname
hostname -I
python3 --version
```

Disk usage:

```bash
df -h
```

Processes:

```bash
htop
```

---

# File Transfer

Copy a file to the Pi:

```bash
scp myfile.py griffin@chillbot.local:~/projects/smartcar-ir/
```

Copy a file from the Pi:

```bash
scp griffin@chillbot.local:~/projects/smartcar-ir/main.py .
```

---

# Project Organization

```text
projects/
    smartcar-ir/
    smartcar-camera/
    smartcar-opencv/
    smartcar-ai/
    smartcar-sensors/
```

Only run the project you want:

```bash
cd ~/projects/project-name
source .venv/bin/activate
python main.py
```

**Camera and OpenCV projects** (`smartcar-camera`, `smartcar-opencv`,
`smartcar-ai`) need one extra step. `picamera2` isn't available on
PyPI — install it system-wide with apt, and create these venvs with
`--system-site-packages` (same reason as `gpiozero` above) so the
venv can see it:

```bash
$ sudo apt install -y python3-picamera2 python3-opencv
```

---

# Optional Auto-Start

Enable later using `systemd` once a project is complete.
