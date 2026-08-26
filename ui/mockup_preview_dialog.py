"""
ui/mockup_preview_dialog.py

Dialog window that displays the 3D mockup preview image.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class MockupPreviewDialog(QDialog):
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("3D Mockup Preview")
        self.resize(600, 600)

        layout = QVBoxLayout(self)
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            label.setPixmap(
                pixmap.scaled(560, 560, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        else:
            label.setText("Could not load mockup preview.")
        layout.addWidget(label)
