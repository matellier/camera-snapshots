import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULTS = {
    "camera_index": 0,
    "interval_minutes": 15,
    "start_time": "07:00",
    "stop_time": "19:00",
    "consecutive_days": 1,
    "retention_days": 7,
    "photos_dir": os.path.expanduser("~/photos"),
    "nas_path": "/mnt/nas/camera-snapshots",
    "video_framerate": 2,
    "video_width": 1920,
    "video_height": 1080,
}


def load() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            data = json.load(f)
        # Fill in any missing keys from defaults
        for key, val in DEFAULTS.items():
            data.setdefault(key, val)
        return data
    return dict(DEFAULTS)


def save(config: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
