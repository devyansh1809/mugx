from __future__ import annotations
import shutil
from pathlib import Path
from typing import List
from .config import MugXConfig

class PhotoImportService:
    def __init__(self, config: MugXConfig | None = None):
        self.config = config or MugXConfig.from_env()
        self.photo_folder = self.config.customer_photo
        self.mobile_folder = self.config.mobile_photo

    def get_sequential_photos(self, count: int, mobile: bool = False) -> List[Path]:
        """Load photos 01, 02, 03... up to count from the appropriate folder."""
        folder = self.mobile_folder if mobile else self.photo_folder
        photos = []
        for i in range(1, count + 1):
            for ext in ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'):
                photo_path = folder / f"{i:02d}{ext}"
                if photo_path.exists():
                    photos.append(photo_path)
                    break
        return photos

    def get_all_photos(self, mobile: bool = False) -> List[Path]:
        """Get all photos in sequential order from the folder."""
        folder = self.mobile_folder if mobile else self.photo_folder
        if not folder.exists():
            return []
        photos = []
        for ext in ('*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG'):
            photos.extend(folder.glob(ext))
        # Sort numerically by filename stem
        def sort_key(p: Path):
            try:
                return int(p.stem)
            except ValueError:
                return float('inf')
        return sorted(photos, key=sort_key)

    def auto_rename_photos(self, photo_paths: List[Path], mobile: bool = False) -> None:
        """Rename photos to 01, 02, 03... sequentially."""
        folder = self.mobile_folder if mobile else self.photo_folder
        # First pass: rename to temp names to avoid collisions
        temp_map = {}
        for idx, photo_path in enumerate(photo_paths, start=1):
            if photo_path.exists():
                temp_name = f"_temp_{idx}{photo_path.suffix}"
                temp_path = folder / temp_name
                photo_path.rename(temp_path)
                temp_map[idx] = temp_path
        # Second pass: rename to final sequential names
        for idx, temp_path in temp_map.items():
            new_name = f"{idx:02d}{temp_path.suffix}"
            new_path = folder / new_name
            temp_path.rename(new_path)

    def import_photos(self, source_paths: List[Path], mobile: bool = False) -> List[Path]:
        """Import photos from source paths, auto-rename sequentially, return new paths."""
        folder = self.mobile_folder if mobile else self.photo_folder
        folder.mkdir(parents=True, exist_ok=True)
        imported = []
        for src in source_paths:
            if src.exists():
                dst = folder / src.name
                shutil.copy2(src, dst)
                imported.append(dst)
        if imported:
            self.auto_rename_photos(self.get_all_photos(mobile=mobile), mobile=mobile)
        return self.get_all_photos(mobile=mobile)

    def remove_photo(self, photo_path: Path, mobile: bool = False) -> None:
        """Remove a photo and renumber remaining sequentially."""
        if photo_path.exists():
            photo_path.unlink()
        remaining = self.get_all_photos(mobile=mobile)
        if remaining:
            self.auto_rename_photos(remaining, mobile=mobile)

    def renumber_all(self, mobile: bool = False) -> List[Path]:
        """Renumber all photos in folder sequentially."""
        photos = self.get_all_photos(mobile=mobile)
        if photos:
            self.auto_rename_photos(photos, mobile=mobile)
        return self.get_all_photos(mobile=mobile)
