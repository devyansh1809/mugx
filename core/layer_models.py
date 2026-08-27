"""
Phase 4: Layer Editor - Core Document and Layer Models
Non-destructive layer system for photo, text, background, clip-art, and overlay layers.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any
from enum import Enum
import uuid


class LayerType(Enum):
    PHOTO = "photo"
    TEXT = "text"
    BACKGROUND = "background"
    CLIP_ART = "clip_art"
    OVERLAY = "overlay"


class LayerTransform:
    """Represents transformation state of a layer (position, scale, rotation)."""
    
    def __init__(self, x: float = 0.0, y: float = 0.0, scale: float = 1.0, rotation: float = 0.0):
        self.x = x
        self.y = y
        self.scale = scale
        self.rotation = rotation
    
    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "scale": self.scale, "rotation": self.rotation}
    
    @classmethod
    def from_dict(cls, data: dict) -> "LayerTransform":
        return cls(x=data.get("x", 0.0), y=data.get("y", 0.0), scale=data.get("scale", 1.0), rotation=data.get("rotation", 0.0))


@dataclass
class LayerProperties:
    visible: bool = True
    locked: bool = False
    opacity: float = 1.0
    blend_mode: str = "normal"


@dataclass
class PhotoLayer:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "photo"
    image_path: str = ""
    image_data: Optional[bytes] = None
    crop_rect: Optional[Tuple[float, float, float, float]] = None
    flip_horizontal: bool = False
    flip_vertical: bool = False
    transform: LayerTransform = field(default_factory=LayerTransform)
    properties: LayerProperties = field(default_factory=LayerProperties)
    
    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "image_path": self.image_path, "crop_rect": self.crop_rect, "flip_horizontal": self.flip_horizontal, "flip_vertical": self.flip_vertical, "transform": self.transform.to_dict(), "properties": {"visible": self.properties.visible, "locked": self.properties.locked, "opacity": self.properties.opacity, "blend_mode": self.properties.blend_mode}}


@dataclass
class TextLayer:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "text"
    text: str = "Sample Text"
    font_family: str = "Arial"
    font_size: float = 24.0
    font_weight: str = "normal"
    font_style: str = "normal"
    color: str = "#000000"
    alignment: str = "center"
    background_color: Optional[str] = None
    border_color: Optional[str] = None
    border_width: float = 0.0
    transform: LayerTransform = field(default_factory=LayerTransform)
    properties: LayerProperties = field(default_factory=LayerProperties)
    
    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "text": self.text, "font_family": self.font_family, "font_size": self.font_size, "font_weight": self.font_weight, "font_style": self.font_style, "color": self.color, "alignment": self.alignment, "background_color": self.background_color, "border_color": self.border_color, "border_width": self.border_width, "transform": self.transform.to_dict(), "properties": {"visible": self.properties.visible, "locked": self.properties.locked, "opacity": self.properties.opacity, "blend_mode": self.properties.blend_mode}}


@dataclass
class BackgroundLayer:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "background"
    color: Optional[str] = "#FFFFFF"
    image_path: Optional[str] = None
    image_data: Optional[bytes] = None
    blur_radius: float = 0.0
    transform: LayerTransform = field(default_factory=LayerTransform)
    properties: LayerProperties = field(default_factory=LayerProperties)
    
    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "color": self.color, "image_path": self.image_path, "blur_radius": self.blur_radius, "transform": self.transform.to_dict(), "properties": {"visible": self.properties.visible, "locked": self.properties.locked, "opacity": self.properties.opacity, "blend_mode": self.properties.blend_mode}}


@dataclass
class ClipArtLayer:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "clip_art"
    asset_path: str = ""
    asset_data: Optional[bytes] = None
    tint_color: Optional[str] = None
    transform: LayerTransform = field(default_factory=LayerTransform)
    properties: LayerProperties = field(default_factory=LayerProperties)
    
    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "asset_path": self.asset_path, "tint_color": self.tint_color, "transform": self.transform.to_dict(), "properties": {"visible": self.properties.visible, "locked": self.properties.locked, "opacity": self.properties.opacity, "blend_mode": self.properties.blend_mode}}


@dataclass
class OverlayLayer:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "overlay"
    asset_path: str = ""
    asset_data: Optional[bytes] = None
    overlay_type: str = "effect"
    transform: LayerTransform = field(default_factory=LayerTransform)
    properties: LayerProperties = field(default_factory=LayerProperties)
    
    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "asset_path": self.asset_path, "overlay_type": self.overlay_type, "transform": self.transform.to_dict(), "properties": {"visible": self.properties.visible, "locked": self.properties.locked, "opacity": self.properties.opacity, "blend_mode": self.properties.blend_mode}}


@dataclass
class Document:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    canvas_width: float = 0.0
    canvas_height: float = 0.0
    dpi: int = 300
    layers: List[Any] = field(default_factory=list)
    active_layer_id: Optional[str] = None
    name: str = "Untitled"
    
    def add_layer(self, layer: Any, index: Optional[int] = None) -> None:
        if index is None: self.layers.append(layer)
        else: self.layers.insert(index, layer)
        self.active_layer_id = layer.id
    
    def remove_layer(self, layer_id: str) -> Optional[Any]:
        for i, layer in enumerate(self.layers):
            if layer.id == layer_id:
                self.layers.pop(i)
                if self.active_layer_id == layer_id: self.active_layer_id = self.layers[-1].id if self.layers else None
                return layer
        return None
    
    def get_layer(self, layer_id: str) -> Optional[Any]:
        for layer in self.layers:
            if layer.id == layer_id: return layer
        return None
    
    def move_layer(self, layer_id: str, new_index: int) -> bool:
        for i, layer in enumerate(self.layers):
            if layer.id == layer_id:
                layer_obj = self.layers.pop(i)
                self.layers.insert(new_index, layer_obj)
                return True
        return False
    
    def to_dict(self) -> dict:
        return {"id": self.id, "canvas_width": self.canvas_width, "canvas_height": self.canvas_height, "dpi": self.dpi, "layers": [layer.to_dict() for layer in self.layers], "active_layer_id": self.active_layer_id, "name": self.name}
    
    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        doc = cls(id=data.get("id", str(uuid.uuid4())), canvas_width=data.get("canvas_width", 0.0), canvas_height=data.get("canvas_height", 0.0), dpi=data.get("dpi", 300), active_layer_id=data.get("active_layer_id"), name=data.get("name", "Untitled"))
        for layer_data in data.get("layers", []):
            layer_type = layer_data.get("type")
            transform = LayerTransform.from_dict(layer_data.get("transform", {}))
            properties = LayerProperties(visible=layer_data.get("properties", {}).get("visible", True), locked=layer_data.get("properties", {}).get("locked", False), opacity=layer_data.get("properties", {}).get("opacity", 1.0), blend_mode=layer_data.get("properties", {}).get("blend_mode", "normal"))
            if layer_type == "photo": layer = PhotoLayer(id=layer_data.get("id", str(uuid.uuid4())), image_path=layer_data.get("image_path", ""), crop_rect=tuple(layer_data["crop_rect"]) if layer_data.get("crop_rect") else None, flip_horizontal=layer_data.get("flip_horizontal", False), flip_vertical=layer_data.get("flip_vertical", False), transform=transform, properties=properties)
            elif layer_type == "text": layer = TextLayer(id=layer_data.get("id", str(uuid.uuid4())), text=layer_data.get("text", "Sample Text"), font_family=layer_data.get("font_family", "Arial"), font_size=layer_data.get("font_size", 24.0), font_weight=layer_data.get("font_weight", "normal"), font_style=layer_data.get("font_style", "normal"), color=layer_data.get("color", "#000000"), alignment=layer_data.get("alignment", "center"), background_color=layer_data.get("background_color"), border_color=layer_data.get("border_color"), border_width=layer_data.get("border_width", 0.0), transform=transform, properties=properties)
            elif layer_type == "background": layer = BackgroundLayer(id=layer_data.get("id", str(uuid.uuid4())), color=layer_data.get("color", "#FFFFFF"), image_path=layer_data.get("image_path"), blur_radius=layer_data.get("blur_radius", 0.0), transform=transform, properties=properties)
            elif layer_type == "clip_art": layer = ClipArtLayer(id=layer_data.get("id", str(uuid.uuid4())), asset_path=layer_data.get("asset_path", ""), tint_color=layer_data.get("tint_color"), transform=transform, properties=properties)
            elif layer_type == "overlay": layer = OverlayLayer(id=layer_data.get("id", str(uuid.uuid4())), asset_path=layer_data.get("asset_path", ""), overlay_type=layer_data.get("overlay_type", "effect"), transform=transform, properties=properties)
            else: continue
            doc.layers.append(layer)
        return doc


def create_photo_layer(image_path: str, x: float = 0, y: float = 0, scale: float = 1.0) -> PhotoLayer:
    return PhotoLayer(image_path=image_path, transform=LayerTransform(x=x, y=y, scale=scale))

def create_text_layer(text: str, x: float = 0, y: float = 0, font_size: float = 24.0, color: str = "#000000") -> TextLayer:
    return TextLayer(text=text, font_size=font_size, color=color, transform=LayerTransform(x=x, y=y))

def create_background_layer(color: str = "#FFFFFF", image_path: Optional[str] = None) -> BackgroundLayer:
    return BackgroundLayer(color=color, image_path=image_path)

def create_clip_art_layer(asset_path: str, x: float = 0, y: float = 0, scale: float = 1.0) -> ClipArtLayer:
    return ClipArtLayer(asset_path=asset_path, transform=LayerTransform(x=x, y=y, scale=scale))

def create_overlay_layer(asset_path: str, overlay_type: str = "effect") -> OverlayLayer:
    return OverlayLayer(asset_path=asset_path, overlay_type=overlay_type)
