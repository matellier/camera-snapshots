import cv2
import numpy as np
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel


class PreviewWidget(QLabel):
    """Displays a live camera feed by polling frames on a QTimer."""

    def __init__(self, camera, fps: int = 10, parent=None):
        super().__init__(parent)
        self._camera = camera
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 180)
        self.setStyleSheet("background-color: black;")

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_frame)
        self._interval = max(1, 1000 // fps)

    def start(self) -> None:
        self._timer.start(self._interval)

    def stop(self) -> None:
        self._timer.stop()
        self.clear()
        self.setStyleSheet("background-color: black;")

    def _update_frame(self) -> None:
        frame = self._camera.read_frame()
        if frame is None:
            return
        pixmap = _frame_to_pixmap(frame)
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaled)


def _frame_to_pixmap(frame: np.ndarray) -> QPixmap:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    # Use tobytes() to copy data — QImage doesn't own the buffer otherwise
    img = QImage(rgb.tobytes(), w, h, ch * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(img)
