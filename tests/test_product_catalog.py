import unittest
from pathlib import Path

from core.product_catalog import ProductCatalog, create_blank_canvas


class ProductCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog_file = Path(__file__).resolve().parent.parent / "assets" / "products" / "catalog.json"
        cls.catalog = ProductCatalog(str(catalog_file))

    def test_catalog_loads_expected_profiles(self):
        self.assertGreaterEqual(len(self.catalog.all()), 9)
        self.assertEqual(self.catalog.get("mug.standard_11oz").category, "Mug")
        self.assertEqual(self.catalog.get("mobile_cover.iphone_17_pro").category, "Mobile Cover")

    def test_categories_are_data_driven(self):
        categories = self.catalog.categories()
        for expected in ("Mug", "Bottle", "T-Shirt", "Tile", "Cushion", "Keyring", "Mobile Cover"):
            self.assertIn(expected, categories)

    def test_print_profile_calculates_production_pixel_size(self):
        mug = self.catalog.get("mug.standard_11oz")
        self.assertEqual(mug.canvas_size_px, (2480, 1063))
        self.assertTrue(mug.mirror_required)
        self.assertGreater(mug.print_area.bleed_pixels, 0)

    def test_product_specific_mirror_rule(self):
        mug = self.catalog.get("mug.standard_11oz")
        cover = self.catalog.get("mobile_cover.iphone_17_pro")
        self.assertTrue(mug.mirror_required)
        self.assertFalse(cover.mirror_required)

    def test_blank_canvas_uses_profile_dimensions(self):
        profile = self.catalog.get("tile.square_6in")
        canvas = create_blank_canvas(profile)
        self.assertEqual(canvas.size, profile.canvas_size_px)
        self.assertEqual(canvas.mode, "RGBA")

    def test_search_supports_name_category_and_tags(self):
        self.assertTrue(any(p.id == "mug.magic_11oz" for p in self.catalog.search("magic")))
        self.assertTrue(any(p.category == "Mobile Cover" for p in self.catalog.search("mobile")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
