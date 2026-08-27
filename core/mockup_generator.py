"""Phase 3 mockup generation with safe asset fallback rendering."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter

from core.models import PrintArea, ProductProfile


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
        area_data = data["print_area"]
        return cls(
            path=path,
            name=data["name"],
            width_px=int(data["width_px"]),
            height_px=int(data["height_px"]),
            print_area=PrintArea(
                width_mm=float(area_data["width_mm"]),
                height_mm=float(area_data["height_mm"]),
                dpi=int(area_data["dpi"]),
                bleed_mm=float(area_data.get("bleed_mm", 0)),
                safe_margin_mm=float(area_data.get("safe_margin_mm", 0)),
            ),
            transform=data.get("transform", {}),
        )


class MockupGenerator:
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._assets: Dict[str, MockupAsset] = {}

    def _asset_paths(self, asset_name: str) -> Tuple[Path, Path]:
        json_path = self.cache_dir / f"mockup_{asset_name}.json"
        return json_path, json_path.with_suffix(".png")

    def load_asset(self, profile: ProductProfile, asset_name: str) -> Optional[MockupAsset]:
        key = f"{profile.id}:{asset_name}"
        if key in self._assets:
            return self._assets[key]
        json_path, image_path = self._asset_paths(asset_name)
        if not json_path.exists() or not image_path.exists():
            return None
        with json_path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        asset = MockupAsset.from_dict(str(image_path), data)
        self._assets[key] = asset
        return asset

    def has_asset(self, profile: ProductProfile, asset_name: str) -> bool:
        return self.load_asset(profile, asset_name) is not None

    def available_assets(self, profile: ProductProfile) -> list[str]:
        return [name for name in profile.mockup_profiles if self.has_asset(profile, name)]

    def render_mockup(self, design: Image.Image, profile: ProductProfile,
                      asset_name: str, output_path: Optional[str] = None) -> Tuple[Image.Image, str]:
        asset = self.load_asset(profile, asset_name)
        if asset is None:
            return self.render_fallback_mockup(design, profile, asset_name, output_path)
        base = Image.open(asset.path).convert("RGBA")
        if base.size != (asset.width_px, asset.height_px):
            base = base.resize((asset.width_px, asset.height_px), Image.Resampling.LANCZOS)
        placed = self._prepare_design_for_area(design, profile, asset.print_area)
        transform = asset.transform
        x = int(transform.get("x", 0))
        y = int(transform.get("y", 0))
        width = int(transform.get("width", placed.width))
        height = int(transform.get("height", placed.height))
        placed = placed.resize((max(1, width), max(1, height)), Image.Resampling.LANCZOS)
        mask = self._build_mask(asset, x, y, placed.width, placed.height)
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        overlay.paste(placed, (x, y), placed)
        if mask is not None:
            clipped = Image.new("RGBA", base.size, (0, 0, 0, 0))
            clipped.paste(overlay, (0, 0), mask)
            overlay = clipped
        result = Image.alpha_composite(base, overlay)
        out_path = output_path or str(self.cache_dir / f"mockup_{profile.id.replace('.', '_')}_{asset_name}.png")
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        result.save(out_path)
        return result, out_path

    def render_fallback_mockup(self, design: Image.Image, profile: ProductProfile,
                               asset_name: str, output_path: Optional[str] = None) -> Tuple[Image.Image, str]:
        """Create an informative generic preview when a real mockup asset is absent."""
        canvas = Image.new("RGBA", (1200, 900), (242, 244, 247, 255))
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle((120, 75, 1080, 825), radius=44, fill=(224, 229, 236, 255), outline=(168, 178, 190, 255), width=5)
        is_bottle = "bottle" in asset_name.lower() or "bottle" in profile.category.lower()
        is_mug = "mug" in asset_name.lower() or "mug" in profile.category.lower()
        if is_bottle:
            body = (430, 175, 770, 745)
            draw.rounded_rectangle(body, radius=85, fill=(235, 238, 241, 255), outline=(105, 115, 125, 255), width=8)
            draw.rounded_rectangle((495, 112, 705, 215), radius=30, fill=(130, 140, 150, 255), outline=(90, 98, 108, 255), width=7)
            area = (470, 300, 730, 635)
        elif is_mug:
            draw.rounded_rectangle((310, 255, 800, 675), radius=38, fill=(235, 238, 241, 255), outline=(105, 115, 125, 255), width=8)
            draw.ellipse((745, 335, 970, 585), outline=(105, 115, 125, 255), width=24)
            area = (355, 310, 755, 620)
        else:
            draw.rounded_rectangle((340, 150, 860, 750), radius=34, fill=(235, 238, 241, 255), outline=(105, 115, 125, 255), width=8)
            area = (390, 225, 810, 670)
        placed = self._prepare_design_for_box(design, profile, area[2] - area[0], area[3] - area[1])
        canvas.alpha_composite(placed, (area[0], area[1]))
        draw = ImageDraw.Draw(canvas)
        draw.text((150, 98), f"Preview fallback — {profile.name} / {asset_name}", fill=(45, 55, 65, 255))
        draw.text((150, 790), "Add a matching PNG + JSON asset to enable the production mockup image.", fill=(70, 80, 90, 255))
        out_path = output_path or str(self.cache_dir / f"fallback_{profile.id.replace('.', '_')}_{asset_name}.png")
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        canvas.save(out_path)
        return canvas, out_path

    def _prepare_design_for_area(self, design: Image.Image, profile: ProductProfile, area: PrintArea) -> Image.Image:
        width = max(1, round(area.width_mm * area.dpi / 25.4))
        height = max(1, round(area.height_mm * area.dpi / 25.4))
        return self._prepare_design_for_box(design, profile, width, height)

    @staticmethod
    def _prepare_design_for_box(design: Image.Image, profile: ProductProfile, width: int, height: int) -> Image.Image:
        image = design.convert("RGBA")
        if profile.mirror_required:
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        placed = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        placed.alpha_composite(image, ((width - image.width) // 2, (height - image.height) // 2))
        return placed

    @staticmethod
    def _build_mask(asset: MockupAsset, x: int, y: int, width: int, height: int) -> Optional[Image.Image]:
        transform = asset.transform
        if "polygon" not in transform:
            return None
        mask = Image.new("L", (asset.width_px, asset.height_px), 0)
        points = [(int(px), int(py)) for px, py in transform["polygon"]]
        ImageDraw.Draw(mask).polygon(points, fill=255)
        return mask
