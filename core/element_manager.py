from __future__ import annotations
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from .config import MugXConfig

@dataclass
class ElementInfo:
    path: str
    category: str  # 'bokeh', 'clipart', 'text', 'alphabet', 'background'
    name: str
    tags: List[str] = None

class ElementManager:
    """Manage design elements: bokeh lights, clipart, ready-made text, alphabet, backgrounds."""
    
    def __init__(self, config: MugXConfig | None = None):
        self.config = config or MugXConfig.from_env()
        self.png_data = self.config.png_data
        self.backgrounds = self.config.backgrounds

    def get_bokeh_lights(self) -> List[ElementInfo]:
        """Get all bokeh light PNG overlays."""
        folder = self.png_data / 'bokeh'
        return self._scan_pngs(folder, 'bokeh')

    def get_clipart(self) -> List[ElementInfo]:
        """Get all clipart PNG elements (hearts, flowers, decorations)."""
        folder = self.png_data / 'clipart'
        return self._scan_pngs(folder, 'clipart')

    def get_ready_text(self) -> List[ElementInfo]:
        """Get all ready-made text PSD/PNG elements."""
        folder = self.png_data / 'text'
        return self._scan_pngs(folder, 'text')

    def get_alphabet(self) -> List[ElementInfo]:
        """Get alphabet PNG elements (A-Z with effects)."""
        folder = self.png_data / 'alphabet'
        return self._scan_pngs(folder, 'alphabet')

    def get_backgrounds(self, category: Optional[str] = None) -> List[ElementInfo]:
        """Get background images, optionally filtered by category."""
        if category:
            folder = self.backgrounds / category
            return self._scan_images(folder, 'background', category)
        # Scan all categories
        results = []
        if self.backgrounds.exists():
            for cat_folder in self.backgrounds.iterdir():
                if cat_folder.is_dir():
                    results.extend(self._scan_images(cat_folder, 'background', cat_folder.name))
        return results

    def _scan_pngs(self, folder: Path, category: str) -> List[ElementInfo]:
        """Scan a folder for PNG files and return ElementInfo list."""
        if not folder.exists():
            return []
        results = []
        for png in folder.glob('*.png'):
            results.append(ElementInfo(
                path=png.as_posix(),
                category=category,
                name=png.stem,
                tags=[]
            ))
        return results

    def _scan_images(self, folder: Path, category: str, subcategory: str = '') -> List[ElementInfo]:
        """Scan a folder for image files (JPG, PNG, PSD)."""
        if not folder.exists():
            return []
        results = []
        for ext in ('*.jpg', '*.jpeg', '*.png', '*.psd'):
            for img in folder.glob(ext):
                results.append(ElementInfo(
                    path=img.as_posix(),
                    category=category,
                    name=img.stem,
                    tags=[subcategory] if subcategory else []
                ))
        return results

    def add_element(self, element_path: Path, target_layer: Optional[str] = None, blend_mode: str = 'normal') -> None:
        """
        Add an element (PNG overlay) to the document.
        
        In production: load PNG, place as new layer above target_layer, set blend mode.
        """
        # Photoshop scripting:
        # var doc = app.activeDocument;
        # var placed = doc.placedLayerFromFile(element_path);
        # if target_layer: place above it
        # layer.blendMode = BlendMode[blend_mode.toUpperCase()]
        pass

    def add_background(self, background_path: Path, blur: bool = False) -> None:
        """
        Add background image to document.
        
        In production: load image, place as bottom layer, resize to canvas, apply blur if needed.
        """
        pass

    def add_bokeh_light(self, light_name: str, target_layer: Optional[str] = None) -> None:
        """Add a specific bokeh light effect by name."""
        lights = self.get_bokeh_lights()
        for light in lights:
            if light.name.lower() == light_name.lower():
                self.add_element(Path(light.path), target_layer, blend_mode='screen')
                return

    def add_ready_text(self, text_name: str) -> None:
        """Add a specific ready-made text element by name."""
        texts = self.get_ready_text()
        for text in texts:
            if text.name.lower() == text_name.lower():
                self.add_element(Path(text.path))
                return

    def add_clipart(self, clipart_name: str) -> None:
        """Add a specific clipart element by name."""
        cliparts = self.get_clipart()
        for clipart in cliparts:
            if clipart.name.lower() == clipart_name.lower():
                self.add_element(Path(clipart.path))
                return

    def add_alphabet(self, letter: str) -> None:
        """Add an alphabet letter element (A-Z)."""
        letter = letter.upper()
        alphabet = self.get_alphabet()
        for item in alphabet:
            if item.name.upper() == letter:
                self.add_element(Path(item.path))
                return
