"""Product-aware Phase 1 desktop workflow.

Phase 1: exact-photo selection, template auto-fill, live manual edit/effect
preview, and final print preview/export.
Phase 2: data-driven ProductCatalog category/model selection controls the
blank canvas, template path, print DPI/mirroring, safe/bleed values, and
mockup profile information.
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

from core.models import PhotoItem, TemplateInfo, TemplateTheme
from core.photo_import_service import PhotoImportService
from core.template_manager import TemplateManager
from core.print_exporter import PrintExporter, PrintSettings
from core.mockup_generator import MockupGenerator
from core.product_catalog import ProductCatalog, ProductProfile, create_blank_canvas
from ui.photo_selection_dialog import PhotoSelectionDialog
from ui.live_canvas_preview import LiveCanvasPreview
from ui.print_settings_dialog import PrintSettingsDialog

APP_DATA = Path.home() / ".subli_studio"
CACHE = APP_DATA / "phase12_cache"


class DesignState:
    def __init__(self):
        self.catalog = ProductCatalog()
        self.profile: Optional[ProductProfile] = None
        self.photos: List[PhotoItem] = []
        self.template: Optional[TemplateInfo] = None
        self.base_canvas: Optional[Image.Image] = None
        self.canvas: Optional[Image.Image] = None
        self.background_path: Optional[str] = None
        self.extra_design_path: Optional[str] = None
        self.selected_frame = 0
        self.photo_service = PhotoImportService(str(CACHE / "thumbnails"))
        self.templates = TemplateManager(str(CACHE / "previews"))
        self.mockups = MockupGenerator(str(CACHE / "mockups"))
        self.printer = PrintExporter()

    def current_canvas(self) -> Optional[Image.Image]:
        return self.canvas if self.canvas is not None else self.base_canvas

    def set_profile(self, profile: ProductProfile) -> None:
        self.profile = profile
        self.base_canvas = create_blank_canvas(profile)
        self.canvas = None
        self.template = None
        self.selected_frame = 0
        self.printer.settings = PrintSettings(
            dpi=profile.print_area.dpi,
            mirror_default=profile.mirror_required,
        )


class Phase1Window(QMainWindow):
    EFFECTS = (
        "None", "Soft Glow", "Warm Light", "Cool Light", "Spotlight",
        "Vignette", "Gold Border", "White Border",
    )

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SubliStudio — Phase 1 + 2")
        self.resize(1500, 940)
        self.state = DesignState()
        self._build()
        self._populate_categories()

    def _build(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.addTab(self._build_design_tab(), "1. Design")
        self.tabs.addTab(self._build_edit_tab(), "2. Manual Edit")
        self.tabs.addTab(self._build_print_tab(), "3. Print Preview")
        self.tabs.currentChanged.connect(lambda _index: self.refresh_all())
        self.statusBar().showMessage("Select a product profile, then choose photos and a template.")

    def _build_design_tab(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        product_box = QGroupBox("A. Product Profile")
        product_grid = QGridLayout(product_box)
        product_grid.addWidget(QLabel("Category:"), 0, 0)
        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self._populate_models)
        product_grid.addWidget(self.category_combo, 0, 1)
        product_grid.addWidget(QLabel("Product model:"), 0, 2)
        self.model_combo = QComboBox()
        self.model_combo.currentIndexChanged.connect(self._on_profile_changed)
        product_grid.addWidget(self.model_combo, 0, 3)
        self.new_blank_button = QPushButton("New Blank Product Design")
        self.new_blank_button.clicked.connect(self._new_blank_design)
        product_grid.addWidget(self.new_blank_button, 1, 0, 1, 2)
        self.profile_info = QLabel("Select a product model.")
        self.profile_info.setWordWrap(True)
        product_grid.addWidget(self.profile_info, 1, 2, 1, 2)
        root.addWidget(product_box)

        photos_box = QGroupBox("B. Select Exact Customer Photos")
        row = QHBoxLayout(photos_box)
        folder = QPushButton("Choose Folder → Select Thumbnails")
        folder.clicked.connect(self.choose_folder)
        row.addWidget(folder)
        files = QPushButton("Select Individual Image Files")
        files.clicked.connect(self.choose_files)
        row.addWidget(files)
        row.addStretch(1)
        self.photo_label = QLabel("0 photos selected")
        row.addWidget(self.photo_label)
        root.addWidget(photos_box)

        template_box = QGroupBox("C. Product-Aware Template")
        template_grid = QGridLayout(template_box)
        self.template_path_label = QLabel("Template folder: select a product")
        self.template_path_label.setWordWrap(True)
        template_grid.addWidget(self.template_path_label, 0, 0, 1, 3)
        self.template_btn = QPushButton("Load Template PSD / Image")
        self.template_btn.clicked.connect(self.choose_template)
        template_grid.addWidget(self.template_btn, 1, 0)
        template_grid.addWidget(QLabel("Theme:"), 1, 1)
        self.theme_combo = QComboBox()
        for theme in TemplateTheme:
            self.theme_combo.addItem(theme.value, theme)
        template_grid.addWidget(self.theme_combo, 1, 2)
        self.template_label = QLabel("No template loaded")
        template_grid.addWidget(self.template_label, 2, 0, 1, 3)
        root.addWidget(template_box)

        fill_box = QGroupBox("D. Auto Fill")
        fill_row = QHBoxLayout(fill_box)
        fill_row.addWidget(QLabel("Use selected photos:"))
        self.fill_count = QSpinBox()
        self.fill_count.setRange(1, 1)
        fill_row.addWidget(self.fill_count)
        self.fill_btn = QPushButton("Auto Fill")
        self.fill_btn.clicked.connect(self.auto_fill)
        fill_row.addWidget(self.fill_btn)
        fill_row.addStretch(1)
        root.addWidget(fill_box)

        root.addWidget(QLabel("Current product design"))
        self.design_preview = LiveCanvasPreview("Select a product profile to create a production canvas")
        root.addWidget(self.design_preview, 1)
        return page

    def _build_edit_tab(self) -> QWidget:
        page = QWidget()
        split = QSplitter(Qt.Orientation.Horizontal)
        controls = QWidget()
        left = QVBoxLayout(controls)
        left.setContentsMargins(16, 12, 12, 12)

        frame_box = QGroupBox("Photo Frame Position / Crop")
        grid = QGridLayout(frame_box)
        grid.addWidget(QLabel("Frame:"), 0, 0)
        self.frame_spin = QSpinBox()
        self.frame_spin.setRange(1, 1)
        self.frame_spin.valueChanged.connect(self._select_frame)
        grid.addWidget(self.frame_spin, 0, 1)
        grid.addWidget(QLabel("Scale:"), 1, 0)
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.5, 2.5)
        self.scale_spin.setValue(1.0)
        self.scale_spin.setSingleStep(0.05)
        self.scale_spin.valueChanged.connect(self._preview_frame)
        grid.addWidget(self.scale_spin, 1, 1)
        grid.addWidget(QLabel("Move X:"), 2, 0)
        self.x_spin = QSpinBox()
        self.x_spin.setRange(-500, 500)
        self.x_spin.valueChanged.connect(self._preview_frame)
        grid.addWidget(self.x_spin, 2, 1)
        grid.addWidget(QLabel("Move Y:"), 3, 0)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(-500, 500)
        self.y_spin.valueChanged.connect(self._preview_frame)
        grid.addWidget(self.y_spin, 3, 1)
        apply_frame = QPushButton("Apply Frame Change")
        apply_frame.clicked.connect(self._apply_frame)
        grid.addWidget(apply_frame, 4, 0, 1, 2)
        left.addWidget(frame_box)

        effect_box = QGroupBox("Box / Light Effects")
        effect_layout = QVBoxLayout(effect_box)
        self.effect_combo = QComboBox()
        self.effect_combo.addItems(self.EFFECTS)
        self.effect_combo.currentTextChanged.connect(self._preview_effect)
        effect_layout.addWidget(self.effect_combo)
        effect_layout.addWidget(QLabel("Intensity"))
        self.effect_intensity = QSlider(Qt.Orientation.Horizontal)
        self.effect_intensity.setRange(10, 100)
        self.effect_intensity.setValue(50)
        self.effect_intensity.valueChanged.connect(self._preview_effect)
        effect_layout.addWidget(self.effect_intensity)
        apply_effect = QPushButton("Apply Effect")
        apply_effect.clicked.connect(self._apply_effect)
        effect_layout.addWidget(apply_effect)
        left.addWidget(effect_box)
        left.addStretch(1)
        self.edit_status = QLabel("Click a frame in the preview, adjust it, and preview before applying.")
        self.edit_status.setWordWrap(True)
        left.addWidget(self.edit_status)

        viewer = QWidget()
        right = QVBoxLayout(viewer)
        right.setContentsMargins(12, 12, 16, 12)
        right.addWidget(QLabel("Live Manual Edit Preview"))
        self.edit_preview = LiveCanvasPreview("Load and Auto Fill a template first")
        self.edit_preview.frame_clicked.connect(self._click_frame)
        right.addWidget(self.edit_preview, 1)
        split.addWidget(controls)
        split.addWidget(viewer)
        split.setSizes([390, 1010])
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(split)
        return page

    def _build_print_tab(self) -> QWidget:
        page = QWidget()
        split = QSplitter(Qt.Orientation.Horizontal)
        controls = QWidget()
        left = QVBoxLayout(controls)
        left.setContentsMargins(16, 12, 12, 12)

        profile_box = QGroupBox("Selected Product Print Rule")
        profile_layout = QVBoxLayout(profile_box)
        self.print_profile_label = QLabel("No product selected")
        self.print_profile_label.setWordWrap(True)
        profile_layout.addWidget(self.print_profile_label)
        left.addWidget(profile_box)

        mirror_box = QGroupBox("Mirror Settings")
        mirror_layout = QVBoxLayout(mirror_box)
        self.primary_mirror = QCheckBox("Mirror primary design")
        self.primary_mirror.toggled.connect(self.refresh_print)
        self.extra_mirror = QCheckBox("Mirror extra design")
        self.extra_mirror.toggled.connect(self.refresh_print)
        mirror_layout.addWidget(self.primary_mirror)
        mirror_layout.addWidget(self.extra_mirror)
        left.addWidget(mirror_box)

        settings = QPushButton("Paper / DPI Settings")
        settings.clicked.connect(self._open_print_settings)
        left.addWidget(settings)
        export = QPushButton("Export Final Preview as PNG + PDF")
        export.clicked.connect(self._export_print)
        left.addWidget(export)
        left.addStretch(1)
        self.print_status = QLabel("This preview uses the same renderer as final export.")
        self.print_status.setWordWrap(True)
        left.addWidget(self.print_status)

        viewer = QWidget()
        right = QVBoxLayout(viewer)
        right.setContentsMargins(12, 12, 16, 12)
        right.addWidget(QLabel("Final Print Preview"))
        self.print_preview = LiveCanvasPreview("Select a product and create a design first")
        right.addWidget(self.print_preview, 1)
        split.addWidget(controls)
        split.addWidget(viewer)
        split.setSizes([390, 1010])
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(split)
        return page

    def _populate_categories(self) -> None:
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItems(self.state.catalog.categories())
        self.category_combo.blockSignals(False)
        self._populate_models(self.category_combo.currentText())

    def _populate_models(self, category: str) -> None:
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        for profile in self.state.catalog.by_category(category):
            self.model_combo.addItem(profile.name, profile.id)
        self.model_combo.blockSignals(False)
        self._on_profile_changed()

    def _on_profile_changed(self) -> None:
        profile_id = self.model_combo.currentData()
        if not profile_id:
            return
        profile = self.state.catalog.get(profile_id)
        self.state.set_profile(profile)
        width, height = profile.canvas_size_px
        self.profile_info.setText(
            f"{profile.description}\nCanvas: {width} × {height} px | "
            f"{profile.print_area.width_mm} × {profile.print_area.height_mm} mm @ {profile.print_area.dpi} DPI | "
            f"Bleed {profile.print_area.bleed_mm} mm | Safe margin {profile.print_area.safe_margin_mm} mm | "
            f"Mirror default: {'On' if profile.mirror_required else 'Off'}"
        )
        self.template_path_label.setText(f"Compatible template folder: {profile.template_path}")
        self.primary_mirror.blockSignals(True)
        self.primary_mirror.setChecked(profile.mirror_required)
        self.primary_mirror.blockSignals(False)
        mockups = ', '.join(profile.mockup_profiles) or 'No mockup profile assigned'
        self.print_profile_label.setText(
            f"{profile.name}\nDPI: {profile.print_area.dpi}\n"
            f"Mirror default: {'On' if profile.mirror_required else 'Off'}\n"
            f"Mockup profiles: {mockups}"
        )
        self.frame_spin.setRange(1, 1)
        self.refresh_all()
        self.statusBar().showMessage(f"Selected {profile.name}. You may create a blank design or load a compatible template.")

    def _new_blank_design(self) -> None:
        if not self.state.profile:
            return
        self.state.base_canvas = create_blank_canvas(self.state.profile)
        self.state.canvas = self.state.base_canvas.copy()
        self.state.template = None
        self.refresh_all()
        self.statusBar().showMessage("Created blank product-sized design canvas.")

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose photo folder", self.state.photo_service.get_last_folder() or "")
        if not folder:
            return
        self.state.photo_service.save_last_folder(folder)
        self._select_photos(self.state.photo_service.scan_folder(folder))

    def choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Choose image files", "",
            "Images (*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.gif *.heic *.heif)",
        )
        self._select_photos([PhotoItem(path, f"{index + 1:02d}", index) for index, path in enumerate(paths)])

    def _select_photos(self, candidates: List[PhotoItem]) -> None:
        if not candidates:
            QMessageBox.warning(self, "No photos", "No supported photos were selected.")
            return
        dialog = PhotoSelectionDialog(candidates, self.state.photo_service, self)
        if dialog.exec():
            self.state.photos = dialog.selected_photos()
            self.photo_label.setText(f"{len(self.state.photos)} selected photo(s)")
            self.fill_count.setRange(1, max(1, len(self.state.photos)))
            self.fill_count.setValue(len(self.state.photos))

    def choose_template(self) -> None:
        start_dir = self.state.profile.template_path if self.state.profile else ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose product template", start_dir,
            "Templates (*.psd *.psb *.png *.jpg *.jpeg *.tiff)",
        )
        if not path:
            return
        profile = self.state.profile
        info, preview_path = self.state.templates.load_template(path, self._legacy_product_type(profile), self.theme_combo.currentData())
        if not info or not preview_path:
            QMessageBox.critical(self, "Template error", "Could not load this template.")
            return
        self.state.template = info
        self.state.base_canvas = Image.open(preview_path).convert("RGBA")
        self.state.canvas = None
        self.template_label.setText(f"Loaded {info.display_name}: {info.frame_count} frame(s)")
        self.frame_spin.setRange(1, max(1, info.frame_count))
        self.refresh_all()

    @staticmethod
    def _legacy_product_type(profile: Optional[ProductProfile]):
        from core.models import ProductType
        mapping = {
            "Mug": ProductType.MUG,
            "Bottle": ProductType.BOTTLE,
            "T-Shirt": ProductType.TSHIRT,
            "Tile": ProductType.TILE,
            "Cushion": ProductType.CUSHION,
            "Keyring": ProductType.KEYRING_ROUND,
            "Mobile Cover": ProductType.MOBILE_COVER,
        }
        return mapping.get(profile.category if profile else "Mug", ProductType.MUG)

    def auto_fill(self) -> None:
        if not self.state.template or not self.state.base_canvas or not self.state.photos:
            QMessageBox.warning(self, "Missing input", "Select photos and a product template first.")
            return
        try:
            self.state.canvas = self.state.templates.fill_frames(
                self.state.template, self.state.base_canvas,
                self.state.photos[:self.fill_count.value()],
            )
            self.refresh_all()
            self.statusBar().showMessage("Auto Fill complete. Use Manual Edit to refine the selected frames.")
        except Exception as exc:
            QMessageBox.critical(self, "Auto Fill error", str(exc))

    def _click_frame(self, index: int) -> None:
        self.frame_spin.setValue(index + 1)

    def _select_frame(self) -> None:
        if not self.state.template:
            return
        index = self.frame_spin.value() - 1
        self.state.selected_frame = index
        frame = self.state.template.frames[index]
        for widget, value in ((self.scale_spin, frame.photo_scale), (self.x_spin, frame.photo_offset_x), (self.y_spin, frame.photo_offset_y)):
            widget.blockSignals(True)
            widget.setValue(value)
            widget.blockSignals(False)
        self.refresh_edit()

    def _require_template_design(self) -> bool:
        if not self.state.template or not self.state.base_canvas:
            QMessageBox.warning(self, "No template design", "Load a template and use Auto Fill first.")
            return False
        return True

    def _render_frame(self, apply: bool) -> Optional[Image.Image]:
        if not self._require_template_design():
            return None
        index = self.frame_spin.value() - 1
        frame = self.state.template.frames[index]
        original = (frame.photo_scale, frame.photo_offset_x, frame.photo_offset_y)
        frame.photo_scale = self.scale_spin.value()
        frame.photo_offset_x = self.x_spin.value()
        frame.photo_offset_y = self.y_spin.value()
        mapping = {i: item.photo_index for i, item in enumerate(self.state.template.frames) if item.photo_index is not None}
        rendered = self.state.templates.fill_frames(self.state.template, self.state.base_canvas, self.state.photos, mapping)
        if not apply:
            frame.photo_scale, frame.photo_offset_x, frame.photo_offset_y = original
        else:
            self.state.canvas = rendered
        return rendered

    def _preview_frame(self) -> None:
        preview = self._render_frame(apply=False)
        if preview is not None:
            self.edit_preview.set_canvas(preview, self.state.template.frames, self.state.selected_frame)
            self.edit_status.setText("Frame preview only. Click Apply Frame Change to keep it.")

    def _apply_frame(self) -> None:
        if self._render_frame(apply=True) is not None:
            self.edit_status.setText("Frame change applied.")
            self.refresh_all()

    def _effect_canvas(self, source: Image.Image) -> Image.Image:
        name = self.effect_combo.currentText()
        amount = self.effect_intensity.value() / 100.0
        result = source.convert("RGBA").copy()
        width, height = result.size
        if name == "None":
            return result
        layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        if name == "Soft Glow":
            draw.ellipse((-width // 4, -height // 4, width * 5 // 4, height * 5 // 4), fill=(255, 255, 255, round(95 * amount)))
            layer = layer.filter(ImageFilter.GaussianBlur(max(5, min(width, height) // 12)))
        elif name == "Warm Light":
            draw.rectangle((0, 0, width, height), fill=(255, 155, 60, round(100 * amount)))
        elif name == "Cool Light":
            draw.rectangle((0, 0, width, height), fill=(70, 165, 255, round(90 * amount)))
        elif name == "Spotlight":
            draw.ellipse((width // 4, height // 6, width * 3 // 4, height * 5 // 6), fill=(255, 255, 220, round(145 * amount)))
            layer = layer.filter(ImageFilter.GaussianBlur(max(8, min(width, height) // 10)))
        elif name == "Vignette":
            draw.rectangle((5, 5, width - 6, height - 6), outline=(0, 0, 0, round(185 * amount)), width=max(8, min(width, height) // 10))
        elif name == "Gold Border":
            draw.rectangle((5, 5, width - 6, height - 6), outline=(230, 180, 35, 255), width=max(4, round(15 * amount)))
        elif name == "White Border":
            draw.rectangle((5, 5, width - 6, height - 6), outline=(255, 255, 255, 255), width=max(4, round(15 * amount)))
        return Image.alpha_composite(result, layer)

    def _preview_effect(self) -> None:
        source = self.state.current_canvas()
        if source is None:
            return
        self.edit_preview.set_canvas(self._effect_canvas(source), self.state.template.frames if self.state.template else [], self.state.selected_frame)
        self.edit_status.setText("Effect preview only. Click Apply Effect to keep it.")

    def _apply_effect(self) -> None:
        source = self.state.current_canvas()
        if source is None:
            return
        self.state.canvas = self._effect_canvas(source)
        self.edit_status.setText("Effect applied.")
        self.refresh_all()

    def _open_print_settings(self) -> None:
        dialog = PrintSettingsDialog(self, self.state.printer.settings)
        if dialog.exec():
            self.state.printer.settings = dialog.get_settings()
            self.refresh_print()

    def refresh_edit(self) -> None:
        self.edit_preview.set_canvas(
            self.state.current_canvas(),
            self.state.template.frames if self.state.template else [],
            self.state.selected_frame,
        )

    def refresh_print(self) -> None:
        source = self.state.current_canvas()
        if source is None:
            self.print_preview.set_canvas(None)
            return
        sheet = self.state.printer.build_print_sheet(
            source,
            mirror_1=self.primary_mirror.isChecked(),
            mirror_2=self.extra_mirror.isChecked(),
        )
        self.print_preview.set_canvas(sheet)

    def refresh_all(self) -> None:
        self.design_preview.set_canvas(
            self.state.current_canvas(),
            self.state.template.frames if self.state.template else [],
            self.state.selected_frame,
        )
        self.refresh_edit()
        self.refresh_print()

    def _export_print(self) -> None:
        source = self.state.current_canvas()
        if source is None:
            QMessageBox.warning(self, "No design", "Create a blank design or Auto Fill a template first.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Choose export folder")
        if not folder:
            return
        name = Path(self.state.template.source_path).stem if self.state.template else self.state.profile.id.replace('.', '_')
        try:
            paths = self.state.printer.export(
                source, folder, name,
                mirror_1=self.primary_mirror.isChecked(),
                mirror_2=self.extra_mirror.isChecked(),
                formats=("png", "pdf"),
            )
            self.print_status.setText("Exported the final preview:\n" + "\n".join(paths))
        except Exception as exc:
            QMessageBox.critical(self, "Export error", str(exc))
