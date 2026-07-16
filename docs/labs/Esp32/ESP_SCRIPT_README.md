# `esp.py` Quick Start

## 1. Install the required tools

### Windows PowerShell

```powershell
py -m pip install --upgrade esptool mpremote
```

### macOS or Linux

```bash
python3 -m pip install --upgrade esptool mpremote
```

## 2. Put `esp.py` in the project directory

Optionally create a configuration file:

```bash
python esp.py config
```

On Windows, `python` may be replaced with `py`:

```powershell
py esp.py config
```

## 3. Useful commands

```bash
python esp.py doctor
python esp.py ports
python esp.py erase
python esp.py flash firmware/ESP32_GENERIC.bin
python esp.py repl
python esp.py run main.py
python esp.py upload
python esp.py ls
python esp.py cat :main.py
python esp.py reset
```

To specify a port:

```powershell
py esp.py --port COM5 repl
```

```bash
python3 esp.py --port /dev/cu.usbserial-0001 repl
```

## Important flashing note

The default offset is `0x1000`, which is appropriate for the classic ESP32
MicroPython firmware used by an ESP-WROOM-32 board. Other ESP32 variants or
firmware packages may require a different offset. Use the offset stated on
the firmware download page:

```bash
python esp.py flash firmware.bin --offset 0x0
```
