"""
core/template_manager.py (v2.2)

Fixes:
- generate_3d_text_stub() no longer hardcodes a Linux-only font path
  that silently fails on macOS. Now tries a cross-platform candidate list
  (macOS, Linux, Windows) before falling back to the default font.
- add_text() uses the same cross-platform font resolution.
- add_overlay() restored (was present in v1, silently dropped in v2).
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

from core.models import FrameInfo, FrameShape, ProductType, TemplateTheme, TemplateInfo, PhotoItem

logger = logging.getLogger("SubliStudio.TemplateManager")

FRAME_NAME_PATTERN = re.compile(r"^frame(?:_round)?[_\-\s]*\d+$", re.IGNORECASE)

_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:\\Windows\\Fonts\\arialbd.ttf",
]


def _resolve_font(font_size: int, font_path: Optional[str] = None) -> ImageFont.FreeTypeFont:
    candidates = ([font_path] if font_path else []) + _FONT_CANDIDATES
    for path in candidates:
        try:
            return ImageFont.truetype(path, font_size)
        except Exception:
            continue
    logger.warning(
        "No TTF font found among candidates; falling back to Pillow's low-resolution default bitmap font."
    )
    return ImageFont.load_default()


class TemplateManager:
    def __init__(self, preview_cache_dir: str):
        self.preview_cache_dir = Path(preview_cache_dir)
        self.preview_cache_dir.mkdir(parents=True, exist_ok=True)

    def load_template(self, file_path: str, product_type: ProductType,
                      theme: TemplateTheme = TemplateTheme.PLAIN) -> Tuple[Optional[TemplateInfo], Optional[str]]:
        path = Path(file_path)
        if not path.exists():
            logger.error("Template file does not exist: %s", file_path)
            return None, None

        is_psd = path.suffix.lower() in (".psd", ".psb")
        try:
            if is_psd:
                info, flattened = self._load_psd(path, product_type, theme)
            else:
                info, flattened = self._load_image_template(path, product_type, theme)
        except Exception:
            logger.exception("Failed to load template %s", file_path)
            return None, None

        preview_path = self.preview_cache_dir / f"{path.stem}_preview.png"
        flattened.convert("RGB").save(preview_path, "PNG")
        return info, str(preview_path)

    def _load_psd(self, path: Path, product_type: ProductType, theme: TemplateTheme) -> Tuple[TemplateInfo, Image.Image]:
        from psd_tools import PSDImage

        psd = PSDImage.open(str(path))
        flattened = psd.composite()
        if flattened is None:
            flattened = Image.new("RGBA", (psd.width, psd.height), (240, 240, 240, 255))

        frames = self.detect_frames_psd(psd)
        phys_w = getattr(psd, 'width', 0) / 118.11
        phys_h = getattr(psd, 'height', 0) / 118.11

        info = TemplateInfo(
            source_path=str(path), display_name=path.name, width=psd.width, height=psd.height,
            is_psd=True, product_type=product_type, theme=theme, frames=frames,
            original_physical_width_cm=phys_w, original_physical_height_cm=phys_h,
        )
        return info, flattened

    def _load_image_template(self, path: Path, product_type: ProductType, theme: TemplateTheme) -> Tuple[TemplateInfo, Image.Image]:
        img = Image.open(path).convert("RGBA")
        frames = self.detect_frames_sidecar(path, img.size)

        phys_w = img.width / 118.11
        phys_h = img.height / 118.11

        info = TemplateInfo(
            source_path=str(path), display_name=path.name, width=img.width, height=img.height,
            is_psd=False, product_type=product_type, theme=theme, frames=frames,
            original_physical_width_cm=phys_w, original_physical_height_cm=phys_h,
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
                    shape = FrameShape.ROUND if "round" in name.lower() else FrameShape.RECT
                    frames.append(FrameInfo(
                        name=name, left=bbox[0], top=bbox[1],
                        width=bbox[2] - bbox[0], height=bbox[3] - bbox[1],
                        shape=shape,
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
                frames = [FrameInfo.from_dict(item) for item in data]
                frames.sort(key=lambda f: f.order_key)
                return frames
            except Exception:
                logger.exception("Failed to parse frame sidecar %s", sidecar)

        width, height = canvas_size
        return [FrameInfo(name="frame_1", left=0, top=0, width=width, height=height)]

    def change_page_size(self, template: TemplateInfo, new_width_cm: float, new_height_cm: float) -> TemplateInfo:
        if template.original_physical_width_cm <= 0 or template.original_physical_height_cm <= 0:
            return template

        scale_x = new_width_cm / template.original_physical_width_cm
        scale_y = new_height_cm / template.original_physical_height_cm

        new_width = round(template.width * scale_x)
        new_height = round(template.height * scale_y)

        new_frames = []
        for f in template.frames:
            new_frames.append(FrameInfo(
                name=f.name,
                left=round(f.left * scale_x),
                top=round(f.top * scale_y),
                width=round(f.width * scale_x),
                height=round(f.height * scale_y),
                shape=f.shape,
                photo_index=f.photo_index,
                photo_scale=f.photo_scale,
                photo_offset_x=round(f.photo_offset_x * scale_x),
                photo_offset_y=round(f.photo_offset_y * scale_y),
            ))

        return TemplateInfo(
            source_path=template.source_path,
            display_name=template.display_name,
            width=new_width,
            height=new_height,
            is_psd=template.is_psd,
            product_type=template.product_type,
            theme=template.theme,
            frames=new_frames,
            original_physical_width_cm=new_width_cm,
            original_physical_height_cm=new_height_cm,
        )

    @staticmethod
    def fit_photo_to_frame(photo: Image.Image, frame: FrameInfo, mode: str = "cover") -> Image.Image:
        target_w = round(frame.width * frame.photo_scale)
        target_h = round(frame.height * frame.photo_scale)
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

    def fill_frames(self, template: TemplateInfo, base_canvas: Image.Image, photos: List[PhotoItem],
                     frame_mapping: Optional[dict] = None, fit_mode: str = "cover",
                     output_png: Optional[str] = None) -> Image.Image:
        if not template.frames:
            raise ValueError("Template has no detected frames to fill.")
        if not photos:
            raise ValueError("No photos supplied to fill frames with.")

        canvas = base_canvas.convert("RGBA").copy()
        frame_mapping = frame_mapping or {}

        next_photo_cursor = 0
        for frame_idx, frame in enumerate(template.frames):
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

            offset_x = frame.left + frame.photo_offset_x
            offset_y = frame.top + frame.photo_offset_y

            if frame.shape == FrameShape.ROUND:
                mask = Image.new("L", fitted.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse([0, 0, fitted.width-1, fitted.height-1], fill=255)
                fitted.putalpha(mask)

            canvas.paste(fitted, (offset_x, offset_y), fitted)
            frame.photo_index = photo_idx

        if output_png:
            canvas.convert("RGB").save(output_png, "PNG")
        return canvas

    def resize_photo_in_frame(self, template: TemplateInfo, base_canvas: Image.Image, photos: List[PhotoItem],
                               frame_index: int, new_scale: float, offset_x: int, offset_y: int,
                               fit_mode: str = "cover") -> Image.Image:
        if frame_index < 0 or frame_index >= len(template.frames):
            raise ValueError(f"Invalid frame index: {frame_index}")

        frame = template.frames[frame_index]
        frame.photo_scale = new_scale
        frame.photo_offset_x = offset_x
        frame.photo_offset_y = offset_y

        mapping = {idx: f.photo_index for idx, f in enumerate(template.frames) if f.photo_index is not None}
        return self.fill_frames(template, base_canvas, photos, frame_mapping=mapping, fit_mode=fit_mode)

    def add_extra_photo(self, canvas: Image.Image, photo: PhotoItem, position: Tuple[int, int],
                         border_size: int = 10, border_color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
        with Image.open(photo.original_path) as src:
            src = src.convert("RGBA")

        max_size = (200, 200)
        src.thumbnail(max_size, Image.LANCZOS)

        bordered = Image.new("RGBA",
                            (src.width + border_size*2, src.height + border_size*2),
                            border_color)
        bordered.paste(src, (border_size, border_size), src)

        shadow = bordered.copy()
        shadow = ImageOps.expand(shadow, border=5, fill=(0, 0, 0, 100))
        shadow = shadow.filter(ImageFilter.GaussianBlur(3))

        result = canvas.convert("RGBA").copy()
        result.paste(shadow, (position[0]-5, position[1]-5), shadow)
        result.paste(bordered, position, bordered)

        return result

    def swap_photos(self, template: TemplateInfo, base_canvas: Image.Image, photos: List[PhotoItem],
                    frame_index_1: int, frame_index_2: int, fit_mode: str = "cover") -> Image.Image:
        if frame_index_1 < 0 or frame_index_1 >= len(template.frames):
            raise ValueError(f"Invalid frame index 1: {frame_index_1}")
        if frame_index_2 < 0 or frame_index_2 >= len(template.frames):
            raise ValueError(f"Invalid frame index 2: {frame_index_2}")

        idx1 = template.frames[frame_index_1].photo_index
        idx2 = template.frames[frame_index_2].photo_index
        template.frames[frame_index_1].photo_index = idx2
        template.frames[frame_index_2].photo_index = idx1

        mapping = {idx: f.photo_index for idx, f in enumerate(template.frames) if f.photo_index is not None}
        return self.fill_frames(template, base_canvas, photos, frame_mapping=mapping, fit_mode=fit_mode)

    def change_background_with_preview(self, design_canvas: Image.Image, background_path: str,
                                        blur_amount: int = 0) -> Image.Image:
        with Image.open(background_path) as bg:
            bg = bg.convert("RGBA").resize(design_canvas.size, Image.LANCZOS)
            if blur_amount > 0:
                bg = bg.filter(ImageFilter.GaussianBlur(blur_amount))

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

    def add_readymade_text(self, design_canvas: Image.Image, preset_name: str,
                           position: Tuple[int, int]) -> Image.Image:
        presets = {
            "Happy Birthday": {"text": "Happy Birthday!", "font_size": 48, "color": (255, 215, 0, 255)},
            "Congratulations": {"text": "Congratulations!", "font_size": 42, "color": (255, 100, 100, 255)},
            "Love You": {"text": "Love You", "font_size": 52, "color": (255, 20, 147, 255)},
            "Happy Diwali": {"text": "Happy Diwali", "font_size": 46, "color": (255, 140, 0, 255)},
            "Happy Holi": {"text": "Happy Holi", "font_size": 46, "color": (147, 112, 219, 255)},
            "Happy New Year": {"text": "Happy New Year", "font_size": 44, "color": (255, 215, 0, 255)},
        }

        preset = presets.get(preset_name, {"text": preset_name, "font_size": 40, "color": (255, 255, 255, 255)})
        return self.add_text(design_canvas, preset["text"], position,
                            font_size=preset["font_size"], color=preset["color"])

    def generate_3d_text_stub(self, text: str, font_size: int = 60,
                              color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
        img = Image.new("RGBA", (400, 150), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = _resolve_font(font_size)
        for offset in [(3, 3), (4, 4), (5, 5)]:
            draw.text((20 + offset[0], 20 + offset[1]), text, fill=(0, 0, 0, 150), font=font)
        draw.text((20, 20), text, fill=color + (255,), font=font)
        return img

    @staticmethod
    def add_text(design_canvas: Image.Image, text: str, position: Tuple[int, int], font_size: int = 48,
                 color: Tuple[int, int, int, int] = (255, 255, 255, 255), font_path: Optional[str] = None) -> Image.Image:
        result = design_canvas.convert("RGBA").copy()
        draw = ImageDraw.Draw(result)
        font = _resolve_font(font_size, font_path)
        draw.text(position, text, fill=color, font=font)
        return result
