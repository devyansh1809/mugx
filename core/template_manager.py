"""
core/template_manager.py

Template loading, frame detection, and design compositing. No PyQt imports.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from core.models import FrameInfo, ProductType, TemplateInfo, PhotoItem

logger = logging.getLogger("SubliStudio.TemplateManager")

FRAME_NAME_PATTERN = re.compile(r"^frame[_\-\s]*\d+$", re.IGNORECASE)


class TemplateManager:
    def __init__(self, preview_cache_dir: str):
        self.preview_cache_dir = Path(preview_cache_dir)
        self.preview_cache_dir.mkdir(parents=True, exist_ok=True)

    def load_template(self, file_path: str, product_type: ProductType) -> Tuple[Optional[TemplateInfo], Optional[str]]:
        path = Path(file_path)
        if not path.exists():
            logger.error("Template file does not exist: %s", file_path)
            return None, None

        is_psd = path.suffix.lower() in (".psd", ".psb")
        try:
            if is_psd:
                info, flattened = self._load_psd(path, product_type)
            else:
                info, flattened = self._load_image_template(path, product_type)
        except Exception:
            logger.exception("Failed to load template %s", file_path)
            return None, None

        preview_path = self.preview_cache_dir / f"{path.stem}_preview.png"
        flattened.convert("RGB").save(preview_path, "PNG")
        return info, str(preview_path)

    def _load_psd(self, path: Path, product_type: ProductType) -> Tuple[TemplateInfo, Image.Image]:
        from psd_tools import PSDImage

        psd = PSDImage.open(str(path))
        flattened = psd.composite()
        if flattened is None:
            flattened = Image.new("RGBA", (psd.width, psd.height), (240, 240, 240, 255))

        frames = self.detect_frames_psd(psd)
        info = TemplateInfo(
            source_path=str(path), display_name=path.name, width=psd.width, height=psd.height,
            is_psd=True, product_type=product_type, frames=frames,
        )
        return info, flattened

    def _load_image_template(self, path: Path, product_type: ProductType) -> Tuple[TemplateInfo, Image.Image]:
        img = Image.open(path).convert("RGBA")
        frames = self.detect_frames_sidecar(path, img.size)
        info = TemplateInfo(
            source_path=str(path), display_name=path.name, width=img.width, height=img.height,
            is_psd=False, product_type=product_type, frames=frames,
        )
        return info, img

    def detect_frames_psd(self, psd) -> List[FrameInfo]:
        frames: List[FrameInfo] = []

        def _walk(layers):
            for layer in layers:
                if getattr(layer, "is_group", False):
                    _walk(layer)
                    continue
                name = (layer.name or "").strip()
                if FRAME_NAME_PATTERN.match(name.replace(" ", "_")):
                    bbox = layer.bbox
                    frames.append(FrameInfo(
                        name=name, left=bbox[0], top=bbox[1],
                        width=bbox[2] - bbox[0], height=bbox[3] - bbox[1],
                    ))

        _walk(psd)
        frames.sort(key=lambda f: f.order_key)
        logger.info("Detected %d frame(s) in PSD template", len(frames))
        return frames

    def detect_frames_sidecar(self, template_path: Path, canvas_size: Tuple[int, int]) -> List[FrameInfo]:
        sidecar = template_path.with_suffix("").with_name(template_path.stem + ".frames.json")
        if sidecar.exists():
            try:
                data = json.loads(sidecar.read_text())
                frames = [
                    FrameInfo(name=item["name"], left=int(item["left"]), top=int(item["top"]),
                              width=int(item["width"]), height=int(item["height"]))
                    for item in data
                ]
                frames.sort(key=lambda f: f.order_key)
                return frames
            except Exception:
                logger.exception("Failed to parse frame sidecar %s", sidecar)

        width, height = canvas_size
        return [FrameInfo(name="frame_1", left=0, top=0, width=width, height=height)]

    @staticmethod
    def fit_photo_to_frame(photo: Image.Image, frame: FrameInfo, mode: str = "cover") -> Image.Image:
        target_w, target_h = frame.width, frame.height
        src_w, src_h = photo.size
        if target_w <= 0 or target_h <= 0 or src_w == 0 or src_h == 0:
            return Image.new("RGBA", (max(target_w, 1), max(target_h, 1)), (0, 0, 0, 0))

        src_ratio = src_w / src_h
        target_ratio = target_w / target_h

        if mode == "fit":
            if src_ratio > target_ratio:
                new_w = target_w
                new_h = round(target_w / src_ratio)
            else:
                new_h = target_h
                new_w = round(target_h * src_ratio)
            resized = photo.convert("RGBA").resize((max(new_w, 1), max(new_h, 1)), Image.LANCZOS)
            canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            offset = ((target_w - new_w) // 2, (target_h - new_h) // 2)
            canvas.paste(resized, offset, resized)
            return canvas

        if src_ratio > target_ratio:
            new_h = target_h
            new_w = round(target_h * src_ratio)
        else:
            new_w = target_w
            new_h = round(target_w / src_ratio)
        resized = photo.convert("RGBA").resize((max(new_w, 1), max(new_h, 1)), Image.LANCZOS)
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h))

    def fill_frames(self, template_info: TemplateInfo, base_canvas: Image.Image, photos: List[PhotoItem],
                     frame_mapping: Optional[dict] = None, fit_mode: str = "cover",
                     output_png: Optional[str] = None) -> Image.Image:
        if not template_info.frames:
            raise ValueError("Template has no detected frames to fill.")
        if not photos:
            raise ValueError("No photos supplied to fill frames with.")

        canvas = base_canvas.convert("RGBA").copy()
        frame_mapping = frame_mapping or {}

        next_photo_cursor = 0
        for frame_idx, frame in enumerate(template_info.frames):
            if frame_idx in frame_mapping:
                photo_idx = frame_mapping[frame_idx]
            else:
                if next_photo_cursor >= len(photos):
                    break
                photo_idx = next_photo_cursor
                next_photo_cursor += 1

            if photo_idx is None or photo_idx >= len(photos):
                continue

            photo_item = photos[photo_idx]
            with Image.open(photo_item.original_path) as src:
                fitted = self.fit_photo_to_frame(src, frame, mode=fit_mode)
            canvas.paste(fitted, (frame.left, frame.top), fitted)
            frame.photo_index = photo_idx

        if output_png:
            canvas.convert("RGB").save(output_png, "PNG")
        return canvas

    def swap_photo(self, template_info: TemplateInfo, base_canvas: Image.Image, photos: List[PhotoItem],
                    frame_index: int, new_photo_index: int, fit_mode: str = "cover") -> Image.Image:
        mapping = {idx: f.photo_index for idx, f in enumerate(template_info.frames) if f.photo_index is not None}
        mapping[frame_index] = new_photo_index
        return self.fill_frames(template_info, base_canvas, photos, frame_mapping=mapping, fit_mode=fit_mode)

    @staticmethod
    def change_background(design_canvas: Image.Image, background_path: str) -> Image.Image:
        with Image.open(background_path) as bg:
            bg = bg.convert("RGBA").resize(design_canvas.size, Image.LANCZOS)
        result = bg.copy()
        result.alpha_composite(design_canvas.convert("RGBA"))
        return result

    @staticmethod
    def add_overlay(design_canvas: Image.Image, overlay_path: str) -> Image.Image:
        with Image.open(overlay_path) as overlay:
            overlay = overlay.convert("RGBA").resize(design_canvas.size, Image.LANCZOS)
        result = design_canvas.convert("RGBA").copy()
        result.alpha_composite(overlay)
        return result

    @staticmethod
    def add_text(design_canvas: Image.Image, text: str, position: Tuple[int, int], font_size: int = 48,
                 color: Tuple[int, int, int, int] = (255, 255, 255, 255), font_path: Optional[str] = None) -> Image.Image:
        result = design_canvas.convert("RGBA").copy()
        draw = ImageDraw.Draw(result)
        try:
            font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default(size=font_size)
        except Exception:
            font = ImageFont.load_default()
        draw.text(position, text, fill=color, font=font)
        return result
