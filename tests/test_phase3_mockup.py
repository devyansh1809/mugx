"""Phase 3 mockup generator integration tests."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.mockup_generator import MockupGenerator
from core.models import PrintArea, ProductProfile


class MockupGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cache = self.tmp / "cache"
        self.cache.mkdir()
        self.generator = MockupGenerator(str(self.cache))
        self.profile = ProductProfile(
            id="mug.standard_11oz", name="11 oz Ceramic Mug", category="Mug",
            description="Standard mug", canvas_size_px=(2480, 1063),
            print_area=PrintArea(203.2, 90.0, 300, 3, 5), orientation="landscape",
            mirror_required=True, template_path="mugs/standard_11oz/templates",
            mockup_profiles=["mug_front"],
        )
        self.design = Image.new("RGB", (2480, 1063), (255, 0, 0))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_asset(self):
        base = Image.new("RGBA", (800, 600), (240, 240, 240, 255))
        base.save(self.cache / "mockup_mug_front.png")
        with (self.cache / "mockup_mug_front.json").open("w") as handle:
            json.dump({
                "name": "mug_front", "width_px": 800, "height_px": 600,
                "print_area": {"width_mm": 203.2, "height_mm": 90.0, "dpi": 300},
                "transform": {"x": 100, "y": 150, "width": 600, "height": 300},
            }, handle)

    def test_load_asset_from_json(self):
        self._write_asset()
        asset = self.generator.load_asset(self.profile, "mug_front")
        self.assertIsNotNone(asset)
        self.assertEqual(asset.name, "mug_front")
        self.assertEqual(asset.width_px, 800)

    def test_render_mockup_with_rectangular_mask(self):
        self._write_asset()
        output = str(self.tmp / "rendered_mug_front.png")
        result, path = self.generator.render_mockup(self.design, self.profile, "mug_front", output)
        self.assertEqual(path, output)
        self.assertEqual(result.size, (800, 600))
        self.assertTrue(Path(output).exists())

    def test_missing_asset_renders_exportable_fallback(self):
        output = str(self.tmp / "fallback.png")
        result, path = self.generator.render_mockup(self.design, self.profile, "missing_view", output)
        self.assertEqual(result.size, (1200, 900))
        self.assertTrue(Path(path).exists())
        self.assertFalse(self.generator.has_asset(self.profile, "missing_view"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
