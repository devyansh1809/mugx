"""Phase 3 mockup preview widget for the mockup tab."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PIL import Image
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget, QComboBox, QPushButton, QHBoxLayout, QGroupBox, QGridLayout, QFileDialog, QMessageBox

from core.models import ProductProfile
from core.mockup_generator import MockupGenerator


class MockupPreviewWidget(QWidget):
    mockup_exported = pyqtSignal(str)

    def __init__(self, generator: MockupGenerator):
        super().__init__()
        self.generator = generator
        self.profile: Optional[ProductProfile] = None
        self.design: Optional[Image.Image] = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        info_box = QGroupBox("A. Product Mockup Profile")
        info_layout = QVBoxLayout(info_box)
        self.info_label = QLabel("Select a product profile to see available mockups.")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        layout.addWidget(info_box)

        select_box = QGroupBox("B. Select Mockup View")
        select_layout = QGridLayout(select_box)
        select_layout.addWidget(QLabel("Mockup view:"), 0, 0)
        self.mockup_combo = QComboBox()
        self.mockup_combo.currentTextChanged.connect(self._on_mockup_changed)
        select_layout.addWidget(self.mockup_combo, 0, 1)
        self.refresh_button = QPushButton("Refresh Mockup")
        self.refresh_button.clicked.connect(self._render_current)
        select_layout.addWidget(self.refresh_button, 0, 2)
        layout.addWidget(select_box)

        export_box = QGroupBox("C. Export Mockup Image")
        export_layout = QHBoxLayout(export_box)
        self.export_button = QPushButton("Export Mockup PNG")
        self.export_button.clicked.connect(self._export)
        export_layout.addWidget(self.export_button)
        export_layout.addStretch(1)
        layout.addWidget(export_box)

        layout.addWidget(QLabel("Mockup Preview"))
        self.preview_label = QLabel("No mockup rendered yet")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        layout.addWidget(self.preview_label, 1)

    def set_product(self, profile: ProductProfile) -> None:
        self.profile = profile
        self.mockup_combo.blockSignals(True)
        self.mockup_combo.clear()
        if profile.mockup_profiles:
            self.mockup_combo.addItems(profile.mockup_profiles)
            self.info_label.setText(f"Product: {profile.name}\nAvailable mockups: {', '.join(profile.mockup_profiles)}")
        else:
            self.info_label.setText(f"Product: {profile.name}\nNo mockup profiles defined for this product.")
        self.mockup_combo.blockSignals(False)
        self._render_current()

    def set_design(self, design: Optional[Image.Image]) -> None:
        self.design = design
        self._render_current()

    def _on_mockup_changed(self, name: str) -> None:
        self._render_current()

    def _render_current(self) -> None:
        if not self.profile or not self.design or not self.mockup_combo.currentText():
            self.preview_label.setText("Select a product, design, and mockup view.")
            self.preview_label.setPixmap(QPixmap())
            return
        try:
            image, path = self.generator.render_mockup(self.design, self.profile, self.mockup_combo.currentText())
            self.preview_label.setText(f"Rendered: {path}")
            qimage = self._pil_to_qimage(image)
            self.preview_label.setPixmap(QPixmap.fromImage(qimage).scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
        except Exception as exc:
            QMessageBox.critical(self, "Mockup error", str(exc))
            self.preview_label.setText("Mockup render failed.")

    def _export(self) -> None:
        if not self.profile or not self.design or not self.mockup_combo.currentText():
            QMessageBox.warning(self, "No mockup", "Render a mockup first.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Choose export folder")
        if not folder:
            return
        try:
            _, path = self.generator.render_mockup(
                self.design, self.profile, self.mockup_combo.currentText(),
                output_path=str(Path(folder) / f"mockup_{self.profile.id}_{self.mockup_combo.currentText()}.png"),
            )
            self.mockup_exported.emit(path)
        except Exception as exc:
            QMessageBox.critical(self, "Export error", str(exc))

    @staticmethod
    def _pil_to_qimage(image: Image.Image) -> QImage:
        image = image.convert("RGBA")
        return QImage(image.tobytes(), image.width, image.height, QImage.Format.Format_RGBA8888)
