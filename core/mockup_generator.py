"""Phase 3 renderer for licensed local product mockup assets.

Real production rendering uses local PNG/JSON assets declared in the manifest.
When they are absent, the generator emits a clearly labelled illustrative
fallback instead of failing or pretending that it is a product photograph.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

from PIL import Image, ImageChops, ImageDraw

from core.mockup_asset_registry import MockupAssetRecord, MockupAssetRegistry
from core.models import ProductProfile


class MockupGenerator:
    def __init__(self, cache_dir: str, asset_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.registry = MockupAssetRegistry(asset_dir)

    def has_asset(self, profile: ProductProfile, asset_name: str) -> bool:
        record = self.registry.record(profile.id, asset_name)
        return bool(record and record.is_installed and not self.registry.validate_record(record))

    def available_assets(self, profile: ProductProfile) -> list[str]:
        return [view for view in profile.mockup_profiles if self.has_asset(profile, view)]

    def validation_errors(self, profile: ProductProfile, asset_name: str) -> list[str]:
        record = self.registry.record(profile.id, asset_name)
        if record is None:
            return ["view is not declared in assets/mockups/manifest.json"]
        return self.registry.validate_record(record)

    def render_mockup(self, design: Image.Image, profile: ProductProfile, asset_name: str,
                      output_path: Optional[str] = None) -> Tuple[Image.Image, str]:
        record = self.registry.record(profile.id, asset_name)
        if record is None or not record.is_installed or self.registry.validate_record(record):
            return self.render_fallback_mockup(design, profile, asset_name, output_path)
        result = self._render_production_asset(design, profile, record)
        destination = Path(output_path) if output_path else self.cache_dir / f"mockup_{profile.id.replace('.', '_')}_{asset_name}.png"
        destination.parent.mkdir(parents=True, exist_ok=True)
        result.save(destination)
        return result, str(destination)

    def _render_production_asset(self, design: Image.Image, profile: ProductProfile,
                                 record: MockupAssetRecord) -> Image.Image:
        metadata = record.metadata
        base = Image.open(record.image_path).convert("RGBA")
        expected = (int(metadata["width_px"]), int(metadata["height_px"]))
        if base.size != expected:
            base = base.resize(expected, Image.Resampling.LANCZOS)
        placement, origin, mask = self._placement(design, profile, base.size, metadata["print_region"])
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.alpha_composite(placement, origin)
        if mask is not None:
            layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
        texture = self._load_optional(record, metadata.get("texture"), base.size)
        if texture is not None:
            layer = Image.blend(layer, ImageChops.multiply(layer, texture), float(metadata.get("texture_strength", 0.18)))
        result = Image.alpha_composite(base, layer)
        for name in ("shadow", "highlight"):
            overlay = self._load_optional(record, metadata.get(name), base.size)
            if overlay is not None:
                result = Image.alpha_composite(result, overlay)
        return result

    def _placement(self, design: Image.Image, profile: ProductProfile, canvas_size: Tuple[int, int], region: Dict):
        if region.get("mode", "rectangle") == "polygon":
            points = [(int(p[0]), int(p[1])) for p in region["points"]]
            xs, ys = zip(*points)
            left, top, right, bottom = min(xs), min(ys), max(xs), max(ys)
            width, height = max(1, right - left), max(1, bottom - top)
            placed = self._fit_design(design, profile, width, height)
            mask = Image.new("L", canvas_size, 0)
            ImageDraw.Draw(mask).polygon(points, fill=255)
            return placed, (left, top), mask
        x, y, width, height = (int(region[key]) for key in ("x", "y", "width", "height"))
        placed = self._fit_design(design, profile, width, height)
        if region.get("surface") == "cylinder":
            placed = self._cylinder_wrap(placed, float(region.get("curve", 0.32)))
        return placed, (x, y), None

    @staticmethod
    def _fit_design(design: Image.Image, profile: ProductProfile, width: int, height: int) -> Image.Image:
        image = design.convert("RGBA")
        if profile.mirror_required:
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        result.alpha_composite(image, ((width - image.width) // 2, (height - image.height) // 2))
        return result

    @staticmethod
    def _cylinder_wrap(image: Image.Image, curve: float) -> Image.Image:
        width, height = image.size
        source = image.load()
        result = Image.new("RGBA", image.size, (0, 0, 0, 0))
        target = result.load()
        curve = max(0.0, min(0.48, curve))
        for x in range(width):
            normalized = (x / max(1, width - 1)) * 2 - 1
            source_x = max(0, min(width - 1, int(round((normalized + curve * normalized ** 3 + 1) * 0.5 * (width - 1)))))
            shade = 1.0 - curve * 0.72 * normalized * normalized
            for y in range(height):
                r, g, b, a = source[source_x, y]
                target[x, y] = (int(r * shade), int(g * shade), int(b * shade), a)
        return result

    @staticmethod
    def _load_optional(record: MockupAssetRecord, filename: Optional[str], size: Tuple[int, int]) -> Optional[Image.Image]:
        if not filename:
            return None
        path = record.image_path.parent / filename
        if not path.is_file():
            return None
        image = Image.open(path).convert("RGBA")
        return image.resize(size, Image.Resampling.LANCZOS) if image.size != size else image

    def render_fallback_mockup(self, design: Image.Image, profile: ProductProfile, asset_name: str,
                               output_path: Optional[str] = None) -> Tuple[Image.Image, str]:
        canvas = Image.new("RGBA", (1200, 900), (242, 244, 247, 255))
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle((110, 70, 1090, 830), radius=42, fill=(224, 229, 236, 255), outline=(165, 175, 187, 255), width=5)
        category = profile.category.lower()
        if "bottle" in category:
            draw.rounded_rectangle((435, 180, 765, 745), radius=84, fill=(237, 240, 243, 255), outline=(95, 105, 115, 255), width=8)
            draw.rounded_rectangle((500, 115, 700, 220), radius=28, fill=(132, 142, 152, 255))
            box = (472, 302, 728, 632)
        elif "mug" in category:
            draw.rounded_rectangle((315, 265, 800, 675), radius=38, fill=(237, 240, 243, 255), outline=(95, 105, 115, 255), width=8)
            draw.ellipse((745, 335, 970, 585), outline=(95, 105, 115, 255), width=24)
            box = (360, 315, 755, 625)
        else:
            draw.rounded_rectangle((345, 155, 855, 750), radius=34, fill=(237, 240, 243, 255), outline=(95, 105, 115, 255), width=8)
            box = (395, 230, 805, 670)
        canvas.alpha_composite(self._fit_design(design, profile, box[2] - box[0], box[3] - box[1]), (box[0], box[1]))
        draw = ImageDraw.Draw(canvas)
        draw.text((145, 102), f"ILLUSTRATIVE FALLBACK — {profile.name} / {asset_name}", fill=(55, 65, 75, 255))
        draw.text((145, 790), "Install licensed PNG + JSON asset files to enable production mockup rendering.", fill=(80, 90, 100, 255))
        destination = Path(output_path) if output_path else self.cache_dir / f"fallback_{profile.id.replace('.', '_')}_{asset_name}.png"
        destination.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(destination)
        return canvas, str(destination)
