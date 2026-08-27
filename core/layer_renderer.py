"""
Phase 4: Layer Editor - Layer Renderer
"""

from typing import Optional, Tuple, Any
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io


class LayerRenderer:
    def __init__(self, document: Any): self.document = document
    
    def render(self, width: Optional[int] = None, height: Optional[int] = None, dpi: Optional[int] = None) -> Image.Image:
        canvas_width = int(width or self.document.canvas_width)
        canvas_height = int(height or self.document.canvas_height)
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
        for layer in self.document.layers:
            if not layer.properties.visible: continue
            layer_image = self._render_layer(layer, canvas_width, canvas_height)
            if layer_image:
                if layer.properties.opacity < 1.0:
                    alpha = layer_image.split()[3]
                    alpha = alpha.point(lambda p: int(p * layer.properties.opacity))
                    layer_image.putalpha(alpha)
                canvas = self._composite_layers(canvas, layer_image, layer.properties.blend_mode)
        return canvas
    
    def _render_layer(self, layer: Any, cw: int, ch: int) -> Optional[Image.Image]:
        t = layer.type
        if t == "background": return self._render_background(layer, cw, ch)
        elif t == "photo": return self._render_photo(layer, cw, ch)
        elif t == "text": return self._render_text(layer, cw, ch)
        elif t == "clip_art": return self._render_clip_art(layer, cw, ch)
        elif t == "overlay": return self._render_overlay(layer, cw, ch)
        return None
    
    def _render_background(self, layer: Any, w: int, h: int) -> Image.Image:
        image = Image.new("RGBA", (w, h))
        draw = ImageDraw.Draw(image)
        if layer.color:
            color = self._hex_to_rgba(layer.color)
            draw.rectangle([0, 0, w, h], fill=color)
        if layer.image_path or layer.image_data:
            try:
                if layer.image_data: bg_image = Image.open(io.BytesIO(layer.image_data))
                else: bg_image = Image.open(layer.image_path)
                bg_image = bg_image.convert("RGBA")
                if layer.blur_radius > 0: bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=layer.blur_radius))
                bg_image = bg_image.resize((w, h), Image.Resampling.LANCZOS)
                if layer.properties.opacity < 1.0:
                    alpha = bg_image.split()[3]
                    alpha = alpha.point(lambda p: int(p * layer.properties.opacity))
                    bg_image.putalpha(alpha)
                image = Image.alpha_composite(image, bg_image)
            except Exception as e: print(f"Warning: Could not load background image: {e}")
        return image
    
    def _render_photo(self, layer: Any, cw: int, ch: int) -> Optional[Image.Image]:
        try:
            if layer.image_data: image = Image.open(io.BytesIO(layer.image_data))
            else: image = Image.open(layer.image_path)
            image = image.convert("RGBA")
            if layer.crop_rect:
                x, y, w, h = layer.crop_rect
                image = image.crop((x, y, x + w, y + h))
            if layer.flip_horizontal: image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if layer.flip_vertical: image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            transform = layer.transform
            if transform.scale != 1.0 or transform.rotation != 0.0:
                new_width = int(image.width * transform.scale)
                new_height = int(image.height * transform.scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            if transform.rotation != 0.0: image = image.rotate(-transform.rotation, expand=True, resample=Image.Resampling.BICUBIC)
            layer_image = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            layer_image.paste(image, (int(transform.x), int(transform.y)))
            return layer_image
        except Exception as e: print(f"Warning: Could not render photo layer: {e}"); return None
    
    def _render_text(self, layer: Any, cw: int, ch: int) -> Image.Image:
        image = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        try:
            try: font = ImageFont.truetype(layer.font_family, int(layer.font_size))
            except: font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), layer.text, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            transform = layer.transform
            x, y = transform.x, transform.y
            if layer.alignment == "center": x -= text_width / 2
            elif layer.alignment == "right": x -= text_width
            if layer.background_color:
                bg_color = self._hex_to_rgba(layer.background_color)
                padding = 5
                draw.rectangle([x - padding, y - padding, x + text_width + padding, y + text_height + padding], fill=bg_color)
            if layer.border_color and layer.border_width > 0:
                border_color = self._hex_to_rgba(layer.border_color)
                for offset in range(int(layer.border_width)):
                    draw.text((x - offset, y), layer.text, font=font, fill=border_color)
                    draw.text((x + offset, y), layer.text, font=font, fill=border_color)
                    draw.text((x, y - offset), layer.text, font=font, fill=border_color)
                    draw.text((x, y + offset), layer.text, font=font, fill=border_color)
            text_color = self._hex_to_rgba(layer.color)
            draw.text((x, y), layer.text, font=font, fill=text_color)
            if transform.rotation != 0.0: image = image.rotate(-transform.rotation, expand=False, resample=Image.Resampling.BICUBIC)
            return image
        except Exception as e: print(f"Warning: Could not render text layer: {e}"); return Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    
    def _render_clip_art(self, layer: Any, cw: int, ch: int) -> Optional[Image.Image]:
        try:
            if layer.asset_data: image = Image.open(io.BytesIO(layer.asset_data))
            else: image = Image.open(layer.asset_path)
            image = image.convert("RGBA")
            if layer.tint_color:
                tint = self._hex_to_rgba(layer.tint_color)
                tint_layer = Image.new("RGBA", image.size, tint)
                image = Image.alpha_composite(image, tint_layer)
            transform = layer.transform
            if transform.scale != 1.0:
                new_width = int(image.width * transform.scale)
                new_height = int(image.height * transform.scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            if transform.rotation != 0.0: image = image.rotate(-transform.rotation, expand=True, resample=Image.Resampling.BICUBIC)
            layer_image = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            layer_image.paste(image, (int(transform.x), int(transform.y)))
            return layer_image
        except Exception as e: print(f"Warning: Could not render clip-art: {e}"); return None
    
    def _render_overlay(self, layer: Any, cw: int, ch: int) -> Optional[Image.Image]:
        try:
            if layer.asset_data: image = Image.open(io.BytesIO(layer.asset_data))
            else: image = Image.open(layer.asset_path)
            image = image.convert("RGBA")
            if layer.overlay_type == "effect": image = image.resize((cw, ch), Image.Resampling.LANCZOS)
            transform = layer.transform
            if transform.scale != 1.0:
                new_width = int(image.width * transform.scale)
                new_height = int(image.height * transform.scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            if transform.rotation != 0.0: image = image.rotate(-transform.rotation, expand=True, resample=Image.Resampling.BICUBIC)
            layer_image = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            layer_image.paste(image, (int(transform.x), int(transform.y)))
            return layer_image
        except Exception as e: print(f"Warning: Could not render overlay: {e}"); return None
    
    def _composite_layers(self, base: Image.Image, overlay: Image.Image, blend_mode: str) -> Image.Image:
        if blend_mode in ("normal", "none"): return Image.alpha_composite(base, overlay)
        try:
            if blend_mode == "multiply":
                base_rgb, overlay_rgb = base.convert("RGB"), overlay.convert("RGB")
                result = Image.blend(base_rgb, overlay_rgb, 0.5)
                return result.convert("RGBA")
            elif blend_mode == "screen":
                base_rgb, overlay_rgb = base.convert("RGB"), overlay.convert("RGB")
                result = Image.blend(base_rgb, overlay_rgb, 0.5)
                return result.convert("RGBA")
            else: return Image.alpha_composite(base, overlay)
        except: return Image.alpha_composite(base, overlay)
    
    def _hex_to_rgba(self, hex_color: str) -> Tuple[int, int, int, int]:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3: hex_color = "".join([c*2 for c in hex_color])
        if len(hex_color) == 6: hex_color += "FF"
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        a = int(hex_color[6:8], 16) if len(hex_color) >= 8 else 255
        return (r, g, b, a)
    
    def render_thumbnail(self, max_size: int = 200) -> Image.Image:
        width, height = self.document.canvas_width, self.document.canvas_height
        if width > height:
            thumb_width, thumb_height = max_size, int(height * (max_size / width))
        else:
            thumb_height, thumb_width = max_size, int(width * (max_size / height))
        full_render = self.render()
        thumbnail = full_render.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        return thumbnail
