"""
Phase 5: Asset Library - Integration with Layer Engine
"""

from typing import Optional, Any
from core.layer_models import Document, PhotoLayer, TextLayer, BackgroundLayer, ClipArtLayer, OverlayLayer, LayerTransform


class AssetLayerFactory:
    @staticmethod
    def create_layer_from_asset(asset, document: Document, x: float = 0, y: float = 0, scale: float = 1.0) -> Optional[Any]:
        from core.asset_browser import AssetType
        if asset.type == AssetType.CLIP_ART:
            return ClipArtLayer(asset_path=asset.path, transform=LayerTransform(x=x, y=y, scale=scale), tint_color=asset.metadata.get("tint_color"))
        elif asset.type == AssetType.BACKGROUND:
            return BackgroundLayer(image_path=asset.path, blur_radius=asset.metadata.get("blur_radius", 0.0), transform=LayerTransform(x=0, y=0, scale=1.0))
        elif asset.type == AssetType.PATTERN:
            return BackgroundLayer(image_path=asset.path, transform=LayerTransform(x=0, y=0, scale=scale))
        elif asset.type == AssetType.EFFECT:
            return OverlayLayer(asset_path=asset.path, overlay_type="effect", transform=LayerTransform(x=0, y=0, scale=1.0))
        elif asset.type == AssetType.COLLAGE_THEME:
            return asset.metadata
        return None
    
    @staticmethod
    def apply_text_preset(text_layer: TextLayer, preset) -> None:
        text_layer.font_family = preset.font_family
        text_layer.font_size = preset.font_size
        text_layer.font_weight = preset.font_weight
        text_layer.font_style = preset.font_style
        text_layer.color = preset.color
        text_layer.background_color = preset.background_color
        text_layer.border_color = preset.border_color
        text_layer.border_width = preset.border_width
    
    @staticmethod
    def create_text_layer_from_preset(preset, text: str, x: float = 0, y: float = 0) -> TextLayer:
        return TextLayer(text=text, font_family=preset.font_family, font_size=preset.font_size, font_weight=preset.font_weight, font_style=preset.font_style, color=preset.color, background_color=preset.background_color, border_color=preset.border_color, border_width=preset.border_width, transform=LayerTransform(x=x, y=y))


def add_asset_to_document(asset, document: Document, engine, x: float = 50, y: float = 50, scale: float = 1.0) -> Optional[Any]:
    layer = AssetLayerFactory.create_layer_from_asset(asset, document, x, y, scale)
    if layer:
        engine.add_layer(layer)
        return layer
    return None


def apply_preset_to_selected_layer(engine, preset) -> bool:
    layer = engine.get_selected_layer()
    if not layer or layer.type != "text": return False
    AssetLayerFactory.apply_text_preset(layer, preset)
    return True
