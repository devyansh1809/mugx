"""Shared live design/print preview widget with frame overlays."""
from __future__ import annotations

from typing import List, Optional

from PIL import Image
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPainter, QPen, QColor, QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy

from core.models import FrameInfo


class LiveCanvasPreview(QLabel):
    """Renders the actual PIL canvas currently being edited.

    Unlike a static template thumbnail, this widget accepts the exact composite
    canvas used for printing, so background/text/effect/photo changes are shown
    immediately. Clicking a frame emits its index for Manual Edit selection.
    """

    frame_clicked = pyqtSignal(int)

    def __init__(self, title: str = "Live Preview", parent=None):
        super().__init__(parent)
        self._canvas: Optional[Image.Image] = None
        self._frames: List[FrameInfo] = []
        self._selected_frame: Optional[int] = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(440, 340)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("QLabel { border: 1px solid #606060; background: #171717; color: #a0a0a0; }")
        self.setText(title)

    def set_canvas(self, canvas: Optional[Image.Image], frames: Optional[List[FrameInfo]] = None,
                   selected_frame: Optional[int] = None):
        self._canvas = canvas.copy() if canvas is not None else None
        self._frames = frames or []
        self._selected_frame = selected_frame
        self._render()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render()

    def _render(self):
        if self._canvas is None:
            return
        image = self._canvas.convert("RGBA")
        data = image.tobytes("raw", "RGBA")
        qimage = QImage(data, image.width, image.height, QImage.Format.Format_RGBA8888).copy()
        pixmap = QPixmap.fromImage(qimage).scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        if self._frames:
            painter = QPainter(pixmap)
            sx = pixmap.width() / image.width
            sy = pixmap.height() / image.height
            for index, frame in enumerate(self._frames):
                color = QColor(40, 180, 255) if index == self._selected_frame else QColor(255, 215, 0)
                pen = QPen(color)
                pen.setWidth(3 if index == self._selected_frame else 2)
                painter.setPen(pen)
                painter.drawRect(round(frame.left * sx), round(frame.top * sy),
                                 round(frame.width * sx), round(frame.height * sy))
            painter.end()
        self.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if self._canvas is None or not self._frames or self.pixmap() is None:
            return super().mousePressEvent(event)
        pixmap = self.pixmap()
        offset_x = (self.width() - pixmap.width()) / 2
        offset_y = (self.height() - pixmap.height()) / 2
        x = event.position().x() - offset_x
        y = event.position().y() - offset_y
        if x < 0 or y < 0 or x > pixmap.width() or y > pixmap.height():
            return
        sx = pixmap.width() / self._canvas.width
        sy = pixmap.height() / self._canvas.height
        for index, frame in enumerate(self._frames):
            if frame.left * sx <= x <= (frame.left + frame.width) * sx and frame.top * sy <= y <= (frame.top + frame.height) * sy:
                self.frame_clicked.emit(index)
                return
