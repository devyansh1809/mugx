"""SubliStudio v2.3: selectable photos, live edit and print previews."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFilter
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QSplitter,
    QPushButton, QComboBox, QLabel, QFileDialog, QMessageBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QTabWidget, QGroupBox, QLineEdit, QSlider,
)

from core.models import ProductType, PhotoItem, TemplateInfo, TemplateTheme, DesignJob
from core.photo_import_service import PhotoImportService
from core.template_manager import TemplateManager
from core.image_processor import ImageEnhancementService
from core.print_exporter import PrintExporter
from core.mockup_generator import MockupGenerator
from ui.template_preview_widget import TemplatePreviewWidget
from ui.photo_selection_dialog import PhotoSelectionDialog
from ui.live_canvas_preview import LiveCanvasPreview
from ui.text_tool_dialog import TextToolDialog
from ui.print_settings_dialog import PrintSettingsDialog
from ui.mockup_preview_dialog import MockupPreviewDialog

logger = logging.getLogger("SubliStudio.MainWindow")
APP_DATA_DIR = Path.home() / ".subli_studio"
THUMB_CACHE_DIR = APP_DATA_DIR / "thumbnails"
ENHANCE_CACHE_DIR = APP_DATA_DIR / "enhanced_thumbnails"
PREVIEW_CACHE_DIR = APP_DATA_DIR / "template_previews"
MOCKUP_CACHE_DIR = APP_DATA_DIR / "mockups"
AUTO_SAVE_DIR = APP_DATA_DIR / "manual_psd"


class SessionState:
    """One shared design state for every tab."""
    def __init__(self):
        self.photo_service = PhotoImportService(str(THUMB_CACHE_DIR))
        self.template_manager = TemplateManager(str(PREVIEW_CACHE_DIR))
        self.enhancement_service = ImageEnhancementService(str(ENHANCE_CACHE_DIR))
        self.print_exporter = PrintExporter()
        self.mockup_generator = MockupGenerator(str(MOCKUP_CACHE_DIR))
        self.photos: List[PhotoItem] = []
        self.template: Optional[TemplateInfo] = None
        self.base_canvas: Optional[Image.Image] = None
        self.canvas: Optional[Image.Image] = None
        self.selected_frame = 0
        self.extra_design_path: Optional[str] = None

    def current_canvas(self) -> Optional[Image.Image]:
        return self.canvas if self.canvas is not None else self.base_canvas

    def save(self):
        if not self.template:
            return
        try:
            DesignJob(template=self.template, photos=self.photos).auto_save(str(AUTO_SAVE_DIR))
        except Exception:
            logger.exception("Autosave failed")


class DesignPanel(QWidget):
    changed = pyqtSignal()
    template_loaded = pyqtSignal()

    def __init__(self, state: SessionState, parent=None):
        super().__init__(parent)
        self.state = state
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        photo_group = QGroupBox("1. Choose Customer Photos")
        photo_layout = QHBoxLayout(photo_group)
        self.folder_btn = QPushButton("Load Folder and Choose Photos")
        self.folder_btn.clicked.connect(self.load_folder)
        photo_layout.addWidget(self.folder_btn)
        self.files_btn = QPushButton("Select Individual Files")
        self.files_btn.clicked.connect(self.select_files)
        photo_layout.addWidget(self.files_btn)
        self.auto_enhance = QCheckBox("Auto Enhance")
        self.auto_enhance.setChecked(True)
        photo_layout.addWidget(self.auto_enhance)
        photo_layout.addStretch(1)
        self.photo_status = QLabel("No photos selected")
        photo_layout.addWidget(self.photo_status)
        root.addWidget(photo_group)

        template_group = QGroupBox("2. Load Template")
        template_layout = QGridLayout(template_group)
        self.template_btn = QPushButton("Load Template")
        self.template_btn.clicked.connect(self.load_template)
        template_layout.addWidget(self.template_btn, 0, 0)
        template_layout.addWidget(QLabel("Product:"), 0, 1)
        self.product = QComboBox()
        for item in ProductType:
            self.product.addItem(item.value, item)
        template_layout.addWidget(self.product, 0, 2)
        template_layout.addWidget(QLabel("Theme:"), 1, 1)
        self.theme = QComboBox()
        for item in TemplateTheme:
            self.theme.addItem(item.value, item)
        template_layout.addWidget(self.theme, 1, 2)
        root.addWidget(template_group)

        fill_group = QGroupBox("3. Auto Fill")
        fill_layout = QHBoxLayout(fill_group)
        fill_layout.addWidget(QLabel("Use selected photos:"))
        self.count = QSpinBox()
        self.count.setMinimum(1)
        self.count.setMaximum(1)
        fill_layout.addWidget(self.count)
        self.fill_btn = QPushButton("Auto Fill Selected Photos")
        self.fill_btn.clicked.connect(self.auto_fill)
        self.fill_btn.setEnabled(False)
        fill_layout.addWidget(self.fill_btn)
        fill_layout.addStretch(1)
        root.addWidget(fill_group)

        self.preview = LiveCanvasPreview("Load photos and a template to begin")
        root.addWidget(self.preview, 1)
        self.status = QLabel("Ready.")
        root.addWidget(self.status)

    def _choose_photos(self, candidates: List[PhotoItem]):
        dialog = PhotoSelectionDialog(candidates, self.state.photo_service, self)
        if dialog.exec():
            self.state.photos = dialog.selected_photos()
            self.photo_status.setText(f"{len(self.state.photos)} selected photo(s)")
            self.count.setMaximum(max(1, len(self.state.photos)))
            self.count.setValue(min(self.count.maximum(), max(1, len(self.state.photos))))
            self._update_fill_enabled()
            self.status.setText("Photo selection updated. Load a template or Auto Fill.")

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Photo Folder", self.state.photo_service.get_last_folder() or "")
        if not folder:
            return
        self.state.photo_service.save_last_folder(folder)
        candidates = self.state.photo_service.scan_folder(folder)
        if not candidates:
            QMessageBox.warning(self, "No Photos", "No supported images were found in that folder.")
            return
        self._choose_photos(candidates)

    def select_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Customer Photos", "",
            "Images (*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.gif *.heic *.heif)",
        )
        if not paths:
            return
        candidates = [PhotoItem(original_path=p, sequence_name=f"{i+1:02d}", index=i) for i, p in enumerate(paths)]
        self._choose_photos(candidates)

    def load_template(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Product Template", "", "Templates (*.psd *.psb *.png *.jpg *.jpeg *.tiff)")
        if not path:
            return
        info, preview_path = self.state.template_manager.load_template(path, self.product.currentData(), self.theme.currentData())
        if not info or not preview_path:
            QMessageBox.critical(self, "Template Load Failed", "Could not load this template.")
            return
        self.state.template = info
        self.state.base_canvas = Image.open(preview_path).convert("RGBA")
        self.state.canvas = None
        self.state.selected_frame = 0
        self.refresh()
        self.template_loaded.emit()
        self._update_fill_enabled()
        self.status.setText(f"Loaded {info.display_name} with {info.frame_count} frame(s).")

    def _update_fill_enabled(self):
        self.fill_btn.setEnabled(bool(self.state.photos and self.state.template and self.state.base_canvas))

    def auto_fill(self):
        if not self.state.template or not self.state.base_canvas:
            return
        try:
            self.state.canvas = self.state.template_manager.fill_frames(
                self.state.template, self.state.base_canvas, self.state.photos[:self.count.value()]
            )
            self.state.save()
            self.refresh()
            self.changed.emit()
            self.status.setText("Auto Fill complete. Open Manual Edit to refine the design.")
        except Exception as exc:
            QMessageBox.critical(self, "Auto Fill Failed", str(exc))

    def refresh(self):
        self.preview.set_canvas(self.state.current_canvas(), self.state.template.frames if self.state.template else [], self.state.selected_frame)


class ManualEditPanel(QWidget):
    changed = pyqtSignal()

    EFFECTS = ["None", "Soft Glow", "Warm Light", "Cool Light", "Spotlight", "Vignette", "Gold Border", "White Border", "Drop Shadow"]

    def __init__(self, state: SessionState, parent=None):
        super().__init__(parent)
        self.state = state
        self._preview_canvas: Optional[Image.Image] = None
        self._build()

    def _build(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        controls = QWidget()
        left = QVBoxLayout(controls)
        left.setContentsMargins(16, 12, 12, 12)

        frame_group = QGroupBox("Frame Edit")
        frame_layout = QGridLayout(frame_group)
        frame_layout.addWidget(QLabel("Frame:"), 0, 0)
        self.frame = QSpinBox(); self.frame.setRange(1, 1)
        self.frame.valueChanged.connect(self.select_frame)
        frame_layout.addWidget(self.frame, 0, 1)
        frame_layout.addWidget(QLabel("Scale:"), 1, 0)
        self.scale = QDoubleSpinBox(); self.scale.setRange(0.5, 2.5); self.scale.setValue(1.0); self.scale.setSingleStep(0.05)
        self.scale.valueChanged.connect(self.preview_resize)
        frame_layout.addWidget(self.scale, 1, 1)
        frame_layout.addWidget(QLabel("Offset X:"), 2, 0)
        self.x = QSpinBox(); self.x.setRange(-500, 500); self.x.valueChanged.connect(self.preview_resize)
        frame_layout.addWidget(self.x, 2, 1)
        frame_layout.addWidget(QLabel("Offset Y:"), 3, 0)
        self.y = QSpinBox(); self.y.setRange(-500, 500); self.y.valueChanged.connect(self.preview_resize)
        frame_layout.addWidget(self.y, 3, 1)
        self.apply_resize = QPushButton("Apply Frame Edit")
        self.apply_resize.clicked.connect(self.commit_resize)
        frame_layout.addWidget(self.apply_resize, 4, 0, 1, 2)
        left.addWidget(frame_group)

        swap_group = QGroupBox("Swap Two Photos")
        swap_layout = QHBoxLayout(swap_group)
        self.swap_one = QSpinBox(); self.swap_one.setRange(1, 1)
        self.swap_two = QSpinBox(); self.swap_two.setRange(1, 1)
        swap_layout.addWidget(self.swap_one); swap_layout.addWidget(QLabel("with")); swap_layout.addWidget(self.swap_two)
        swap_btn = QPushButton("Swap")
        swap_btn.clicked.connect(self.swap)
        swap_layout.addWidget(swap_btn)
        left.addWidget(swap_group)

        bg_group = QGroupBox("Background")
        bg_layout = QVBoxLayout(bg_group)
        self.bg_btn = QPushButton("Choose Background Image")
        self.bg_btn.clicked.connect(self.choose_background)
        bg_layout.addWidget(self.bg_btn)
        self.blur = QSlider(Qt.Orientation.Horizontal); self.blur.setRange(0, 20); self.blur.valueChanged.connect(self.preview_background)
        bg_layout.addWidget(QLabel("Blur preview")); bg_layout.addWidget(self.blur)
        self.apply_bg = QPushButton("Apply Background")
        self.apply_bg.clicked.connect(self.commit_background)
        bg_layout.addWidget(self.apply_bg)
        left.addWidget(bg_group)

        fx_group = QGroupBox("Box / Light Effects")
        fx_layout = QVBoxLayout(fx_group)
        self.effect = QComboBox(); self.effect.addItems(self.EFFECTS); self.effect.currentTextChanged.connect(self.preview_effect)
        fx_layout.addWidget(self.effect)
        fx_layout.addWidget(QLabel("Effect intensity"))
        self.intensity = QSlider(Qt.Orientation.Horizontal); self.intensity.setRange(10, 100); self.intensity.setValue(55); self.intensity.valueChanged.connect(self.preview_effect)
        fx_layout.addWidget(self.intensity)
        apply_fx = QPushButton("Apply Effect")
        apply_fx.clicked.connect(self.commit_effect)
        fx_layout.addWidget(apply_fx)
        reset = QPushButton("Reset Preview")
        reset.clicked.connect(self.refresh)
        fx_layout.addWidget(reset)
        left.addWidget(fx_group)
        left.addStretch(1)
        self.status = QLabel("Select a frame or click a frame in the preview.")
        left.addWidget(self.status)

        right = QWidget(); right_layout = QVBoxLayout(right); right_layout.setContentsMargins(12, 12, 16, 12)
        right_layout.addWidget(QLabel("Live Edit Preview — this is the current printable composition"))
        self.preview = LiveCanvasPreview("Load and Auto Fill a design first")
        self.preview.frame_clicked.connect(self.click_frame)
        right_layout.addWidget(self.preview, 1)
        splitter.addWidget(controls); splitter.addWidget(right); splitter.setSizes([410, 990])
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.addWidget(splitter)

    def update_frames(self):
        n = self.state.template.frame_count if self.state.template else 1
        for spin in [self.frame, self.swap_one, self.swap_two]: spin.setRange(1, max(1, n))
        self.refresh()

    def click_frame(self, index):
        self.frame.setValue(index + 1)

    def select_frame(self):
        if not self.state.template: return
        index = self.frame.value() - 1
        self.state.selected_frame = index
        info = self.state.template.frames[index]
        self.scale.blockSignals(True); self.x.blockSignals(True); self.y.blockSignals(True)
        self.scale.setValue(info.photo_scale); self.x.setValue(info.photo_offset_x); self.y.setValue(info.photo_offset_y)
        self.scale.blockSignals(False); self.x.blockSignals(False); self.y.blockSignals(False)
        self.refresh()

    def _require(self):
        if not self.state.template or self.state.current_canvas() is None:
            QMessageBox.warning(self, "No Design", "Load a template and run Auto Fill first.")
            return False
        return True

    def preview_resize(self):
        if not self._require(): return
        index = self.frame.value() - 1
        frame = self.state.template.frames[index]
        old = (frame.photo_scale, frame.photo_offset_x, frame.photo_offset_y)
        frame.photo_scale, frame.photo_offset_x, frame.photo_offset_y = self.scale.value(), self.x.value(), self.y.value()
        mapping = {i: f.photo_index for i, f in enumerate(self.state.template.frames) if f.photo_index is not None}
        self._preview_canvas = self.state.template_manager.fill_frames(self.state.template, self.state.base_canvas, self.state.photos, mapping)
        frame.photo_scale, frame.photo_offset_x, frame.photo_offset_y = old
        self.preview.set_canvas(self._preview_canvas, self.state.template.frames, index)
        self.status.setText("Previewing scale/position. Click Apply Frame Edit to keep it.")

    def commit_resize(self):
        if not self._require(): return
        frame = self.state.template.frames[self.frame.value() - 1]
        frame.photo_scale, frame.photo_offset_x, frame.photo_offset_y = self.scale.value(), self.x.value(), self.y.value()
        mapping = {i: f.photo_index for i, f in enumerate(self.state.template.frames) if f.photo_index is not None}
        self.state.canvas = self.state.template_manager.fill_frames(self.state.template, self.state.base_canvas, self.state.photos, mapping)
        self.state.save(); self.refresh(); self.changed.emit(); self.status.setText("Frame edit applied.")

    def swap(self):
        if not self._require(): return
        try:
            self.state.canvas = self.state.template_manager.swap_photos(self.state.template, self.state.base_canvas, self.state.photos, self.swap_one.value()-1, self.swap_two.value()-1)
            self.state.save(); self.refresh(); self.changed.emit(); self.status.setText("Photos swapped.")
        except Exception as exc: QMessageBox.warning(self, "Swap Failed", str(exc))

    def choose_background(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose Background", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if path:
            self._background = path; self.preview_background()

    def preview_background(self):
        if not self._require() or not hasattr(self, "_background"): return
        self._preview_canvas = self.state.template_manager.change_background_with_preview(self.state.current_canvas(), self._background, self.blur.value())
        self.preview.set_canvas(self._preview_canvas, self.state.template.frames, self.state.selected_frame)
        self.status.setText("Background preview only. Click Apply Background to keep it.")

    def commit_background(self):
        if not self._require() or not hasattr(self, "_background"): return
        self.state.canvas = self.state.template_manager.change_background_with_preview(self.state.current_canvas(), self._background, self.blur.value())
        self.state.save(); self.refresh(); self.changed.emit(); self.status.setText("Background applied.")

    def _effect_canvas(self, canvas: Image.Image) -> Image.Image:
        name, amount = self.effect.currentText(), self.intensity.value() / 100.0
        result = canvas.convert("RGBA").copy(); w, h = result.size
        if name == "None": return result
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); draw = ImageDraw.Draw(overlay)
        if name == "Soft Glow":
            draw.ellipse((-w//4, -h//4, w*5//4, h*5//4), fill=(255,255,255,round(90*amount)))
            overlay = overlay.filter(ImageFilter.GaussianBlur(max(5, round(min(w,h)*0.08))))
        elif name == "Warm Light": draw.rectangle((0,0,w,h), fill=(255,170,70,round(85*amount)))
        elif name == "Cool Light": draw.rectangle((0,0,w,h), fill=(70,170,255,round(75*amount)))
        elif name == "Spotlight":
            draw.ellipse((w//4, h//5, w*3//4, h*4//5), fill=(255,255,230,round(135*amount)))
            overlay = overlay.filter(ImageFilter.GaussianBlur(max(8, round(min(w,h)*0.06))))
        elif name == "Vignette":
            thickness = max(10, round(min(w,h)*0.1)); draw.rectangle((0,0,w,h), outline=(0,0,0,round(170*amount)), width=thickness)
        elif name == "Gold Border": draw.rectangle((5,5,w-6,h-6), outline=(230,180,50,255), width=max(4, round(12*amount)))
        elif name == "White Border": draw.rectangle((5,5,w-6,h-6), outline=(255,255,255,255), width=max(4, round(12*amount)))
        elif name == "Drop Shadow":
            shadow = Image.new("RGBA", (w,h), (0,0,0,0)); shadow.paste(result, (max(2,round(12*amount)), max(2,round(12*amount))))
            shadow = shadow.filter(ImageFilter.GaussianBlur(max(2,round(10*amount))))
            result = Image.alpha_composite(shadow, result)
        return Image.alpha_composite(result, overlay)

    def preview_effect(self):
        if not self._require(): return
        self._preview_canvas = self._effect_canvas(self.state.current_canvas())
        self.preview.set_canvas(self._preview_canvas, self.state.template.frames, self.state.selected_frame)
        self.status.setText("Effect preview. Click Apply Effect to keep it.")

    def commit_effect(self):
        if not self._require(): return
        self.state.canvas = self._effect_canvas(self.state.current_canvas())
        self.state.save(); self.refresh(); self.changed.emit(); self.status.setText("Effect applied.")

    def refresh(self):
        self._preview_canvas = None
        self.preview.set_canvas(self.state.current_canvas(), self.state.template.frames if self.state.template else [], self.state.selected_frame)


class PrintPanel(QWidget):
    def __init__(self, state: SessionState, parent=None):
        super().__init__(parent); self.state = state; self._build()

    def _build(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        controls = QWidget(); left = QVBoxLayout(controls); left.setContentsMargins(16,12,12,12)
        mirror = QGroupBox("Mirror Settings")
        ml = QVBoxLayout(mirror); self.mirror1 = QCheckBox("Mirror primary design"); self.mirror1.setChecked(True); self.mirror2 = QCheckBox("Mirror extra design")
        self.mirror1.toggled.connect(self.refresh); self.mirror2.toggled.connect(self.refresh); ml.addWidget(self.mirror1); ml.addWidget(self.mirror2); left.addWidget(mirror)
        extra = QGroupBox("Add Extra Design")
        el = QVBoxLayout(extra); self.extra_btn = QPushButton("Choose Extra Design Image"); self.extra_btn.clicked.connect(self.choose_extra); el.addWidget(self.extra_btn)
        self.rotate = QCheckBox("Rotate extra design 90 degrees"); self.rotate.toggled.connect(self.refresh); el.addWidget(self.rotate); left.addWidget(extra)
        self.settings_btn = QPushButton("Paper / DPI Settings"); self.settings_btn.clicked.connect(self.settings); left.addWidget(self.settings_btn)
        self.export_btn = QPushButton("Export Final Print PNG + PDF"); self.export_btn.clicked.connect(self.export); left.addWidget(self.export_btn); left.addStretch(1)
        self.status = QLabel("The preview shows the exact print sheet that will be exported."); self.status.setWordWrap(True); left.addWidget(self.status)
        right = QWidget(); rl = QVBoxLayout(right); rl.setContentsMargins(12,12,16,12); rl.addWidget(QLabel("Final Print Preview — exact output layout")); self.preview = LiveCanvasPreview("Load and edit a design first"); rl.addWidget(self.preview,1)
        splitter.addWidget(controls); splitter.addWidget(right); splitter.setSizes([380,1020]); layout=QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.addWidget(splitter)

    def choose_extra(self):
        path,_ = QFileDialog.getOpenFileName(self,"Choose Extra Design","","Images (*.png *.jpg *.jpeg)")
        if path: self.state.extra_design_path=path; self.refresh()

    def settings(self):
        dialog = PrintSettingsDialog(self, self.state.print_exporter.settings)
        if dialog.exec(): self.state.print_exporter.settings=dialog.get_settings(); self.refresh()

    def refresh(self):
        canvas=self.state.current_canvas()
        if canvas is None: self.preview.set_canvas(None); return
        extra=None
        if self.state.extra_design_path: extra=Image.open(self.state.extra_design_path).convert("RGB")
        sheet=self.state.print_exporter.build_print_sheet(canvas, self.mirror1.isChecked(), self.mirror2.isChecked(), extra, self.rotate.isChecked())
        self.preview.set_canvas(sheet)

    def export(self):
        if self.state.current_canvas() is None: QMessageBox.warning(self,"No Design","Load and edit a design first."); return
        folder=QFileDialog.getExistingDirectory(self,"Choose Export Folder")
        if not folder:return
        extra=Image.open(self.state.extra_design_path).convert("RGB") if self.state.extra_design_path else None
        name=Path(self.state.template.source_path).stem if self.state.template else "design"
        try:
            paths=self.state.print_exporter.export(self.state.current_canvas(),folder,name,self.mirror1.isChecked(),self.mirror2.isChecked(),extra,self.rotate.isChecked(),formats=("png","pdf"))
            self.status.setText("Exported:\n"+"\n".join(paths))
        except Exception as exc: QMessageBox.critical(self,"Export Failed",str(exc))


class TextPanel(QWidget):
    changed=pyqtSignal()
    def __init__(self,state,parent=None): super().__init__(parent); self.state=state; self._build()
    def _build(self):
        layout=QVBoxLayout(self); layout.addWidget(QLabel("Text tools apply directly to the live design.")); self.manual=QPushButton("Add Manual Text"); self.manual.clicked.connect(self.add_manual); layout.addWidget(self.manual); self.text3d=QLineEdit(); self.text3d.setPlaceholderText("3D text"); layout.addWidget(self.text3d); self.three=QPushButton("Add 3D Text"); self.three.clicked.connect(self.add_3d); layout.addWidget(self.three); layout.addStretch(1)
    def add_manual(self):
        if self.state.current_canvas() is None:return
        d=TextToolDialog(self)
        if d.exec():
            v=d.get_values(); w,h=self.state.current_canvas().size; self.state.canvas=self.state.template_manager.add_text(self.state.current_canvas(),v['text'],(round(w*v['pos_x_ratio']),round(h*v['pos_y_ratio'])),v['font_size'],v['color']); self.changed.emit()
    def add_3d(self):
        if self.state.current_canvas() is None or not self.text3d.text().strip():return
        layer=self.state.template_manager.generate_3d_text_stub(self.text3d.text().strip()); canvas=self.state.current_canvas().copy(); canvas.alpha_composite(layer,(50,50)); self.state.canvas=canvas; self.changed.emit()


class MockupPanel(QWidget):
    def __init__(self,state,parent=None): super().__init__(parent); self.state=state; self._last=None; self._build()
    def _build(self):
        layout=QVBoxLayout(self); self.variant=QComboBox(); [self.variant.addItem(v.name,v) for v in self.state.mockup_generator.mug_variants]; layout.addWidget(self.variant); b=QPushButton("Generate 3D Preview"); b.clicked.connect(self.generate); layout.addWidget(b); e=QPushButton("Export JPG"); e.clicked.connect(self.export); layout.addWidget(e); layout.addStretch(1)
    def generate(self):
        if self.state.current_canvas() is None:return
        self._last=self.state.mockup_generator.render_cylinder_mockup(self.state.current_canvas(),variant=self.variant.currentData()); path=MOCKUP_CACHE_DIR/'live.png'; path.parent.mkdir(parents=True,exist_ok=True); self._last.save(path); MockupPreviewDialog(str(path),self).exec()
    def export(self):
        if self._last is None:return
        path,_=QFileDialog.getSaveFileName(self,"Export JPG","mockup.jpg","JPEG (*.jpg)")
        if path:self.state.mockup_generator.export_mockup_jpg(self._last,path)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("SubliStudio v2.3"); self.resize(1500,950); self.state=SessionState(); self._build()
    def _build(self):
        tabs=QTabWidget(); self.setCentralWidget(tabs)
        self.design=DesignPanel(self.state); self.manual=ManualEditPanel(self.state); self.text=TextPanel(self.state); self.print=PrintPanel(self.state); self.mockup=MockupPanel(self.state)
        tabs.addTab(self.design,"🎨 Design"); tabs.addTab(self.manual,"✏️ Manual Edit"); tabs.addTab(self.text,"🔤 Text"); tabs.addTab(self.print,"🖨 Print"); tabs.addTab(self.mockup,"🧶 Mockup")
        self.design.template_loaded.connect(self.manual.update_frames)
        self.design.changed.connect(self._refresh_all); self.manual.changed.connect(self._refresh_all); self.text.changed.connect(self._refresh_all)
        tabs.currentChanged.connect(lambda _: self._refresh_all())
        self.statusBar().showMessage("SubliStudio v2.3 Ready")
    def _refresh_all(self):
        self.design.refresh(); self.manual.refresh(); self.print.refresh()
