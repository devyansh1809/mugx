"""
ui/main_window.py (v2.2)

Fix: a single SessionState object is created once in MainWindow and
passed into every panel. All panels read/write the SAME
loaded_photos / current_template / base_canvas / design_canvas. Every
button now has a real .clicked.connect(). All three dialogs are now
actually instantiated and used. Manual text goes through
TextToolDialog, which has a real QLineEdit.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, List

from PIL import Image

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QComboBox, QLabel, QFileDialog, QMessageBox, QCheckBox, QSpinBox,
    QTabWidget, QDoubleSpinBox, QGroupBox, QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.models import ProductType, PhotoItem, TemplateInfo, TemplateTheme, DesignJob
from core.photo_import_service import PhotoImportService
from core.template_manager import TemplateManager
from core.image_processor import ImageEnhancementService
from core.print_exporter import PrintExporter, PrintSettings
from core.mockup_generator import MockupGenerator

from ui.template_preview_widget import TemplatePreviewWidget
from ui.print_settings_dialog import PrintSettingsDialog
from ui.text_tool_dialog import TextToolDialog
from ui.mockup_preview_dialog import MockupPreviewDialog

logger = logging.getLogger("SubliStudio.MainWindow")

APP_DATA_DIR = Path.home() / ".subli_studio"
THUMB_CACHE_DIR = APP_DATA_DIR / "thumbnails"
PREVIEW_CACHE_DIR = APP_DATA_DIR / "template_previews"
MOCKUP_CACHE_DIR = APP_DATA_DIR / "mockups"
AUTO_SAVE_DIR = APP_DATA_DIR / "manual_psd"
BUILTIN_EFFECTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "effects"


class SessionState:
    def __init__(self):
        self.photo_service = PhotoImportService(str(THUMB_CACHE_DIR))
        self.template_manager = TemplateManager(str(PREVIEW_CACHE_DIR))
        self.image_enhancement_service = ImageEnhancementService(str(THUMB_CACHE_DIR))
        self.print_exporter = PrintExporter()
        self.mockup_generator = MockupGenerator(str(MOCKUP_CACHE_DIR))
        self.loaded_photos: List[PhotoItem] = []
        self.current_template: Optional[TemplateInfo] = None
        self.base_canvas: Optional[Image.Image] = None
        self.design_canvas: Optional[Image.Image] = None
        self._pending_bg_path: Optional[str] = None

    def working_canvas(self) -> Optional[Image.Image]:
        return self.design_canvas if self.design_canvas is not None else self.base_canvas

    def auto_save(self):
        if not self.current_template:
            return
        job = DesignJob(template=self.current_template, photos=self.loaded_photos)
        try:
            job.auto_save(str(AUTO_SAVE_DIR))
        except Exception:
            logger.exception("Auto-save failed")


class DesignPanel(QWidget):
    templateLoaded = pyqtSignal()

    def __init__(self, session: SessionState, on_change, parent=None):
        super().__init__(parent)
        self.session = session
        self.on_change = on_change
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        photo_group = QGroupBox("Photos")
        photo_layout = QHBoxLayout(photo_group)
        self.load_photos_btn = QPushButton("\U0001F4C1 Load Photos")
        self.load_photos_btn.clicked.connect(self._on_load_photos)
        photo_layout.addWidget(self.load_photos_btn)
        self.auto_enhance_checkbox = QCheckBox("\u2728 Auto Enhance")
        photo_layout.addWidget(self.auto_enhance_checkbox)
        photo_layout.addStretch()
        self.photo_count_label = QLabel("0 photos loaded")
        photo_layout.addWidget(self.photo_count_label)
        layout.addWidget(photo_group)

        tmpl_group = QGroupBox("Template")
        tmpl_layout = QGridLayout(tmpl_group)
        self.load_template_btn = QPushButton("\U0001F5BC Load Template")
        self.load_template_btn.clicked.connect(self._on_load_template)
        tmpl_layout.addWidget(self.load_template_btn, 0, 0)
        tmpl_layout.addWidget(QLabel("Product:"), 0, 1)
        self.product_filter = QComboBox()
        for pt in ProductType:
            self.product_filter.addItem(pt.value, userData=pt)
        tmpl_layout.addWidget(self.product_filter, 0, 2)
        layout.addWidget(tmpl_group)

        fill_group = QGroupBox("Auto Fill")
        fill_layout = QHBoxLayout(fill_group)
        fill_layout.addWidget(QLabel("Use photos:"))
        self.photo_count_spin = QSpinBox()
        self.photo_count_spin.setRange(1, 1)
        fill_layout.addWidget(self.photo_count_spin)
        self.auto_fill_btn = QPushButton("\U0001F9E9 Auto Fill")
        self.auto_fill_btn.clicked.connect(self._on_auto_fill)
        self.auto_fill_btn.setEnabled(False)
        fill_layout.addWidget(self.auto_fill_btn)
        layout.addWidget(fill_group)

        self.preview = TemplatePreviewWidget()
        self.preview.setMinimumHeight(300)
        layout.addWidget(self.preview, stretch=1)
        self.status_label = QLabel("Ready.")
        layout.addWidget(self.status_label)

    def _on_load_photos(self):
        last_folder = self.session.photo_service.get_last_folder()
        folder = QFileDialog.getExistingDirectory(self, "Select Customer Photos Folder", last_folder or "")
        if not folder:
            return
        self.session.photo_service.save_last_folder(folder)
        photos = self.session.photo_service.scan_folder(folder)
        if not photos:
            QMessageBox.warning(self, "No Photos Found", f"No supported images in:\n{folder}")
            return
        self.session.loaded_photos = photos
        self.photo_count_label.setText(f"{len(photos)} photos")
        self._update_auto_fill_enabled()
        self.on_change()

    def _on_load_template(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Product Template", "",
            "Templates (*.psd *.psb *.png *.jpg *.jpeg *.tiff);;All Files (*)",
        )
        if not file_path:
            return
        product_type = self.product_filter.currentData() or ProductType.MUG
        theme = self.theme_filter.currentData() or TemplateTheme.PLAIN
        info, preview_path = self.session.template_manager.load_template(file_path, product_type, theme)
        if not info or not preview_path:
            QMessageBox.critical(self, "Template Load Failed", f"Could not load:\n{file_path}")
            return
        self.session.current_template = info
        self.session.base_canvas = Image.open(preview_path).convert("RGBA")
        self.session.design_canvas = None
        self.preview.set_preview(preview_path, frames=info.frames, source_size=(info.width, info.height))
        self._update_auto_fill_enabled()
        self.templateLoaded.emit()
        self.on_change()

    def _update_auto_fill_enabled(self):
        can_fill = bool(self.session.loaded_photos) and self.session.current_template is not None
        self.auto_fill_btn.setEnabled(can_fill)
        if can_fill:
            max_photos = min(len(self.session.loaded_photos), self.session.current_template.frame_count)
            self.photo_count_spin.setRange(1, max(1, max_photos))
            self.photo_count_spin.setValue(max_photos)

    def _on_auto_fill(self):
        s = self.session
        if not s.current_template or not s.loaded_photos or s.base_canvas is None:
            return
        n = self.photo_count_spin.value()
        photos_to_use = s.loaded_photos[:n]
        try:
            s.design_canvas = s.template_manager.fill_frames(s.current_template, s.base_canvas, photos_to_use)
        except ValueError as exc:
            QMessageBox.warning(self, "Auto Fill Failed", str(exc))
            return
        s.auto_save()
        self.on_change()

    def refresh_preview(self):
        s = self.session
        canvas = s.working_canvas()
        if canvas is None or s.current_template is None:
            self.preview.show_empty_state()
            return
        tmp_path = str(PREVIEW_CACHE_DIR / "_live_preview.png")
        Path(PREVIEW_CACHE_DIR).mkdir(parents=True, exist_ok=True)
        canvas.convert("RGB").save(tmp_path, "PNG")
        self.preview.set_preview(tmp_path, frames=s.current_template.frames,
                                  source_size=(s.current_template.width, s.current_template.height))


class ManualEditPanel(QWidget):
    def __init__(self, session: SessionState, on_change, parent=None):
        super().__init__(parent)
        self.session = session
        self.on_change = on_change
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        resize_group = QGroupBox("Resize Photo in Frame")
        resize_layout = QGridLayout(resize_group)
        resize_layout.addWidget(QLabel("Frame #:"), 0, 0)
        self.resize_frame_spin = QSpinBox()
        self.resize_frame_spin.setRange(1, 1)
        resize_layout.addWidget(self.resize_frame_spin, 0, 1)
        resize_layout.addWidget(QLabel("Scale:"), 0, 2)
        self.resize_scale_spin = QDoubleSpinBox()
        self.resize_scale_spin.setRange(0.5, 2.0)
        self.resize_scale_spin.setValue(1.0)
        resize_layout.addWidget(self.resize_scale_spin, 0, 3)
        self.apply_resize_btn = QPushButton("Apply Resize")
        self.apply_resize_btn.clicked.connect(self._on_apply_resize)
        resize_layout.addWidget(self.apply_resize_btn, 2, 0, 1, 4)
        layout.addWidget(resize_group)

        swap_group = QGroupBox("Swap Photos")
        swap_layout = QHBoxLayout(swap_group)
        swap_layout.addWidget(QLabel("Frame 1:"))
        self.swap_frame1 = QSpinBox()
        self.swap_frame1.setRange(1, 1)
        swap_layout.addWidget(self.swap_frame1)
        swap_layout.addWidget(QLabel("Frame 2:"))
        self.swap_frame2 = QSpinBox()
        self.swap_frame2.setRange(1, 1)
        swap_layout.addWidget(self.swap_frame2)
        self.swap_btn = QPushButton("\U0001F504 Swap")
        self.swap_btn.clicked.connect(self._on_swap)
        swap_layout.addWidget(self.swap_btn)
        layout.addWidget(swap_group)

        bg_group = QGroupBox("Change Background")
        bg_layout = QHBoxLayout(bg_group)
        self.choose_bg_btn = QPushButton("\U0001F5BC Choose Background...")
        self.choose_bg_btn.clicked.connect(self._on_choose_background)
        bg_layout.addWidget(self.choose_bg_btn)
        self.commit_bg_btn = QPushButton("Commit Background")
        self.commit_bg_btn.clicked.connect(self._on_commit_background)
        bg_layout.addWidget(self.commit_bg_btn)
        layout.addWidget(bg_group)

        effects_group = QGroupBox("Box/Light Effects")
        effects_layout = QHBoxLayout(effects_group)
        self.effects_dropdown = QComboBox()
        self.effects_dropdown.addItem("(none)", userData=None)
        effects_layout.addWidget(self.effects_dropdown)
        self.apply_effect_btn = QPushButton("Apply Effect")
        self.apply_effect_btn.clicked.connect(self._on_apply_effect)
        effects_layout.addWidget(self.apply_effect_btn)
        layout.addWidget(effects_group)

        layout.addStretch()
        self.status_label = QLabel("Manual Edit Panel Ready.")
        layout.addWidget(self.status_label)

    def update_frame_ranges(self):
        s = self.session
        n = s.current_template.frame_count if s.current_template else 1
        for spin in (self.resize_frame_spin, self.swap_frame1, self.swap_frame2):
            spin.setRange(1, max(1, n))

    def _require_design(self) -> bool:
        s = self.session
        if not s.current_template or s.working_canvas() is None:
            QMessageBox.warning(self, "No Design", "Load a template and run Auto Fill first.")
            return False
        return True

    def _on_apply_resize(self):
        if not self._require_design():
            return
        s = self.session
        frame_idx = self.resize_frame_spin.value() - 1
        try:
            s.design_canvas = s.template_manager.resize_photo_in_frame(
                s.current_template, s.base_canvas, s.loaded_photos, frame_idx,
                self.resize_scale_spin.value(), 0, 0,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Resize Failed", str(exc))
            return
        s.auto_save()
        self.on_change()

    def _on_swap(self):
        if not self._require_design():
            return
        s = self.session
        idx1, idx2 = self.swap_frame1.value() - 1, self.swap_frame2.value() - 1
        try:
            s.design_canvas = s.template_manager.swap_photos(s.current_template, s.base_canvas, s.loaded_photos, idx1, idx2)
        except ValueError as exc:
            QMessageBox.warning(self, "Swap Failed", str(exc))
            return
        s.auto_save()
        self.on_change()

    def _on_choose_background(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Background Image", "", "Images (*.png *.jpg *.jpeg)")
        if not file_path:
            return
        self.session._pending_bg_path = file_path

    def _on_commit_background(self):
        if not self._require_design():
            return
        if not self.session._pending_bg_path:
            QMessageBox.warning(self, "No Background Chosen", "Click 'Choose Background...' first.")
            return
        s = self.session
        s.design_canvas = s.template_manager.change_background_with_preview(
            s.working_canvas(), s._pending_bg_path, blur_amount=0
        )
        s.auto_save()
        self.on_change()

    def _on_apply_effect(self):
        if not self._require_design():
            return
        overlay_path = self.effects_dropdown.currentData()
        if not overlay_path:
            self.status_label.setText("Select an effect from the dropdown first.")
            return
        s = self.session
        s.design_canvas = s.template_manager.add_overlay(s.working_canvas(), overlay_path)
        s.auto_save()
        self.on_change()


class TextPanel(QWidget):
    def __init__(self, session: SessionState, on_change, parent=None):
        super().__init__(parent)
        self.session = session
        self.on_change = on_change
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        ready_group = QGroupBox("Readymade Text")
        ready_layout = QGridLayout(ready_group)
        self.readymade_dropdown = QComboBox()
        for p in ["Happy Birthday", "Congratulations", "Love You", "Happy Diwali", "Happy Holi", "Happy New Year"]:
            self.readymade_dropdown.addItem(p)
        ready_layout.addWidget(self.readymade_dropdown, 0, 0)
        self.add_readymade_btn = QPushButton("Add Readymade Text")
        self.add_readymade_btn.clicked.connect(self._on_add_readymade)
        ready_layout.addWidget(self.add_readymade_btn, 1, 0)
        layout.addWidget(ready_group)

        manual_group = QGroupBox("Manual Text")
        manual_layout = QVBoxLayout(manual_group)
        self.add_manual_btn = QPushButton("Add Manual Text...")
        self.add_manual_btn.clicked.connect(self._on_add_manual_text)
        manual_layout.addWidget(self.add_manual_btn)
        layout.addWidget(manual_group)

        text3d_group = QGroupBox("3D Text Generator")
        text3d_layout = QGridLayout(text3d_group)
        text3d_layout.addWidget(QLabel("Text:"), 0, 0)
        self.text3d_edit = QLineEdit()
        text3d_layout.addWidget(self.text3d_edit, 0, 1)
        self.generate_3d_btn = QPushButton("Generate 3D Text")
        self.generate_3d_btn.clicked.connect(self._on_generate_3d_text)
        text3d_layout.addWidget(self.generate_3d_btn, 1, 0, 1, 2)
        layout.addWidget(text3d_group)

        layout.addStretch()
        self.status_label = QLabel("Text Panel Ready.")
        layout.addWidget(self.status_label)

    def _require_design(self) -> bool:
        s = self.session
        if not s.current_template or s.working_canvas() is None:
            QMessageBox.warning(self, "No Design", "Load a template and run Auto Fill first.")
            return False
        return True

    def _on_add_readymade(self):
        if not self._require_design():
            return
        s = self.session
        position = (50, 250)
        s.design_canvas = s.template_manager.add_readymade_text(
            s.working_canvas(), self.readymade_dropdown.currentText(), position
        )
        s.auto_save()
        self.on_change()

    def _on_add_manual_text(self):
        if not self._require_design():
            return
        dialog = TextToolDialog(self)
        if not dialog.exec():
            return
        values = dialog.get_values()
        if not values["text"]:
            return
        s = self.session
        w, h = s.working_canvas().size
        position = (round(values["pos_x_ratio"] * w), round(values["pos_y_ratio"] * h))
        s.design_canvas = s.template_manager.add_text(
            s.working_canvas(), values["text"], position,
            font_size=values["font_size"], color=values["color"],
        )
        s.auto_save()
        self.on_change()

    def _on_generate_3d_text(self):
        if not self._require_design():
            return
        text = self.text3d_edit.text().strip()
        if not text:
            QMessageBox.warning(self, "No Text", "Enter text for the 3D text generator first.")
            return
        s = self.session
        text_layer = s.template_manager.generate_3d_text_stub(text)
        canvas = s.working_canvas().convert("RGBA").copy()
        canvas.alpha_composite(text_layer, (50, 50))
        s.design_canvas = canvas
        s.auto_save()
        self.on_change()


class PrintPanel(QWidget):
    def __init__(self, session: SessionState, on_change, parent=None):
        super().__init__(parent)
        self.session = session
        self.on_change = on_change
        self._extra_design_path: Optional[str] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        mirror_group = QGroupBox("Mirror Settings (Mirror 1 = primary, Mirror 2 = extra design)")
        mirror_layout = QHBoxLayout(mirror_group)
        self.mirror1_checkbox = QCheckBox("Mirror 1")
        self.mirror1_checkbox.setChecked(True)
        mirror_layout.addWidget(self.mirror1_checkbox)
        self.mirror2_checkbox = QCheckBox("Mirror 2")
        mirror_layout.addWidget(self.mirror2_checkbox)
        layout.addWidget(mirror_group)

        extra_group = QGroupBox("Add Extra Design")
        extra_layout = QGridLayout(extra_group)
        self.choose_extra_btn = QPushButton("Choose Extra Design Image...")
        self.choose_extra_btn.clicked.connect(self._on_choose_extra_design)
        extra_layout.addWidget(self.choose_extra_btn, 0, 0, 1, 2)
        self.extra_path_label = QLabel("(none selected)")
        extra_layout.addWidget(self.extra_path_label, 1, 0, 1, 2)
        self.rotate_extra_checkbox = QCheckBox("Rotate 90 degrees")
        extra_layout.addWidget(self.rotate_extra_checkbox, 2, 0, 1, 2)
        layout.addWidget(extra_group)

        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)
        self.prepare_print_btn = QPushButton("\U0001F5A8 Prepare for Print")
        self.prepare_print_btn.clicked.connect(self._on_prepare_print)
        export_layout.addWidget(self.prepare_print_btn)
        layout.addWidget(export_group)

        layout.addStretch()
        self.status_label = QLabel("Print Panel Ready.")
        layout.addWidget(self.status_label)

    def _on_choose_extra_design(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Extra Design Image", "", "Images (*.png *.jpg *.jpeg)")
        if not file_path:
            return
        self._extra_design_path = file_path
        self.extra_path_label.setText(Path(file_path).name)

    def _on_prepare_print(self):
        s = self.session
        if s.working_canvas() is None:
            QMessageBox.warning(self, "No Design", "Load a template and run Auto Fill first.")
            return

        dialog = PrintSettingsDialog(self, initial=s.print_exporter.settings)
        if not dialog.exec():
            return
        s.print_exporter.settings = dialog.get_settings()

        output_dir = QFileDialog.getExistingDirectory(self, "Choose Output Folder")
        if not output_dir:
            return

        extra_design_img = None
        if self._extra_design_path:
            extra_design_img = Image.open(self._extra_design_path).convert("RGB")

        base_name = Path(s.current_template.source_path).stem if s.current_template else "design"
        try:
            outputs = s.print_exporter.export(
                s.working_canvas(), output_dir, base_name,
                mirror_1=self.mirror1_checkbox.isChecked(),
                mirror_2=self.mirror2_checkbox.isChecked(),
                extra_design=extra_design_img,
                extra_design_rotate=self.rotate_extra_checkbox.isChecked(),
                formats=("png", "pdf"),
            )
        except Exception as exc:
            logger.exception("Print export failed")
            QMessageBox.critical(self, "Export Failed", str(exc))
            return

        self.status_label.setText(f"Exported: {', '.join(outputs)}")
        QMessageBox.information(self, "Prepare for Print", "Print-ready file(s) created:\n" + "\n".join(outputs))


class MockupPanel(QWidget):
    def __init__(self, session: SessionState, on_change, parent=None):
        super().__init__(parent)
        self.session = session
        self.on_change = on_change
        self._last_mockup: Optional[Image.Image] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        variant_group = QGroupBox("3D Mockup Variant")
        variant_layout = QHBoxLayout(variant_group)
        self.variant_dropdown = QComboBox()
        for v in self.session.mockup_generator.mug_variants:
            self.variant_dropdown.addItem(v.name, userData=v)
        variant_layout.addWidget(self.variant_dropdown)
        layout.addWidget(variant_group)

        preview_group = QGroupBox("Preview")
        preview_layout = QHBoxLayout(preview_group)
        self.generate_mockup_btn = QPushButton("\U0001F9F6 Generate 3D Preview")
        self.generate_mockup_btn.clicked.connect(self._on_generate_mockup)
        preview_layout.addWidget(self.generate_mockup_btn)
        layout.addWidget(preview_group)

        export_group = QGroupBox("Export for WhatsApp/Email")
        export_layout = QHBoxLayout(export_group)
        self.export_jpg_btn = QPushButton("\U0001F4E4 Export JPG")
        self.export_jpg_btn.clicked.connect(self._on_export_jpg)
        export_layout.addWidget(self.export_jpg_btn)
        layout.addWidget(export_group)

        layout.addStretch()
        self.status_label = QLabel("Mockup Panel Ready.")
        layout.addWidget(self.status_label)

    def _on_generate_mockup(self):
        s = self.session
        if s.working_canvas() is None:
            QMessageBox.warning(self, "No Design", "Load a template and run Auto Fill first.")
            return
        variant = self.variant_dropdown.currentData()
        self._last_mockup = s.mockup_generator.render_cylinder_mockup(s.working_canvas(), variant=variant)
        MOCKUP_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        out_path = str(MOCKUP_CACHE_DIR / "_live_mockup.png")
        self._last_mockup.save(out_path, "PNG")
        dialog = MockupPreviewDialog(out_path, self)
        dialog.exec()
        self.status_label.setText(f"Generated 3D preview: {self.variant_dropdown.currentText()}")

    def _on_export_jpg(self):
        if self._last_mockup is None:
            QMessageBox.warning(self, "No Mockup Yet", "Click 'Generate 3D Preview' first.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Mockup JPG", "mockup.jpg", "JPEG (*.jpg)")
        if not file_path:
            return
        self.session.mockup_generator.export_mockup_jpg(self._last_mockup, file_path)
        self.status_label.setText(f"Exported: {file_path}")
        QMessageBox.information(self, "Export Complete", f"Mockup exported for WhatsApp/email:\n{file_path}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SubliStudio v2.2")
        self.resize(1400, 900)
        self.session = SessionState()
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        self.tabs = QTabWidget()
        self.design_panel = DesignPanel(self.session, self._on_session_changed)
        self.manual_panel = ManualEditPanel(self.session, self._on_session_changed)
        self.text_panel = TextPanel(self.session, self._on_session_changed)
        self.print_panel = PrintPanel(self.session, self._on_session_changed)
        self.mockup_panel = MockupPanel(self.session, self._on_session_changed)

        self.tabs.addTab(self.design_panel, "\U0001F3A8 Design")
        self.tabs.addTab(self.manual_panel, "\u270F\uFE0F Manual Edit")
        self.tabs.addTab(self.text_panel, "\U0001F524 Text")
        self.tabs.addTab(self.print_panel, "\U0001F5A8 Print")
        self.tabs.addTab(self.mockup_panel, "\U0001F9F6 Mockup")

        root_layout.addWidget(self.tabs, stretch=1)
        self.design_panel.templateLoaded.connect(self._on_template_loaded)
        self.statusBar().showMessage("SubliStudio v2.2 Ready.")

    def _on_template_loaded(self):
        self.manual_panel.update_frame_ranges()

    def _on_session_changed(self, preview_override: Optional[Image.Image] = None):
        self.design_panel.refresh_preview()
