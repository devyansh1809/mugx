import json
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.mockup_asset_registry import MockupAssetRegistry
from core.mockup_generator import MockupGenerator
from core.mockup_validation import validate_mockup_coverage
from core.models import PrintArea, ProductProfile


class CatalogStub:
    def __init__(self, profile): self.profile = profile
    def categories(self): return [self.profile.category]
    def by_category(self, category): return [self.profile] if category == self.profile.category else []


class Phase3AssetPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.assets = self.tmp / "assets"; self.assets.mkdir()
        self.profile = ProductProfile("bottle.steel_600ml", "600 ml Steel Bottle", "Bottle", "test", (1200, 2400), PrintArea(210, 100, 300), "portrait", False, "", ["bottle_front"])
        self.design = Image.new("RGBA", (600, 300), (220, 20, 60, 255))
        (self.assets / "manifest.json").write_text(json.dumps({"version": 1, "assets": [{"product_id": self.profile.id, "view_id": "bottle_front", "image": "bottle_front.png", "metadata": "bottle_front.json"}]}))
    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)
    def _write_valid_asset(self):
        Image.new("RGBA", (800, 1000), (240, 240, 240, 255)).save(self.assets / "bottle_front.png")
        (self.assets / "bottle_front.json").write_text(json.dumps({"width_px": 800, "height_px": 1000, "print_region": {"mode": "rectangle", "x": 220, "y": 250, "width": 370, "height": 480, "surface": "cylinder", "curve": 0.25}}))
    def test_missing_asset_is_reported_and_fallback_exports(self):
        report = validate_mockup_coverage(CatalogStub(self.profile), MockupAssetRegistry(str(self.assets)))
        self.assertIn(self.profile.id, report.missing)
        image, path = MockupGenerator(str(self.tmp / "cache"), str(self.assets)).render_mockup(self.design, self.profile, "bottle_front", str(self.tmp / "fallback.png"))
        self.assertEqual(image.size, (1200, 900)); self.assertTrue(Path(path).is_file())
    def test_valid_asset_is_discovered_rendered_and_exported(self):
        self._write_valid_asset()
        report = validate_mockup_coverage(CatalogStub(self.profile), MockupAssetRegistry(str(self.assets)))
        self.assertTrue(report.production_ready)
        result, path = MockupGenerator(str(self.tmp / "cache"), str(self.assets)).render_mockup(self.design, self.profile, "bottle_front", str(self.tmp / "production.png"))
        self.assertEqual(result.size, (800, 1000)); self.assertTrue(Path(path).is_file())
    def test_malformed_metadata_is_invalid(self):
        Image.new("RGBA", (800, 1000)).save(self.assets / "bottle_front.png")
        (self.assets / "bottle_front.json").write_text("{bad json")
        report = validate_mockup_coverage(CatalogStub(self.profile), MockupAssetRegistry(str(self.assets)))
        self.assertIn(self.profile.id, report.invalid)


if __name__ == "__main__": unittest.main()
