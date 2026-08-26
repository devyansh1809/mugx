"""
ui/template_preview_widget.py

A simple bordered label that displays the flattened template preview image,
scaled to fit while preserving aspect ratio. Kept separate from
main_window.py so preview-rendering logic (rescaling on resize, empty-state
text) doesn't clutter the window class.
"""

from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class TemplatePreviewWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            "QLabel { border: 1px solid #444; background-color: #1e1e1e; color: #888; }"
        )
        self._source_pixmap: QPixmap | None = None
        self.show_empty_state()

    def show_empty_state(self):
        self._source_pixmap = None
        self.setText("No template loaded.\nUse “Load Template” to choose a PSD or PNG file.")

    def set_preview(self, image_path: str):
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.setText(f"Could not display preview:\n{image_path}")
            self._source_pixmap = None
            return
        self._source_pixmap = pixmap
        self._rescale()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rescale()

    def _rescale(self):
        if self._source_pixmap is None:
            return
        scaled = self._source_pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaled)
