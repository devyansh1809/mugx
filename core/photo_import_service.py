"""
core/photo_import_service.py

Handles turning a folder of customer photos into PhotoItem objects:
- scans a folder for supported image files
- assigns sequential names (01, 02, 03 ...) — display only in this milestone,
  files on disk are NOT renamed yet (that's a deliberate choice: don't mutate
  the customer's original folder until the operator confirms a job)
- generates cached thumbnails for fast list-view rendering
"""

import logging
from pathlib import Path
from typing import Optional

from PIL import Image

from core.models import PhotoItem

logger = logging.getLogger("SubliStudio.PhotoImport")

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
THUMBNAIL_SIZE = (128, 128)


class PhotoImportService:
    def __init__(self, thumbnail_cache_dir: str):
        self.thumbnail_cache_dir = Path(thumbnail_cache_dir)
        self.thumbnail_cache_dir.mkdir(parents=True, exist_ok=True)

    def scan_folder(self, folder_path: str) -> list[PhotoItem]:
        """
        Scan a folder for supported images and return PhotoItem objects
        with sequential display names assigned (01, 02, 03 ...).
        Files are sorted by name before numbering so results are deterministic.
        """
        folder = Path(folder_path)
        if not folder.is_dir():
            logger.warning(f"Not a directory: {folder_path}")
            return []

        files = sorted(
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        )

        items: list[PhotoItem] = []
        for i, f in enumerate(files, start=1):
            seq = f"{i:02d}"
            items.append(PhotoItem(
                original_path=str(f),
                sequence_name=seq,
                display_name=f"{seq} — {f.name}",
            ))

        logger.info(f"Scanned {folder_path}: {len(items)} photo(s) found.")
        return items

    def get_thumbnail(self, photo: PhotoItem) -> Optional[str]:
        """
        Generate (or reuse a cached) thumbnail for a photo.
        Returns the thumbnail file path, or None if generation failed.
        """
        src = Path(photo.original_path)
        if not src.exists():
            logger.error(f"Source photo missing: {src}")
            return None

        thumb_path = self.thumbnail_cache_dir / f"thumb_{src.stem}_{abs(hash(str(src)))}.jpg"

        if thumb_path.exists():
            return str(thumb_path)

        try:
            with Image.open(src) as img:
                img = img.convert("RGB")
                img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)
                img.save(thumb_path, "JPEG", quality=85)
            return str(thumb_path)
        except Exception as e:
            logger.error(f"Thumbnail generation failed for {src.name}: {e}")
            return None
