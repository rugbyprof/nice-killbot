#!/usr/bin/env python3
"""
esp.py - Small cross-platform helper for ESP32 + MicroPython projects.

Requirements:
    python -m pip install esptool mpremote

Typical use:
    python esp.py doctor
    python esp.py ports
    python esp.py erase
    python esp.py flash firmware/ESP32_GENERIC.bin
    python esp.py repl
    python esp.py run main.py
    python esp.py upload
    python esp.py ls
    python esp.py reset

A project-local configuration file named .esp.json may contain:
{
  "port": "auto",
  "chip": "esp32",
  "baud": 460800,
  "offset": "0x1000",
  "source": ".",
  "exclude": [".git", ".venv", "__pycache__", ".vscode", "firmware"]
}
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

CONFIG_FILE = ".esp.json"

DEFAULT_CONFIG = {
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
        "firmware",
    ],
}

UPLOAD_SUFFIXES = {".py", ".json", ".txt", ".csv", ".html", ".css", ".js"}


class EspError(RuntimeError):
    """A friendly command-line error."""


def load_config() -> dict:
    """Load .esp.json and merge it with the defaults."""
    config = DEFAULT_CONFIG.copy()
    config["exclude"] = list(DEFAULT_CONFIG["exclude"])

    path = Path(CONFIG_FILE)
    if not path.exists():
        return config

    try:
        user_config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EspError(
            f"{CONFIG_FILE} contains invalid JSON: line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(user_config, dict):
        raise EspError(f"{CONFIG_FILE} must contain a JSON object.")

    config.update(user_config)
    return config


def save_default_config(force: bool = False) -> None:
    """Create a starter .esp.json file."""
    path = Path(CONFIG_FILE)
    if path.exists() and not force:
        raise EspError(
            f"{CONFIG_FILE} already exists. Use 'config --force' to replace it."
        )

    text = json.dumps(DEFAULT_CONFIG, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")
    print(f"Created {path.resolve()}")


def module_installed(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def module_command(module_name: str, args: Sequence[str]) -> list[str]:
    """
    Prefer an installed command from PATH.

    This supports Homebrew, pipx, pip-installed command wrappers,
    Windows executables, and active virtual environments.

    Fall back to `python -m module` when no command is available.
    """
    executable = shutil.which(module_name)

    if executable:
        return [executable, *args]

    if importlib.util.find_spec(module_name) is not None:
        return [sys.executable, "-m", module_name, *args]

    raise EspError(
        f"Could not find '{module_name}' as either:\n"
        f"  1. a command on PATH, or\n"
        f"  2. a module installed for {sys.executable}\n\n"
        f"Install it with one of these:\n"
        f"  python3 -m pip install {module_name}\n"
        f"  pipx install {module_name}\n"
        f"  brew install {module_name}"
    )


# def module_command(module_name: str, args: Sequence[str]) -> list[str]:
#     """
#     Run tools through the active Python interpreter.

#     This avoids Windows PATH problems such as:
#         'mpremote' is not recognized...
#     """
#     return [sys.executable, "-m", module_name, *args]


