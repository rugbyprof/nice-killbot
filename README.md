# nice-killbot

AI car project assignment — Raspberry Pi-based robot: setup docs, dev environment scripts, and (more coming) the robot's control code.

## Contents

| File | Description |
| --- | --- |
| [docs/raspberry-pi-first-setup.md](docs/raspberry-pi-first-setup.md) | Initial hardware and OS setup for the Pi |
| [docs/linux-essentials.md](docs/linux-essentials.md) | Linux command line basics/reference |
| [docs/Raspberry_Pi_Robotics_Handbook_v0.1.md](docs/Raspberry_Pi_Robotics_Handbook_v0.1.md) | Practical reference handbook for the robotics build |
| [docs/images/pinout.png](docs/images/pinout.png) | Pi GPIO pinout reference image |
| [griffins_setup_scripts/chillbot_bootstrap.sh](griffins_setup_scripts/chillbot_bootstrap.sh) | Phased bootstrap script for the dev environment on the Pi (terminal tools, GPIO/camera libs, Python venv, etc.) |
| [griffins_setup_scripts/setup_pi_shell.py](griffins_setup_scripts/setup_pi_shell.py) | Configures zsh + oh-my-zsh on the Pi over SSH for both `griffin` and `root` |
| [killbot-controller/](killbot-controller/README.md) | ESP32-based IR remote (joystick + transmitter) for manually driving the car before autonomy is added |

More to come as the project develops.
