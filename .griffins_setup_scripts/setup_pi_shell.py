#!/usr/bin/env python3
"""Configure zsh + oh-my-zsh on chillbot.local for both griffin and root, over SSH."""

import subprocess
import sys
from pathlib import Path

SSH_USER = "griffin"
HOST = "chillbot.local"
SUDO_PW = "1029"  # rotate this once you're done scripting against it

THEME_LOCAL = Path("/Users/griffin/.oh-my-zsh/themes/griffin.zsh-theme")
ZSHRC_LOCAL = Path("/Users/griffin/Downloads/killbot.zshrc")

SSH_OPTS = ["-o", "ConnectTimeout=10", "-o", "BatchMode=yes"]


def ssh_exec(step: str, script: str) -> None:
    print(f"\n== {step} ==")
    cmd = ["ssh", *SSH_OPTS, f"{SSH_USER}@{HOST}", "bash", "-s"]
    proc = subprocess.run(cmd, input=script, text=True)
    if proc.returncode != 0:
        sys.exit(f"'{step}' failed (exit {proc.returncode})")


def scp_upload(step: str, local: Path, remote_dest: str) -> None:
    print(f"\n== {step} ==")
    if not local.is_file():
        sys.exit(f"Missing local file: {local}")
    cmd = ["scp", *SSH_OPTS, str(local), f"{SSH_USER}@{HOST}:{remote_dest}"]
    subprocess.run(cmd, check=True)


SUDO_HELPER = f"""
SUDO_PW='{SUDO_PW}'
sudo_pw() {{ printf '%s\\n' "$SUDO_PW" | sudo -S -p '' "$@"; }}
"""


def main() -> None:
    ssh_exec(
        "System update",
        SUDO_HELPER + """
set -e
sudo_pw apt update
sudo_pw apt upgrade -y
""",
    )

    ssh_exec(
        "Install zsh and set default shell for griffin + root",
        SUDO_HELPER + """
set -e
command -v zsh >/dev/null 2>&1 || sudo_pw apt install -y zsh
ZSH_PATH=$(command -v zsh)
grep -qxF "$ZSH_PATH" /etc/shells || printf '%s\\n' "$ZSH_PATH" | sudo_pw tee -a /etc/shells >/dev/null
sudo_pw usermod -s "$ZSH_PATH" griffin
sudo_pw usermod -s "$ZSH_PATH" root
echo "griffin shell: $(getent passwd griffin | cut -d: -f7)"
echo "root shell:    $(getent passwd root | cut -d: -f7)"
""",
    )

    ssh_exec(
        "Install oh-my-zsh (unattended)",
        """
set -e
if [ -d "$HOME/.oh-my-zsh" ]; then
    echo "oh-my-zsh already installed, skipping"
else
    RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi
""",
    )

    scp_upload(
        "Upload custom theme", THEME_LOCAL, "~/.oh-my-zsh/themes/griffin.zsh-theme"
    )
    scp_upload("Upload custom .zshrc", ZSHRC_LOCAL, "~/.zshrc")

    ssh_exec(
        "Verify",
        SUDO_HELPER + """
set -e
echo "griffin shell: $(getent passwd griffin | cut -d: -f7)"
echo "root shell:    $(getent passwd root | cut -d: -f7)"
ls -la "$HOME/.oh-my-zsh/themes/griffin.zsh-theme"
ls -la "$HOME/.zshrc"
""",
    )

    print("\nDone. Log out/in (or reboot) for the new default shell to take effect.")


if __name__ == "__main__":
    main()
