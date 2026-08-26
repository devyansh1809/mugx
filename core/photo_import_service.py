"""
core/photo_import_service.py (v2.2)

Fixes:
- Restored .gif support in SUPPORTED_EXTENSIONS (dropped in v2 rewrite).
- Added optional HEIC/HEIF support via pillow-heif (lazy import,
  graceful fallback -- same pattern as cv2 in image_processor.py).
"""
from __future__ import annotations

import hashlib
import logging
import os
import json
from pathlib import Path
from typing import List, Optional, Dict

from PIL import Image

from core.models import PhotoItem

logger = logging.getLogger("SubliStudio.PhotoImportService")

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    _HAS_HEIF = True
except Exception:
    _HAS_HEIF = False

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp", ".gif"}
HEIF_EXTENSIONS = {".heic", ".heif"}

THUMB_SIZE = (96, 96)
LAST_FOLDER_PATH = Path.home() / ".subli_studio" / "last_folder.json"


class PhotoImportService:
    def __init__(self, thumbnail_cache_dir: str):
        self.thumbnail_cache_dir = Path(thumbnail_cache_dir)
        self.thumbnail_cache_dir.mkdir(parents=True, exist_ok=True)
        if not _HAS_HEIF:
            logger.info(
                "pillow-heif not installed -- .heic/.heif photos will be skipped. "
                "Install with: pip install pillow-heif"
            )

    def get_last_folder(self) -> Optional[str]:
        if LAST_FOLDER_PATH.exists():
            try:
                return json.loads(LAST_FOLDER_PATH.read_text()).get("last_folder")
            except Exception:
                pass
        return None

    def save_last_folder(self, folder: str):
        LAST_FOLDER_PATH.parent.mkdir(parents=True, exist_ok=True)
        LAST_FOLDER_PATH.write_text(json.dumps({"last_folder": folder}))

    def _supported_extensions(self) -> set:
        exts = set(SUPPORTED_EXTENSIONS)
        if _HAS_HEIF:
            exts |= HEIF_EXTENSIONS
        return exts

    def scan_folder(self, folder: str, name_overrides: Optional[Dict[int, str]] = None) -> List[PhotoItem]:
        folder_path = Path(folder)
        if not folder_path.is_dir():
            logger.warning("scan_folder: %s is not a directory", folder)
            return []

        supported = self._supported_extensions()
        skipped_heif = 0
        candidates = []
        for p in sorted(folder_path.iterdir()):
            if not p.is_file():
                continue
            suffix = p.suffix.lower()
            if suffix in supported:
                candidates.append(p)
            elif suffix in HEIF_EXTENSIONS and not _HAS_HEIF:
                skipped_heif += 1

        if skipped_heif:
            logger.warning(
                "Skipped %d .heic/.heif file(s) -- install pillow-heif to support them.",
                skipped_heif,
            )

        photos: List[PhotoItem] = []
        for idx, path in enumerate(candidates, start=1):
            seq_name = name_overrides.get(idx - 1, f"{idx:02d}") if name_overrides else f"{idx:02d}"
            photos.append(
                PhotoItem(original_path=str(path), sequence_name=seq_name, index=idx - 1)
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
                if getattr(img, "is_animated", False):
                    img.seek(0)
                img = img.convert("RGB")
                img.thumbnail(THUMB_SIZE)
                img.save(cache_path, "PNG")
            return str(cache_path)
        except Exception:
            logger.exception("Failed to build thumbnail for %s", photo.original_path)
            return None
