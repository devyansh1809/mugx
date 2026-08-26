"""
core/mockup_generator.py

3D-ish product mockup preview proof-of-concept. No PyQt imports.
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger("SubliStudio.MockupGenerator")


class MockupGenerator:
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def render_cylinder_mockup(self, design: Image.Image, canvas_size: tuple[int, int] = (800, 800),
                                wrap_width_ratio: float = 0.55, wrap_height_ratio: float = 0.55) -> Image.Image:
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

    def render_smart_object_mockup(self, mockup_psd_path: str, design: Image.Image) -> Image.Image:
        from psd_tools import PSDImage

        psd = PSDImage.open(mockup_psd_path)
        smart_object_layer = None

        def _walk(layers):
            nonlocal smart_object_layer
            for layer in layers:
                if getattr(layer, "is_group", False):
                    _walk(layer)
                    continue
                if getattr(layer, "kind", "") == "smartobject":
                    smart_object_layer = layer
                    return

        _walk(psd)
        if smart_object_layer is None:
            raise NotImplementedError(
                "No Smart Object layer found in mockup PSD -- use render_cylinder_mockup() as a fallback."
            )

        raise NotImplementedError(
            "Smart Object pixel replacement is not supported by the installed psd-tools write API "
            "for this mockup file. Use render_cylinder_mockup() for now."
        )
