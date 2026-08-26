"""
core/template_manager.py

Loads a template file (PSD or PNG/JPG) chosen by the operator and produces:
  - a TemplateInfo record (dimensions, product type, source path)
  - a flattened preview image path the UI can display

PSD rendering uses psd-tools' composite() to flatten all visible layers into
a single image — this is read-only preview rendering. Actually parsing frame
slots (layer names / bounding rects) for auto-fill is a later milestone
(PSDReaderService); this manager only needs enough to show the operator what
they loaded.
"""

import logging
from pathlib import Path
from typing import Optional

from PIL import Image

from core.models import TemplateInfo, ProductType

logger = logging.getLogger("SubliStudio.TemplateManager")

PSD_EXTENSIONS = {".psd", ".psb"}
FLAT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif"}


class TemplateManager:
    def __init__(self, preview_cache_dir: str):
        self.preview_cache_dir = Path(preview_cache_dir)
        self.preview_cache_dir.mkdir(parents=True, exist_ok=True)

    def load_template(
        self, file_path: str, product_type: ProductType
    ) -> tuple[Optional[TemplateInfo], Optional[str]]:
        """
        Load a template file and return (TemplateInfo, preview_image_path).
        Returns (None, None) on failure — caller is responsible for
        surfacing an error message to the operator.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Template file not found: {file_path}")
            return None, None

        ext = path.suffix.lower()

        if ext in PSD_EXTENSIONS:
            return self._load_psd(path, product_type)
        elif ext in FLAT_EXTENSIONS:
            return self._load_flat_image(path, product_type)
        else:
            logger.error(f"Unsupported template file type: {ext}")
            return None, None

    def _load_psd(
        self, path: Path, product_type: ProductType
    ) -> tuple[Optional[TemplateInfo], Optional[str]]:
        try:
            from psd_tools import PSDImage
        except ImportError:
            logger.error(
                "psd-tools is not installed — cannot preview PSD templates. "
                "Install with: pip install psd-tools"
            )
            return None, None

        try:
            psd = PSDImage.open(str(path))
            flattened = psd.composite()
            if flattened is None:
                logger.error(f"PSD produced no composite image: {path}")
                return None, None
            if flattened.mode != "RGB":
                flattened = flattened.convert("RGB")

            preview_path = self._save_preview(flattened, path.stem)

            info = TemplateInfo(
                file_path=str(path),
                product_type=product_type,
                display_name=path.name,
                width=psd.width,
                height=psd.height,
                is_psd=True,
            )
            logger.info(f"Loaded PSD template: {path.name} ({psd.width}x{psd.height})")
            return info, preview_path

        except Exception as e:
            logger.error(f"Failed to open PSD {path}: {e}")
            return None, None

    def _load_flat_image(
        self, path: Path, product_type: ProductType
    ) -> tuple[Optional[TemplateInfo], Optional[str]]:
        try:
            with Image.open(path) as img:
                img_rgb = img.convert("RGB")
                width, height = img_rgb.size
                preview_path = self._save_preview(img_rgb, path.stem)

            info = TemplateInfo(
                file_path=str(path),
                product_type=product_type,
                display_name=path.name,
                width=width,
                height=height,
                is_psd=False,
            )
            logger.info(f"Loaded image template: {path.name} ({width}x{height})")
            return info, preview_path

        except Exception as e:
            logger.error(f"Failed to open template image {path}: {e}")
            return None, None

    def _save_preview(self, image: Image.Image, stem: str) -> str:
        """Save a size-capped preview JPEG to the cache dir and return its path."""
        preview = image.copy()
        preview.thumbnail((900, 900), Image.LANCZOS)
        out_path = self.preview_cache_dir / f"preview_{stem}.jpg"
        preview.save(out_path, "JPEG", quality=90)
        return str(out_path)
