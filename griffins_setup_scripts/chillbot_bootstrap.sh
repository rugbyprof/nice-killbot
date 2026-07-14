#!/usr/bin/env bash
#
# Killbot dev environment bootstrap — Raspberry Pi OS Bookworm
# Usage: ./killbot_bootstrap.sh [phase ...]
#   No args   -> run all phases in order
#   Phase name(s) -> run only those, e.g. ./killbot_bootstrap.sh gpio camera
#
# Safe to re-run: apt/pip installs are idempotent.

set -euo pipefail

log() { printf '\n\033[1;32m==> %s\033[0m\n' "$1"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$1"; }

phase_essential() {
    log "Phase 1: Essential development"
    sudo apt update
    sudo apt install -y \
        git curl wget unzip zip \
        build-essential cmake ninja-build pkg-config \
        gdb valgrind make \
        python3 python3-pip python3-venv python3-dev pipx
}

phase_terminal() {
    log "Phase 2: Better terminal"
    sudo apt install -y \
        zsh tmux fzf zoxide eza bat fd-find ripgrep tree \
        btop htop ncdu neofetch

    # bat and fd-find install their binaries as `batcat` / `fdfind` on
    # Debian-based systems (name clashes with unrelated existing packages).
    # Symlink them into ~/.local/bin so `bat`/`fd` work as expected.
    mkdir -p "$HOME/.local/bin"
    ln -sf "$(command -v batcat)" "$HOME/.local/bin/bat" 2>/dev/null || true
    ln -sf "$(command -v fdfind)" "$HOME/.local/bin/fd" 2>/dev/null || true

    # fastfetch is NOT in Bookworm's stable repo (testing/unstable only as of
    # this writing). Pull the latest arm64 .deb from GitHub releases instead.
    if ! command -v fastfetch >/dev/null 2>&1; then
        log "Installing fastfetch from GitHub release (not in Bookworm apt)"
        FASTFETCH_URL=$(curl -fsSL https://api.github.com/repos/fastfetch-cli/fastfetch/releases/latest \
            | grep -o '"browser_download_url": *"[^"]*linux-aarch64\.deb"' \
            | head -n1 | cut -d'"' -f4)
        if [ -n "${FASTFETCH_URL:-}" ]; then
            tmp_deb=$(mktemp --suffix=.deb)
            curl -fsSL "$FASTFETCH_URL" -o "$tmp_deb"
            sudo apt install -y "$tmp_deb"
            rm -f "$tmp_deb"
        else
            warn "Could not resolve fastfetch release asset; skipping (neofetch still installed)"
        fi
    fi
}

phase_networking() {
    log "Phase 3: Networking"
    sudo apt install -y \
        openssh-server avahi-daemon net-tools \
        nmap dnsutils iperf3 tcpdump
    sudo systemctl enable --now ssh avahi-daemon
    echo "SSH available at: killbot.local"
}

phase_gpio() {
    log "Phase 4: GPIO / robotics"
    # spi-tools is an orphaned/unreliable Debian package (often unresolvable
    # on Bookworm) — dropped. python3-spidev covers Python-side SPI access;
    # i2c-tools/gpiod already give CLI diagnostics for both buses.
    sudo apt install -y \
        gpiod libgpiod-dev python3-libgpiod \
        i2c-tools python3-spidev

    log "Enabling I2C, SPI, SSH via raspi-config (non-interactive)"
    sudo raspi-config nonint do_i2c 0
    sudo raspi-config nonint do_spi 0
    sudo raspi-config nonint do_ssh 0
    warn "I2C/SPI changes require a reboot to take effect (sudo reboot when convenient)"
}

phase_camera() {
    log "Phase 5: Camera"
    # libcamera-apps was renamed to rpicam-apps on Bookworm; install the
    # current name directly rather than relying on a transitional package.
    sudo apt install -y rpicam-apps python3-picamera2
}

phase_cpp() {
    log "Phase 6: C++"
    sudo apt install -y clang clang-format clang-tidy cppcheck
}

phase_git() {
    log "Phase 7: Git quality of life"
    sudo apt install -y git-lfs

    if ! command -v gh >/dev/null 2>&1; then
        log "Installing GitHub CLI from GitHub's official apt repo (Bookworm's own gh package is stale)"
        sudo mkdir -p -m 755 /etc/apt/keyrings
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
            | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null
        sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
            | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
        sudo apt update
        sudo apt install -y gh
    fi
}

phase_utilities() {
    log "Phase 8: Nice utilities"
    sudo apt install -y jq yq sqlite3 imagemagick ffmpeg
}

phase_sensors() {
    log "Phase 9: Sensors"
    sudo apt install -y lm-sensors stress stress-ng
}

phase_docs() {
    log "Phase 10: Documentation"
    sudo apt install -y man-db manpages-dev tldr
    tldr --update || true
}

phase_shell_setup() {
    log "Phase 11: VS Code Remote SSH / shell PATH setup"
    mkdir -p "$HOME/.local/bin" "$HOME/.local/share"

    ZSHRC="$HOME/.zshrc"
    touch "$ZSHRC"
    if ! grep -q 'HOME/.local/bin' "$ZSHRC"; then
        {
            echo ''
            echo '# Killbot: local scripts / tool shims'
            echo 'export PATH="$HOME/.local/bin:$PATH"'
        } >> "$ZSHRC"
    fi
}

phase_python_venv() {
    log "Phase 12: Python virtual environment"
    # Bookworm marks the system Python as "externally managed" (PEP 668),
    # so a venv isn't just best practice here — apt/pip will refuse a
    # global `pip install` outside one by default.
    if [ ! -d "$HOME/.venv" ]; then
        python3 -m venv "$HOME/.venv"
    fi
    # shellcheck disable=SC1091
    source "$HOME/.venv/bin/activate"
    pip install --upgrade pip
    pip install \
        rich click typer requests pillow numpy matplotlib \
        opencv-python gpiozero lgpio pyserial
    warn "Robotics extras (ultralytics, onnxruntime, pyzmq, fastapi, uvicorn, paho-mqtt) intentionally deferred — install later when needed"
    deactivate
}

phase_extras() {
    log "Phase 13 (optional): Killbot extras"
    sudo apt install -y cowsay fortune-mod lolcat cmatrix sl
}

ALL_PHASES=(essential terminal networking gpio camera cpp git utilities sensors docs shell_setup python_venv extras)

run_phase() {
    case "$1" in
        essential) phase_essential ;;
        terminal) phase_terminal ;;
        networking) phase_networking ;;
        gpio) phase_gpio ;;
        camera) phase_camera ;;
        cpp) phase_cpp ;;
        git) phase_git ;;
        utilities) phase_utilities ;;
        sensors) phase_sensors ;;
        docs) phase_docs ;;
        shell_setup) phase_shell_setup ;;
        python_venv) phase_python_venv ;;
        extras) phase_extras ;;
        *) warn "Unknown phase: $1" ; exit 1 ;;
    esac
}

if [ "$#" -eq 0 ]; then
    for p in "${ALL_PHASES[@]}"; do run_phase "$p"; done
else
    for p in "$@"; do run_phase "$p"; done
fi

log "Done. Reboot if I2C/SPI were just enabled: sudo reboot"