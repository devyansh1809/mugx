"""Data-driven sublimation product catalog and print-profile engine.

Product profiles replace hard-coded canvas/mirror assumptions. A selected profile
provides the print area, DPI, bleed, safe area, template directory and supported
mockup identifiers required by Design, Print, and Mockup workflows.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

MM_PER_INCH = 25.4


@dataclass(frozen=True)
class PrintArea:
    width_mm: float
    height_mm: float
    dpi: int = 300
    bleed_mm: float = 3.0
    safe_margin_mm: float = 4.0

    @property
    def pixel_size(self) -> Tuple[int, int]:
        return (
            round(self.width_mm / MM_PER_INCH * self.dpi),
            round(self.height_mm / MM_PER_INCH * self.dpi),
        )

    @property
    def bleed_pixels(self) -> int:
        return round(self.bleed_mm / MM_PER_INCH * self.dpi)

    @property
    def safe_margin_pixels(self) -> int:
        return round(self.safe_margin_mm / MM_PER_INCH * self.dpi)


@dataclass(frozen=True)
class ProductProfile:
    id: str
    name: str
    category: str
    print_area: PrintArea
    mirror_required: bool = True
    orientation: str = "landscape"
    template_path: str = ""
    mockup_profiles: Tuple[str, ...] = ()
    description: str = ""
    tags: Tuple[str, ...] = ()

    @property
    def canvas_size_px(self) -> Tuple[int, int]:
        return self.print_area.pixel_size

    def to_dict(self) -> dict:
        data = asdict(self)
        data["mockup_profiles"] = list(self.mockup_profiles)
        data["tags"] = list(self.tags)
        return data


class ProductCatalog:
    """Loads and queries product print profiles from JSON.

    The catalog is deliberately data-driven so a new bottle or mobile-cover
    model can be added by updating catalog.json instead of changing Python UI
    logic.
    """

    def __init__(self, catalog_path: Optional[str] = None):
        if catalog_path is None:
            catalog_path = str(Path(__file__).resolve().parent.parent / "assets" / "products" / "catalog.json")
        self.catalog_path = Path(catalog_path)
        self._profiles: Dict[str, ProductProfile] = {}
        self.reload()

    def reload(self) -> None:
        self._profiles = {}
        if not self.catalog_path.exists():
            return
        data = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        for item in data.get("products", []):
            area = PrintArea(**item["print_area"])
            profile = ProductProfile(
                id=item["id"],
                name=item["name"],
                category=item["category"],
                print_area=area,
                mirror_required=item.get("mirror_required", True),
                orientation=item.get("orientation", "landscape"),
                template_path=item.get("template_path", ""),
                mockup_profiles=tuple(item.get("mockup_profiles", [])),
                description=item.get("description", ""),
                tags=tuple(item.get("tags", [])),
            )
            self._profiles[profile.id] = profile

    def all(self) -> List[ProductProfile]:
        return sorted(self._profiles.values(), key=lambda p: (p.category, p.name))

    def get(self, profile_id: str) -> ProductProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise KeyError(f"Unknown product profile: {profile_id}") from exc

    def maybe_get(self, profile_id: Optional[str]) -> Optional[ProductProfile]:
        return self._profiles.get(profile_id) if profile_id else None

    def categories(self) -> List[str]:
        return sorted({profile.category for profile in self._profiles.values()})

    def by_category(self, category: str) -> List[ProductProfile]:
        return [p for p in self.all() if p.category == category]

    def search(self, query: str) -> List[ProductProfile]:
        needle = query.lower().strip()
        if not needle:
            return self.all()
        return [
            profile for profile in self.all()
            if needle in profile.name.lower()
            or needle in profile.category.lower()
            or needle in profile.id.lower()
            or any(needle in tag.lower() for tag in profile.tags)
        ]

    def default_for_category(self, category: str) -> Optional[ProductProfile]:
        profiles = self.by_category(category)
        return profiles[0] if profiles else None


def create_blank_canvas(profile: ProductProfile, color=(255, 255, 255, 255)):
    """Create a product-sized RGBA canvas at the profile's production DPI."""
    from PIL import Image
    return Image.new("RGBA", profile.canvas_size_px, color)
