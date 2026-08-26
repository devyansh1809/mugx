"""
ui/print_settings_dialog.py

Dialog to configure PrintSettings before exporting.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QComboBox, QSpinBox, QCheckBox, QDialogButtonBox, QDoubleSpinBox,
)

from core.print_exporter import PrintSettings, PAPER_SIZES_MM


class PrintSettingsDialog(QDialog):
    def __init__(self, parent=None, initial: Optional[PrintSettings] = None):
        super().__init__(parent)
        self.setWindowTitle("Prepare for Print -- Settings")
        initial = initial or PrintSettings()

        layout = QFormLayout(self)

        self.paper_size_combo = QComboBox()
        self.paper_size_combo.addItems(list(PAPER_SIZES_MM.keys()))
        self.paper_size_combo.setCurrentText(initial.paper_size)
        layout.addRow("Paper size:", self.paper_size_combo)

        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 1200)
        self.dpi_spin.setValue(initial.dpi)
        layout.addRow("DPI:", self.dpi_spin)

        self.designs_per_sheet_spin = QSpinBox()
        self.designs_per_sheet_spin.setRange(1, 20)
        self.designs_per_sheet_spin.setValue(initial.designs_per_sheet)
        layout.addRow("Designs per sheet:", self.designs_per_sheet_spin)

        self.margin_spin = QDoubleSpinBox()
        self.margin_spin.setRange(0.0, 50.0)
        self.margin_spin.setValue(initial.margin_mm)
        self.margin_spin.setSuffix(" mm")
        layout.addRow("Margin:", self.margin_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_settings(self) -> PrintSettings:
        return PrintSettings(
            paper_size=self.paper_size_combo.currentText(),
            dpi=self.dpi_spin.value(),
            designs_per_sheet=self.designs_per_sheet_spin.value(),
            margin_mm=self.margin_spin.value(),
        )
