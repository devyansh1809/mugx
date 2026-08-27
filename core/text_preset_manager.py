"""
Phase 5: Asset Library - Text Preset Manager
"""

import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TextPreset:
    id: str
    name: str
    font_family: str
    font_size: float
    font_weight: str = "normal"
    font_style: str = "normal"
    color: str = "#000000"
    background_color: Optional[str] = None
    border_color: Optional[str] = None
    border_width: float = 0.0
    shadow: bool = False
    shadow_color: str = "#808080"
    shadow_offset_x: float = 2.0
    shadow_offset_y: float = 2.0
    outline: bool = False
    outline_color: str = "#000000"
    outline_width: float = 1.0
    category: str = "basic"
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "font_family": self.font_family, "font_size": self.font_size, "font_weight": self.font_weight, "font_style": self.font_style, "color": self.color, "background_color": self.background_color, "border_color": self.border_color, "border_width": self.border_width, "shadow": self.shadow, "shadow_color": self.shadow_color, "shadow_offset_x": self.shadow_offset_x, "shadow_offset_y": self.shadow_offset_y, "outline": self.outline, "outline_color": self.outline_color, "outline_width": self.outline_width, "category": self.category, "tags": self.tags}
    
    @classmethod
    def from_dict(cls, data: dict) -> "TextPreset":
        return cls(id=data.get("id", ""), name=data.get("name", ""), font_family=data.get("font_family", "Arial"), font_size=data.get("font_size", 24.0), font_weight=data.get("font_weight", "normal"), font_style=data.get("font_style", "normal"), color=data.get("color", "#000000"), background_color=data.get("background_color"), border_color=data.get("border_color"), border_width=data.get("border_width", 0.0), shadow=data.get("shadow", False), shadow_color=data.get("shadow_color", "#808080"), shadow_offset_x=data.get("shadow_offset_x", 2.0), shadow_offset_y=data.get("shadow_offset_y", 2.0), outline=data.get("outline", False), outline_color=data.get("outline_color", "#000000"), outline_width=data.get("outline_width", 1.0), category=data.get("category", "basic"), tags=data.get("tags", []))


