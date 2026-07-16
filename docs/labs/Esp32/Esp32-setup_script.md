## Simplify common MicroPython ESP32 commands

> **OPTIONAL!!!!!!!!!!!!!!!!!!!!!!!!!!**

This is a **single cross-platform Python script**, so students can use the same commands on Windows, macOS, and Linux.

## Downloads

Make sure esp.py is in your project directory. A copy is in this folder: [esp.py](./esp.py).

The script runs `esptool` and `mpremote` through the active Python interpreter, which avoids the common Windows problem where PowerShell claims:

```text
'mpremote' is not recognized as the name of a cmdlet...
```

Instead of relying on PATH, the script effectively runs:

```bash
python -m mpremote
python -m esptool
```

That is much more dependable across different machines.

---

# Installation

## Windows PowerShell

Make sure you have `esptool` and `mpremote` installed (should have been done in the [Esp32 First Setup](./Esp32-first-setup.md)).

```powershell
py -m pip install --upgrade esptool mpremote
```

## macOS or Linux

```bash
python3 -m pip install --upgrade esptool mpremote
```

Then place `esp.py` in the ESP32 project directory that you are currently working with. We can talk about making it a global script later.

---

# First Test

## Windows

```powershell
py esp.py doctor
```

## macOS or Linux

```bash
python3 esp.py doctor
```

The `doctor` command checks:

- Python
- `esptool`
- `mpremote`
- operating system
- project directory
- configured serial port

---

# Typical Commands

For brevity, these examples use:

```bash
python esp.py
```

Windows students may use:

```powershell
py esp.py
```

## List connected boards

```bash
python esp.py ports
```

## Erase the ESP32

```bash
python esp.py erase
```

## Flash MicroPython

```bash
python esp.py flash firmware/ESP32_GENERIC.bin
```

For your classic **ESP-WROOM-32**, the script defaults to:

```text
chip: esp32
offset: 0x1000
baud: 460800
```

The ESP32 MicroPython documentation and current Espressif tooling use `mpremote` for device interaction and the modern hyphenated `esptool` commands such as `erase-flash` and `write-flash`. [oai_citation:0‡MicroPython Documentation](https://docs.micropython.org/en/latest/reference/mpremote.html?utm_source=chatgpt.com)

## Open the MicroPython REPL

```bash
python esp.py repl
```

Exit the REPL with:

```text
Ctrl-]
```

## Run a program without saving it

```bash
python esp.py run joystick.py
```

This is ideal during development because students can test code without repeatedly copying it to the board.

## Upload one file

```bash
python esp.py upload joystick.py
```

## Upload the whole project

```bash
python esp.py upload
```

By default, it uploads common project files such as:

```text
.py
.json
.txt
.csv
.html
.css
.js
```

It ignores clutter such as:

```text
.git
.venv
venv
__pycache__
.vscode
firmware
```

That keeps students from heroically attempting to upload a 400 MB virtual environment onto a 4 MB microcontroller.

## List files on the ESP32

```bash
python esp.py ls
```

## Display a file stored on the ESP32

```bash
python esp.py cat :main.py
```

## Download a file from the ESP32

```bash
python esp.py get :data.csv
```

## Delete a file

```bash
python esp.py rm :old_test.py
```

## Reset the ESP32

```bash
python esp.py reset
```

Soft reset:

```bash
python esp.py reset --soft
```

## Execute one line of MicroPython

```bash
python esp.py exec "print('Hello from Killbot')"
```

In PowerShell, the same command works:

```powershell
py esp.py exec "print('Hello from Killbot')"
```

---

# Selecting a Serial Port

Normally, `mpremote` can automatically choose the board when only one compatible device is connected. That is the easiest student workflow. [oai_citation:1‡MicroPython Documentation](https://docs.micropython.org/en/latest/reference/mpremote.html?utm_source=chatgpt.com)

When multiple devices are connected, explicitly provide the port.

## Windows

```powershell
py esp.py --port COM5 repl
```

## macOS

```bash
python3 esp.py --port /dev/cu.usbserial-0001 repl
```

## Linux

```bash
python3 esp.py --port /dev/ttyUSB0 repl
```

Notice that `--port` comes **before** the command:

```bash
python esp.py --port COM5 repl
```

Not:

```bash
python esp.py repl --port COM5
```

Argparse is fussy because computers enjoy rules more than humans do.

---

# Project Configuration

The script can create a local `.esp.json` configuration file:

```bash
python esp.py config
```

It creates:

```json
{
  "port": "auto",
  "chip": "esp32",
  "baud": 460800,
  "offset": "0x1000",
  "source": ".",
  "exclude": [
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".vscode",
    ".idea",
    "firmware"
  ]
}
```

A Windows student could change it to:

```json
{
  "port": "COM5",
  "chip": "esp32",
  "baud": 460800,
  "offset": "0x1000",
  "source": ".",
  "exclude": [".git", ".venv", "__pycache__", ".vscode", "firmware"]
}
```

Then all commands automatically use `COM5`:

```powershell
py esp.py repl
py esp.py upload
py esp.py reset
```

---

# Suggested Project Layout

```text
joystick-project/
├── esp.py
├── .esp.json
├── main.py
├── joystick.py
├── config.json
├── lib/
│   └── controller.py
└── firmware/
    └── ESP32_GENERIC-20260406-v1.28.0.bin
```

Then the normal student workflow becomes:

```bash
python esp.py run joystick.py
```

Once it works:

```bash
python esp.py upload
python esp.py reset
```

---

# Optional Short Command

Typing `python esp.py` is not terrible, but students will inevitably complain as though they are manually transcribing the Encyclopedia Britannica.

## macOS or Linux

Make it executable:

```bash
chmod +x esp.py
```

Then run:

```bash
./esp.py doctor
./esp.py repl
./esp.py upload
```

You could rename it simply:

```bash
mv esp.py esp
chmod +x esp
```

Then:

```bash
./esp repl
```

## Windows PowerShell Function

Students can add this to their PowerShell profile:

```powershell
function esp {
    py "$PWD\esp.py" @args
}
```

Then they can run:

```powershell
esp doctor
esp ports
esp repl
esp upload
```

For a first lab, though, I would keep it explicit:

```powershell
py esp.py repl
```

That makes it clear they are running a Python program rather than invoking mysterious professor sorcery.
