"""
ui/main_window.py (v2)

Multi-panel UI with tabs: Design | Manual Edit | Text | Print | Mockup
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, List, Dict

from PIL import Image

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QComboBox, QLabel, QFileDialog, QMessageBox, QSplitter, QFrame,
    QCheckBox, QSpinBox, QTabWidget, QScrollArea, QButtonGroup, QRadioButton,
    QDoubleSpinBox, QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.models import ProductType, PhotoItem, TemplateInfo, TemplateTheme, FrameShape, DesignJob
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
AUTO_SAVE_DIR = APP_DATA_DIR / "manual_psd"

BUILTIN_EFFECTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "effects"
BUILTIN_BG_DIR = Path(__file__).resolve().parent.parent / "assets" / "backgrounds"
BUILTIN_TEXT_PRESETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "text_presets"


class DesignPanel(QWidget):
    """Main design panel with photo load, template selection, auto-fill."""
    templateLoaded = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.photo_service = PhotoImportService(str(THUMB_CACHE_DIR))
        self.template_manager = TemplateManager(str(PREVIEW_CACHE_DIR))
        self.loaded_photos: List[PhotoItem] = []
        self.current_template: Optional[TemplateInfo] = None
        self.base_canvas: Optional[Image.Image] = None
        self.design_canvas: Optional[Image.Image] = None
        
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
        
        tmpl_layout.addWidget(QLabel("Frames:"), 1, 1)
        self.frame_count_filter = QComboBox()
        self.frame_count_filter.addItem("Any", userData=None)
        for i in range(1, 7):
            self.frame_count_filter.addItem(f"{i} photo{chr(115) if i > 1 else chr(39)}", userData=i)
        tmpl_layout.addWidget(self.frame_count_filter, 1, 2)
        
        tmpl_layout.addWidget(QLabel("Theme:"), 2, 1)
        self.theme_filter = QComboBox()
        for theme in TemplateTheme:
            self.theme_filter.addItem(theme.value, userData=theme)
        tmpl_layout.addWidget(self.theme_filter, 2, 2)
        
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
        last_folder = self.photo_service.get_last_folder()
        folder = QFileDialog.getExistingDirectory(self, "Select Customer Photos Folder", 
                                                   last_folder or "")
        if not folder:
            return
        
        self.photo_service.save_last_folder(folder)
        photos = self.photo_service.scan_folder(folder)
        if not photos:
            QMessageBox.warning(self, "No Photos Found", f"No supported images in:\n{folder}")
            return
        
        self.loaded_photos = photos
        self.photo_count_label.setText(f"{len(photos)} photos (01..{photos[-1].sequence_name})")
        self.status_label.setText(f"Loaded {len(photos)} photos from {folder}")
        self._update_auto_fill_enabled()
    
    def _on_load_template(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Product Template", "",
            "Templates (*.psd *.psb *.png *.jpg *.jpeg *.tiff);;All Files (*)",
        )
        if not file_path:
            return
        
        product_type = self.product_filter.currentData() or ProductType.MUG
        theme = self.theme_filter.currentData() or TemplateTheme.PLAIN
        
        self.status_label.setText(f"Loading template...")
        info, preview_path = self.template_manager.load_template(file_path, product_type, theme)
        
        if not info or not preview_path:
            QMessageBox.critical(self, "Template Load Failed", f"Could not load:\n{file_path}")
            self.status_label.setText("Template load failed.")
            return
        
        self.current_template = info
        self.base_canvas = Image.open(preview_path).convert("RGBA")
        self.design_canvas = None
        
        self.preview.set_preview(preview_path, frames=info.frames, 
                                source_size=(info.width, info.height))
        self.status_label.setText(f"Loaded: {info.display_name} ({info.frame_count} frames, {info.theme.value})")
        self.templateLoaded.emit(info)
        self._update_auto_fill_enabled()
    
    def _update_auto_fill_enabled(self):
        can_fill = bool(self.loaded_photos) and self.current_template is not None
        self.auto_fill_btn.setEnabled(can_fill)
        if can_fill:
            max_photos = min(len(self.loaded_photos), self.current_template.frame_count)
            self.photo_count_spin.setRange(1, max(1, max_photos))
            self.photo_count_spin.setValue(max_photos)
    
    def _on_auto_fill(self):
        if not self.current_template or not self.loaded_photos or not self.base_canvas:
            return
        
        n = self.photo_count_spin.value()
        photos_to_use = self.loaded_photos[:n]
        
        try:
            self.design_canvas = self.template_manager.fill_frames(
                self.current_template, self.base_canvas, photos_to_use
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Auto Fill Failed", str(exc))
            return
        
        self._refresh_preview()
        self.status_label.setText(f"Auto-filled {min(n, self.current_template.frame_count)} frames.")
    
    def _refresh_preview(self):
        if not self.current_template or not self.design_canvas:
            return
        tmp_path = str(PREVIEW_CACHE_DIR / "_live_preview.png")
        Path(PREVIEW_CACHE_DIR).mkdir(parents=True, exist_ok=True)
        self.design_canvas.convert("RGB").save(tmp_path, "PNG")
        self.preview.set_preview(tmp_path, frames=self.current_template.frames,
                                source_size=(self.current_template.width, self.current_template.height))


class ManualEditPanel(QWidget):
    """Manual editing panel: resize-in-frame, extra photo, swap, background, effects."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.template_manager = TemplateManager(str(PREVIEW_CACHE_DIR))
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        resize_group = QGroupBox("Resize Photo in Frame")
        resize_layout = QGridLayout(resize_group)
        
        resize_layout.addWidget(QLabel("Frame:"), 0, 0)
        self.resize_frame_spin = QSpinBox()
        self.resize_frame_spin.setRange(1, 1)
        resize_layout.addWidget(self.resize_frame_spin, 0, 1)
        
        resize_layout.addWidget(QLabel("Scale:"), 0, 2)
        self.resize_scale_spin = QDoubleSpinBox()
        self.resize_scale_spin.setRange(0.5, 2.0)
        self.resize_scale_spin.setValue(1.0)
        self.resize_scale_spin.setSingleStep(0.1)
        resize_layout.addWidget(self.resize_scale_spin, 0, 3)
        
        resize_layout.addWidget(QLabel("Offset X:"), 1, 0)
        self.resize_offset_x = QSpinBox()
        self.resize_offset_x.setRange(-100, 100)
        resize_layout.addWidget(self.resize_offset_x, 1, 1)
        
        resize_layout.addWidget(QLabel("Offset Y:"), 1, 2)
        self.resize_offset_y = QSpinBox()
        self.resize_offset_y.setRange(-100, 100)
        resize_layout.addWidget(self.resize_offset_y, 1, 3)
        
        self.apply_resize_btn = QPushButton("Apply Resize")
        resize_layout.addWidget(self.apply_resize_btn, 2, 0, 1, 4)
        
        layout.addWidget(resize_group)
        
        extra_group = QGroupBox("Extra Photo")
        extra_layout = QHBoxLayout(extra_group)
        
        self.extra_photo_btn = QPushButton("\u2795 Add Extra Photo")
        extra_layout.addWidget(self.extra_photo_btn)
        
        layout.addWidget(extra_group)
        
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
        swap_layout.addWidget(self.swap_btn)
        
        layout.addWidget(swap_group)
        
        bg_group = QGroupBox("Change Background")
        bg_layout = QHBoxLayout(bg_group)
        
        self.change_bg_btn = QPushButton("\U0001F5BC Change Background")
        bg_layout.addWidget(self.change_bg_btn)
        
        bg_layout.addWidget(QLabel("Blur:"))
        self.bg_blur_spin = QSpinBox()
        self.bg_blur_spin.setRange(0, 20)
        bg_layout.addWidget(self.bg_blur_spin)
        
        self.preview_bg_btn = QPushButton("Preview")
        bg_layout.addWidget(self.preview_bg_btn)
        
        layout.addWidget(bg_group)
        
        effects_group = QGroupBox("Box/Light Effects")
        effects_layout = QHBoxLayout(effects_group)
        
        self.effects_dropdown = QComboBox()
        self.effects_dropdown.addItem("(none)", userData=None)
        effects_layout.addWidget(self.effects_dropdown)
        
        self.apply_effect_btn = QPushButton("Apply Effect")
        effects_layout.addWidget(self.apply_effect_btn)
        
        layout.addWidget(effects_group)
        
        layout.addStretch()
        self.status_label = QLabel("Manual Edit Panel Ready.")
        layout.addWidget(self.status_label)


