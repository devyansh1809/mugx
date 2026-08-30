from __future__ import annotations
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from .config import MugXConfig

@dataclass
class PrintSettings:
    paper_size: str = 'A4'  # A4, A3, Letter
    dpi: int = 300
    mirror: bool = True  # Flip horizontally for sublimation
    color_mode: str = 'RGB'
    units: str = 'mm'

    @property
    def a4_pixels(self) -> tuple[int, int]:
        """A4 dimensions at specified DPI (210x297mm)."""
        # 210mm = 8.27in, 297mm = 11.69in
        width = int(8.27 * self.dpi)
        height = int(11.69 * self.dpi)
        return width, height


class PrintExporter:
    """Print preparation: mirror, A4 layout, multiple designs per sheet, export."""
    
    def __init__(self, config: MugXConfig | None = None):
        self.config = config or MugXConfig.from_env()
        self.settings = PrintSettings()

    def prepare_for_print(self, mirror: bool = True, paper_size: str = 'A4') -> None:
        """
        Prepare design for sublimation printing.
        
        In production:
        1. Create new A4 canvas at 300 DPI
        2. Copy active document
        3. Mirror if needed
        4. Center on page
        """
        self.settings.mirror = mirror
        self.settings.paper_size = paper_size
        # Photoshop scripting would create the A4 document and place the design
        pass

    def mirror_design(self) -> None:
        """Flip the active design horizontally for sublimation."""
        # Photoshop: app.activeDocument.activeLayer.flip(Direction.HORIZONTAL)
        pass

    def add_extra_design(self, design_path: Path) -> None:
        """
        Add another design to the same sheet to save paper.
        
        In production: load design, place in available space, auto-arrange.
        """
        pass

    def auto_layout_on_a4(self, designs: List[Path]) -> None:
        """
        Auto-arrange multiple designs on a single A4 sheet.
        
        In production: calculate optimal positions, place each design.
        """
        pass

    def export(self, output_path: Path, format: str = 'JPG', quality: int = 95) -> None:
        """
        Export the prepared design to file.
        
        Supported formats: JPG, PNG, PSD, TIFF
        """
        # Photoshop: doc.saveAs(output_path, options)
        pass

    def export_to_auto_folder(self, hd: bool = True) -> Path:
        """Export to the Auto/HD or Auto/JPG folder."""
        folder = self.config.auto / ('HD' if hd else 'JPG')
        folder.mkdir(parents=True, exist_ok=True)
        # Generate filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = 'psd' if hd else 'jpg'
        output = folder / f"MugX_{timestamp}.{ext}"
        self.export(output, format='PSD' if hd else 'JPG')
        return output

    def get_print_settings_dialog(self) -> PrintSettings:
        """Return print settings (in production, show dialog to user)."""
        return self.settings
