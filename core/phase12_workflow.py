"""Phase 1 + 2 controller workflow.

This module provides a non-GUI controller that wires product selection,
template loading, photo selection, auto-fill, manual edit, effects, and
final print preview/export. It is used by both tests and the Phase1Window.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter

from core.models import FrameInfo, PhotoItem, ProductProfile, TemplateInfo, TemplateTheme
from core.photo_import_service import PhotoImportService
from core.template_manager import TemplateManager
from core.print_exporter import PrintExporter, PrintSettings
from core.product_catalog import ProductCatalog, create_blank_canvas

APP_DATA = Path.home() / ".subli_studio"
CACHE = APP_DATA / "phase12_cache"


class Phase12Workflow:
    EFFECTS = (
        "None", "Soft Glow", "Warm Light", "Cool Light", "Spotlight",
        "Vignette", "Gold Border", "White Border",
    )

    def __init__(self, catalog: Optional[ProductCatalog] = None, cache_dir: Optional[str] = None):
        self.catalog = catalog or ProductCatalog()
        self.cache_dir = Path(cache_dir) if cache_dir else CACHE
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.profile: Optional[ProductProfile] = None
        self.photos: List[PhotoItem] = []
        self.template: Optional[TemplateInfo] = None
        self.base_canvas: Optional[Image.Image] = None
        self.canvas: Optional[Image.Image] = None
        self.selected_frame = 0
        self.photo_service = PhotoImportService(str(self.cache_dir / "thumbnails"))
        self.templates = TemplateManager(str(self.cache_dir / "previews"))
        self.printer = PrintExporter()

    def select_product(self, profile_id: str) -> "DesignState":
        profile = self.catalog.get(profile_id)
        if profile is None:
            raise ValueError(f"Product profile '{profile_id}' not found.")
        self.profile = profile
        self.base_canvas = create_blank_canvas(profile)
        self.canvas = None
        self.template = None
        self.selected_frame = 0
        self.printer.settings = PrintSettings(
            dpi=profile.print_area.dpi,
            mirror_default=profile.mirror_required,
        )
        return DesignState(self)

    def select_photos(self, photos: List[PhotoItem]) -> None:
        self.photos = photos

    def load_template(self, template: TemplateInfo, base: Image.Image) -> None:
        self.template = template
        self.base_canvas = base.convert("RGBA")
        self.canvas = None

    def auto_fill(self) -> Image.Image:
        if not self.template or not self.base_canvas or not self.photos:
            raise ValueError("Select photos and load a template first.")
        self.canvas = self.templates.fill_frames(
            self.template, self.base_canvas,
            self.photos,
        )
        return self.canvas

    def edit_frame(self, index: int, scale: float, offset_x: int, offset_y: int,
                   preview_only: bool = False) -> Image.Image:
        if not self.template or not self.base_canvas:
            raise ValueError("Load a template first.")
        frame = self.template.frames[index]
        original = (frame.photo_scale, frame.photo_offset_x, frame.photo_offset_y)
        frame.photo_scale = scale
        frame.photo_offset_x = offset_x
        frame.photo_offset_y = offset_y
        mapping = {i: item.photo_index for i, item in enumerate(self.template.frames) if item.photo_index is not None}
        rendered = self.templates.fill_frames(self.template, self.base_canvas, self.photos, mapping)
        if not preview_only:
            self.canvas = rendered
        else:
            frame.photo_scale, frame.photo_offset_x, frame.photo_offset_y = original
        return rendered

    def apply_effect(self, name: str, intensity: int) -> Image.Image:
        source = self.canvas if self.canvas is not None else self.base_canvas
        if source is None:
            raise ValueError("No design canvas available.")
        amount = intensity / 100.0
        result = source.convert("RGBA").copy()
        width, height = result.size
        if name == "None":
            pass
        else:
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
            result = Image.alpha_composite(result, layer)
        self.canvas = result
        return result

    def final_print_preview(self) -> Image.Image:
        source = self.canvas if self.canvas is not None else self.base_canvas
        if source is None:
            raise ValueError("No design canvas available.")
        return self.printer.build_print_sheet(source, mirror_1=self.profile.mirror_required if self.profile else False)

    def template_directory(self) -> Path:
        if not self.profile:
            raise ValueError("No product selected.")
        return Path(self.profile.template_path)

    def configured_print_exporter(self) -> PrintExporter:
        return self.printer


class DesignState:
    def __init__(self, workflow: Phase12Workflow):
        self.workflow = workflow
        self.profile = workflow.profile
        self.base_canvas = workflow.base_canvas
