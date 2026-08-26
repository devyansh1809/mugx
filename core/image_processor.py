"""
core/image_processor.py (v2)

Auto-enhance pipeline (unchanged from v1).
"""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from core.models import PhotoItem

logger = logging.getLogger("SubliStudio.ImageProcessor")

try:
    import cv2
    _HAS_CV2 = True
except Exception:
    _HAS_CV2 = False

THUMB_SIZE = (96, 96)


def _enhance_with_cv2(image: Image.Image) -> Image.Image:
    rgb = np.array(image.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    smoothed = cv2.bilateralFilter(bgr, d=9, sigmaColor=60, sigmaSpace=60)
    lab = cv2.cvtColor(smoothed, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(16, 16))
    l_channel = clahe.apply(l_channel)
    lab = cv2.merge((l_channel, a_channel, b_channel))
    contrasted = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    hsv = cv2.cvtColor(contrasted, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.12, 0, 255)
    saturated = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    blurred = cv2.GaussianBlur(saturated, (0, 0), sigmaX=2)
    sharpened = cv2.addWeighted(saturated, 1.15, blurred, -0.15, 0)
    result_rgb = cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB)
    return Image.fromarray(result_rgb)


def _enhance_with_pillow(image: Image.Image) -> Image.Image:
    img = image.convert("RGB")
    img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    img = ImageEnhance.Contrast(img).enhance(1.06)
    img = ImageEnhance.Color(img).enhance(1.10)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=40, threshold=3))
    return img


def enhance_image(image: Image.Image) -> Image.Image:
    if _HAS_CV2:
        try:
            return _enhance_with_cv2(image)
        except Exception:
            logger.exception("cv2 enhancement failed, falling back to Pillow-only")
    return _enhance_with_pillow(image)


class ImageEnhancementService:
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: dict[str, str] = {}

    def _cache_key(self, photo: PhotoItem) -> str:
        try:
            stat = os.stat(photo.original_path)
            fingerprint = f"{photo.original_path}|{stat.st_mtime}|{stat.st_size}|{THUMB_SIZE}|enhanced"
        except OSError:
            fingerprint = f"{photo.original_path}|{THUMB_SIZE}|enhanced"
        return hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()

    def get_thumbnail(self, photo: PhotoItem) -> Optional[str]:
        key = self._cache_key(photo)
        cached = self._memory_cache.get(key)
        if cached and Path(cached).exists():
            return cached
        disk_path = self.cache_dir / f"{key}.png"
        if disk_path.exists():
            self._memory_cache[key] = str(disk_path)
            return str(disk_path)
        try:
            with Image.open(photo.original_path) as img:
                enhanced = enhance_image(img)
                enhanced.thumbnail(THUMB_SIZE)
                enhanced.save(disk_path, "PNG")
            self._memory_cache[key] = str(disk_path)
            return str(disk_path)
        except Exception:
            logger.exception("Failed to build enhanced thumbnail for %s", photo.original_path)
            return None
