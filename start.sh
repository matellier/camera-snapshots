#!/usr/bin/env bash
# Launch camera-snapshots on the local Wayland display.
# Run from any terminal on the RPi4: ./start.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/run/user/$(id -u)

exec "$HOME/camera-snapshots-venv/bin/python" "$SCRIPT_DIR/main.py" "$@"
