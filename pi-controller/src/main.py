"""
Chillbot entry point: listen for IR commands from esp32-controller,
drive the wheels accordingly, and mirror the current command on the
OLED status display.

Ties ir_receiver.py, motors.py, and oled_screen.py together without
any of them knowing about each other - this file is the only thing
that imports all three.
"""

import commands
import motors

# import ir_receiver
# import oled_screen


def handle_command(command):
    name = commands.NAMES.get(command, "UNKNOWN")
    print(f"command={command:3d}  {name}")
    motors.drive(command)
    # oled_screen.show_status(name)


def main():
    print("Chillbot ready. Waiting for IR commands.")
    print()
    # ir_receiver.listen(handle_command)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Chillbot stopped.")
    finally:
        motors.stop()
        # ir_receiver.close()