class TextPanel(QWidget):
    """Text panel: readymade presets, manual text, 3D text generator."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.template_manager = TemplateManager(str(PREVIEW_CACHE_DIR))
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        ready_group = QGroupBox("Readymade Text")
        ready_layout = QHBoxLayout(ready_group)
        
        self.readymade_dropdown = QComboBox()
        presets = ["Happy Birthday", "Congratulations", "Love You", "Happy Diwali", "Happy Holi", "Happy New Year"]
        for p in presets:
            self.readymade_dropdown.addItem(p)
        ready_layout.addWidget(self.readymade_dropdown)
        
        self.add_readymade_btn = QPushButton("Add Readymade Text")
        ready_layout.addWidget(self.add_readymade_btn)
        
        layout.addWidget(ready_group)
        
        manual_group = QGroupBox("Manual Text")
        manual_layout = QGridLayout(manual_group)
        
        manual_layout.addWidget(QLabel("Text:"), 0, 0)
        self.manual_text_edit = QLabel("Enter text...")
        manual_layout.addWidget(self.manual_text_edit, 0, 1)
        
        self.add_manual_btn = QPushButton("Add Manual Text")
        manual_layout.addWidget(self.add_manual_btn, 1, 0, 1, 2)
        
        layout.addWidget(manual_group)
        
        text3d_group = QGroupBox("3D Text Generator")
        text3d_layout = QHBoxLayout(text3d_group)
        
        self.text3d_edit = QLabel("Enter 3D text...")
        text3d_layout.addWidget(self.text3d_edit)
        
        self.generate_3d_btn = QPushButton("Generate 3D Text")
        text3d_layout.addWidget(self.generate_3d_btn)
        
        layout.addWidget(text3d_group)
        
        layout.addStretch()
        self.status_label = QLabel("Text Panel Ready.")
        layout.addWidget(self.status_label)


class PrintPanel(QWidget):
    """Print panel: Mirror 1/Mirror 2 toggle, Add Extra Design, export."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.print_exporter = PrintExporter()
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        mirror_group = QGroupBox("Mirror Settings")
        mirror_layout = QHBoxLayout(mirror_group)
        
        self.mirror1_checkbox = QCheckBox("Mirror 1")
        self.mirror1_checkbox.setChecked(True)
        mirror_layout.addWidget(self.mirror1_checkbox)
        
        self.mirror2_checkbox = QCheckBox("Mirror 2")
        mirror_layout.addWidget(self.mirror2_checkbox)
        
        layout.addWidget(mirror_group)
        
        extra_group = QGroupBox("Add Extra Design")
        extra_layout = QHBoxLayout(extra_group)
        
        self.add_extra_checkbox = QCheckBox("Add extra design to fill space")
        extra_layout.addWidget(self.add_extra_checkbox)
        
        self.rotate_extra_checkbox = QCheckBox("Rotate 90 degrees")
        extra_layout.addWidget(self.rotate_extra_checkbox)
        
        layout.addWidget(extra_group)
        
        export_group = QGroupBox("Export")
        export_layout = QHBoxLayout(export_group)
        
        self.prepare_print_btn = QPushButton("\U0001F5A8 Prepare for Print")
        export_layout.addWidget(self.prepare_print_btn)
        
        layout.addWidget(export_group)
        
        layout.addStretch()
        self.status_label = QLabel("Print Panel Ready.")
        layout.addWidget(self.status_label)


