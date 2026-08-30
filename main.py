from __future__ import annotations
import sys
from pathlib import Path
from core.config import MugXConfig
from core.folder_manager import FolderManager
from core.photo_import_service import PhotoImportService
from core.template_manager import TemplateManager
from core.image_processor import AutoFillEngine, ImageProcessor
from core.element_manager import ElementManager
from core.print_exporter import PrintExporter

def main():
    """MugX Print Plugin - Main entry point."""
    print("MugX Print Plugin Pro - Initializing...")
    
    # Initialize configuration and folders
    config = MugXConfig.from_env()
    folder_mgr = FolderManager(config)
    folder_mgr.initialize()
    print(f"Data root: {config.root}")
    
    # Initialize services
    photo_service = PhotoImportService(config)
    template_mgr = TemplateManager(config)
    auto_fill = AutoFillEngine(config)
    img_proc = ImageProcessor(config)
    elem_mgr = ElementManager(config)
    print_exp = PrintExporter(config)
    
    print("Services initialized:")
    print(f"  - Photo folder: {config.customer_photo}")
    print(f"  - Templates: {config.templates}")
    print(f"  - Backgrounds: {config.backgrounds}")
    print(f"  - PNG Data: {config.png_data}")
    
    # Demo: list available templates
    templates = template_mgr.list_templates()
    print(f"\nFound {len(templates)} templates.")
    
    # Demo: list available photos
    photos = photo_service.get_all_photos()
    print(f"Found {len(photos)} photos in {config.customer_photo}.")
    
    print("\nMugX ready. Use the Photoshop panel or UI to design.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
