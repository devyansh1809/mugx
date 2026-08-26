"""
ui/text_tool_dialog.py

Simple text tool: text, font size, color, and position.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox, QPushButton, QDialogButtonBox,
    QColorDialog, QHBoxLayout, QDoubleSpinBox,
)
from PyQt6.QtGui import QColor


class TextToolDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Text")
        self._color = QColor(255, 255, 255)

        layout = QFormLayout(self)

        self.text_edit = QLineEdit()
        layout.addRow("Text:", self.text_edit)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 300)
        self.font_size_spin.setValue(48)
        layout.addRow("Font size:", self.font_size_spin)

        color_row = QHBoxLayout()
        self.color_preview_btn = QPushButton()
        self.color_preview_btn.setFixedWidth(60)
        self._update_color_preview()
        self.color_preview_btn.clicked.connect(self._pick_color)
        color_row.addWidget(self.color_preview_btn)
        layout.addRow("Color:", color_row)

        self.pos_x_spin = QDoubleSpinBox()
        self.pos_x_spin.setRange(0.0, 1.0)
        self.pos_x_spin.setSingleStep(0.05)
        self.pos_x_spin.setValue(0.5)
        layout.addRow("Position X (0-1):", self.pos_x_spin)

        self.pos_y_spin = QDoubleSpinBox()
        self.pos_y_spin.setRange(0.0, 1.0)
        self.pos_y_spin.setSingleStep(0.05)
        self.pos_y_spin.setValue(0.85)
        layout.addRow("Position Y (0-1):", self.pos_y_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _update_color_preview(self):
        self.color_preview_btn.setStyleSheet(f"background-color: {self._color.name()};")

    def _pick_color(self):
        color = QColorDialog.getColor(self._color, self, "Choose text color")
        if color.isValid():
            self._color = color
            self._update_color_preview()

    def get_values(self):
        return {
            "text": self.text_edit.text(),
            "font_size": self.font_size_spin.value(),
            "color": (self._color.red(), self._color.green(), self._color.blue(), 255),
            "pos_x_ratio": self.pos_x_spin.value(),
            "pos_y_ratio": self.pos_y_spin.value(),
        }
