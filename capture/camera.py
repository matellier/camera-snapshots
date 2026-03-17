import os
import cv2
import numpy as np
from datetime import datetime


class Camera:
    def __init__(self, index: int = 0):
        self._index = index
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> bool:
        self._cap = cv2.VideoCapture(self._index, cv2.CAP_V4L2)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        return self._cap.isOpened()

    def close(self) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None

    def switch(self, index: int) -> bool:
        self.close()
        self._index = index
        return self.open()

    @property
    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def read_frame(self) -> np.ndarray | None:
        if not self.is_open:
            return None
        ok, frame = self._cap.read()
        return frame if ok else None

    def capture(self, output_dir: str) -> str | None:
        """Grab a frame, burn timestamp, save JPEG. Returns saved path or None."""
        frame = self.read_frame()
        if frame is None:
            return None

        ts = datetime.now()
        _burn_timestamp(frame, ts)

        os.makedirs(output_dir, exist_ok=True)
        filename = ts.strftime("%H-%M-%S") + ".jpg"
        path = os.path.join(output_dir, filename)
        cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return path


def _burn_timestamp(frame: np.ndarray, ts: datetime) -> None:
    text = ts.strftime("%Y-%m-%d  %H:%M:%S")
    h, w = frame.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = w / 1920  # scale relative to 1080p
    thickness = max(1, int(2 * scale))
    shadow_offset = max(1, int(2 * scale))

    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    x = w - tw - int(20 * scale)
    y = h - int(20 * scale)

    # Shadow for legibility on any background
    cv2.putText(frame, text, (x + shadow_offset, y + shadow_offset),
                font, scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(frame, text, (x, y),
                font, scale, (0, 165, 255), thickness + 1, cv2.LINE_AA)
