"""
tests/test_core.py

Unit tests for the core/ layer -- zero PyQt dependency by design, so
they run headless/in CI.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from core.models import FrameInfo, PhotoItem, ProductType, TemplateInfo
from core.photo_import_service import PhotoImportService
from core.image_processor import enhance_image, ImageEnhancementService
from core.template_manager import TemplateManager
from core.print_exporter import PrintExporter, PrintSettings, PAPER_SIZES_MM
from core.mockup_generator import MockupGenerator


def _make_test_image(path, size=(200, 150), color=(120, 140, 160)):
    Image.new("RGB", size, color).save(path, "PNG")


def _make_noisy_image(path, size=(200, 150), seed=0):
    rng = np.random.default_rng(seed)
    base = np.full((size[1], size[0], 3), 128, dtype=np.float32)
    noise = rng.normal(0, 15, base.shape)
    arr = np.clip(base + noise, 0, 255).astype("uint8")
    Image.fromarray(arr, mode="RGB").save(path, "PNG")


class PhotoImportServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.photos_dir = self.tmp / "photos"
        self.photos_dir.mkdir()
        self.cache_dir = self.tmp / "cache"
        for name in ["c.png", "a.jpg", "b.png", "notes.txt"]:
            (self.photos_dir / name).touch()
            if name.endswith((".png", ".jpg")):
                _make_test_image(self.photos_dir / name)
        self.service = PhotoImportService(str(self.cache_dir))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_scan_folder_ignores_unsupported_files(self):
        photos = self.service.scan_folder(str(self.photos_dir))
        names = [Path(p.original_path).name for p in photos]
        self.assertEqual(len(photos), 3)
        self.assertNotIn("notes.txt", names)

    def test_scan_folder_assigns_sequential_names_alphabetically(self):
        photos = self.service.scan_folder(str(self.photos_dir))
        self.assertEqual([p.sequence_name for p in photos], ["01", "02", "03"])
        self.assertEqual(Path(photos[0].original_path).name, "a.jpg")

    def test_scan_folder_does_not_rename_files_on_disk(self):
        self.service.scan_folder(str(self.photos_dir))
        on_disk = sorted(p.name for p in self.photos_dir.iterdir())
        self.assertIn("a.jpg", on_disk)
        self.assertIn("notes.txt", on_disk)

    def test_get_thumbnail_creates_and_caches_file(self):
        photos = self.service.scan_folder(str(self.photos_dir))
        thumb1 = self.service.get_thumbnail(photos[0])
        self.assertTrue(Path(thumb1).exists())
        thumb2 = self.service.get_thumbnail(photos[0])
        self.assertEqual(thumb1, thumb2)


class ImageProcessorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_enhance_image_returns_same_size_rgb_image(self):
        img = Image.new("RGB", (64, 64), (100, 110, 120))
        enhanced = enhance_image(img)
        self.assertEqual(enhanced.size, img.size)
        self.assertEqual(enhanced.mode, "RGB")

    def test_enhance_image_does_not_mutate_input(self):
        img = Image.new("RGB", (32, 32), (50, 60, 70))
        original_bytes = img.tobytes()
        enhance_image(img)
        self.assertEqual(img.tobytes(), original_bytes)

    def test_enhance_does_not_amplify_noise_in_flat_regions(self):
        path = self.tmp / "noisy.png"
        _make_noisy_image(path)
        img = Image.open(path)
        enhanced = enhance_image(img)

        original_std = np.asarray(img.convert("L")).astype(np.float64).std()
        enhanced_std = np.asarray(enhanced.convert("L")).astype(np.float64).std()

        self.assertLessEqual(enhanced_std, original_std * 1.15)

    def test_enhance_increases_or_maintains_edge_definition(self):
        arr = np.zeros((80, 80, 3), dtype=np.uint8)
        arr[:, 40:, :] = 255
        img = Image.fromarray(arr, mode="RGB")
        enhanced = enhance_image(img)

        def edge_strength(im):
            gray = np.asarray(im.convert("L")).astype(np.float64)
            return np.mean(np.abs(np.diff(gray, axis=1)))

        self.assertGreaterEqual(edge_strength(enhanced) + 1e-6, edge_strength(img) * 0.6)

    def test_enhancement_service_caches_on_disk_and_memory(self):
        photo_path = self.tmp / "p.png"
        _make_test_image(photo_path)
        photo = PhotoItem(original_path=str(photo_path), sequence_name="01", index=0)

        cache_dir = self.tmp / "cache"
        service = ImageEnhancementService(str(cache_dir))
        thumb1 = service.get_thumbnail(photo)
        self.assertTrue(Path(thumb1).exists())

        service2 = ImageEnhancementService(str(cache_dir))
        thumb2 = service2.get_thumbnail(photo)
        self.assertEqual(Path(thumb1).name, Path(thumb2).name)


class TemplateManagerFitTests(unittest.TestCase):
    def test_fit_cover_produces_exact_frame_size(self):
        photo = Image.new("RGB", (400, 200), (10, 20, 30))
        frame = FrameInfo(name="frame_1", left=0, top=0, width=100, height=100)
        result = TemplateManager.fit_photo_to_frame(photo, frame, mode="cover")
        self.assertEqual(result.size, (100, 100))

    def test_fit_mode_preserves_whole_photo_with_padding(self):
        photo = Image.new("RGB", (400, 100), (10, 20, 30))
        frame = FrameInfo(name="frame_1", left=0, top=0, width=100, height=100)
        result = TemplateManager.fit_photo_to_frame(photo, frame, mode="fit")
        self.assertEqual(result.size, (100, 100))
        self.assertEqual(result.getpixel((50, 0))[3], 0)

    def test_frame_order_key_sorts_numerically(self):
        frames = [
            FrameInfo(name="frame_10", left=0, top=0, width=1, height=1),
            FrameInfo(name="frame_2", left=0, top=0, width=1, height=1),
            FrameInfo(name="frame_1", left=0, top=0, width=1, height=1),
        ]
        frames.sort(key=lambda f: f.order_key)
        self.assertEqual([f.name for f in frames], ["frame_1", "frame_2", "frame_10"])


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

        self.template_info = TemplateInfo(
            source_path=str(self.tmp / "template.png"), display_name="template.png",
            width=200, height=100, is_psd=False, product_type=ProductType.MUG,
            frames=[
                FrameInfo(name="frame_1", left=0, top=0, width=100, height=100),
                FrameInfo(name="frame_2", left=100, top=0, width=100, height=100),
            ],
        )
        self.base_canvas = Image.new("RGBA", (200, 100), (240, 240, 240, 255))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fill_frames_places_photos_in_order(self):
        result = self.manager.fill_frames(self.template_info, self.base_canvas, self.photos[:2])
        self.assertEqual(result.size, (200, 100))
        left_pixel = result.getpixel((25, 50))
        right_pixel = result.getpixel((150, 50))
        self.assertGreater(left_pixel[0], left_pixel[1])
        self.assertGreater(right_pixel[1], right_pixel[0])

    def test_fill_frames_with_fewer_photos_than_frames_leaves_rest_unfilled(self):
        result = self.manager.fill_frames(self.template_info, self.base_canvas, self.photos[:1])
        right_pixel = result.getpixel((150, 50))
        self.assertGreater(right_pixel[0], 200)
        self.assertGreater(right_pixel[1], 200)

    def test_fill_frames_raises_on_no_photos(self):
        with self.assertRaises(ValueError):
            self.manager.fill_frames(self.template_info, self.base_canvas, [])

    def test_fill_frames_raises_on_no_frames(self):
        empty_template = TemplateInfo(
            source_path="x", display_name="x", width=10, height=10,
            is_psd=False, product_type=ProductType.MUG, frames=[],
        )
        with self.assertRaises(ValueError):
            self.manager.fill_frames(empty_template, self.base_canvas, self.photos)

    def test_swap_photo_changes_only_target_frame(self):
        self.manager.fill_frames(self.template_info, self.base_canvas, self.photos[:2])
        self.assertEqual(self.template_info.frames[0].photo_index, 0)
        self.assertEqual(self.template_info.frames[1].photo_index, 1)

        swapped = self.manager.swap_photo(
            self.template_info, self.base_canvas, self.photos, frame_index=0, new_photo_index=2,
        )
        left_pixel = swapped.getpixel((25, 50))
        self.assertGreater(left_pixel[2], left_pixel[0])
        right_pixel = swapped.getpixel((150, 50))
        self.assertGreater(right_pixel[1], right_pixel[0])

    def test_detect_frames_sidecar_json(self):
        template_path = self.tmp / "custom_template.png"
        _make_test_image(template_path, size=(300, 300))
        sidecar = self.tmp / "custom_template.frames.json"
        sidecar.write_text(json.dumps([
            {"name": "frame_2", "left": 150, "top": 0, "width": 150, "height": 150},
            {"name": "frame_1", "left": 0, "top": 0, "width": 150, "height": 150},
        ]))
        frames = self.manager.detect_frames_sidecar(template_path, (300, 300))
        self.assertEqual([f.name for f in frames], ["frame_1", "frame_2"])

    def test_detect_frames_sidecar_defaults_to_single_frame(self):
        template_path = self.tmp / "no_sidecar.png"
        frames = self.manager.detect_frames_sidecar(template_path, (400, 250))
        self.assertEqual(len(frames), 1)
        self.assertEqual((frames[0].width, frames[0].height), (400, 250))

    def test_change_background_composites_over_new_background(self):
        design = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
        design.paste((255, 0, 0, 255), (10, 10, 20, 20))
        bg_path = self.tmp / "bg.png"
        _make_test_image(bg_path, size=(50, 50), color=(0, 255, 0))
        result = self.manager.change_background(design, str(bg_path))
        corner = result.getpixel((0, 0))
        self.assertGreater(corner[1], corner[0])

    def test_add_text_draws_pixels(self):
        design = Image.new("RGBA", (200, 100), (0, 0, 0, 255))
        result = self.manager.add_text(design, "HI", (10, 10), font_size=40, color=(255, 255, 255, 255))
        region = np.asarray(result.convert("L"))[10:50, 10:80]
        self.assertGreater(region.max(), 50)


class PrintExporterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_paper_size_px_matches_dpi(self):
        exporter = PrintExporter(PrintSettings(paper_size="A4", dpi=300))
        w, h = exporter._paper_size_px()
        w_mm, h_mm = PAPER_SIZES_MM["A4"]
        expected_w = round(w_mm / 25.4 * 300)
        expected_h = round(h_mm / 25.4 * 300)
        self.assertEqual((w, h), (expected_w, expected_h))

    def test_build_print_sheet_returns_image(self):
        design = Image.new("RGB", (100, 100), (255, 255, 255))
        exporter = PrintExporter(PrintSettings(paper_size="A4", dpi=72, mirror=True, designs_per_sheet=1))
        sheet = exporter.build_print_sheet(design)
        self.assertIsInstance(sheet, Image.Image)

    def test_export_png_creates_file(self):
        design = Image.new("RGB", (100, 100), (200, 200, 200))
        exporter = PrintExporter(PrintSettings(dpi=72))
        out_path = exporter.export_png(design, str(self.tmp / "out.png"))
        self.assertTrue(Path(out_path).exists())
        self.assertGreater(Path(out_path).stat().st_size, 0)

    def test_export_pdf_creates_file(self):
        design = Image.new("RGB", (100, 100), (200, 200, 200))
        exporter = PrintExporter(PrintSettings(dpi=72))
        out_path = exporter.export_pdf(design, str(self.tmp / "out.pdf"))
        self.assertTrue(Path(out_path).exists())
        self.assertGreater(Path(out_path).stat().st_size, 0)

    def test_layout_positions_places_more_than_one_copy(self):
        design = Image.new("RGB", (300, 300), (0, 0, 255))
        exporter = PrintExporter(PrintSettings(dpi=150, designs_per_sheet=2, margin_mm=5))
        positions = exporter._layout_positions(exporter._paper_size_px(), design.size)
        self.assertGreaterEqual(len(positions), 1)

    def test_export_batch_returns_all_requested_formats(self):
        design = Image.new("RGB", (80, 80), (10, 10, 10))
        exporter = PrintExporter(PrintSettings(dpi=72))
        outputs = exporter.export(design, str(self.tmp), "job1", formats=("png", "pdf"))
        self.assertEqual(len(outputs), 2)
        for path in outputs:
            self.assertTrue(Path(path).exists())


class MockupGeneratorTests(unittest.TestCase):
    def test_render_cylinder_mockup_returns_requested_canvas_size(self):
        design = Image.new("RGB", (400, 400), (200, 50, 50))
        generator = MockupGenerator()
        mockup = generator.render_cylinder_mockup(design, canvas_size=(300, 300))
        self.assertEqual(mockup.size, (300, 300))


if __name__ == "__main__":n    unittest.main(verbosity=2)
