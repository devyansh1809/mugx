"""
core/image_processor.py

Auto-enhance pipeline for customer photos, plus a disk+memory cache so
enhanced thumbnails aren't recomputed on every UI redraw (checkbox toggle,
window resize, re-selecting the same folder, etc).

Framework-free — no PyQt imports — consistent with the rest of core/.
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from core.models import PhotoItem

logger = logging.getLogger("SubliStudio.ImageProcessor")

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
    logger.warning("OpenCV not installed — enhance_image() will use a Pillow-only fallback.")


# ─────────────────────────────────────────────────────────────────
#  enhance_image() — the actual pixel-processing function
# ─────────────────────────────────────────────────────────────────

def enhance_image(image: Image.Image) -> Image.Image:
    """
    Apply a mild, print-shop-friendly auto-enhancement to a customer photo:

      1. Edge-preserving smoothing (bilateral filter) — reduces sensor
         noise/grain without blurring edges the way a plain Gaussian blur
         would. This is the "smoothing" step.
      2. Adaptive local contrast (CLAHE on the L channel in LAB space) —
         boosts contrast in under/over-exposed regions without blowing out
         highlights or crushing shadows the way a flat/global contrast
         multiplier does. Better than PIL's ImageEnhance.Contrast for real
         customer photos, which are rarely evenly lit.
      3. Saturation boost (~12%) in HSV space — colors "pop" slightly,
         similar to a phone camera's default auto-enhance.
      4. Unsharp mask — mild sharpening to restore the crispness that
         step 1 softens, and to make the print output look sharp.

    Falls back to a Pillow-only version (ImageEnhance.Contrast / .Color /
    ImageFilter.UnsharpMask) if OpenCV isn't installed — this function
    never hard-fails just because a dependency is missing.

    Does not mutate the input image. Always returns RGB.
    """
    if image.mode != "RGB":
        image = image.convert("RGB")

    if _CV2_AVAILABLE:
        return _enhance_with_opencv(image)
    return _enhance_with_pillow_only(image)


def _enhance_with_opencv(image: Image.Image) -> Image.Image:
    rgb = np.array(image)

    # 1. Edge-preserving smoothing. d/sigma values tuned to give a real,
    #    measurable noise reduction (~15-20% std reduction on sensor-noise-
    #    like input) while keeping edges intact — see tests/test_core.py
    #    TestImageProcessor for the regression check on this.
    smoothed = cv2.bilateralFilter(rgb, d=9, sigmaColor=60, sigmaSpace=60)

    # 2. Adaptive contrast via CLAHE on the L (lightness) channel only,
    #    so colors (a/b channels) are left untouched. clipLimit is kept low
    #    and tileGridSize large — a tighter clip limit / smaller tiles
    #    measurably re-amplifies noise in flat regions, which defeats the
    #    point of step 1.
    lab = cv2.cvtColor(smoothed, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(16, 16))
    l_eq = clahe.apply(l_channel)
    lab_eq = cv2.merge([l_eq, a_channel, b_channel])
    contrasted = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2RGB)

    # 3. Saturation boost in HSV space
    hsv = cv2.cvtColor(contrasted, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.12, 0, 255)
    saturated = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

    # 4. Mild unsharp mask (Gaussian-blur-subtract technique). Weights kept
    #    gentle (1.15 / -0.15, not the more typical 1.5 / -0.5) specifically
    #    because a stronger unsharp mask was measured to amplify residual
    #    noise faster than it added real edge definition — see the module
    #    docstring history / tests for the noise-vs-sharpness tradeoff.
    blurred = cv2.GaussianBlur(saturated, (0, 0), sigmaX=2)
    sharpened = cv2.addWeighted(saturated, 1.15, blurred, -0.15, 0)

    return Image.fromarray(sharpened, mode="RGB")


def _enhance_with_pillow_only(image: Image.Image) -> Image.Image:
    from PIL import ImageEnhance, ImageFilter
    img = ImageEnhance.Contrast(image).enhance(1.08)
    img = ImageEnhance.Color(img).enhance(1.12)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=110, threshold=3))
    return img


# ─────────────────────────────────────────────────────────────────
#  ImageEnhancementService — caching wrapper used by the UI
# ─────────────────────────────────────────────────────────────────

class ImageEnhancementService:
    """
    Produces enhanced thumbnails for the photo list and caches them so
    enhance_image() is never re-run for a photo that hasn't changed.

    Two cache layers:
      - In-memory dict: instant lookups within the current app session
        (e.g. toggling "Auto Enhance" on/off repeatedly, or scrolling a
        long photo list that redraws visible items).
      - Disk cache: survives app restarts. Cache filenames are derived
        from the source file's path + modification time + size, so if the
        operator replaces a customer's photo on disk, the cache naturally
        invalidates instead of serving a stale enhanced version.
    """

    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: dict[str, str] = {}

    def get_thumbnail(
        self, photo: PhotoItem, size: tuple[int, int] = (128, 128)
    ) -> Optional[str]:
        """
        Return a file path to an enhanced + thumbnailed version of `photo`,
        generating and caching it if this is the first request.
        """
        src = Path(photo.original_path)
        if not src.exists():
            logger.error(f"Source photo missing: {src}")
            return None

        cache_key = self._cache_key(src, size)

        # Layer 1: in-memory
        if cache_key in self._memory_cache:
            cached_path = self._memory_cache[cache_key]
            if Path(cached_path).exists():
                return cached_path

        # Layer 2: disk
        disk_path = self.cache_dir / f"{cache_key}.jpg"
        if disk_path.exists():
            self._memory_cache[cache_key] = str(disk_path)
            return str(disk_path)

        # Cache miss on both layers — actually process the image
        try:
            with Image.open(src) as img:
                img = img.convert("RGB")
                enhanced = enhance_image(img)
                enhanced.thumbnail(size, Image.LANCZOS)
                enhanced.save(disk_path, "JPEG", quality=88)
        except Exception as e:
            logger.error(f"Enhancement failed for {src.name}: {e}")
            return None

        self._memory_cache[cache_key] = str(disk_path)
        logger.debug(f"Enhanced + cached: {src.name} -> {disk_path.name}")
        return str(disk_path)

    def _cache_key(self, src: Path, size: tuple[int, int]) -> str:
        """
        Key includes path, mtime, file size, and thumbnail size — so the
        cache auto-invalidates if the source file is replaced/edited, and
        different requested sizes don't collide.
        """
        stat = src.stat()
        raw = f"{src}|{stat.st_mtime}|{stat.st_size}|{size[0]}x{size[1]}"
        return "enh_" + hashlib.sha1(raw.encode()).hexdigest()[:20]

    def clear_memory_cache(self):
        """Drop the in-memory layer only — disk cache is left intact."""
        self._memory_cache.clear()
