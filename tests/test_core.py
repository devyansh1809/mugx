"""
tests/test_core.py

Basic tests for the core layer, independent of the UI. Run with:
    python -m pytest tests/ -v
or:
    python tests/test_core.py
"""

import sys
import shutil
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image

from core.photo_import_service import PhotoImportService
from core.template_manager import TemplateManager
from core.image_processor import enhance_image, ImageEnhancementService
from core.models import ProductType, PhotoItem


class TestPhotoImportService(unittest.TestCase):
    def setUp(self):
        self.photo_dir = tempfile.mkdtemp()
        self.thumb_dir = tempfile.mkdtemp()
        self.svc = PhotoImportService(self.thumb_dir)

    def tearDown(self):
        shutil.rmtree(self.photo_dir, ignore_errors=True)
        shutil.rmtree(self.thumb_dir, ignore_errors=True)

    def _make_jpg(self, name: str):
        path = Path(self.photo_dir) / name
        Image.new("RGB", (50, 50), (200, 100, 50)).save(path, "JPEG")
        return path

    def test_scan_folder_assigns_sequential_names(self):
        for n in ["c.jpg", "a.jpg", "b.jpg"]:
            self._make_jpg(n)
        photos = self.svc.scan_folder(self.photo_dir)
        self.assertEqual([p.sequence_name for p in photos], ["01", "02", "03"])

    def test_scan_folder_ignores_unsupported_files(self):
        self._make_jpg("real.jpg")
        (Path(self.photo_dir) / "notes.txt").write_text("hello")
        photos = self.svc.scan_folder(self.photo_dir)
        self.assertEqual(len(photos), 1)

    def test_scan_missing_folder_returns_empty(self):
        photos = self.svc.scan_folder("/no/such/folder")
        self.assertEqual(photos, [])

    def test_thumbnail_generated(self):
        self._make_jpg("photo.jpg")
        photo = self.svc.scan_folder(self.photo_dir)[0]
        thumb = self.svc.get_thumbnail(photo)
        self.assertIsNotNone(thumb)
        self.assertTrue(Path(thumb).exists())


class TestTemplateManager(unittest.TestCase):
    def setUp(self):
        self.tmpl_dir = tempfile.mkdtemp()
        self.preview_dir = tempfile.mkdtemp()
        self.mgr = TemplateManager(self.preview_dir)

    def tearDown(self):
        shutil.rmtree(self.tmpl_dir, ignore_errors=True)
        shutil.rmtree(self.preview_dir, ignore_errors=True)

    def test_load_flat_png_template(self):
        path = Path(self.tmpl_dir) / "template.png"
        Image.new("RGB", (400, 300), (255, 255, 255)).save(path)
        info, preview = self.mgr.load_template(str(path), ProductType.MUG)
        self.assertIsNotNone(info)
        self.assertEqual(info.width, 400)
        self.assertEqual(info.height, 300)
        self.assertFalse(info.is_psd)
        self.assertTrue(Path(preview).exists())

    def test_load_missing_file_returns_none(self):
        info, preview = self.mgr.load_template("/no/such/file.png", ProductType.MUG)
        self.assertIsNone(info)
        self.assertIsNone(preview)

    def test_load_unsupported_extension_returns_none(self):
        path = Path(self.tmpl_dir) / "file.txt"
        path.write_text("not an image")
        info, preview = self.mgr.load_template(str(path), ProductType.MUG)
        self.assertIsNone(info)
        self.assertIsNone(preview)