def run_command(
    command: Sequence[str],
    *,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Print and execute an external command."""
    printable = subprocess.list2cmdline(list(command))
    print(f"\n> {printable}\n")

    try:
        return subprocess.run(
            list(command),
            check=check,
            text=True,
            capture_output=capture,
        )
    except FileNotFoundError as exc:
        raise EspError(f"Could not run command: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise EspError(f"Command failed with exit code {exc.returncode}.") from exc


# def require_tools(*module_names: str) -> None:
#     missing = [name for name in module_names if not module_installed(name)]
#     if not missing:
#         return

#     package_list = " ".join(missing)
#     raise EspError(
#         "Missing required package(s): "
#         f"{', '.join(missing)}\n\n"
#         "Install them with:\n"
#         f'  "{sys.executable}" -m pip install {package_list}'
#     )


def tool_available(tool_name: str) -> bool:
    """Return True if the tool exists on PATH or as a Python module."""
    return (
        shutil.which(tool_name) is not None
        or importlib.util.find_spec(tool_name) is not None
    )


def require_tools(*tool_names: str) -> None:
    """Require tools installed either as executables or Python modules."""
    missing = [name for name in tool_names if not tool_available(name)]

    if not missing:
        return

    package_list = " ".join(missing)

    raise EspError(
        "Missing required tool(s): "
        f"{', '.join(missing)}\n\n"
        "Install them with one of these approaches:\n\n"
        f"  python3 -m pip install {package_list}\n"
        f"  pipx install {' && pipx install '.join(missing)}\n"
        f"  brew install {package_list}"
    )


def effective_port(args: argparse.Namespace, config: dict) -> str:
    return args.port or str(config.get("port", "auto"))


def mpremote_prefix(args: argparse.Namespace, config: dict) -> list[str]:
    """
    Return mpremote connection arguments.

    'auto' lets mpremote choose the only available MicroPython device.
    """
    port = effective_port(args, config)
    return ["connect", port]


def esptool_port_args(args: argparse.Namespace, config: dict) -> list[str]:
    """
    esptool can auto-detect when --port is omitted.

    A configured port of 'auto' therefore produces no --port argument.
    """
    port = effective_port(args, config)
    return [] if port.lower() == "auto" else ["--port", port]


def command_doctor(args: argparse.Namespace, config: dict) -> None:
    print("ESP32 MicroPython environment check")
    print("-----------------------------------")
    print(f"Python executable : {sys.executable}")
    print(f"Python version    : {sys.version.split()[0]}")
    print(f"Operating system  : {sys.platform}")
    print(f"Project directory : {Path.cwd()}")
    print(f"Configuration     : {Path(CONFIG_FILE).resolve()}")
    print(f"Configured port   : {effective_port(args, config)}")
    print()

    problems = False

    # for module_name in ("esptool", "mpremote"):
    #     installed = module_installed(module_name)
    #     status = "OK" if installed else "MISSING"
    #     print(f"{module_name:<10}: {status}")
    #     problems |= not installed

    for tool_name in ("esptool", "mpremote"):
        executable = shutil.which(tool_name)
        module = importlib.util.find_spec(tool_name)

        if executable:
            print(f"{tool_name:<10}: OK — command at {executable}")
        elif module:
            print(f"{tool_name:<10}: OK — Python module for " f"{sys.executable}")
        else:
            print(f"{tool_name:<10}: MISSING")
            problems = True

    if shutil.which("code"):
        print("VS Code CLI: OK")
    else:
        print("VS Code CLI: not found (optional)")

    if problems:
        print("\nInstall the missing tools with:")
        print(f'  "{sys.executable}" -m pip install esptool mpremote')
        raise EspError("Environment setup is incomplete.")

    print("\nEnvironment looks good. The tiny computer may now be annoyed safely.")


def command_ports(args: argparse.Namespace, config: dict) -> None:
    require_tools("mpremote")
    # mpremote's connect list prints available serial devices.
    run_command(module_command("mpremote", ["connect", "list"]))


def command_erase(args: argparse.Namespace, config: dict) -> None:
    require_tools("esptool")

    chip = args.chip or str(config.get("chip", "esp32"))
    command = module_command(
        "esptool",
        [
            "--chip",
            chip,
            *esptool_port_args(args, config),
            "erase-flash",
        ],
    )
    run_command(command)


def command_flash(args: argparse.Namespace, config: dict) -> None:
    require_tools("esptool")

    firmware = Path(args.firmware).expanduser()
    if not firmware.is_file():
        raise EspError(f"Firmware file not found: {firmware}")

    chip = args.chip or str(config.get("chip", "esp32"))
    baud = args.baud or int(config.get("baud", 460800))
    offset = args.offset or str(config.get("offset", "0x1000"))

    command = module_command(
        "esptool",
        [
            "--chip",
            chip,
            *esptool_port_args(args, config),
            "--baud",
            str(baud),
            "write-flash",
            "-z",
            offset,
            str(firmware),
        ],
    )
    run_command(command)

    print("\nFirmware written successfully.")
    print("The board may reset automatically. If not, press EN once.")


def command_repl(args: argparse.Namespace, config: dict) -> None:
    require_tools("mpremote")
    run_command(
        module_command(
            "mpremote",
            [*mpremote_prefix(args, config), "repl"],
        )
    )


def command_run(args: argparse.Namespace, config: dict) -> None:
    require_tools("mpremote")

    source = Path(args.file)
    if not source.is_file():
        raise EspError(f"Program file not found: {source}")

    run_command(
        module_command(
            "mpremote",
            [*mpremote_prefix(args, config), "run", str(source)],
        )
    )


def command_exec(args: argparse.Namespace, config: dict) -> None:
    require_tools("mpremote")
    run_command(
        module_command(
            "mpremote",
            [*mpremote_prefix(args, config), "exec", args.code],
        )
    )


def command_reset(args: argparse.Namespace, config: dict) -> None:
    require_tools("mpremote")
    reset_command = "soft-reset" if args.soft else "reset"

    run_command(
        module_command(
            "mpremote",
            [*mpremote_prefix(args, config), reset_command],
        )
    )


def command_ls(args: argparse.Namespace, config: dict) -> None:
    require_tools("mpremote")
    remote_path = args.path or ":"

    run_command(
        module_command(
            "mpremote",
            [*mpremote_prefix(args, config), "fs", "ls", remote_path],
        )
    )


def command_cat(args: argparse.Namespace, config: dict) -> None:
    require_tools("mpremote")
    run_command(
        module_command(
            "mpremote",
            [*mpremote_prefix(args, config), "fs", "cat", args.path],
        )
    )


def command_rm(args: argparse.Namespace, config: dict) -> None:
    require_tools("mpremote")
    operation = "rm" if not args.recursive else "rm"

    command = [
        *mpremote_prefix(args, config),
        "fs",
        operation,
    ]
    if args.recursive:
        command.append("-r")
    command.append(args.path)

    run_command(module_command("mpremote", command))


def command_mkdir(args: argparse.Namespace, config: dict) -> None:
    require_tools("mpremote")
    run_command(
        module_command(
            "mpremote",
            [*mpremote_prefix(args, config), "fs", "mkdir", args.path],
        )
    )


def command_get(args: argparse.Namespace, config: dict) -> None:
    require_tools("mpremote")

    local = args.local or Path(args.remote).name
    run_command(
        module_command(
            "mpremote",
            [
                *mpremote_prefix(args, config),
                "fs",
                "cp",
                args.remote,
                local,
            ],
        )
    )


def should_exclude(path: Path, root: Path, excluded_names: set[str]) -> bool:
    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in excluded_names for part in relative_parts)


def uploadable_files(
    source_root: Path,
    excluded_names: set[str],
    include_all: bool,
) -> Iterable[Path]:
    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        if should_exclude(path, source_root, excluded_names):
            continue
        if path.name == CONFIG_FILE or path.name == Path(__file__).name:
            continue
        if include_all or path.suffix.lower() in UPLOAD_SUFFIXES:
            yield path


def remote_parent_directories(relative_path: Path) -> list[str]:
    directories: list[str] = []
    current = relative_path.parent

    while current != Path("."):
        directories.append(current.as_posix())
        current = current.parent

    return list(reversed(directories))


def ensure_remote_directory(
    args: argparse.Namespace,
    config: dict,
    remote_dir: str,
    created: set[str],
) -> None:
    if not remote_dir or remote_dir in created:
        return

    result = run_command(
        module_command(
            "mpremote",
            [
                *mpremote_prefix(args, config),
                "fs",
                "mkdir",
                f":{remote_dir}",
            ],
        ),
        check=False,
        capture=True,
    )

    # mkdir returns an error when the directory already exists. That is harmless.
    if result.returncode != 0:
        combined = f"{result.stdout}\n{result.stderr}".lower()
        harmless = "exist" in combined or "eexist" in combined or "errno 17" in combined
        if not harmless:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            raise EspError(f"Could not create remote directory :{remote_dir}")

    created.add(remote_dir)


def command_upload(args: argparse.Namespace, config: dict) -> None:
    """
    Upload one file or a project directory while preserving subdirectories.

    By default, only common source/data file extensions are copied. Use
    --all-files to copy every non-excluded file.
    """
    require_tools("mpremote")

    source = Path(args.source or config.get("source", ".")).expanduser().resolve()
    if not source.exists():
        raise EspError(f"Upload source does not exist: {source}")

    if source.is_file():
        destination = args.destination or f":{source.name}"
        run_command(
            module_command(
                "mpremote",
                [
                    *mpremote_prefix(args, config),
                    "fs",
                    "cp",
                    str(source),
                    destination,
                ],
            )
        )
        print(f"\nUploaded {source.name} -> {destination}")
        return

    excluded_names = set(config.get("exclude", []))
    excluded_names.update(args.exclude or [])

    files = list(uploadable_files(source, excluded_names, args.all_files))
    if not files:
        raise EspError("No uploadable files were found.")

    print(f"Uploading {len(files)} file(s) from {source}")
    created_directories: set[str] = set()

    for local_path in files:
        relative = local_path.relative_to(source)

        for remote_dir in remote_parent_directories(relative):
            ensure_remote_directory(
                args,
                config,
                remote_dir,
                created_directories,
            )

        remote_path = f":{relative.as_posix()}"
        run_command(
            module_command(
                "mpremote",
                [
                    *mpremote_prefix(args, config),
                    "fs",
                    "cp",
                    str(local_path),
                    remote_path,
                ],
            )
        )

    print(f"\nUploaded {len(files)} file(s).")


def command_mount(args: argparse.Namespace, config: dict) -> None:
    require_tools("mpremote")

    directory = Path(args.directory).expanduser().resolve()
    if not directory.is_dir():
        raise EspError(f"Mount directory not found: {directory}")

    run_command(
        module_command(
            "mpremote",
            [
                *mpremote_prefix(args, config),
                "mount",
                str(directory),
                "repl",
            ],
        )
    )


def add_connection_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--port",
        help="Serial port, such as COM5 or /dev/cu.usbserial-0001. "
        "Default: value in .esp.json or auto.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="esp",
        description="Cross-platform ESP32 + MicroPython helper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python esp.py doctor
  python esp.py ports
  python esp.py --port COM5 erase
  python esp.py --port COM5 flash firmware/ESP32_GENERIC.bin
  python esp.py repl
  python esp.py run main.py
  python esp.py upload
  python esp.py upload joystick.py
  python esp.py ls
  python esp.py cat :main.py
  python esp.py reset
""",
    )
    add_connection_options(parser)

    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check Python and required tools.")
    doctor.set_defaults(handler=command_doctor)

    ports = subparsers.add_parser("ports", help="List available serial devices.")
    ports.set_defaults(handler=command_ports)

    config = subparsers.add_parser("config", help=f"Create {CONFIG_FILE}.")
    config.add_argument("--force", action="store_true", help="Replace existing config.")
    config.set_defaults(handler=lambda args, cfg: save_default_config(args.force))

    erase = subparsers.add_parser("erase", help="Erase the ESP32 flash.")
    erase.add_argument("--chip", help="Chip name. Default: esp32.")
    erase.set_defaults(handler=command_erase)

    flash = subparsers.add_parser("flash", help="Write a MicroPython .bin file.")
    flash.add_argument("firmware", help="Path to the MicroPython .bin file.")
    flash.add_argument("--chip", help="Chip name. Default: esp32.")
    flash.add_argument("--baud", type=int, help="Upload baud rate.")
    flash.add_argument(
        "--offset",
        help="Flash offset. Classic ESP32 MicroPython normally uses 0x1000.",
    )
    flash.set_defaults(handler=command_flash)

    repl = subparsers.add_parser("repl", help="Open the MicroPython REPL.")
    repl.set_defaults(handler=command_repl)

    run = subparsers.add_parser(
        "run",
        help="Run a local Python file without saving it to the ESP32.",
    )
    run.add_argument("file", help="Local Python file.")
    run.set_defaults(handler=command_run)

    execute = subparsers.add_parser("exec", help="Execute a MicroPython statement.")
    execute.add_argument("code", help='Code such as: print("hello")')
    execute.set_defaults(handler=command_exec)

    upload = subparsers.add_parser(
        "upload",
        help="Upload one file or the current project.",
    )
    upload.add_argument(
        "source",
        nargs="?",
        help="File or directory. Default: project source in .esp.json.",
    )
    upload.add_argument(
        "--destination",
        help="Remote destination when uploading one file, such as :main.py.",
    )
    upload.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Additional directory or file name to exclude. Repeat as needed.",
    )
    upload.add_argument(
        "--all-files",
        action="store_true",
        help="Upload every non-excluded file, not only common source/data files.",
    )
    upload.set_defaults(handler=command_upload)

    ls_parser = subparsers.add_parser("ls", help="List files on the ESP32.")
    ls_parser.add_argument("path", nargs="?", help="Remote path. Default: :")
    ls_parser.set_defaults(handler=command_ls)

    cat = subparsers.add_parser("cat", help="Display a remote file.")
    cat.add_argument("path", help="Remote path, such as :main.py.")
    cat.set_defaults(handler=command_cat)

    get = subparsers.add_parser("get", help="Copy a file from the ESP32.")
    get.add_argument("remote", help="Remote path, such as :data.csv.")
    get.add_argument("local", nargs="?", help="Optional local destination.")
    get.set_defaults(handler=command_get)

    rm = subparsers.add_parser("rm", help="Remove a remote file or directory.")
    rm.add_argument("path", help="Remote path.")
    rm.add_argument("-r", "--recursive", action="store_true")
    rm.set_defaults(handler=command_rm)

    mkdir = subparsers.add_parser("mkdir", help="Create a remote directory.")
    mkdir.add_argument("path", help="Remote path, such as :lib.")
    mkdir.set_defaults(handler=command_mkdir)

    reset = subparsers.add_parser("reset", help="Reset the ESP32.")
    reset.add_argument(
        "--soft",
        action="store_true",
        help="Perform a MicroPython soft reset instead of a hardware reset.",
    )
    reset.set_defaults(handler=command_reset)

    mount = subparsers.add_parser(
        "mount",
        help="Mount a local directory and enter the REPL.",
    )
    mount.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Local directory. Default: current directory.",
    )
    mount.set_defaults(handler=command_mount)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = load_config()
        args.handler(args, config)
        return 0
    except EspError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
