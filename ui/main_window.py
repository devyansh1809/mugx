"""
ui/main_window.py

The main application window. Responsibilities are deliberately limited to:
  - laying out widgets
  - handling button clicks / dialogs
  - calling into core/ services and updating widgets with the results

No image processing, PSD parsing, or file scanning logic lives here —
that all belongs in core/. This keeps the window testable-by-inspection
and easy to extend as more panels are added later.
"""

import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QFileDialog, QMessageBox, QSplitter, QFrame,
    QCheckBox,
)
from PyQt6.QtCore import Qt

from core.models import ProductType, PhotoItem, TemplateInfo
from core.photo_import_service import PhotoImportService
from core.template_manager import TemplateManager
from core.image_processor import ImageEnhancementService

from ui.photo_list_widget import PhotoListWidget
from ui.template_preview_widget import TemplatePreviewWidget

logger = logging.getLogger("SubliStudio.MainWindow")

APP_DATA_DIR = Path.home() / ".subli_studio"
THUMB_CACHE_DIR = APP_DATA_DIR / "thumbnails"
ENHANCE_CACHE_DIR = APP_DATA_DIR / "enhanced_thumbnails"
PREVIEW_CACHE_DIR = APP_DATA_DIR / "template_previews"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SubliStudio")
        self.resize(1100, 700)

        # ── Services (core layer) ──
        self.photo_import_service = PhotoImportService(str(THUMB_CACHE_DIR))
        self.template_manager = TemplateManager(str(PREVIEW_CACHE_DIR))
        self.image_enhancement_service = ImageEnhancementService(str(ENHANCE_CACHE_DIR))

        # ── State ──
        self.loaded_photos: list[PhotoItem] = []
        self.current_template: TemplateInfo | None = None

        self._build_ui()

    # ─────────────────────────────────────────────────────────────
    #  UI construction
    # ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        root_layout.addWidget(self._build_toolbar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root_layout.addWidget(splitter, stretch=1)

        root_layout.addWidget(self._build_bottom_bar())

        self.status_label = QLabel("Ready.")
        self.statusBar().addWidget(self.status_label)

    def _build_toolbar(self) -> QWidget:
        bar = QFrame()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)

        self.load_photos_btn = QPushButton("📁  Load Photos")
        self.load_photos_btn.clicked.connect(self._on_load_photos_clicked)
        layout.addWidget(self.load_photos_btn)

        layout.addSpacing(20)

        layout.addWidget(QLabel("Product Type:"))
        self.product_dropdown = QComboBox()
        for pt in ProductType:
            self.product_dropdown.addItem(pt.value, userData=pt)
        layout.addWidget(self.product_dropdown)

        layout.addSpacing(20)

        self.load_template_btn = QPushButton("🖼  Load Template")
        self.load_template_btn.clicked.connect(self._on_load_template_clicked)
        layout.addWidget(self.load_template_btn)

        layout.addSpacing(20)

        self.auto_enhance_checkbox = QCheckBox("✨ Auto Enhance")
        self.auto_enhance_checkbox.setToolTip(
            "Applies mild color correction, smoothing, and sharpening to\n"
            "photo thumbnails (contrast, saturation, noise reduction)."
        )
        self.auto_enhance_checkbox.toggled.connect(self._on_auto_enhance_toggled)
        layout.addWidget(self.auto_enhance_checkbox)

        layout.addStretch(1)
        return bar

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        layout.addWidget(QLabel("Customer Photos"))
        self.photo_list = PhotoListWidget()
        layout.addWidget(self.photo_list, stretch=1)

        self.photo_count_label = QLabel("0 photos loaded")
        self.photo_count_label.setStyleSheet("color: #888;")
        layout.addWidget(self.photo_count_label)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        layout.addWidget(QLabel("Template Preview"))
        self.template_preview = TemplatePreviewWidget()
        layout.addWidget(self.template_preview, stretch=1)

        self.template_info_label = QLabel("No template loaded.")
        self.template_info_label.setStyleSheet("color: #888;")
        layout.addWidget(self.template_info_label)

        return panel

    def _build_bottom_bar(self) -> QWidget:
        bar = QFrame()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)

        self.prepare_print_btn = QPushButton("🖨  Prepare for Print")
        self.prepare_print_btn.setEnabled(False)  # wired up in a later milestone
        self.prepare_print_btn.setMinimumHeight(36)
        self.prepare_print_btn.clicked.connect(self._on_prepare_print_clicked)
        layout.addWidget(self.prepare_print_btn)

        return bar

    # ─────────────────────────────────────────────────────────────
    #  Event handlers
    # ─────────────────────────────────────────────────────────────

    def _on_load_photos_clicked(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Customer Photos Folder"
        )
        if not folder:
            return

        photos = self.photo_import_service.scan_folder(folder)
        if not photos:
            QMessageBox.warning(
                self, "No Photos Found",
                f"No supported image files were found in:\n{folder}"
            )
            return

        self.loaded_photos = photos
        self._render_photo_thumbnails()
        self.photo_count_label.setText(
            f"{len(photos)} photo(s) loaded — named 01…{photos[-1].sequence_name}"
        )
        self.status_label.setText(f"Loaded {len(photos)} photo(s) from {folder}")

    def _on_auto_enhance_toggled(self, checked: bool):
        if not self.loaded_photos:
            return  # nothing loaded yet — just remember the checkbox state
        self.status_label.setText(
            "Enhancing photos…" if checked else "Reverting to originals…"
        )
        self._render_photo_thumbnails()
        self.status_label.setText(
            f"Auto Enhance {'on' if checked else 'off'} — "
            f"{len(self.loaded_photos)} photo(s)."
        )

    def _render_photo_thumbnails(self):
        """
        Build the thumbnail dict for self.loaded_photos using either the
        plain PhotoImportService thumbnails or the enhanced+cached ones,
        depending on the current "Auto Enhance" checkbox state, and push
        the result into the photo list widget.
        """
        use_enhanced = self.auto_enhance_checkbox.isChecked()
        service = self.image_enhancement_service if use_enhanced else self.photo_import_service

        thumbnail_paths = {}
        for photo in self.loaded_photos:
            thumb = service.get_thumbnail(photo)
            if thumb:
                thumbnail_paths[photo.original_path] = thumb

        self.photo_list.set_photos(self.loaded_photos, thumbnail_paths)

    def _on_load_template_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Product Template",
            "",
            "Templates (*.psd *.psb *.png *.jpg *.jpeg *.tiff);;All Files (*)",
        )
        if not file_path:
            return

        product_type = self.product_dropdown.currentData()

        self.status_label.setText(f"Loading template: {Path(file_path).name} …")
        info, preview_path = self.template_manager.load_template(file_path, product_type)

        if info is None or preview_path is None:
            QMessageBox.critical(
                self, "Template Load Failed",
                f"Could not load template file:\n{file_path}\n\n"
                "Check the log for details, or try a different file."
            )
            self.status_label.setText("Template load failed.")
            return

        self.current_template = info
        self.template_preview.set_preview(preview_path)
        self.template_info_label.setText(
            f"{info.display_name}  —  {info.width}×{info.height}px  "
            f"({'PSD' if info.is_psd else 'Image'})  —  {info.product_type.value}"
        )
        self.status_label.setText(f"Template loaded: {info.display_name}")

    def _on_prepare_print_clicked(self):
        # Disabled for now — compositing/print-export pipeline lands in a later milestone.
        pass
