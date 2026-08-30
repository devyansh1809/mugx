from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Callable
from .config import MugXConfig
from .template_manager import TemplateManager
from .photo_import_service import PhotoImportService

class AutoFillEngine:
    """Auto-fill engine for placing photos into PSD template smart objects."""
    
    def __init__(self, config: MugXConfig | None = None):
        self.config = config or MugXConfig.from_env()
        self.template_manager = TemplateManager(config)
        self.photo_service = PhotoImportService(config)
        self._progress_callback: Optional[Callable[[str], None]] = None

    def set_progress_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for progress updates (e.g., 'Placing photo 1/6...')."""
        self._progress_callback = callback

    def _report(self, message: str) -> None:
        if self._progress_callback:
            self._progress_callback(message)

    def fill_template(self, template_path: Path, photo_count: int, mobile: bool = False) -> List[Path]:
        """
        Auto-fill photos into template smart objects.
        
        Returns list of photo paths actually placed (may be fewer than photo_count).
        """
        # Get sequential photos 01, 02, 03... up to photo_count
        photos = self.photo_service.get_sequential_photos(photo_count, mobile=mobile)
        
        # Get smart object names from template
        smart_objects = self.template_manager.get_smart_object_names(template_path)
        
        placed = []
        for idx, photo_path in enumerate(photos):
            if idx >= len(smart_objects):
                break
            smart_object_name = smart_objects[idx]
            self._report(f"Placing photo {idx + 1}/{len(photos)}: {photo_path.name} -> {smart_object_name}")
            # In production: call Photoshop scripting to replace smart object contents
            # self._replace_smart_object(template_path, smart_object_name, photo_path)
            placed.append(photo_path)
        
        self._report(f"Complete! {len(placed)} images placed.")
        return placed

    def fill_template_auto(self, template_path: Path, mobile: bool = False) -> List[Path]:
        """Auto-detect frame count and fill all available photos."""
        photo_count = self.template_manager.detect_frame_count(template_path)
        return self.fill_template(template_path, photo_count, mobile=mobile)


class ImageProcessor:
    """Photo editing tools: auto color, smooth, swap, resize, etc."""
    
    def __init__(self, config: MugXConfig | None = None):
        self.config = config or MugXConfig.from_env()

    def auto_color_correction(self, layer_name: Optional[str] = None) -> None:
        """Apply auto color correction to selected layer or active layer."""
        # Photoshop scripting would go here:
        # var doc = app.activeDocument;
        # var layer = layerName ? doc.layers.getByName(layerName) : doc.activeLayer;
        # doc.activeLayer = layer;
        # ... apply auto color action
        pass

    def auto_smooth(self, layer_name: Optional[str] = None) -> None:
        """Apply skin smoothing/enhancement filter."""
        # Photoshop scripting for surface blur or similar
        pass

    def swap_photos(self, layer1_name: str, layer2_name: str) -> None:
        """Swap positions of two photo layers."""
        # Get layer bounds, exchange smart object contents, maintain positions
        pass

    def resize_photo(self, layer_name: str, scale: float = 1.0) -> None:
        """Resize photo layer by scale factor."""
        # Photoshop transform: layer.resize(scale * 100, scale * 100)
        pass

    def change_background(self, background_path: Path, blur: bool = False) -> None:
        """Replace background layer with new image, optionally blur."""
        # Load background, place as bottom layer, apply Gaussian blur if needed
        pass

    def apply_color_effect(self, effect: str) -> None:
        """Apply color effect: 'black_white', 'sepia', 'vintage', etc."""
        # Photoshop adjustment layers or filters
        pass

    def mirror_layer(self, layer_name: str) -> None:
        """Mirror (flip horizontally) a layer for sublimation printing."""
        # layer.flip(Direction.HORIZONTAL)
        pass
