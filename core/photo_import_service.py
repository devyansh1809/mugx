"""
core/photo_import_service.py

Scans a folder of customer photos, assigns in-memory sequential names
(01, 02, 03...), and generates/cache plain (non-enhanced) thumbnails.
No PyQt imports.
"""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import List, Optional

from PIL import Image

from core.models import PhotoItem

logger = logging.getLogger("SubliStudio.PhotoImportService")

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
THUMB_SIZE = (96, 96)


class PhotoImportService:
    def __init__(self, thumbnail_cache_dir: str):
        self.thumbnail_cache_dir = Path(thumbnail_cache_dir)
        self.thumbnail_cache_dir.mkdir(parents=True, exist_ok=True)

    def scan_folder(self, folder: str) -> List[PhotoItem]:
        folder_path = Path(folder)
        if not folder_path.is_dir():
            logger.warning("scan_folder: %s is not a directory", folder)
            return []

        files_found = sorted(
            p for p in folder_path.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        )

        photos: List[PhotoItem] = []
        for idx, path in enumerate(files_found, start=1):
            photos.append(
                PhotoItem(original_path=str(path), sequence_name=f"{idx:02d}", index=idx - 1)
            )
        logger.info("scan_folder: found %d photo(s) in %s", len(photos), folder)
        return photos

    def _cache_key(self, photo: PhotoItem) -> str:
        try:
            stat = os.stat(photo.original_path)
            fingerprint = f"{photo.original_path}|{stat.st_mtime}|{stat.st_size}|{THUMB_SIZE}"
        except OSError:
            fingerprint = f"{photo.original_path}|{THUMB_SIZE}"
        return hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()

    def get_thumbnail(self, photo: PhotoItem) -> Optional[str]:
        cache_path = self.thumbnail_cache_dir / f"{self._cache_key(photo)}.png"
        if cache_path.exists():
            return str(cache_path)
        try:
            with Image.open(photo.original_path) as img:
                img = img.convert("RGB")
                img.thumbnail(THUMB_SIZE)
                img.save(cache_path, "PNG")
            return str(cache_path)
        except Exception:
            logger.exception("Failed to build thumbnail for %s", photo.original_path)
            return None