class TextPresetManager:
    def __init__(self, presets_dir: str):
        self.presets_dir = Path(presets_dir)
        self.presets: Dict[str, TextPreset] = {}
        self.categories: Dict[str, List[str]] = {}
        self._load_presets()
    
    def _load_presets(self) -> None:
        if not self.presets_dir.exists(): return
        for json_file in self.presets_dir.glob("*.json"):
            try:
                with open(json_file, "r") as f: data = json.load(f)
                if isinstance(data, list):
                    for preset_data in data:
                        preset = TextPreset.from_dict(preset_data)
                        self.presets[preset.id] = preset
                        self._add_to_category(preset.category, preset.id)
                else:
                    preset = TextPreset.from_dict(data)
                    self.presets[preset.id] = preset
                    self._add_to_category(preset.category, preset.id)
            except Exception as e: print(f"Warning: Could not load preset {json_file}: {e}")
        if not self.presets: self._load_builtin_presets()
    
    def _load_builtin_presets(self) -> None:
        builtin_presets = [
            TextPreset(id="basic_black", name="Basic Black", font_family="Arial", font_size=24.0, color="#000000", category="basic", tags=["simple", "black", "default"]),
            TextPreset(id="basic_white", name="Basic White", font_family="Arial", font_size=24.0, color="#FFFFFF", category="basic", tags=["simple", "white"]),
            TextPreset(id="bold_red", name="Bold Red", font_family="Arial Black", font_size=32.0, font_weight="bold", color="#FF0000", category="bold", tags=["bold", "red", "attention"]),
            TextPreset(id="elegant_serif", name="Elegant Serif", font_family="Georgia", font_size=28.0, font_weight="bold", font_style="italic", color="#4A4A4A", category="elegant", tags=["elegant", "serif", "formal"]),
            TextPreset(id="shadow_3d", name="3D Shadow", font_family="Arial Black", font_size=36.0, font_weight="bold", color="#FFD700", shadow=True, shadow_color="#808000", shadow_offset_x=3.0, shadow_offset_y=3.0, category="effects", tags=["3d", "shadow", "gold", "bold"]),
            TextPreset(id="outline_neon", name="Neon Outline", font_family="Arial", font_size=32.0, font_weight="bold", color="#00FFFF", outline=True, outline_color="#FF00FF", outline_width=2.0, category="effects", tags=["neon", "outline", "bright", "modern"]),
            TextPreset(id="background_box", name="Background Box", font_family="Arial", font_size=24.0, color="#FFFFFF", background_color="#000000", category="styled", tags=["background", "box", "contrast"]),
            TextPreset(id="romantic_script", name="Romantic Script", font_family="Brush Script MT", font_size=32.0, font_style="italic", color="#FF69B4", category="romantic", tags=["romantic", "script", "pink", "elegant"]),
            TextPreset(id="kids_playful", name="Kids Playful", font_family="Comic Sans MS", font_size=28.0, font_weight="bold", color="#FF6347", category="kids", tags=["kids", "playful", "colorful", "fun"]),
            TextPreset(id="minimal_thin", name="Minimal Thin", font_family="Helvetica Neue Light", font_size=24.0, font_weight="normal", color="#333333", category="minimal", tags=["minimal", "thin", "modern", "clean"])
        ]
        for preset in builtin_presets:
            self.presets[preset.id] = preset
            self._add_to_category(preset.category, preset.id)
    
    def _add_to_category(self, category: str, preset_id: str) -> None:
        if category not in self.categories: self.categories[category] = []
        if preset_id not in self.categories[category]: self.categories[category].append(preset_id)
    
    def get_presets(self, category: Optional[str] = None) -> List[TextPreset]:
        presets = list(self.presets.values())
        if category:
            preset_ids = self.categories.get(category, [])
            presets = [p for p in presets if p.id in preset_ids]
        return presets
    
    def get_preset(self, preset_id: str) -> Optional[TextPreset]: return self.presets.get(preset_id)
    
    def get_categories(self) -> List[str]: return sorted(list(self.categories.keys()))
    
    def search_presets(self, query: str) -> List[TextPreset]:
        query = query.lower()
        results = []
        for preset in self.presets.values():
            if query in preset.name.lower() or query in preset.category.lower() or any(query in tag.lower() for tag in preset.tags): results.append(preset)
        return results
    
    def save_preset(self, preset: TextPreset) -> bool:
        self.presets[preset.id] = preset
        self._add_to_category(preset.category, preset.id)
        preset_file = self.presets_dir / f"{preset.id}.json"
        try:
            with open(preset_file, "w") as f: json.dump(preset.to_dict(), f, indent=2)
            return True
        except Exception as e: print(f"Error saving preset: {e}"); return False
    
    def delete_preset(self, preset_id: str) -> bool:
        if preset_id not in self.presets: return False
        preset = self.presets.pop(preset_id)
        if preset.category in self.categories and preset_id in self.categories[preset.category]: self.categories[preset.category].remove(preset_id)
        preset_file = self.presets_dir / f"{preset.id}.json"
        if preset_file.exists():
            try: preset_file.unlink()
            except: pass
        return True
    
    def create_preset_from_layer(self, text_layer, name: str, category: str = "custom") -> TextPreset:
        return TextPreset(id=f"custom_{name.lower().replace(' ', '_')}", name=name, font_family=text_layer.font_family, font_size=text_layer.font_size, font_weight=text_layer.font_weight, font_style=text_layer.font_style, color=text_layer.color, background_color=text_layer.background_color, border_color=text_layer.border_color, border_width=text_layer.border_width, category=category, tags=["custom"])
