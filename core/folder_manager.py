from __future__ import annotations
from pathlib import Path
from .config import MugXConfig

class FolderManager:
    def __init__(self, config: MugXConfig | None = None):
        self.config = config or MugXConfig.from_env()

    def initialize(self) -> None:
        """Create the full D:/SublimationBag directory structure on first run."""
        self.config.ensure()

    def get_customer_photo_folder(self, mobile: bool = False) -> Path:
        return self.config.mobile_photo if mobile else self.config.customer_photo

    def get_templates_folder(self, product: str = 'mug') -> Path:
        return self.config.templates / product.capitalize()

    def get_backgrounds_folder(self) -> Path:
        return self.config.backgrounds

    def get_png_data_folder(self, category: str = '') -> Path:
        base = self.config.png_data
        return base / category if category else base

    def get_auto_save_folder(self, hd: bool = True) -> Path:
        return self.config.auto / ('HD' if hd else 'JPG')

    def get_my_own_psd_folder(self) -> Path:
        return self.config.my_own_psd
