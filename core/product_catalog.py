"""Product catalog and profile-driven canvas creation.

This module defines the product catalog data structure and helpers to create
blank production canvases sized for each product profile.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

from core.models import PrintArea, ProductProfile


class ProductCatalog:
    def __init__(self, catalog_path: Optional[str] = None):
        if catalog_path is None:
            catalog_path = str(Path(__file__).resolve().parent.parent / "assets" / "products" / "catalog.json")
        self.catalog_path = catalog_path
        self._profiles: Dict[str, ProductProfile] = {}
        self._by_category: Dict[str, List[ProductProfile]] = {}
        self._load()

    def _load(self) -> None:
        path = Path(self.catalog_path)
        if not path.exists():
            self._load_default()
            return
        with path.open() as f:
            data = json.load(f)
        for item in data:
            profile = ProductProfile(
                id=item["id"],
                name=item["name"],
                category=item["category"],
                description=item.get("description", ""),
                canvas_size_px=tuple(item["canvas_size_px"]),
                print_area=PrintArea(**item["print_area"]),
                orientation=item.get("orientation", "landscape"),
                mirror_required=item.get("mirror_required", False),
                template_path=item.get("template_path", ""),
                mockup_profiles=item.get("mockup_profiles", []),
            )
            self._profiles[profile.id] = profile
            self._by_category.setdefault(profile.category, []).append(profile)

    def _load_default(self) -> None:
        defaults = [
            ProductProfile(
                id="mug.standard_11oz",
                name="11 oz Ceramic Mug",
                category="Mug",
                description="Standard 11 oz white ceramic mug",
                canvas_size_px=(2480, 1063),
                print_area=PrintArea(width_mm=203.2, height_mm=90.0, dpi=300, bleed_mm=3, safe_margin_mm=5),
                orientation="landscape",
                mirror_required=True,
                template_path="mugs/standard_11oz/templates",
                mockup_profiles=["mug_front"],
            ),
            ProductProfile(
                id="mobile_cover.iphone_17_pro",
                name="Apple iPhone 17 Pro Cover",
                category="Mobile Cover",
                description="Apple iPhone 17 Pro back cover",
                canvas_size_px=(1179, 2556),
                print_area=PrintArea(width_mm=72.0, height_mm=146.0, dpi=300, bleed_mm=2, safe_margin_mm=3),
                orientation="portrait",
                mirror_required=False,
                template_path="mobile_covers/apple/iphone_17_pro/templates",
                mockup_profiles=["mobile_back"],
            ),
        ]
        for profile in defaults:
            self._profiles[profile.id] = profile
            self._by_category.setdefault(profile.category, []).append(profile)

    def categories(self) -> List[str]:
        return sorted(self._by_category.keys())

    def by_category(self, category: str) -> List[ProductProfile]:
        return self._by_category.get(category, [])

    def get(self, profile_id: str) -> Optional[ProductProfile]:
        return self._profiles.get(profile_id)


def create_blank_canvas(profile: ProductProfile) -> Image.Image:
    width, height = profile.canvas_size_px
    return Image.new("RGBA", (width, height), (255, 255, 255, 255))
