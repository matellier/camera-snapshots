import os
import shutil
from datetime import datetime, timedelta


class StorageManager:
    def __init__(self, photos_dir: str, nas_path: str, retention_days: int):
        self._photos_dir = photos_dir
        self._nas_path = nas_path
        self._retention = retention_days

    def today_dir(self) -> str:
        """Return local photo directory for today, creating it if needed."""
        path = os.path.join(self._photos_dir, datetime.now().strftime("%Y-%m-%d"))
        os.makedirs(path, exist_ok=True)
        return path

    def archive_to_nas(self, date_str: str) -> str | None:
        """Copy a date folder to NAS. Returns destination path or None on failure."""
        src = os.path.join(self._photos_dir, date_str)
        if not os.path.isdir(src):
            return None
        dst = os.path.join(self._nas_path, date_str)
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return dst

    def purge_old(self) -> list[str]:
        """Delete local date folders older than retention_days. Returns list of removed paths."""
        cutoff = datetime.now() - timedelta(days=self._retention)
        removed = []
        if not os.path.isdir(self._photos_dir):
            return removed
        for entry in os.scandir(self._photos_dir):
            if not entry.is_dir():
                continue
            try:
                folder_date = datetime.strptime(entry.name, "%Y-%m-%d")
            except ValueError:
                continue
            if folder_date < cutoff:
                shutil.rmtree(entry.path)
                removed.append(entry.path)
        return removed

    def nas_available(self) -> bool:
        return os.path.ismount(self._nas_path) or os.path.isdir(self._nas_path)
