# nice-killbot

AI car project assignment — Raspberry Pi-based robot: setup docs, dev environment scripts, and (more coming) the robot's control code.

## Contents

| File | Description |
| --- | --- |
| [docs/labs/Pi/Raspberry-pi-first-setup.md](docs/labs/Pi/Raspberry-pi-first-setup.md) | Initial hardware and OS setup for the Pi |
| [docs/Linux-essentials.md](docs/Linux-essentials.md) | Linux command line basics/reference |
| [docs/labs/Pi/Raspberry_Pi_Robotics_Handbook_v0.1.md](docs/labs/Pi/Raspberry_Pi_Robotics_Handbook_v0.1.md) | Practical reference handbook for the robotics build |
| [docs/labs/Pi/](docs/labs/Pi/) | Hands-on Pi labs: LED, button, motors, IR receiver, OLED screen |
| [docs/labs/Esp32/](docs/labs/Esp32/) | Hands-on ESP32 labs: joystick, IR transmitter |
| [docs/images/pinout.png](docs/images/pinout.png) | Pi GPIO pinout reference image |
| [griffins_setup_scripts/chillbot_bootstrap.sh](griffins_setup_scripts/chillbot_bootstrap.sh) | Phased bootstrap script for the dev environment on the Pi (terminal tools, GPIO/camera libs, Python venv, etc.) |
| [griffins_setup_scripts/setup_pi_shell.py](griffins_setup_scripts/setup_pi_shell.py) | Configures zsh + oh-my-zsh on the Pi over SSH for both `griffin` and `root` |
| [esp32-controller/](esp32-controller/README.md) | ESP32-based IR remote (joystick + transmitter) for manually driving the car before autonomy is added |
| [pi-controller/](pi-controller/README.md) | Raspberry Pi-based IR receiver + OLED status display, running on the car itself |
| [esp32-controller/docs/protocol.md](esp32-controller/docs/protocol.md) | Shared IR wire protocol between esp32-controller and pi-controller |

More to come as the project develops.
