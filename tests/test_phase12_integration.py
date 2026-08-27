"""Integration tests for complete Phase 1 + 2 product-aware flow.

These tests avoid a GUI display but exercise the same profile-to-design-to-print
logic that Phase1Window wires into PyQt controls.
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.models import FrameInfo, PhotoItem, ProductType, TemplateInfo, TemplateTheme
from core.phase12_workflow import Phase12Workflow
from core.product_catalog import ProductCatalog


class Phase12IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        catalog = ProductCatalog(str(Path(__file__).resolve().parent.parent / "assets" / "products" / "catalog.json"))
        self.workflow = Phase12Workflow(catalog, str(self.tmp / "cache"))
        self.photo_paths = []
        for index, color in enumerate(((255, 0, 0), (0, 255, 0))):
            path = self.tmp / f"photo_{index}.png"
            Image.new("RGB", (240, 240), color).save(path)
            self.photo_paths.append(path)
        self.photos = [PhotoItem(str(path), f"{index + 1:02d}", index) for index, path in enumerate(self.photo_paths)]
        self.template = TemplateInfo(
            source_path=str(self.tmp / "two_photo_template.png"),
            display_name="two_photo_template.png",
            width=400, height=200, is_psd=False,
            product_type=ProductType.MUG, theme=TemplateTheme.PLAIN,
            frames=[FrameInfo("frame_1", 0, 0, 200, 200), FrameInfo("frame_2", 200, 0, 200, 200)],
        )
        self.base = Image.new("RGBA", (400, 200), (255, 255, 255, 255))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_mug_profile_controls_canvas_template_print_and_mockup_data(self):
        state = self.workflow.select_product("mug.standard_11oz")
        self.assertEqual(state.base_canvas.size, (2480, 1063))
        self.assertIn("mugs/standard_11oz/templates", str(self.workflow.template_directory()))
        self.assertTrue(state.profile.mirror_required)
        self.assertIn("mug_front", state.profile.mockup_profiles)
        self.assertEqual(self.workflow.configured_print_exporter().settings.dpi, 300)

    def test_mobile_profile_controls_portrait_canvas_and_mirror_default(self):
        state = self.workflow.select_product("mobile_cover.iphone_17_pro")
        self.assertEqual(state.profile.orientation, "portrait")
        self.assertFalse(state.profile.mirror_required)
        self.assertGreater(state.base_canvas.height, state.base_canvas.width)
        self.assertIn("mobile_covers/apple/iphone_17_pro/templates", str(self.workflow.template_directory()))

    def test_selected_photo_order_to_autofill_edit_effect_and_print_preview(self):
        self.workflow.select_product("mug.standard_11oz")
        self.workflow.select_photos([self.photos[1], self.photos[0]])
        self.workflow.load_template(self.template, self.base)
        design = self.workflow.auto_fill()
        self.assertGreater(design.getpixel((100, 100))[1], design.getpixel((100, 100))[0])
        preview = self.workflow.edit_frame(0, 1.2, 12, -8, preview_only=True)
        self.assertEqual(preview.size, (400, 200))
        self.workflow.edit_frame(0, 1.2, 12, -8, preview_only=False)
        edited = self.workflow.apply_effect("Gold Border", 80)
        self.assertNotEqual(edited.getpixel((6, 6)), (255, 255, 255, 255))
        sheet = self.workflow.final_print_preview()
        self.assertEqual(sheet.mode, "RGB")
        self.assertGreater(sheet.width, edited.width)


if __name__ == "__main__":
    unittest.main(verbosity=2)
