# CLAUDE.md

## Project Overview

Python application for a Raspberry Pi 4 that captures time-lapse photos from a Logitech USB webcam throughout the day, then stitches them into a video saved to a Synology NAS. Purpose: document sun/shadow patterns in the backyard to inform planting decisions.

Full project notes: `~/Vaults/obsidian-ai/01-Projects/camera-snapshots.md`

## Target Hardware

- Raspberry Pi 4 (4GB RAM)
- Official 7" DSI touchscreen display
- Logitech USB webcam (046d:0825) → `/dev/video1` (video0 absent on this RPi)
- Synology NAS mounted via NFS at `/mnt/nas/camera-snapshots`

## OS

Raspberry Pi OS (64-bit) Debian Trixie Desktop
(As of RPi Imager 1.9.0 — Bookworm is now 32-bit legacy only)

## Tech Stack

| Concern | Library |
|---|---|
| GUI | PyQt6 |
| Camera / preview + overlay | opencv-python (cv2) |
| Scheduling | Python threading + datetime |
| Config | JSON (stdlib) |
| Video stitching | ffmpeg (subprocess) |
| NAS writes | NFS mount, treated as local path |

## Project Structure

```
main.py                  # Entry point — launches GUI
start.sh                 # Launch script for RPi4 (sets Wayland env)
ui/
  main_window.py         # Main window: preview + controls
  preview.py             # OpenCV → QPixmap live feed widget
capture/
  camera.py              # Camera open/close, frame grab, timestamp overlay, JPEG save
  scheduler.py           # Background thread: interval timing, start/stop window
postprocess/
  stitch.py              # ffmpeg wrapper: photos → video, NAS copy
storage/
  manager.py             # Date folder creation, archival/deletion logic
config.py                # Load/save config.json
config.json              # User settings (gitignored)
requirements.txt
```

## RPi4 Setup Log

All changes made to the RPi4 (192.168.50.144) must be documented in the Obsidian project note under the **RPi4 Setup Log** table before or immediately after making the change. This is the source of truth for the device's configuration state.

SSH access: `ssh rpi4` (configured in `~/.ssh/config` using `id_ed25519_ansible`)

## Key Conventions

- Photos saved as `photos/YYYYMMDD/HH-MM-SS.jpg` (local), then archived to NAS
- Video output filename: `YYYYMMDD.mp4`
- NAS path: `/mnt/nas/camera-snapshots/`
- Config is persisted in `config.json` (excluded from git)
- No root/sudo required at runtime; NFS mount is configured at OS level in `/etc/fstab`

## Running on RPi4

```bash
# Start (from any terminal on the RPi4)
~/camera-snapshots/start.sh

# Stop — close the window, or Ctrl+C in the terminal
```

The `start.sh` script sets `WAYLAND_DISPLAY` and `XDG_RUNTIME_DIR` automatically.

## Development

```bash
# Install dependencies (on RPi or dev machine)
pip install -r requirements.txt

# Run the application (dev machine, if display available)
python main.py
```

## ffmpeg Stitch Reference

```bash
ffmpeg -framerate 2 -pattern_type glob -i 'photos/YYYYMMDD/*.jpg' \
  -vf "scale=1920:1080" -c:v libx264 -pix_fmt yuv420p \
  /mnt/nas/camera-snapshots/YYYYMMDD.mp4
```