class MockupPanel(QWidget):
    """Mockup panel: variant selector, 3D preview, JPG export."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mockup_generator = MockupGenerator(str(MOCKUP_CACHE_DIR))
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        variant_group = QGroupBox("3D Mockup Variant")
        variant_layout = QHBoxLayout(variant_group)
        
        self.variant_dropdown = QComboBox()
        for v in self.mockup_generator.mug_variants:
            self.variant_dropdown.addItem(v.name, userData=v)
        variant_layout.addWidget(self.variant_dropdown)
        
        layout.addWidget(variant_group)
        
        preview_group = QGroupBox("Preview")
        preview_layout = QHBoxLayout(preview_group)
        
        self.generate_mockup_btn = QPushButton("\U0001F9F6 Generate 3D Preview")
        preview_layout.addWidget(self.generate_mockup_btn)
        
        layout.addWidget(preview_group)
        
        export_group = QGroupBox("Export for WhatsApp/Email")
        export_layout = QHBoxLayout(export_group)
        
        self.export_jpg_btn = QPushButton("\U0001F4E4 Export JPG")
        export_layout.addWidget(self.export_jpg_btn)
        
        layout.addWidget(export_group)
        
        layout.addStretch()
        self.status_label = QLabel("Mockup Panel Ready.")
        layout.addWidget(self.status_label)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SubliStudio v2")
        self.resize(1400, 900)
        
        self.design_job: Optional[DesignJob] = None
        
        self._init_ui()
        self._load_auto_save_if_exists()
    
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        
        self.tabs = QTabWidget()
        self.design_panel = DesignPanel()
        self.manual_panel = ManualEditPanel()
        self.text_panel = TextPanel()
        self.print_panel = PrintPanel()
        self.mockup_panel = MockupPanel()
        
        self.tabs.addTab(self.design_panel, "\U0001F3A8 Design")
        self.tabs.addTab(self.manual_panel, "\u270F\uFE0F Manual Edit")
        self.tabs.addTab(self.text_panel, "\U0001F524 Text")
        self.tabs.addTab(self.print_panel, "\U0001F5A8 Print")
        self.tabs.addTab(self.mockup_panel, "\U0001F9F6 Mockup")
        
        root_layout.addWidget(self.tabs, stretch=1)
        
        self.statusBar().showMessage("SubliStudio v2 Ready.")
    
    def _load_auto_save_if_exists(self):
        if not AUTO_SAVE_DIR.exists():
            return
        
        job_files = sorted(AUTO_SAVE_DIR.glob("*.job.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if job_files:
            try:
                self.design_job = DesignJob.load_from_auto_save(str(job_files[0]))
                self.statusBar().showMessage(f"Auto-loaded: {job_files[0].name}")
            except Exception as exc:
                logger.warning("Failed to auto-load %s: %s", job_files[0], exc)
