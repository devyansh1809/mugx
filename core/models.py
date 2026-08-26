"""
core/models.py

Plain dataclasses shared across the app. No PyQt or Pillow imports here —
this module stays framework-free so it can be tested in isolation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProductType(str, Enum):
    MUG = "Mug"
    BOTTLE = "Bottle"
    TSHIRT = "T-shirt"
    TILE = "Tile"
    CUSHION = "Cushion"
    KEYRING = "Keyring"
    MOBILE_COVER = "Mobile Cover"


@dataclass
class PhotoItem:
    """A single customer photo tracked by the app."""
    original_path: str
    sequence_name: str = ""       # "01", "02", ... assigned on import
    display_name: str = ""        # filename shown in the UI list
    thumbnail_path: Optional[str] = None


@dataclass
class TemplateInfo:
    """
    Metadata about a loaded template file (PSD or PNG).
    For this scaffold, frame slots are not yet parsed from the PSD —
    that lands in PSDReaderService in a later milestone. For now this
    just tracks what file was loaded and lets the preview render it.
    """
    file_path: str
    product_type: ProductType
    display_name: str = ""
    width: int = 0
    height: int = 0
    is_psd: bool = False


@dataclass
class DesignJob:
    """
    Represents one print job in progress: the chosen template plus the
    photos assigned to it. Placeholder for the compositing step —
    populated once CompositorService exists.
    """
    template: Optional[TemplateInfo] = None
    photos: list[PhotoItem] = field(default_factory=list)
