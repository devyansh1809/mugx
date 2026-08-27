"""Phase 3 mockup generator integration tests."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.mockup_generator import MockupGenerator, MockupAsset
from core.models import PrintArea, ProductProfile


class MockupGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cache = self.tmp / "cache"
        self.cache.mkdir()
        self.generator = MockupGenerator(str(self.cache))
        self.mockup_dir = self.tmp / "mockups"
        self.mockup_dir.mkdir()
        base = Image.new("RGBA", (800, 600), (240, 240, 240, 255))
        self.mockup_path = self.mockup_dir / "mug_front.png"
        base.save(self.mockup_path)
        asset = {
            "name": "mug_front",
            "width_px": 800,
            "height_px": 600,
            "print_area": {
                "width_mm": 203.2,
                "height_mm": 90.0,
                "dpi": 300,
                "bleed_mm": 3,
                "safe_margin_mm": 5,
            },
            "transform": {
                "x": 100,
                "y": 150,
                "width": 600,
                "height": 300,
            },
        }
        self.asset_json = self.cache / "mockup_mug_front.json"
        with self.asset_json.open("w") as f:
            json.dump(asset, f)
        self.profile = ProductProfile(
            id="mug.standard_11oz",
            name="11 oz Ceramic Mug",
            category="Mug",
            description="Standard 11 oz white ceramic mug",
            canvas_size_px=(2480, 1063),
            print_area=PrintArea(
                width_mm=203.2,
                height_mm=90.0,
                dpi=300,
                bleed_mm=3,
                safe_margin_mm=5,
            ),
            orientation="landscape",
            mirror_required=True,
            template_path="mugs/standard_11oz/templates",
            mockup_profiles=["mug_front"],
        )
        self.design = Image.new("RGB", (2480, 1063), (255, 0, 0))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_load_asset_from_json(self):
        asset = self.generator.load_asset(self.profile, "mug_front")
        self.assertIsNotNone(asset)
        self.assertEqual(asset.name, "mug_front")
        self.assertEqual(asset.width_px, 800)
        self.assertEqual(asset.height_px, 600)
        self.assertEqual(asset.print_area.dpi, 300)

    def test_render_mockup_with_rectangular_mask(self):
        output = str(self.tmp / "rendered_mug_front.png")
        result, path = self.generator.render_mockup(self.design, self.profile, "mug_front", output)
        self.assertEqual(path, output)
        self.assertEqual(result.size, (800, 600))
        self.assertEqual(result.mode, "RGBA")
        self.assertTrue(Path(output).exists())

    def test_mirror_applied_when_profile_requires_it(self):
        self.profile.mirror_required = True
        output = str(self.tmp / "mirrored_mockup.png")
        result, _ = self.generator.render_mockup(self.design, self.profile, "mug_front", output)
        left = result.getpixel((150, 300))
        right = result.getpixel((650, 300))
        self.assertNotEqual(left[:3], right[:3])


if __name__ == "__main__":
    unittest.main(verbosity=2)
