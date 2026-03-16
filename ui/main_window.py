import os
from PyQt6.QtCore import QTime, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QSpinBox, QPushButton, QTimeEdit, QGroupBox,
    QFormLayout, QSizePolicy,
)

from capture.camera import Camera
from capture.scheduler import Scheduler
from postprocess.stitch import stitch
from storage.manager import StorageManager
from ui.preview import PreviewWidget
import config as cfg


class _Signals(QObject):
    status_updated = pyqtSignal(str)
    count_updated = pyqtSignal(int)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Snapshots")
        self._config = cfg.load()

        self._camera = Camera(self._config["camera_index"])
        self._storage = StorageManager(
            self._config["photos_dir"],
            self._config["nas_path"],
            self._config["retention_days"],
        )
        self._scheduler: Scheduler | None = None
        self._capture_count = 0

        self._signals = _Signals()
        self._signals.status_updated.connect(self._set_status)
        self._signals.count_updated.connect(
            lambda n: self._count_label.setText(f"Captures: {n}")
        )

        self._build_ui()
        self._open_camera()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Left: live preview
        self._preview = PreviewWidget(self._camera, fps=10)
        self._preview.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        root.addWidget(self._preview, stretch=3)

        # Right: controls
        root.addLayout(self._build_controls(), stretch=1)

    def _build_controls(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # --- Scheduler settings ---
        group = QGroupBox("Scheduler")
        form = QFormLayout(group)

        self._start_edit = QTimeEdit()
        self._start_edit.setDisplayFormat("HH:mm")
        self._start_edit.setTime(QTime.fromString(self._config["start_time"], "HH:mm"))
        form.addRow("Start", self._start_edit)

        self._stop_edit = QTimeEdit()
        self._stop_edit.setDisplayFormat("HH:mm")
        self._stop_edit.setTime(QTime.fromString(self._config["stop_time"], "HH:mm"))
        form.addRow("Stop", self._stop_edit)

        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(1, 120)
        self._interval_spin.setSuffix(" min")
        self._interval_spin.setValue(self._config["interval_minutes"])
        form.addRow("Interval", self._interval_spin)

        self._days_spin = QSpinBox()
        self._days_spin.setRange(1, 365)
        self._days_spin.setSuffix(" day(s)")
        self._days_spin.setValue(self._config["consecutive_days"])
        form.addRow("Days", self._days_spin)

        layout.addWidget(group)

        # --- Start / Stop button ---
        self._toggle_btn = QPushButton("Start")
        self._toggle_btn.setMinimumHeight(50)
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.clicked.connect(self._toggle_scheduler)
        layout.addWidget(self._toggle_btn)

        # --- Status ---
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)

        self._status_label = QLabel("Idle")
        self._status_label.setWordWrap(True)
        status_layout.addWidget(self._status_label)

        self._count_label = QLabel("Captures: 0")
        status_layout.addWidget(self._count_label)

        self._nas_label = QLabel()
        self._update_nas_status()
        status_layout.addWidget(self._nas_label)

        layout.addWidget(status_group)
        layout.addStretch()

        return layout

    # ------------------------------------------------------------------
    # Camera
    # ------------------------------------------------------------------

    def _open_camera(self) -> None:
        if self._camera.open():
            self._preview.start()
        else:
            self._set_status("Camera not found")

    # ------------------------------------------------------------------
    # Scheduler toggle
    # ------------------------------------------------------------------

    def _toggle_scheduler(self, checked: bool) -> None:
        if checked:
            self._start_scheduler()
        else:
            self._stop_scheduler()

    def _start_scheduler(self) -> None:
        # Persist current settings
        self._config["start_time"] = self._start_edit.time().toString("HH:mm")
        self._config["stop_time"] = self._stop_edit.time().toString("HH:mm")
        self._config["interval_minutes"] = self._interval_spin.value()
        self._config["consecutive_days"] = self._days_spin.value()
        cfg.save(self._config)

        # Rebuild storage manager in case config changed
        self._storage = StorageManager(
            self._config["photos_dir"],
            self._config["nas_path"],
            self._config["retention_days"],
        )

        self._capture_count = 0
        self._scheduler = Scheduler(
            interval_minutes=self._config["interval_minutes"],
            start_time=self._config["start_time"],
            stop_time=self._config["stop_time"],
            on_capture=self._do_capture,
            on_day_end=self._do_day_end,
        )
        self._scheduler.start()

        self._toggle_btn.setText("Stop")
        self._set_status("Running")
        self._update_nas_status()

        # Lock settings while running
        for w in (self._start_edit, self._stop_edit,
                  self._interval_spin, self._days_spin):
            w.setEnabled(False)

    def _stop_scheduler(self) -> None:
        if self._scheduler:
            self._scheduler.stop()
            self._scheduler = None

        self._toggle_btn.setText("Start")
        self._set_status("Stopped")

        for w in (self._start_edit, self._stop_edit,
                  self._interval_spin, self._days_spin):
            w.setEnabled(True)

    # ------------------------------------------------------------------
    # Capture + day-end callbacks (called from background thread)
    # ------------------------------------------------------------------

    def _do_capture(self) -> None:
        output_dir = self._storage.today_dir()
        path = self._camera.capture(output_dir)
        if path:
            self._capture_count += 1
            ts = os.path.basename(path).replace(".jpg", "").replace("-", ":")
            self._signals.status_updated.emit(f"Last: {ts}")
            self._signals.count_updated.emit(self._capture_count)

    def _do_day_end(self, date_str: str) -> None:
        self._signals.status_updated.emit(f"Day ended — stitching {date_str}…")

        video_path = stitch(
            date_str=date_str,
            photos_dir=self._config["photos_dir"],
            output_dir=self._config["nas_path"],
            framerate=self._config["video_framerate"],
            width=self._config["video_width"],
            height=self._config["video_height"],
        )

        if video_path:
            self._signals.status_updated.emit(f"Video saved: {date_str}.mp4")
        else:
            self._signals.status_updated.emit(f"Stitch failed for {date_str}")

        self._storage.archive_to_nas(date_str)
        self._storage.purge_old()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def _update_nas_status(self) -> None:
        ok = self._storage.nas_available()
        self._nas_label.setText(f"NAS: {'OK' if ok else 'Not mounted'}")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        self._stop_scheduler()
        self._preview.stop()
        self._camera.close()
        super().closeEvent(event)
