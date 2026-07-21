# Killbot Controller

ESP32 handheld IR controller.

Hardware

- ESP-WROOM-32
- KY-023 Joystick
- 38 kHz IR transmitter

Language

- MicroPython

## Project layout

```text
src/
    joystick.py               top-level script - the remote's main program
    button_encoder_remote.py   top-level script - a separate, unrelated
                                remote design (button + rotary encoder)
    lib/
        oled_screen.py          dependency, imported by joystick.py
        ssd1306.py                dependency, imported by oled_screen.py
        ir_transmitter.py         dependency, imported by joystick.py
tests/
    button_test.py             standalone hardware bring-up script
    obstacle_avoidance_test.py  standalone hardware bring-up script
    adc_test.py, ir_test.py,    empty placeholders
    joystick_test.py
```

`src/` holds top-level programs you actually run on the board -
right now that's two independent, unrelated remote designs
(`joystick.py` and `button_encoder_remote.py`), not two files of the
same project. `src/lib/` holds the modules those programs import.
MicroPython automatically searches a device's `/lib` folder for
imports, so `upload.sh` copies `src/lib/` to the board's `/lib` and
everything else in `src/` to the board's root - `import oled_screen`
in `joystick.py` doesn't need to know or care that the file lives in
a subfolder on your computer.

`tests/` is standalone, single-purpose hardware bring-up scripts (run
directly on the board to confirm one sensor/module is wired correctly)
- not automated unit tests. None of them import from `src/` or
`src/lib/`.
