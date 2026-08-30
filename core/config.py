from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class MugXConfig:
    root: Path

    @property
    def customer_photo(self) -> Path: return self.root / 'Customer' / 'Photo'
    @property
    def mobile_photo(self) -> Path: return self.customer_photo / 'Mobile'
    @property
    def mosaic_photo(self) -> Path: return self.customer_photo / 'Mosaic'
    @property
    def auto(self) -> Path: return self.root / 'Auto'
    @property
    def templates(self) -> Path: return self.root / 'Templates'
    @property
    def backgrounds(self) -> Path: return self.root / 'Background'
    @property
    def png_data(self) -> Path: return self.root / 'PNG Data'
    @property
    def my_own_psd(self) -> Path: return self.root / 'My Own PSD'
    @property
    def three_d_text(self) -> Path: return self.root / '3D Text'

    @classmethod
    def from_env(cls) -> 'MugXConfig':
        default = Path('D:/SublimationBag') if os.name == 'nt' else Path.home() / 'SublimationBag'
        return cls(Path(os.getenv('MUGX_DATA_ROOT', str(default))).expanduser())

    def ensure(self) -> None:
        for path in (self.root, self.customer_photo, self.mobile_photo, self.mosaic_photo,
                     self.auto / 'HD', self.auto / 'JPG', self.templates, self.backgrounds,
                     self.png_data / 'bokeh', self.png_data / 'clipart', self.png_data / 'text',
                     self.png_data / 'alphabet', self.my_own_psd, self.three_d_text):
            path.mkdir(parents=True, exist_ok=True)
