"""
Chillbot entry point: listen for IR commands from killbot-controller
and mirror the current command on the OLED status display.

Ties ir_receiver.py and oled_screen.py together without either module
knowing about the other - this file is the only thing that imports
both.
"""

import ir_receiver
import oled_screen


def handle_command(command):
    name = ir_receiver.COMMAND_NAMES.get(command, "UNKNOWN")
    print(f"command={command:3d}  {name}")
    oled_screen.show_status(name)


def main():
    print("Chillbot ready. Waiting for IR commands.")
    print()
    ir_receiver.listen(handle_command)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Chillbot stopped.")
    finally:
        ir_receiver.close()
