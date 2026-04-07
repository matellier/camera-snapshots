import threading
import time
from datetime import datetime, date
from typing import Callable


class Scheduler:
    """Fires a capture callback at fixed intervals within a daily time window."""

    def __init__(
        self,
        interval_minutes: int,
        start_time: str,   # "HH:MM"
        stop_time: str,    # "HH:MM"
        on_capture: Callable[[], None],
        on_day_end: Callable[[str], None],  # receives date_str "YYYY-MM-DD"
    ):
        self._interval = interval_minutes * 60
        self._start = _parse_time(start_time)
        self._stop = _parse_time(stop_time)
        self._on_capture = on_capture
        self._on_day_end = on_day_end

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._active_date: date | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            now = datetime.now()
            current_time = (now.hour, now.minute)
            today = now.date()

            in_window = self._start <= current_time < self._stop

            if in_window:
                # First capture of a new day
                if self._active_date != today:
                    self._active_date = today

                self._on_capture()
                # Sleep for interval, but wake early if stopped
                self._stop_event.wait(timeout=self._interval)

            else:
                # Window just closed — trigger day-end processing once
                if self._active_date == today and current_time >= self._stop:
                    self._on_day_end(today.strftime("%Y-%m-%d"))
                    self._active_date = None

                # Sleep briefly and poll again
                self._stop_event.wait(timeout=30)


def _parse_time(t: str) -> tuple[int, int]:
    h, m = t.split(":")
    return int(h), int(m)
