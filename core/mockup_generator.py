"""Phase 3 mockup generator.

Renders the final design onto product mockup images using profile-defined
mockup assets and print-area geometry.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from core.models import ProductProfile, PrintArea


class MockupAsset:
    def __init__(self, path: str, name: str, width_px: int, height_px: int,
                 print_area: PrintArea, transform: Dict[str, Any]):
        self.path = path
        self.name = name
        self.width_px = width_px
        self.height_px = height_px
        self.print_area = print_area
        self.transform = transform

    @classmethod
    def from_dict(cls, path: str, data: Dict[str, Any]) -> "MockupAsset":
        area = PrintArea(
            width_mm=data["print_area"]["width_mm"],
            height_mm=data["print_area"]["height_mm"],
            dpi=data["print_area"]["dpi"],
            bleed_mm=data["print_area"].get("bleed_mm", 0),
            safe_margin_mm=data["print_area"].get("safe_margin_mm", 0),
        )
        return cls(
            path=path,
            name=data["name"],
            width_px=data["width_px"],
            height_px=data["height_px"],
            print_area=area,
            transform=data.get("transform", {}),
        )


class MockupGenerator:
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._assets: Dict[str, MockupAsset] = {}

    def load_asset(self, profile: ProductProfile, asset_name: str) -> Optional[MockupAsset]:
        key = f"{profile.id}:{asset_name}"
        if key in self._assets:
            return self._assets[key]
        asset_path = self.cache_dir / f"mockup_{asset_name}.json"
        if not asset_path.exists():
            return None
        with asset_path.open() as f:
            data = json.load(f)
        asset = MockupAsset.from_dict(str(asset_path.with_suffix(".png")), data)
        self._assets[key] = asset
        return asset

    def render_mockup(self, design: Image.Image, profile: ProductProfile,
                      asset_name: str, output_path: Optional[str] = None) -> Tuple[Image.Image, str]:
        asset = self.load_asset(profile, asset_name)
        if asset is None:
            raise ValueError(f"Mockup asset '{asset_name}' not found for product '{profile.id}'.")
        base = Image.open(asset.path).convert("RGBA")
        if base.size != (asset.width_px, asset.height_px):
            base = base.resize((asset.width_px, asset.height_px), Image.Resampling.LANCZOS)
        design_for_print = self._prepare_design_for_print(design, profile, asset)
        mask = self._build_mask(asset)
        result = base.copy()
        result.paste(design_for_print, (0, 0), mask)
        out_path = output_path or str(self.cache_dir / f"mockup_{profile.id}_{asset_name}.png")
        result.save(out_path)
        return result, out_path

    def _prepare_design_for_print(self, design: Image.Image, profile: ProductProfile,
                                   asset: MockupAsset) -> Image.Image:
        print_w_px = int(asset.print_area.width_mm * asset.print_area.dpi / 25.4)
        print_h_px = int(asset.print_area.height_mm * asset.print_area.dpi / 25.4)
        resized = design.resize((print_w_px, print_h_px), Image.Resampling.LANCZOS)
        if profile.mirror_required:
            resized = resized.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        return resized

    def _build_mask(self, asset: MockupAsset) -> Image.Image:
        transform = asset.transform
        if "polygon" in transform:
            mask = Image.new("L", (asset.width_px, asset.height_px), 0)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(mask)
            points = [(int(x), int(y)) for x, y in transform["polygon"]]
            draw.polygon(points, fill=255)
            return mask
        w, h = asset.width_px, asset.height_px
        x = int(transform.get("x", 0))
        y = int(transform.get("y", 0))
        mw = int(transform.get("width", w))
        mh = int(transform.get("height", h))
        mask = Image.new("L", (w, h), 0)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(mask)
        draw.rectangle((x, y, x + mw, y + mh), fill=255)
        return mask
