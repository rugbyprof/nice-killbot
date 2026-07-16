# ESP32 Getting Started Guide

## Installing MicroPython, Flashing Firmware, and Running Programs

The goal is to have **one workflow** for every operating system so we don't spend the semester fighting installers.

---

# Why this setup?

There are dozens of ways to program an ESP32.

You could use:

- Arduino IDE
- PlatformIO
- Thonny
- Mu
- esptool
- mpremote
- ampy
- rshell
- WebREPL
- etc...

For this introductory class, we will use two command-line tools:

- **esptool** — install firmware
- **mpremote** — communicate with the board

That's it.

Everything else happens inside VS Code.

---

# Step 1 — Install Python

Download Python 3.13 (or newer).

During installation make sure

> ✅ Add Python to PATH

is checked.

Verify installation.

```bash
python --version
```

or

```bash
python3 --version
```

---

# Step 2 — Install VS Code

Install VS Code.

I recommend the following extensions.

- Python
- Pylance
- Ruff (optional)
- Markdown All in One

That's all you need initially.

---

# Step 3 — Install the tools

Open the VS Code terminal.

Install:

```bash
pip install esptool mpremote
```

or

```bash
python -m pip install esptool mpremote
```

Verify.

```bash
esptool version
```

```bash
mpremote version
```

> If you have issues, remember our talk about `pipx`

---

# Windows

Surprisingly...

**PowerShell works perfectly fine for our needs.**

We don't **need WSL** (which I normally insist) just to use an ESP32.

Using WSL actually complicates USB access.

I recommend:

- VS Code
- PowerShell terminal

That's it.

You can type

```powershell
python -m pip install esptool mpremote
```

and everything `should` works.

---

# macOS

Exactly the same.

```bash
python3 -m pip install esptool mpremote
```

---

# Linux

Exactly the same.

```bash
python3 -m pip install esptool mpremote
```

---

# Step 4 — Plug in the ESP32

After connecting:

Windows

```powershell
mode
```

or

Open Device Manager

Look under

```
Ports (COM & LPT)
```

Example

```
COM5
```

---

macOS

```bash
ls /dev/cu.*
```

Typical output

```
/dev/cu.usbserial-0001
```

---

Linux

```bash
ls /dev/ttyUSB*
```

or

```bash
ls /dev/ttyACM*
```

---

# Step 5 — Download MicroPython

Download the latest ESP32 firmware.

**Example File Name:**

```
ESP32_GENERIC-20260406-v1.28.0.bin
```

- Page:
  - https://micropython.org/download/ESP32_GENERIC/
- Link to Binary on Above Page:
  - https://micropython.org/resources/firmware/ESP32_GENERIC-20260406-v1.28.0.bin

---

# Step 6 — Erase Flash

Windows

```powershell
esptool --chip esp32 --port COM5 erase_flash
```

Mac

```bash
esptool --chip esp32 --port /dev/cu.usbserial-0001 erase_flash
```

Linux

```bash
esptool --chip esp32 --port /dev/ttyUSB0 erase_flash
```

---

# Step 7 — Install Firmware

Example

Windows

```powershell
esptool --chip esp32 --port COM5 --baud 460800 write_flash -z 0x1000 ESP32_GENERIC.bin
```

Mac

```bash
esptool --chip esp32 --port /dev/cu.usbserial-0001 --baud 460800 write_flash -z 0x1000 ESP32_GENERIC.bin
```

---

# Step 8 — Test MicroPython

Open the REPL.

```bash
mpremote connect auto repl
```

You should see

```
MicroPython v1.xx

>>>
```

Congratulations.

You're now inside the ESP32.

Exit with

```
Ctrl-]
```

---

# Step 9 — Run a Program

Create

```
hello.py
```

```python
print("Hello from the ESP32!")
```

Run it without copying it to the board.

```bash
mpremote run hello.py
```

Output

```
Hello from the ESP32!
```

---

# Step 10 — Copy Files

Copy a file.

```bash
mpremote fs cp blink.py :
```

Copy an entire directory.

```bash
mpremote fs cp -r lib :
```

List files.

```bash
mpremote fs ls
```

---

# Step 11 — Edit Files

Students edit files locally in VS Code.

```
project/
    blink.py
    joystick.py
    main.py
```

When ready

```bash
mpremote fs cp *.py :
```

Run

```bash
mpremote reset
```

---

# Useful mpremote Commands

Open REPL

```bash
mpremote repl
```

Reset

```bash
mpremote reset
```

Run

```bash
mpremote run blink.py
```

Copy file

```bash
mpremote fs cp blink.py :
```

Delete file

```bash
mpremote fs rm blink.py
```

List files

```bash
mpremote fs ls
```

Read a file

```bash
mpremote fs cat main.py
```

Mount your PC folder (very cool)

```bash
mpremote mount .
```

Now the ESP32 can import modules directly from your computer without copying them.

---

# Suggested Workflow

```
Create Project
        │
        ▼
Edit in VS Code
        │
        ▼
Run locally (syntax check)
        │
        ▼
mpremote run
        │
        ▼
Works?
        │
      Yes
        │
        ▼
Copy to ESP32
        │
        ▼
Reset
```

---

# Common Errors

## "Port Busy"

Close possible other users:

- Arduino IDE
- Thonny
- Serial Monitor
- PuTTY

Only one program can use the serial port at a time.

---

## "Device not found"

Hold the **BOOT** button while connecting or while flashing if your ESP32 doesn't automatically enter download mode.

---

## "Permission denied" (Linux)

Add your user to the `dialout` group:

```bash
sudo usermod -aG dialout $USER
```

Then log out and back in.

---

## "Command not found"

Try:

```bash
python -m esptool
```

instead of

```bash
esptool
```

or

```bash
python -m mpremote
```

instead of

```bash
mpremote
```

---

# My Recommendations for Your Lab

Given what I know about your teaching style and your Raspberry Pi/ESP32 lab, I'd standardize on these tools:

| Tool                   | Recommendation | Why                                                                                                          |
| ---------------------- | -------------- | ------------------------------------------------------------------------------------------------------------ |
| Python                 | ✅ Required    | Shared across all courses                                                                                    |
| VS Code                | ✅ Required    | Same IDE for Python, C++, Go, ESP32, and Raspberry Pi                                                        |
| PowerShell (Windows)   | ✅ Yes         | Simpler than introducing WSL just for ESP32                                                                  |
| Terminal (macOS/Linux) | ✅ Yes         | Native terminals work well                                                                                   |
| esptool                | ✅ Required    | Flash firmware                                                                                               |
| mpremote               | ✅ Required    | File transfer, REPL, execution                                                                               |
| Thonny                 | ❌ Skip        | Good for hobbyists, but another interface to learn                                                           |
| Arduino IDE            | ❌ Later       | Save it for the Arduino unit                                                                                 |
| WSL                    | ❌ Optional    | Excellent for systems programming, but unnecessary—and sometimes inconvenient—for USB-connected ESP32 boards |
