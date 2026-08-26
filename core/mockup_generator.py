"""
core/mockup_generator.py (v2)

3D mockup with multiple angle variants + JPG export for WhatsApp.
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Optional, List

import numpy as np
from PIL import Image

logger = logging.getLogger("SubliStudio.MockupGenerator")


class MockupVariant:
    def __init__(self, name: str, angle_degrees: int = 0):
        self.name = name
        self.angle_degrees = angle_degrees


class MockupGenerator:
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.mug_variants = [
            MockupVariant("Front View", 0),
            MockupVariant("3/4 Angle Left", -30),
            MockupVariant("3/4 Angle Right", 30),
            MockupVariant("Side View", 90),
        ]

    def get_variants(self, product_type: str) -> List[MockupVariant]:
        if product_type.lower() == "mug":
            return self.mug_variants
        return [MockupVariant("Default", 0)]

    def render_cylinder_mockup(self, design: Image.Image, canvas_size: tuple[int, int] = (800, 800),
                                wrap_width_ratio: float = 0.55, wrap_height_ratio: float = 0.55,
                                variant: Optional[MockupVariant] = None) -> Image.Image:
        angle = variant.angle_degrees if variant else 0
        
        if angle != 0:
            design = design.rotate(angle, expand=False, resample=Image.BICUBIC)
        
        canvas_w, canvas_h = canvas_size
        canvas = Image.new("RGB", (canvas_w, canvas_h), (235, 235, 235))

        wrap_w = round(canvas_w * wrap_width_ratio)
        wrap_h = round(canvas_h * wrap_height_ratio)

        design_rgb = design.convert("RGB").resize((wrap_w, wrap_h), Image.LANCZOS)
        arr = np.asarray(design_rgb).astype(np.float32)

        xs = np.linspace(-1, 1, wrap_w)
        curve = np.cos(xs * (math.pi / 2))
        curve = np.clip(curve, 0.35, 1.0)

        shade = 0.55 + 0.45 * curve
        shade = shade[np.newaxis, :, np.newaxis]
        shaded = np.clip(arr * shade, 0, 255).astype(np.uint8)

        mask_arr = np.tile((curve * 255).astype(np.uint8), (wrap_h, 1))
        mask = Image.fromarray(mask_arr, mode="L")

        warped = Image.fromarray(shaded)
        offset = ((canvas_w - wrap_w) // 2, (canvas_h - wrap_h) // 2)
        canvas.paste(warped, offset, mask)
        return canvas

    def export_mockup_jpg(self, mockup: Image.Image, output_path: str, quality: int = 85) -> str:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        max_size = (1280, 1280)
        mockup.thumbnail(max_size, Image.LANCZOS)
        mockup.convert("RGB").save(output_path, "JPEG", quality=quality, optimize=True)
        return output_path
