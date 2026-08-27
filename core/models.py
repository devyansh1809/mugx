"""Core domain models for SubliStudio.

This module defines the data structures used across photo import, templates,
products, print export, and mockups.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class ProductType(Enum):
    MUG = "Mug"
    BOTTLE = "Bottle"
    TSHIRT = "T-Shirt"
    TILE = "Tile"
    CUSHION = "Cushion"
    KEYRING_ROUND = "Keyring"
    MOBILE_COVER = "Mobile Cover"


class TemplateTheme(Enum):
    BIRTHDAY = "Birthday"
    ANNIVERSARY = "Anniversary"
    WEDDING = "Wedding"
    BABY_SHOWER = "Baby Shower"
    FESTIVAL = "Festival"
    TRAVEL = "Travel"
    PET = "Pet"
    GRADUATION = "Graduation"
    PLAIN = "Plain"


class FrameShape(Enum):
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    OVAL = "oval"


@dataclass
class PhotoItem:
    path: str
    label: str
    photo_index: int


@dataclass
class FrameInfo:
    frame_id: str
    photo_index: Optional[int]
    x: int
    y: int
    width: int
    height: int
    photo_scale: float = 1.0
    photo_offset_x: int = 0
    photo_offset_y: int = 0
    shape: FrameShape = FrameShape.RECTANGLE


@dataclass
class TemplateInfo:
    source_path: str
    display_name: str
    width: int
    height: int
    is_psd: bool
    product_type: ProductType
    theme: TemplateTheme
    frames: List[FrameInfo] = field(default_factory=list)

    @property
    def frame_count(self) -> int:
        return len(self.frames)


@dataclass
class PrintArea:
    width_mm: float
    height_mm: float
    dpi: int
    bleed_mm: float = 0.0
    safe_margin_mm: float = 0.0


@dataclass
class ProductProfile:
    id: str
    name: str
    category: str
    description: str
    canvas_size_px: Tuple[int, int]
    print_area: PrintArea
    orientation: str
    mirror_required: bool
    template_path: str
    mockup_profiles: List[str] = field(default_factory=list)


@dataclass
class PrintSettings:
    dpi: int = 300
    paper_size_mm: Tuple[float, float] = (210.0, 297.0)
    margin_mm: float = 10.0
    mirror_default: bool = False
