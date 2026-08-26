"""
ui/template_preview_widget.py

Displays the flattened template/design preview, scaled to fit, with an
optional overlay of clickable frame rectangles.
"""
from __future__ import annotations

from typing import List, Optional

from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QMouseEvent
from PyQt6.QtCore import Qt, pyqtSignal

from core.models import FrameInfo


class TemplatePreviewWidget(QLabel):
    frame_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("QLabel { border: 1px solid #444; background-color: #1e1e1e; color: #888; }")
        self._source_pixmap: Optional[QPixmap] = None
        self._frames: List[FrameInfo] = []
        self._source_size = (0, 0)
        self._show_frames = False
        self.show_empty_state()

    def show_empty_state(self):
        self._source_pixmap = None
        self._frames = []
        self.setText("No template loaded.\nUse \u201cLoad Template\u201d to choose a PSD or PNG file.")

    def set_preview(self, image_path: str, frames: Optional[List[FrameInfo]] = None, source_size: Optional[tuple] = None):
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.setText(f"Could not display preview:\n{image_path}")
            self._source_pixmap = None
            return
        self._source_pixmap = pixmap
        self._frames = frames or []
        self._source_size = source_size or (pixmap.width(), pixmap.height())
        self._rescale()

    def set_show_frames(self, show: bool):
        self._show_frames = show
        self._rescale()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rescale()

    def _current_scaled_pixmap(self) -> Optional[QPixmap]:
        if self._source_pixmap is None:
            return None
        return self._source_pixmap.scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )

    def _rescale(self):
        scaled = self._current_scaled_pixmap()
        if scaled is None:
            return
        if not self._show_frames or not self._frames:
            self.setPixmap(scaled)
            return

        painted = QPixmap(scaled)
        painter = QPainter(painted)
        pen = QPen(QColor(0, 200, 255, 220))
        pen.setWidth(2)
        painter.setPen(pen)

        src_w, src_h = self._source_size
        if src_w and src_h:
            scale_x = scaled.width() / src_w
            scale_y = scaled.height() / src_h
            for frame in self._frames:
                painter.drawRect(
                    round(frame.left * scale_x), round(frame.top * scale_y),
                    round(frame.width * scale_x), round(frame.height * scale_y),
                )
        painter.end()
        self.setPixmap(painted)

    def _pixmap_offset(self) -> tuple:
        scaled = self._current_scaled_pixmap()
        if scaled is None:
            return (0, 0)
        return ((self.width() - scaled.width()) // 2, (self.height() - scaled.height()) // 2)

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        if not self._frames or self._source_pixmap is None:
            return
        scaled = self._current_scaled_pixmap()
        if scaled is None:
            return
        off_x, off_y = self._pixmap_offset()
        click_x = event.position().x() - off_x
        click_y = event.position().y() - off_y

        src_w, src_h = self._source_size
        if not src_w or not src_h:
            return
        scale_x = scaled.width() / src_w
        scale_y = scaled.height() / src_h

        for idx, frame in enumerate(self._frames):
            rx0 = frame.left * scale_x
            ry0 = frame.top * scale_y
            rx1 = rx0 + frame.width * scale_x
            ry1 = ry0 + frame.height * scale_y
            if rx0 <= click_x <= rx1 and ry0 <= click_y <= ry1:
                self.frame_clicked.emit(idx)
                return
