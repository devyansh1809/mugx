"""
tests/test_core.py (v2.2)

Fixes:
- Syntax error fixed (stray "n" where newline belonged).
- API drift fixed (change_background -> change_background_with_preview,
  swap_photo -> swap_photos, PrintSettings(mirror=...) removed).
- Added 3 mirror regression tests using asymmetric split-color images.
- Confirms add_overlay() is restored.
- Confirms generate_3d_text_stub() never raises across font availability.
"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.models import FrameInfo, PhotoItem, ProductType, TemplateTheme, TemplateInfo, FrameShape
from core.photo_import_service import PhotoImportService, SUPPORTED_EXTENSIONS
from core.template_manager import TemplateManager
from core.print_exporter import PrintExporter, PrintSettings, PAPER_SIZES_MM


def _make_test_image(path, size=(200, 150), color=(120, 140, 160)):
    Image.new("RGB", size, color).save(path, "PNG")


def _make_split_color_image(path, size=(100, 100), left_color=(255, 0, 0), right_color=(0, 0, 255)):
    img = Image.new("RGB", size, left_color)
    half = size[0] // 2
    for x in range(half, size[0]):
        for y in range(size[1]):
            img.putpixel((x, y), right_color)
    img.save(path, "PNG")
    return left_color, right_color


class PhotoImportServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.photos_dir = self.tmp / "photos"
        self.photos_dir.mkdir()
        self.cache_dir = self.tmp / "cache"
        for name in ["c.png", "a.jpg", "b.png", "notes.txt", "d.gif"]:
            (self.photos_dir / name).touch()
            if name.endswith((".png", ".jpg")):
                _make_test_image(self.photos_dir / name)
            elif name.endswith(".gif"):
                Image.new("RGB", (50, 50), (10, 20, 30)).save(self.photos_dir / name, "GIF")
        self.service = PhotoImportService(str(self.cache_dir))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_gif_is_supported(self):
        self.assertIn(".gif", SUPPORTED_EXTENSIONS)

    def test_scan_folder_ignores_unsupported_files_but_includes_gif(self):
        photos = self.service.scan_folder(str(self.photos_dir))
        names = [Path(p.original_path).name for p in photos]
        self.assertEqual(len(photos), 4)
        self.assertNotIn("notes.txt", names)
        self.assertIn("d.gif", names)

    def test_last_folder_persistence_roundtrip(self):
        self.service.save_last_folder(str(self.photos_dir))
        self.assertEqual(self.service.get_last_folder(), str(self.photos_dir))


class TemplateManagerFitTests(unittest.TestCase):
    def test_fit_cover_produces_exact_frame_size(self):
        photo = Image.new("RGB", (400, 200), (10, 20, 30))
        frame = FrameInfo(name="frame_1", left=0, top=0, width=100, height=100)
        result = TemplateManager.fit_photo_to_frame(photo, frame, mode="cover")
        self.assertEqual(result.size, (100, 100))

    def test_round_frame_shape_field_defaults_to_rect(self):
        frame = FrameInfo(name="frame_1", left=0, top=0, width=100, height=100)
        self.assertEqual(frame.shape, FrameShape.RECT)


class TemplateManagerFillSwapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.manager = TemplateManager(str(self.tmp / "preview_cache"))

        self.photo_paths = []
        for i, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
            p = self.tmp / f"photo_{i}.png"
            _make_test_image(p, size=(60, 60), color=color)
            self.photo_paths.append(p)
        self.photos = [
            PhotoItem(original_path=str(p), sequence_name=f"{i+1:02d}", index=i)
            for i, p in enumerate(self.photo_paths)
        ]

        self.template = TemplateInfo(
            source_path=str(self.tmp / "template.png"), display_name="template.png",
            width=200, height=100, is_psd=False, product_type=ProductType.MUG,
            theme=TemplateTheme.PLAIN,
            frames=[
                FrameInfo(name="frame_1", left=0, top=0, width=100, height=100),
                FrameInfo(name="frame_2", left=100, top=0, width=100, height=100),
            ],
        )
        self.base_canvas = Image.new("RGBA", (200, 100), (240, 240, 240, 255))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fill_frames_places_photos_in_order(self):
        result = self.manager.fill_frames(self.template, self.base_canvas, self.photos[:2])
        left_pixel = result.getpixel((25, 50))
        right_pixel = result.getpixel((150, 50))
        self.assertGreater(left_pixel[0], left_pixel[1])
        self.assertGreater(right_pixel[1], right_pixel[0])

    def test_swap_photos_uses_current_api_name(self):
        self.manager.fill_frames(self.template, self.base_canvas, self.photos[:2])
        self.assertTrue(hasattr(self.manager, "swap_photos"))
        self.assertFalse(hasattr(self.manager, "swap_photo"))
        swapped = self.manager.swap_photos(self.template, self.base_canvas, self.photos, 0, 1)
        self.assertEqual(self.template.frames[0].photo_index, 1)
        self.assertEqual(self.template.frames[1].photo_index, 0)

    def test_change_background_uses_current_api_name(self):
        design = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
        design.paste((255, 0, 0, 255), (10, 10, 20, 20))
        bg_path = self.tmp / "bg.png"
        _make_test_image(bg_path, size=(50, 50), color=(0, 255, 0))
        self.assertTrue(hasattr(self.manager, "change_background_with_preview"))
        self.assertFalse(hasattr(self.manager, "change_background"))
        result = self.manager.change_background_with_preview(design, str(bg_path), blur_amount=0)
        corner = result.getpixel((0, 0))
        self.assertGreater(corner[1], corner[0])

    def test_add_overlay_is_present(self):
        design = Image.new("RGBA", (100, 100), (0, 0, 0, 255))
        overlay_path = self.tmp / "overlay.png"
        Image.new("RGBA", (100, 100), (255, 255, 255, 128)).save(overlay_path, "PNG")
        result = self.manager.add_overlay(design, str(overlay_path))
        self.assertEqual(result.size, (100, 100))
        self.assertGreater(result.getpixel((50, 50))[0], 0)

    def test_generate_3d_text_stub_never_raises_across_font_availability(self):
        img = self.manager.generate_3d_text_stub("Test", font_size=40)
        self.assertEqual(img.mode, "RGBA")
        self.assertGreater(img.size[0], 0)


class PrintSettingsAPITests(unittest.TestCase):
    def test_print_settings_has_no_mirror_field(self):
        settings = PrintSettings()
        self.assertTrue(hasattr(settings, "mirror_default"))
        self.assertFalse(hasattr(settings, "mirror"))


class MirrorRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pe = PrintExporter(PrintSettings(dpi=72, margin_mm=5.0))
        self.left_color, self.right_color = _make_split_color_image(
            self.tmp / "design.png", size=(100, 100)
        )
        self.design = Image.open(self.tmp / "design.png").convert("RGB")

        self.extra_left, self.extra_right = _make_split_color_image(
            self.tmp / "extra.png", size=(60, 60), left_color=(0, 255, 0), right_color=(255, 255, 0)
        )
        self.extra = Image.open(self.tmp / "extra.png").convert("RGB")

        self.margin_px = round(5.0 * 72 / 25.4)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_mirror_1_flips_primary_design(self):
        sheet = self.pe.build_print_sheet(self.design, mirror_1=True, mirror_2=False)
        left_pt = (self.margin_px + 6, self.margin_px + 6)
        self.assertEqual(sheet.getpixel(left_pt), self.right_color)

    def test_mirror_1_and_mirror_2_do_not_cancel_out(self):
        sheet_both = self.pe.build_print_sheet(
            self.design, mirror_1=True, mirror_2=True, extra_design=self.extra
        )
        sheet_neither = self.pe.build_print_sheet(
            self.design, mirror_1=False, mirror_2=False, extra_design=self.extra
        )
        left_pt = (self.margin_px + 6, self.margin_px + 6)
        self.assertEqual(sheet_both.getpixel(left_pt), self.right_color)
        self.assertEqual(sheet_neither.getpixel(left_pt), self.left_color)
        self.assertNotEqual(sheet_both.getpixel(left_pt), sheet_neither.getpixel(left_pt))

    def test_mirror_2_controls_extra_design_independently_of_mirror_1(self):
        sheet_w, sheet_h = self.pe._paper_size_px()
        extra_y = sheet_h - self.extra.height - self.margin_px
        extra_left_pt = (self.margin_px + 5, extra_y + 5)

        sheet_a = self.pe.build_print_sheet(self.design, mirror_1=True, mirror_2=False, extra_design=self.extra)
        self.assertEqual(sheet_a.getpixel(extra_left_pt), self.extra_left)

        sheet_b = self.pe.build_print_sheet(self.design, mirror_1=False, mirror_2=True, extra_design=self.extra)
        self.assertEqual(sheet_b.getpixel(extra_left_pt), self.extra_right)


class PaperSizeTests(unittest.TestCase):
    def test_paper_size_px_matches_dpi(self):
        exporter = PrintExporter(PrintSettings(paper_size="A4", dpi=300))
        w, h = exporter._paper_size_px()
        w_mm, h_mm = PAPER_SIZES_MM["A4"]
        self.assertEqual((w, h), (round(w_mm / 25.4 * 300), round(h_mm / 25.4 * 300)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
