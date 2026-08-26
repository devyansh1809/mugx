"""
ui/main_window.py

The main application window. Lays out widgets, wires signals, and
calls into core/ services -- never the reverse.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PIL import Image

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QFileDialog, QMessageBox, QSplitter, QFrame,
    QCheckBox, QSpinBox,
)
from PyQt6.QtCore import Qt

from core.models import ProductType, PhotoItem, TemplateInfo
from core.photo_import_service import PhotoImportService
from core.template_manager import TemplateManager
from core.image_processor import ImageEnhancementService
from core.print_exporter import PrintExporter, PrintSettings
from core.mockup_generator import MockupGenerator

from ui.photo_list_widget import PhotoListWidget
from ui.template_preview_widget import TemplatePreviewWidget
from ui.print_settings_dialog import PrintSettingsDialog
from ui.text_tool_dialog import TextToolDialog
from ui.mockup_preview_dialog import MockupPreviewDialog

logger = logging.getLogger("SubliStudio.MainWindow")

APP_DATA_DIR = Path.home() / ".subli_studio"
THUMB_CACHE_DIR = APP_DATA_DIR / "thumbnails"
ENHANCE_CACHE_DIR = APP_DATA_DIR / "enhanced_thumbnails"
PREVIEW_CACHE_DIR = APP_DATA_DIR / "template_previews"
MOCKUP_CACHE_DIR = APP_DATA_DIR / "mockups"
DESIGN_OUTPUT_DIR = APP_DATA_DIR / "designs"

BUILTIN_EFFECTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "effects"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SubliStudio")
        self.resize(1200, 760)

        self.photo_import_service = PhotoImportService(str(THUMB_CACHE_DIR))
        self.template_manager = TemplateManager(str(PREVIEW_CACHE_DIR))
        self.image_enhancement_service = ImageEnhancementService(str(ENHANCE_CACHE_DIR))
        self.print_exporter = PrintExporter()
        self.mockup_generator = MockupGenerator(str(MOCKUP_CACHE_DIR))

        self.loaded_photos: list[PhotoItem] = []
        self.current_template: Optional[TemplateInfo] = None
        self.base_template_canvas: Optional[Image.Image] = None
        self.current_design_canvas: Optional[Image.Image] = None
        self._pending_swap_frame_index: Optional[int] = None

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        root_layout.addWidget(self._build_toolbar())
        root_layout.addWidget(self._build_template_toolbar())

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

        self.load_photos_btn = QPushButton("\U0001F4C1 Load Photos")
        self.load_photos_btn.clicked.connect(self._on_load_photos_clicked)
        layout.addWidget(self.load_photos_btn)

        layout.addSpacing(20)

        layout.addWidget(QLabel("Product Type:"))
        self.product_dropdown = QComboBox()
        for pt in ProductType:
            self.product_dropdown.addItem(pt.value, userData=pt)
        layout.addWidget(self.product_dropdown)

        layout.addSpacing(20)

        self.load_template_btn = QPushButton("\U0001F5BC Load Template")
        self.load_template_btn.clicked.connect(self._on_load_template_clicked)
        layout.addWidget(self.load_template_btn)

        layout.addSpacing(20)

        self.auto_enhance_checkbox = QCheckBox("\u2728 Auto Enhance")
        self.auto_enhance_checkbox.setToolTip(
            "Applies mild color correction, smoothing, and sharpening to\n"
            "photo thumbnails (contrast, saturation, noise reduction)."
        )
        self.auto_enhance_checkbox.toggled.connect(self._on_auto_enhance_toggled)
        layout.addWidget(self.auto_enhance_checkbox)

        layout.addStretch(1)
        return bar

    def _build_template_toolbar(self) -> QWidget:
        bar = QFrame()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Photos to use:"))
        self.photo_count_spin = QSpinBox()
        self.photo_count_spin.setRange(1, 1)
        layout.addWidget(self.photo_count_spin)

        self.show_frames_checkbox = QCheckBox("Show frame overlays")
        self.show_frames_checkbox.toggled.connect(self._on_show_frames_toggled)
        layout.addWidget(self.show_frames_checkbox)

        self.auto_fill_btn = QPushButton("\U0001F9E9 Auto Fill")
        self.auto_fill_btn.clicked.connect(self._on_auto_fill_clicked)
        self.auto_fill_btn.setEnabled(False)
        layout.addWidget(self.auto_fill_btn)

        layout.addSpacing(10)

        self.change_background_btn = QPushButton("\U0001F3D4 Change Background")
        self.change_background_btn.clicked.connect(self._on_change_background_clicked)
        self.change_background_btn.setEnabled(False)
        layout.addWidget(self.change_background_btn)

        layout.addWidget(QLabel("Effect:"))
        self.effects_dropdown = QComboBox()
        self.effects_dropdown.addItem("(none)", userData=None)
        self._populate_effects_dropdown()
        layout.addWidget(self.effects_dropdown)

        self.apply_effect_btn = QPushButton("Apply Effect")
        self.apply_effect_btn.clicked.connect(self._on_apply_effect_clicked)
        self.apply_effect_btn.setEnabled(False)
        layout.addWidget(self.apply_effect_btn)

        self.add_text_btn = QPushButton("\U0001F524 Add Text")
        self.add_text_btn.clicked.connect(self._on_add_text_clicked)
        self.add_text_btn.setEnabled(False)
        layout.addWidget(self.add_text_btn)

        self.mockup_preview_btn = QPushButton("\U0001F9F6 3D Preview")
        self.mockup_preview_btn.clicked.connect(self._on_mockup_preview_clicked)
        self.mockup_preview_btn.setEnabled(False)
        layout.addWidget(self.mockup_preview_btn)

        layout.addStretch(1)
        return bar

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        layout.addWidget(QLabel("Customer Photos (double-click to swap into selected frame)"))
        self.photo_list = PhotoListWidget()
        self.photo_list.photo_double_clicked.connect(self._on_photo_double_clicked)
        layout.addWidget(self.photo_list, stretch=1)

        self.photo_count_label = QLabel("0 photos loaded")
        self.photo_count_label.setStyleSheet("color: #888;")
        layout.addWidget(self.photo_count_label)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        layout.addWidget(QLabel("Template / Design Preview (click a frame, then double-click a photo, to swap)"))
        self.template_preview = TemplatePreviewWidget()
        self.template_preview.frame_clicked.connect(self._on_frame_clicked)
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

        self.prepare_print_btn = QPushButton("\U0001F5A8 Prepare for Print")
        self.prepare_print_btn.setEnabled(False)
        self.prepare_print_btn.setMinimumHeight(36)
        self.prepare_print_btn.clicked.connect(self._on_prepare_print_clicked)
        layout.addWidget(self.prepare_print_btn)

        return bar

    def _populate_effects_dropdown(self):
        if BUILTIN_EFFECTS_DIR.exists():
            for path in sorted(BUILTIN_EFFECTS_DIR.glob("*.png")):
                self.effects_dropdown.addItem(path.stem.replace("_", " ").title(), userData=str(path))

    def _on_load_photos_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Customer Photos Folder")
        if not folder:
            return

        photos = self.photo_import_service.scan_folder(folder)
        if not photos:
            QMessageBox.warning(self, "No Photos Found", f"No supported image files were found in:\n{folder}")
            return

        self.loaded_photos = photos
        self._render_photo_thumbnails()
        self.photo_count_label.setText(f"{len(photos)} photo(s) loaded -- named 01...{photos[-1].sequence_name}")
        self.status_label.setText(f"Loaded {len(photos)} photo(s) from {folder}")

        max_photos = max(1, len(photos))
        if self.current_template:
            max_photos = min(max_photos, max(1, self.current_template.frame_count))
        self.photo_count_spin.setRange(1, max_photos)
        self.photo_count_spin.setValue(max_photos)
        self._update_auto_fill_enabled()

    def _on_auto_enhance_toggled(self, checked: bool):
        if not self.loaded_photos:
            return
        self.status_label.setText("Enhancing photos..." if checked else "Reverting to originals...")
        self._render_photo_thumbnails()
        self.status_label.setText(f"Auto Enhance {'on' if checked else 'off'} -- {len(self.loaded_photos)} photo(s).")

    def _render_photo_thumbnails(self):
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
            self, "Select Product Template", "",
            "Templates (*.psd *.psb *.png *.jpg *.jpeg *.tiff);;All Files (*)",
        )
        if not file_path:
            return

        product_type = self.product_dropdown.currentData()

        self.status_label.setText(f"Loading template: {Path(file_path).name} ...")
        info, preview_path = self.template_manager.load_template(file_path, product_type)

        if info is None or preview_path is None:
            QMessageBox.critical(
                self, "Template Load Failed",
                f"Could not load template file:\n{file_path}\n\nCheck the log for details, or try a different file."
            )
            self.status_label.setText("Template load failed.")
            return

        self.current_template = info
        self.base_template_canvas = Image.open(preview_path).convert("RGBA")
        self.current_design_canvas = None

        self._refresh_template_preview()
        self.template_info_label.setText(
            f"{info.display_name} -- {info.width}x{info.height}px "
            f"({'PSD' if info.is_psd else 'Image'}) -- {info.product_type.value} -- "
            f"Detected {info.frame_count} frame(s)"
        )
        self.status_label.setText(f"Template loaded: {info.display_name}")

        max_photos = max(1, info.frame_count)
        if self.loaded_photos:
            max_photos = min(max_photos, len(self.loaded_photos))
        self.photo_count_spin.setRange(1, max(1, info.frame_count))
        self.photo_count_spin.setValue(max_photos)
        self._update_auto_fill_enabled()

    def _on_show_frames_toggled(self, checked: bool):
        self.template_preview.set_show_frames(checked)

    def _refresh_template_preview(self):
        canvas = self.current_design_canvas or self.base_template_canvas
        if canvas is None or self.current_template is None:
            return
        tmp_path = str(PREVIEW_CACHE_DIR / "_live_preview.png")
        Path(PREVIEW_CACHE_DIR).mkdir(parents=True, exist_ok=True)
        canvas.convert("RGB").save(tmp_path, "PNG")
        self.template_preview.set_preview(
            tmp_path, frames=self.current_template.frames,
            source_size=(self.current_template.width, self.current_template.height),
        )

    def _update_auto_fill_enabled(self):
        can_fill = bool(self.loaded_photos) and self.current_template is not None
        self.auto_fill_btn.setEnabled(can_fill)

    def _on_auto_fill_clicked(self):
        if not self.current_template or not self.loaded_photos or self.base_template_canvas is None:
            return
        n = self.photo_count_spin.value()
        photos_to_use = self.loaded_photos[:n]
        try:
            self.current_design_canvas = self.template_manager.fill_frames(
                self.current_template, self.base_template_canvas, photos_to_use,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Auto Fill Failed", str(exc))
            return

        self._refresh_template_preview()
        self._enable_design_editing_controls(True)
        self.status_label.setText(f"Auto-filled {min(n, self.current_template.frame_count)} frame(s).")

    def _on_frame_clicked(self, frame_index: int):
        self._pending_swap_frame_index = frame_index
        self.status_label.setText(f"Frame {frame_index + 1} selected -- double-click a photo in the list to swap it in.")

    def _on_photo_double_clicked(self, photo_index: int):
        if self._pending_swap_frame_index is None:
            self.status_label.setText("Click a frame in the preview first, then double-click a photo to swap it in.")
            return
        if not self.current_template or self.current_design_canvas is None:
            return

        try:
            self.current_design_canvas = self.template_manager.swap_photo(
                self.current_template, self.base_template_canvas, self.loaded_photos,
                frame_index=self._pending_swap_frame_index, new_photo_index=photo_index,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Swap Failed", str(exc))
            return

        self._refresh_template_preview()
        self.status_label.setText(f"Swapped photo into frame {self._pending_swap_frame_index + 1}.")
        self._pending_swap_frame_index = None

    def _enable_design_editing_controls(self, enabled: bool):
        self.change_background_btn.setEnabled(enabled)
        self.apply_effect_btn.setEnabled(enabled)
        self.add_text_btn.setEnabled(enabled)
        self.mockup_preview_btn.setEnabled(enabled)
        self.prepare_print_btn.setEnabled(enabled)

    def _on_change_background_clicked(self):
        if self.current_design_canvas is None:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Background Image", "", "Images (*.png *.jpg *.jpeg);;All Files (*)"
        )
        if not file_path:
            return
        self.current_design_canvas = self.template_manager.change_background(self.current_design_canvas, file_path)
        self._refresh_template_preview()
        self.status_label.setText(f"Background changed to {Path(file_path).name}.")

    def _on_apply_effect_clicked(self):
        if self.current_design_canvas is None:
            return
        overlay_path = self.effects_dropdown.currentData()
        if not overlay_path:
            self.status_label.setText("Select an effect from the dropdown first.")
            return
        self.current_design_canvas = self.template_manager.add_overlay(self.current_design_canvas, overlay_path)
        self._refresh_template_preview()
        self.status_label.setText(f"Applied effect: {self.effects_dropdown.currentText()}.")

    def _on_add_text_clicked(self):
        if self.current_design_canvas is None:
            return
        dialog = TextToolDialog(self)
        if dialog.exec():
            values = dialog.get_values()
            if not values["text"]:
                return
            w, h = self.current_design_canvas.size
            position = (round(values["pos_x_ratio"] * w), round(values["pos_y_ratio"] * h))
            self.current_design_canvas = self.template_manager.add_text(
                self.current_design_canvas, values["text"], position,
                font_size=values["font_size"], color=values["color"],
            )
            self._refresh_template_preview()
            text_value = values['text']
            self.status_label.setText(f'Added text: "{text_value}"')

    def _on_mockup_preview_clicked(self):
        if self.current_design_canvas is None:
            return
        mockup = self.mockup_generator.render_cylinder_mockup(self.current_design_canvas)
        MOCKUP_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        out_path = str(MOCKUP_CACHE_DIR / "_live_mockup.png")
        mockup.save(out_path, "PNG")
        dialog = MockupPreviewDialog(out_path, self)
        dialog.exec()

    def _on_prepare_print_clicked(self):
        if self.current_design_canvas is None:
            return

        dialog = PrintSettingsDialog(self, initial=self.print_exporter.settings)
        if not dialog.exec():
            return
        settings: PrintSettings = dialog.get_settings()
        self.print_exporter.settings = settings

        output_dir = QFileDialog.getExistingDirectory(self, "Choose Output Folder")
        if not output_dir:
            return

        base_name = Path(self.current_template.source_path).stem if self.current_template else "design"
        try:
            outputs = self.print_exporter.export(
                self.current_design_canvas, output_dir, base_name, formats=("png", "pdf"),
            )
        except Exception as exc:
            logger.exception("Print export failed")
            QMessageBox.critical(self, "Export Failed", str(exc))
            return

        self.status_label.setText(f"Exported print-ready file(s): {', '.join(outputs)}")
        QMessageBox.information(self, "Prepare for Print", "Print-ready file(s) created:\n" + "\n".join(outputs))
