"""Integrated Phase 1 workflow for SubliStudio.

This window is intentionally self-contained and uses the existing core services:
photo selection -> template auto-fill -> live edit preview/effects -> final print preview/export.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFilter
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QSplitter,
    QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QTabWidget, QGroupBox, QFileDialog, QMessageBox, QSlider,
)

from core.models import ProductType, TemplateTheme, PhotoItem, TemplateInfo
from core.photo_import_service import PhotoImportService
from core.template_manager import TemplateManager
from core.print_exporter import PrintExporter
from ui.photo_selection_dialog import PhotoSelectionDialog
from ui.live_canvas_preview import LiveCanvasPreview
from ui.print_settings_dialog import PrintSettingsDialog

APP_DATA = Path.home() / ".subli_studio"
CACHE = APP_DATA / "phase1_cache"


class Phase1State:
    def __init__(self):
        self.photos: List[PhotoItem] = []
        self.template: Optional[TemplateInfo] = None
        self.base_canvas: Optional[Image.Image] = None
        self.canvas: Optional[Image.Image] = None
        self.background_path: Optional[str] = None
        self.extra_design_path: Optional[str] = None
        self.selected_frame = 0
        self.photo_service = PhotoImportService(str(CACHE / "thumbnails"))
        self.templates = TemplateManager(str(CACHE / "previews"))
        self.printer = PrintExporter()

    def current(self) -> Optional[Image.Image]:
        return self.canvas if self.canvas is not None else self.base_canvas


class Phase1Window(QMainWindow):
    EFFECTS = ("None", "Soft Glow", "Warm Light", "Cool Light", "Spotlight", "Vignette", "Gold Border", "White Border")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SubliStudio — Phase 1")
        self.resize(1500, 920)
        self.state = Phase1State()
        self._build()

    def _build(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.design_tab = self._build_design()
        self.edit_tab = self._build_edit()
        self.print_tab = self._build_print()
        self.tabs.addTab(self.design_tab, "1. Design")
        self.tabs.addTab(self.edit_tab, "2. Manual Edit")
        self.tabs.addTab(self.print_tab, "3. Print Preview")
        self.tabs.currentChanged.connect(lambda _: self.refresh_all())
        self.statusBar().showMessage("Phase 1 ready: choose photos, template, then Auto Fill.")

    def _build_design(self):
        page = QWidget(); root = QVBoxLayout(page)
        root.setContentsMargins(16, 12, 16, 12)
        photos = QGroupBox("A. Select exactly the photos to use")
        row = QHBoxLayout(photos)
        folder = QPushButton("Choose Folder → Select Thumbnails")
        folder.clicked.connect(self.choose_folder)
        row.addWidget(folder)
        files = QPushButton("Select Individual Image Files")
        files.clicked.connect(self.choose_files)
        row.addWidget(files)
        row.addStretch(1)
        self.photo_label = QLabel("0 photos selected")
        row.addWidget(self.photo_label)
        root.addWidget(photos)

        tmpl = QGroupBox("B. Choose product template")
        grid = QGridLayout(tmpl)
        self.template_btn = QPushButton("Load Template PSD / Image")
        self.template_btn.clicked.connect(self.choose_template)
        grid.addWidget(self.template_btn, 0, 0)
        grid.addWidget(QLabel("Product:"), 0, 1)
        self.product = QComboBox()
        for p in ProductType: self.product.addItem(p.value, p)
        grid.addWidget(self.product, 0, 2)
        grid.addWidget(QLabel("Theme:"), 1, 1)
        self.theme = QComboBox()
        for theme in TemplateTheme: self.theme.addItem(theme.value, theme)
        grid.addWidget(self.theme, 1, 2)
        self.template_label = QLabel("No template selected")
        grid.addWidget(self.template_label, 1, 0)
        root.addWidget(tmpl)

        fill = QGroupBox("C. Auto Fill selected photos")
        fl = QHBoxLayout(fill)
        fl.addWidget(QLabel("Use first:"))
        self.fill_count = QSpinBox(); self.fill_count.setRange(1, 1)
        fl.addWidget(self.fill_count)
        self.fill_btn = QPushButton("Auto Fill")
        self.fill_btn.clicked.connect(self.auto_fill)
        fl.addWidget(self.fill_btn)
        fl.addStretch(1)
        root.addWidget(fill)

        root.addWidget(QLabel("Current design preview"))
        self.design_preview = LiveCanvasPreview("Choose photos and a template")
        root.addWidget(self.design_preview, 1)
        return page

    def _build_edit(self):
        page = QWidget(); split = QSplitter(Qt.Orientation.Horizontal)
        controls = QWidget(); left = QVBoxLayout(controls)
        left.setContentsMargins(16, 12, 12, 12)

        frame_box = QGroupBox("Frame position / crop")
        fg = QGridLayout(frame_box)
        fg.addWidget(QLabel("Frame:"), 0, 0)
        self.frame_no = QSpinBox(); self.frame_no.setRange(1, 1); self.frame_no.valueChanged.connect(self.select_frame)
        fg.addWidget(self.frame_no, 0, 1)
        fg.addWidget(QLabel("Scale:"), 1, 0)
        self.scale = QDoubleSpinBox(); self.scale.setRange(0.5, 2.5); self.scale.setValue(1.0); self.scale.setSingleStep(0.05); self.scale.valueChanged.connect(self.preview_frame)
        fg.addWidget(self.scale, 1, 1)
        fg.addWidget(QLabel("Move X:"), 2, 0)
        self.offset_x = QSpinBox(); self.offset_x.setRange(-500, 500); self.offset_x.valueChanged.connect(self.preview_frame)
        fg.addWidget(self.offset_x, 2, 1)
        fg.addWidget(QLabel("Move Y:"), 3, 0)
        self.offset_y = QSpinBox(); self.offset_y.setRange(-500, 500); self.offset_y.valueChanged.connect(self.preview_frame)
        fg.addWidget(self.offset_y, 3, 1)
        apply_frame = QPushButton("Apply Frame Change")
        apply_frame.clicked.connect(self.apply_frame)
        fg.addWidget(apply_frame, 4, 0, 1, 2)
        left.addWidget(frame_box)

        background = QGroupBox("Background")
        bg = QVBoxLayout(background)
        choose_bg = QPushButton("Choose Background")
        choose_bg.clicked.connect(self.choose_background)
        bg.addWidget(choose_bg)
        bg.addWidget(QLabel("Blur"))
        self.blur = QSlider(Qt.Orientation.Horizontal); self.blur.setRange(0, 20); self.blur.valueChanged.connect(self.preview_background)
        bg.addWidget(self.blur)
        apply_bg = QPushButton("Apply Background")
        apply_bg.clicked.connect(self.apply_background)
        bg.addWidget(apply_bg)
        left.addWidget(background)

        effects = QGroupBox("Box / Light Effect")
        ef = QVBoxLayout(effects)
        self.effect = QComboBox(); self.effect.addItems(self.EFFECTS); self.effect.currentTextChanged.connect(self.preview_effect)
        ef.addWidget(self.effect)
        ef.addWidget(QLabel("Intensity"))
        self.intensity = QSlider(Qt.Orientation.Horizontal); self.intensity.setRange(10, 100); self.intensity.setValue(50); self.intensity.valueChanged.connect(self.preview_effect)
        ef.addWidget(self.intensity)
        apply_effect = QPushButton("Apply Effect")
        apply_effect.clicked.connect(self.apply_effect)
        ef.addWidget(apply_effect)
        reset = QPushButton("Reset Preview")
        reset.clicked.connect(self.refresh_all)
        ef.addWidget(reset)
        left.addWidget(effects)
        left.addStretch(1)
        self.edit_status = QLabel("Live preview: changes are shown before they are applied.")
        self.edit_status.setWordWrap(True)
        left.addWidget(self.edit_status)

        viewer = QWidget(); right = QVBoxLayout(viewer)
        right.setContentsMargins(12, 12, 16, 12)
        right.addWidget(QLabel("Live editing preview — click a frame to select it"))
        self.edit_preview = LiveCanvasPreview("Auto Fill a design first")
        self.edit_preview.frame_clicked.connect(self.frame_clicked)
        right.addWidget(self.edit_preview, 1)
        split.addWidget(controls); split.addWidget(viewer); split.setSizes([390, 1000])
        layout = QVBoxLayout(page); layout.setContentsMargins(0, 0, 0, 0); layout.addWidget(split)
        return page

    def _build_print(self):
        page = QWidget(); split = QSplitter(Qt.Orientation.Horizontal)
        controls = QWidget(); left = QVBoxLayout(controls); left.setContentsMargins(16, 12, 12, 12)
        mirror = QGroupBox("Mirror settings")
        ml = QVBoxLayout(mirror)
        self.mirror_primary = QCheckBox("Mirror primary design"); self.mirror_primary.setChecked(True); self.mirror_primary.toggled.connect(self.refresh_print)
        self.mirror_extra = QCheckBox("Mirror extra design"); self.mirror_extra.toggled.connect(self.refresh_print)
        ml.addWidget(self.mirror_primary); ml.addWidget(self.mirror_extra); left.addWidget(mirror)
        extra = QGroupBox("Optional extra design")
        el = QVBoxLayout(extra)
        choose = QPushButton("Choose Extra Design")
        choose.clicked.connect(self.choose_extra)
        el.addWidget(choose)
        self.rotate_extra = QCheckBox("Rotate extra design 90°"); self.rotate_extra.toggled.connect(self.refresh_print)
        el.addWidget(self.rotate_extra); left.addWidget(extra)
        settings = QPushButton("Paper / DPI Settings")
        settings.clicked.connect(self.open_settings)
        left.addWidget(settings)
        export = QPushButton("Export This Final Preview")
        export.clicked.connect(self.export_print)
        left.addWidget(export)
        left.addStretch(1)
        self.print_status = QLabel("This preview is the same print sheet used for export.")
        self.print_status.setWordWrap(True); left.addWidget(self.print_status)
        viewer = QWidget(); right = QVBoxLayout(viewer); right.setContentsMargins(12, 12, 16, 12)
        right.addWidget(QLabel("Final print preview"))
        self.print_preview = LiveCanvasPreview("Auto Fill and edit a design first")
        right.addWidget(self.print_preview, 1)
        split.addWidget(controls); split.addWidget(viewer); split.setSizes([390, 1000])
        layout = QVBoxLayout(page); layout.setContentsMargins(0, 0, 0, 0); layout.addWidget(split)
        return page

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose photo folder", self.state.photo_service.get_last_folder() or "")
        if not folder: return
        self.state.photo_service.save_last_folder(folder)
        candidates = self.state.photo_service.scan_folder(folder)
        self.select_photos(candidates)

    def choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose image files", "", "Images (*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.gif *.heic *.heif)")
        candidates = [PhotoItem(p, f"{i+1:02d}", i) for i, p in enumerate(paths)]
        self.select_photos(candidates)

    def select_photos(self, candidates):
        if not candidates:
            QMessageBox.warning(self, "No photos", "No supported photos were selected."); return
        dialog = PhotoSelectionDialog(candidates, self.state.photo_service, self)
        if dialog.exec():
            self.state.photos = dialog.selected_photos()
            self.photo_label.setText(f"{len(self.state.photos)} photo(s) selected")
            self.fill_count.setRange(1, max(1, len(self.state.photos)))
            self.fill_count.setValue(len(self.state.photos))

    def choose_template(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose template", "", "Templates (*.psd *.psb *.png *.jpg *.jpeg *.tiff)")
        if not path: return
        info, preview = self.state.templates.load_template(path, self.product.currentData(), self.theme.currentData())
        if not info or not preview:
            QMessageBox.critical(self, "Template error", "Could not load the template."); return
        self.state.template = info
        self.state.base_canvas = Image.open(preview).convert("RGBA")
        self.state.canvas = None
        self.template_label.setText(f"{info.display_name} — {info.frame_count} frame(s)")
        for spin in [self.frame_no]: spin.setRange(1, max(1, info.frame_count))
        self.refresh_all()

    def auto_fill(self):
        if not self.state.template or not self.state.base_canvas or not self.state.photos:
            QMessageBox.warning(self, "Missing input", "Select photos and a template first."); return
        try:
            self.state.canvas = self.state.templates.fill_frames(self.state.template, self.state.base_canvas, self.state.photos[:self.fill_count.value()])
            self.refresh_all()
            self.statusBar().showMessage("Auto Fill complete. Use Manual Edit for live adjustments.")
        except Exception as exc:
            QMessageBox.critical(self, "Auto Fill error", str(exc))

    def frame_clicked(self, index):
        self.frame_no.setValue(index + 1)

    def select_frame(self):
        if not self.state.template: return
        i = self.frame_no.value() - 1
        self.state.selected_frame = i
        frame = self.state.template.frames[i]
        for widget, value in [(self.scale, frame.photo_scale), (self.offset_x, frame.photo_offset_x), (self.offset_y, frame.photo_offset_y)]:
            widget.blockSignals(True); widget.setValue(value); widget.blockSignals(False)
        self.refresh_edit()

    def _require_canvas(self):
        if not self.state.template or self.state.current() is None:
            QMessageBox.warning(self, "No design", "Auto Fill a template first."); return False
        return True

    def preview_frame(self):
        if not self._require_canvas(): return
        i = self.frame_no.value() - 1; f = self.state.template.frames[i]
        original = (f.photo_scale, f.photo_offset_x, f.photo_offset_y)
        f.photo_scale, f.photo_offset_x, f.photo_offset_y = self.scale.value(), self.offset_x.value(), self.offset_y.value()
        mapping = {n: frame.photo_index for n, frame in enumerate(self.state.template.frames) if frame.photo_index is not None}
        preview = self.state.templates.fill_frames(self.state.template, self.state.base_canvas, self.state.photos, mapping)
        f.photo_scale, f.photo_offset_x, f.photo_offset_y = original
        self.edit_preview.set_canvas(preview, self.state.template.frames, i)
        self.edit_status.setText("Preview only. Click Apply Frame Change to keep it.")

    def apply_frame(self):
        if not self._require_canvas(): return
        f = self.state.template.frames[self.frame_no.value()-1]
        f.photo_scale, f.photo_offset_x, f.photo_offset_y = self.scale.value(), self.offset_x.value(), self.offset_y.value()
        mapping = {n: frame.photo_index for n, frame in enumerate(self.state.template.frames) if frame.photo_index is not None}
        self.state.canvas = self.state.templates.fill_frames(self.state.template, self.state.base_canvas, self.state.photos, mapping)
        self.edit_status.setText("Frame change applied."); self.refresh_all()

    def choose_background(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose background", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if path: self.state.background_path = path; self.preview_background()

    def preview_background(self):
        if not self._require_canvas() or not self.state.background_path: return
        preview = self.state.templates.change_background_with_preview(self.state.current(), self.state.background_path, self.blur.value())
        self.edit_preview.set_canvas(preview, self.state.template.frames, self.state.selected_frame)
        self.edit_status.setText("Background preview only. Click Apply Background to keep it.")

    def apply_background(self):
        if not self._require_canvas() or not self.state.background_path: return
        self.state.canvas = self.state.templates.change_background_with_preview(self.state.current(), self.state.background_path, self.blur.value())
        self.edit_status.setText("Background applied."); self.refresh_all()

    def effect_image(self, image):
        name = self.effect.currentText(); opacity = self.intensity.value() / 100.0
        result = image.convert("RGBA").copy(); w, h = result.size
        if name == "None": return result
        layer = Image.new("RGBA", (w, h), (0,0,0,0)); d = ImageDraw.Draw(layer)
        if name == "Soft Glow":
            d.ellipse((-w//4,-h//4,w*5//4,h*5//4), fill=(255,255,255,int(95*opacity))); layer = layer.filter(ImageFilter.GaussianBlur(max(5, min(w,h)//12)))
        elif name == "Warm Light": d.rectangle((0,0,w,h), fill=(255,155,60,int(100*opacity)))
        elif name == "Cool Light": d.rectangle((0,0,w,h), fill=(70,165,255,int(90*opacity)))
        elif name == "Spotlight":
            d.ellipse((w//4,h//6,w*3//4,h*5//6), fill=(255,255,220,int(145*opacity))); layer = layer.filter(ImageFilter.GaussianBlur(max(8,min(w,h)//10)))
        elif name == "Vignette": d.rectangle((5,5,w-6,h-6), outline=(0,0,0,int(185*opacity)), width=max(8,min(w,h)//10))
        elif name == "Gold Border": d.rectangle((5,5,w-6,h-6), outline=(230,180,35,255), width=max(4,int(15*opacity)))
        elif name == "White Border": d.rectangle((5,5,w-6,h-6), outline=(255,255,255,255), width=max(4,int(15*opacity)))
        return Image.alpha_composite(result, layer)

    def preview_effect(self):
        if not self._require_canvas(): return
        self.edit_preview.set_canvas(self.effect_image(self.state.current()), self.state.template.frames, self.state.selected_frame)
        self.edit_status.setText("Effect preview only. Click Apply Effect to keep it.")

    def apply_effect(self):
        if not self._require_canvas(): return
        self.state.canvas = self.effect_image(self.state.current())
        self.edit_status.setText("Effect applied."); self.refresh_all()

    def choose_extra(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose extra design", "", "Images (*.png *.jpg *.jpeg)")
        if path: self.state.extra_design_path = path; self.refresh_print()

    def open_settings(self):
        d = PrintSettingsDialog(self, self.state.printer.settings)
        if d.exec(): self.state.printer.settings = d.get_settings(); self.refresh_print()

    def refresh_edit(self):
        self.edit_preview.set_canvas(self.state.current(), self.state.template.frames if self.state.template else [], self.state.selected_frame)

    def refresh_print(self):
        if not self.state.current(): self.print_preview.set_canvas(None); return
        extra = Image.open(self.state.extra_design_path).convert("RGB") if self.state.extra_design_path else None
        sheet = self.state.printer.build_print_sheet(self.state.current(), self.mirror_primary.isChecked(), self.mirror_extra.isChecked(), extra, self.rotate_extra.isChecked())
        self.print_preview.set_canvas(sheet)

    def refresh_all(self):
        self.design_preview.set_canvas(self.state.current(), self.state.template.frames if self.state.template else [], self.state.selected_frame)
        self.refresh_edit(); self.refresh_print()

    def export_print(self):
        if not self._require_canvas(): return
        folder = QFileDialog.getExistingDirectory(self, "Choose export folder")
        if not folder: return
        extra = Image.open(self.state.extra_design_path).convert("RGB") if self.state.extra_design_path else None
        name = Path(self.state.template.source_path).stem if self.state.template else "design"
        try:
            paths = self.state.printer.export(self.state.current(), folder, name, self.mirror_primary.isChecked(), self.mirror_extra.isChecked(), extra, self.rotate_extra.isChecked(), formats=("png", "pdf"))
            self.print_status.setText("Exported final preview:\n" + "\n".join(paths))
        except Exception as exc: QMessageBox.critical(self, "Export error", str(exc))
