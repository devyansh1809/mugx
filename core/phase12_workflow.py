"""Phase 1+2 integration service.

This service binds the data-driven ProductCatalog to the existing design,
print and mockup services. It is deliberately GUI-independent so the complete
workflow is unit-testable on macOS/Linux CI without a display server.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFilter

from core.models import PhotoItem, TemplateInfo
from core.product_catalog import ProductCatalog, ProductProfile, create_blank_canvas
from core.template_manager import TemplateManager
from core.print_exporter import PrintExporter, PrintSettings
from core.mockup_generator import MockupGenerator


@dataclass
class WorkflowState:
    profile: ProductProfile
    template: Optional[TemplateInfo] = None
    photos: List[PhotoItem] = field(default_factory=list)
    base_canvas: Optional[Image.Image] = None
    design_canvas: Optional[Image.Image] = None
    selected_frame: int = 0
    background_path: Optional[str] = None

    def current_canvas(self) -> Image.Image:
        if self.design_canvas is not None:
            return self.design_canvas
        if self.base_canvas is not None:
            return self.base_canvas
        raise ValueError("No design canvas has been created.")


class Phase12Workflow:
    """Testable controller for product-aware Phase 1 design flow.

    Responsibilities:
    - Select a ProductProfile and create a product-sized blank canvas.
    - Expose a profile-specific template directory.
    - Keep selected-photo order intact for auto-fill.
    - Apply product DPI/mirroring rules to PrintExporter.
    - Resolve profile mockup variants.
    - Provide non-destructive preview helpers for effects/backgrounds.
    """

    def __init__(self, catalog: Optional[ProductCatalog] = None, cache_dir: Optional[str] = None):
        self.catalog = catalog or ProductCatalog()
        root = Path(cache_dir or (Path.home() / ".subli_studio" / "phase12"))
        self.templates = TemplateManager(str(root / "previews"))
        self.mockups = MockupGenerator(str(root / "mockups"))
        self.state: Optional[WorkflowState] = None

    def select_product(self, profile_id: str) -> WorkflowState:
        profile = self.catalog.get(profile_id)
        blank = create_blank_canvas(profile)
        self.state = WorkflowState(profile=profile, base_canvas=blank)
        return self.state

    def template_directory(self) -> Path:
        if not self.state:
            raise ValueError("Select a product first.")
        return Path(self.state.profile.template_path)

    def select_photos(self, photos: List[PhotoItem]) -> None:
        if not self.state:
            raise ValueError("Select a product first.")
        if not photos:
            raise ValueError("Select at least one photo.")
        self.state.photos = list(photos)

    def load_template(self, template: TemplateInfo, base_canvas: Image.Image) -> None:
        if not self.state:
            raise ValueError("Select a product first.")
        self.state.template = template
        self.state.base_canvas = base_canvas.convert("RGBA").copy()
        self.state.design_canvas = None
        self.state.selected_frame = 0

    def auto_fill(self, photo_count: Optional[int] = None) -> Image.Image:
        if not self.state or not self.state.template:
            raise ValueError("Load a template first.")
        selected = self.state.photos[:photo_count] if photo_count else self.state.photos
        self.state.design_canvas = self.templates.fill_frames(
            self.state.template, self.state.base_canvas, selected
        )
        return self.state.design_canvas

    def edit_frame(self, frame_index: int, scale: float, offset_x: int, offset_y: int, preview_only: bool = False) -> Image.Image:
        if not self.state or not self.state.template:
            raise ValueError("Load and auto-fill a template first.")
        if frame_index < 0 or frame_index >= self.state.template.frame_count:
            raise ValueError("Invalid frame index.")
        frame = self.state.template.frames[frame_index]
        original = (frame.photo_scale, frame.photo_offset_x, frame.photo_offset_y)
        frame.photo_scale, frame.photo_offset_x, frame.photo_offset_y = scale, offset_x, offset_y
        mapping = {i: f.photo_index for i, f in enumerate(self.state.template.frames) if f.photo_index is not None}
        rendered = self.templates.fill_frames(self.state.template, self.state.base_canvas, self.state.photos, mapping)
        if preview_only:
            frame.photo_scale, frame.photo_offset_x, frame.photo_offset_y = original
        else:
            self.state.design_canvas = rendered
            self.state.selected_frame = frame_index
        return rendered

    def preview_background(self, path: str, blur_amount: int = 0) -> Image.Image:
        if not self.state:
            raise ValueError("Select a product first.")
        return self.templates.change_background_with_preview(self.state.current_canvas(), path, blur_amount)

    def apply_background(self, path: str, blur_amount: int = 0) -> Image.Image:
        result = self.preview_background(path, blur_amount)
        self.state.design_canvas = result
        self.state.background_path = path
        return result

    @staticmethod
    def effect_preview(canvas: Image.Image, effect: str, intensity: int = 50) -> Image.Image:
        amount = max(0.0, min(1.0, intensity / 100.0))
        result = canvas.convert("RGBA").copy()
        width, height = result.size
        if effect == "None":
            return result
        layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        if effect == "Soft Glow":
            draw.ellipse((-width // 4, -height // 4, width * 5 // 4, height * 5 // 4), fill=(255, 255, 255, round(95 * amount)))
            layer = layer.filter(ImageFilter.GaussianBlur(max(5, min(width, height) // 12)))
        elif effect == "Warm Light":
            draw.rectangle((0, 0, width, height), fill=(255, 155, 60, round(100 * amount)))
        elif effect == "Cool Light":
            draw.rectangle((0, 0, width, height), fill=(70, 165, 255, round(90 * amount)))
        elif effect == "Spotlight":
            draw.ellipse((width // 4, height // 6, width * 3 // 4, height * 5 // 6), fill=(255, 255, 220, round(145 * amount)))
            layer = layer.filter(ImageFilter.GaussianBlur(max(8, min(width, height) // 10)))
        elif effect == "Vignette":
            draw.rectangle((5, 5, width - 6, height - 6), outline=(0, 0, 0, round(185 * amount)), width=max(8, min(width, height) // 10))
        elif effect == "Gold Border":
            draw.rectangle((5, 5, width - 6, height - 6), outline=(230, 180, 35, 255), width=max(4, round(15 * amount)))
        elif effect == "White Border":
            draw.rectangle((5, 5, width - 6, height - 6), outline=(255, 255, 255, 255), width=max(4, round(15 * amount)))
        else:
            raise ValueError(f"Unknown effect: {effect}")
        return Image.alpha_composite(result, layer)

    def apply_effect(self, effect: str, intensity: int = 50) -> Image.Image:
        if not self.state:
            raise ValueError("Select a product first.")
        self.state.design_canvas = self.effect_preview(self.state.current_canvas(), effect, intensity)
        return self.state.design_canvas

    def configured_print_exporter(self) -> PrintExporter:
        if not self.state:
            raise ValueError("Select a product first.")
        profile = self.state.profile
        settings = PrintSettings(
            dpi=profile.print_area.dpi,
            mirror_default=profile.mirror_required,
        )
        return PrintExporter(settings)

    def final_print_preview(self, mirror_override: Optional[bool] = None, extra_design: Optional[Image.Image] = None, extra_mirror: bool = False, extra_rotate: bool = False) -> Image.Image:
        if not self.state:
            raise ValueError("Select a product first.")
        exporter = self.configured_print_exporter()
        primary_mirror = self.state.profile.mirror_required if mirror_override is None else mirror_override
        return exporter.build_print_sheet(
            self.state.current_canvas(),
            mirror_1=primary_mirror,
            mirror_2=extra_mirror,
            extra_design=extra_design,
            extra_design_rotate=extra_rotate,
        )

    def mockup_variants(self):
        if not self.state:
            raise ValueError("Select a product first.")
        category = self.state.profile.category.lower()
        # Existing generator has mug variants; this preserves profile-specific
        # identifiers now and permits product-specific renderer expansion later.
        return self.mockups.get_variants("mug" if category == "mug" else category)
