"""
core/models.py

Framework-free data models shared across the SubliStudio core services.
No PyQt imports here -- see architecture notes in README.md ("core/ has
zero PyQt imports").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple, List, Dict, Any


class ProductType(Enum):
    MUG = "Mug"
    BOTTLE = "Bottle"
    TSHIRT = "T-shirt"
    TILE = "Tile"
    CUSHION = "Cushion"
    KEYRING = "Keyring"
    MOBILE_COVER = "Mobile Cover"


@dataclass
class PhotoItem:
    original_path: str
    sequence_name: str
    index: int


@dataclass
class FrameInfo:
    name: str
    left: int
    top: int
    width: int
    height: int
    photo_index: Optional[int] = None

    @property
    def box(self) -> Tuple[int, int, int, int]:
        return (self.left, self.top, self.left + self.width, self.top + self.height)

    @property
    def order_key(self) -> int:
        digits = "".join(ch for ch in self.name.split("_")[-1] if ch.isdigit())
        return int(digits) if digits else 0


@dataclass
class TemplateInfo:
    source_path: str
    display_name: str
    width: int
    height: int
    is_psd: bool
    product_type: ProductType
    frames: List[FrameInfo] = field(default_factory=list)

    @property
    def frame_count(self) -> int:
        return len(self.frames)


@dataclass
class DesignJob:
    template: TemplateInfo
    photos: List[PhotoItem] = field(default_factory=list)
    background_path: Optional[str] = None
    overlay_effect: Optional[str] = None
    text_layers: List[Dict[str, Any]] = field(default_factory=list)
    output_psd_path: Optional[str] = None
    output_png_path: Optional[str] = None