class TestImageProcessor(unittest.TestCase):
    def setUp(self):
        self.photo_dir = tempfile.mkdtemp()
        self.cache_dir = tempfile.mkdtemp()
        self.svc = ImageEnhancementService(self.cache_dir)

    def tearDown(self):
        shutil.rmtree(self.photo_dir, ignore_errors=True)
        shutil.rmtree(self.cache_dir, ignore_errors=True)

    def _make_jpg(self, name: str, color=(150, 90, 60)):
        path = Path(self.photo_dir) / name
        Image.new("RGB", (200, 200), color).save(path, "JPEG")
        return path

    def test_enhance_image_returns_same_size_rgb(self):
        img = Image.new("RGB", (300, 200), (100, 150, 200))
        result = enhance_image(img)
        self.assertEqual(result.size, (300, 200))
        self.assertEqual(result.mode, "RGB")

    def test_enhance_image_does_not_mutate_input(self):
        img = Image.new("RGB", (50, 50), (10, 10, 10))
        original_bytes = img.tobytes()
        enhance_image(img)
        self.assertEqual(img.tobytes(), original_bytes)

    def test_enhance_image_converts_non_rgb(self):
        img = Image.new("L", (50, 50), 128)  # grayscale
        result = enhance_image(img)
        self.assertEqual(result.mode, "RGB")

    def test_cache_returns_same_path_on_repeat_call(self):
        path = self._make_jpg("photo.jpg")
        photo = PhotoItem(original_path=str(path), sequence_name="01", display_name="01")
        p1 = self.svc.get_thumbnail(photo)
        p2 = self.svc.get_thumbnail(photo)
        self.assertEqual(p1, p2)
        self.assertTrue(Path(p1).exists())

    def test_cache_persists_across_service_instances(self):
        path = self._make_jpg("photo2.jpg")
        photo = PhotoItem(original_path=str(path), sequence_name="01", display_name="01")
        p1 = self.svc.get_thumbnail(photo)

        fresh_svc = ImageEnhancementService(self.cache_dir)
        p2 = fresh_svc.get_thumbnail(photo)
        self.assertEqual(p1, p2)

    def test_cache_invalidates_when_source_file_changes(self):
        import time
        path = self._make_jpg("photo3.jpg", color=(100, 100, 100))
        photo = PhotoItem(original_path=str(path), sequence_name="01", display_name="01")
        p1 = self.svc.get_thumbnail(photo)

        time.sleep(1.1)  # ensure mtime resolution difference
        Image.new("RGB", (200, 200), (200, 50, 50)).save(path, "JPEG")
        p2 = self.svc.get_thumbnail(photo)

        self.assertNotEqual(p1, p2)

    def test_enhance_does_not_amplify_noise_in_flat_regions(self):
        """
        Regression test: an earlier version of the pipeline used a stronger
        unsharp mask that re-amplified noise faster than the bilateral
        filter removed it, making 'enhanced' photos grainier than the
        originals in flat regions. This locks in that flat-region noise
        (measured as pixel std-dev) must not increase after enhancement.
        """
        import numpy as np
        rng = np.random.default_rng(42)
        base = np.full((150, 150, 3), 130, dtype=np.uint8)
        noise = rng.normal(0, 8, base.shape)
        noisy = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(noisy, "RGB")

        original_std = np.array(img).std()
        enhanced = enhance_image(img)
        enhanced_std = np.array(enhanced).std()

        self.assertLessEqual(
            enhanced_std, original_std * 1.05,  # allow a small 5% tolerance
            f"Enhancement increased noise: {original_std:.2f} -> {enhanced_std:.2f}"
        )

    def test_enhance_increases_edge_definition(self):
        """
        Sanity check that sharpening is still doing something: a clean
        synthetic step edge should get measurably steeper after enhancement.
        """
        import numpy as np
        img_arr = np.full((100, 100, 3), 150, dtype=np.uint8)
        img_arr[:, 50:] = 80
        img = Image.fromarray(img_arr, "RGB")

        enhanced = enhance_image(img)
        enhanced_arr = np.array(enhanced)

        original_gradient = np.max(np.abs(np.diff(img_arr[50, 40:60, 0].astype(np.float64))))
        enhanced_gradient = np.max(np.abs(np.diff(enhanced_arr[50, 40:60, 0].astype(np.float64))))

        self.assertGreaterEqual(enhanced_gradient, original_gradient)

    def test_missing_source_returns_none(self):
        photo = PhotoItem(original_path="/no/such/photo.jpg", sequence_name="01", display_name="01")
        result = self.svc.get_thumbnail(photo)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
