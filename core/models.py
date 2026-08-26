"""core/models.py (unchanged from v2)"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import json


class ProductType(Enum):
    MUG = "Mug"; BOTTLE = "Bottle"; TSHIRT = "T-shirt"; TILE = "Tile"
    CUSHION = "Cushion"; KEYRING_ROUND = "Keyring (Round)"
    KEYRING_SQUARE = "Keyring (Square)"; MOBILE_COVER = "Mobile Cover"


class FrameShape(Enum):
    RECT = "rect"; ROUND = "round"


class TemplateTheme(Enum):
    PLAIN = "Plain"; COLLAGE_BIRTHDAY = "Collage: Birthday"
    COLLAGE_DIWALI = "Collage: Diwali"; COLLAGE_HOLI = "Collage: Holi"
    COLLAGE_NEWYEAR = "Collage: New Year"; COLLAGE_VALENTINE = "Collage: Valentine"


@dataclass
class PhotoItem:
    original_path: str
    sequence_name: str
    index: int
    auto_enhanced: bool = False

    def to_dict(self) -> dict:
        return {"original_path": self.original_path, "sequence_name": self.sequence_name,
                "index": self.index, "auto_enhanced": self.auto_enhanced}

    @classmethod
    def from_dict(cls, data: dict) -> "PhotoItem":
        return cls(original_path=data["original_path"], sequence_name=data["sequence_name"],
                    index=data["index"], auto_enhanced=data.get("auto_enhanced", False))


@dataclass
class FrameInfo:
    name: str; left: int; top: int; width: int; height: int
    shape: FrameShape = FrameShape.RECT
    photo_index: Optional[int] = None
    photo_scale: float = 1.0
    photo_offset_x: int = 0
    photo_offset_y: int = 0

    @property
    def box(self) -> Tuple[int, int, int, int]:
        return (self.left, self.top, self.left + self.width, self.top + self.height)

    @property
    def order_key(self) -> int:
        import re
        match = re.search(r"\d+", self.name)
        return int(match.group()) if match else 0

    def to_dict(self) -> dict:
        return {"name": self.name, "left": self.left, "top": self.top, "width": self.width,
                "height": self.height, "shape": self.shape.value, "photo_index": self.photo_index,
                "photo_scale": self.photo_scale, "photo_offset_x": self.photo_offset_x,
                "photo_offset_y": self.photo_offset_y}

    @classmethod
    def from_dict(cls, data: dict) -> "FrameInfo":
        return cls(name=data["name"], left=data["left"], top=data["top"], width=data["width"],
                   height=data["height"], shape=FrameShape(data.get("shape", "rect")),
                   photo_index=data.get("photo_index"), photo_scale=data.get("photo_scale", 1.0),
                   photo_offset_x=data.get("photo_offset_x", 0), photo_offset_y=data.get("photo_offset_y", 0))


@dataclass
class TemplateInfo:
    source_path: str; display_name: str; width: int; height: int; is_psd: bool
    product_type: ProductType
    theme: TemplateTheme = TemplateTheme.PLAIN
    frames: List[FrameInfo] = field(default_factory=list)
    original_physical_width_cm: float = 0.0
    original_physical_height_cm: float = 0.0

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    def to_dict(self) -> dict:
        return {"source_path": self.source_path, "display_name": self.display_name, "width": self.width,
                "height": self.height, "is_psd": self.is_psd, "product_type": self.product_type.value,
                "theme": self.theme.value, "frames": [f.to_dict() for f in self.frames],
                "original_physical_width_cm": self.original_physical_width_cm,
                "original_physical_height_cm": self.original_physical_height_cm}

    @classmethod
    def from_dict(cls, data: dict) -> "TemplateInfo":
        return cls(source_path=data["source_path"], display_name=data["display_name"], width=data["width"],
                   height=data["height"], is_psd=data["is_psd"], product_type=ProductType(data["product_type"]),
                   theme=TemplateTheme(data.get("theme", "Plain")),
                   frames=[FrameInfo.from_dict(f) for f in data.get("frames", [])],
                   original_physical_width_cm=data.get("original_physical_width_cm", 0.0),
                   original_physical_height_cm=data.get("original_physical_height_cm", 0.0))


@dataclass
class DesignJob:
    template: TemplateInfo
    photos: List[PhotoItem] = field(default_factory=list)
    background_path: Optional[str] = None
    overlay_effects: List[Dict[str, Any]] = field(default_factory=list)
    text_layers: List[Dict[str, Any]] = field(default_factory=list)
    output_psd_path: Optional[str] = None
    output_png_path: Optional[str] = None
    last_saved_path: Optional[str] = None
    auto_save_enabled: bool = True

    def to_dict(self) -> dict:
        return {"template": self.template.to_dict() if self.template else None,
                "photos": [p.to_dict() for p in self.photos], "background_path": self.background_path,
                "overlay_effects": self.overlay_effects, "text_layers": self.text_layers,
                "output_psd_path": self.output_psd_path, "output_png_path": self.output_png_path,
                "last_saved_path": self.last_saved_path, "auto_save_enabled": self.auto_save_enabled}

    @classmethod
    def from_dict(cls, data: dict) -> "DesignJob":
        return cls(template=TemplateInfo.from_dict(data["template"]) if data.get("template") else None,
                   photos=[PhotoItem.from_dict(p) for p in data.get("photos", [])],
                   background_path=data.get("background_path"), overlay_effects=data.get("overlay_effects", []),
                   text_layers=data.get("text_layers", []), output_psd_path=data.get("output_psd_path"),
                   output_png_path=data.get("output_png_path"), last_saved_path=data.get("last_saved_path"),
                   auto_save_enabled=data.get("auto_save_enabled", True))

    def auto_save(self, folder: str) -> str:
        if not self.auto_save_enabled:
            return ""
        folder_path = Path(folder)
        folder_path.mkdir(parents=True, exist_ok=True)
        import time
        ts = int(time.time())
        base_name = Path(self.template.source_path).stem if self.template else "design"
        save_path = folder_path / f"{base_name}_{ts}.job.json"
        save_path.write_text(json.dumps(self.to_dict(), indent=2))
        self.last_saved_path = str(save_path)
        return str(save_path)

    @classmethod
    def load_from_auto_save(cls, path: str) -> "DesignJob":
        data = json.loads(Path(path).read_text())
        return cls.from_dict(data)
