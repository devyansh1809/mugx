import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.models import FrameInfo, PhotoItem, ProductType, TemplateInfo, TemplateTheme
from core.phase12_workflow import Phase12Workflow
from core.product_catalog import ProductCatalog


class Phase12WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        catalog_path = Path(__file__).resolve().parent.parent / "assets" / "products" / "catalog.json"
        self.workflow = Phase12Workflow(ProductCatalog(str(catalog_path)), str(self.tmp / "cache"))
        self.photo_paths = []
        for index, color in enumerate(((255, 0, 0), (0, 255, 0))):
            path = self.tmp / f"photo_{index}.png"
            Image.new("RGB", (300, 300), color).save(path)
            self.photo_paths.append(path)
        self.photos = [PhotoItem(str(path), f"{index + 1:02d}", index) for index, path in enumerate(self.photo_paths)]
        self.template = TemplateInfo(
            source_path=str(self.tmp / "template.png"),
            display_name="template.png",
            width=400,
            height=200,
            is_psd=False,
            product_type=ProductType.MUG,
            theme=TemplateTheme.PLAIN,
            frames=[
                FrameInfo("frame_1", 0, 0, 200, 200),
                FrameInfo("frame_2", 200, 0, 200, 200),
            ],
        )
        self.base = Image.new("RGBA", (400, 200), (240, 240, 240, 255))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_product_profile_sets_blank_canvas_and_template_path(self):
        state = self.workflow.select_product("mug.standard_11oz")
        self.assertEqual(state.base_canvas.size, (2480, 1063))
        self.assertTrue(str(self.workflow.template_directory()).endswith("mugs/standard_11oz/templates"))

    def test_selected_photo_order_is_preserved_for_auto_fill(self):
        self.workflow.select_product("mug.standard_11oz")
        self.workflow.select_photos([self.photos[1], self.photos[0]])
        self.workflow.load_template(self.template, self.base)
        canvas = self.workflow.auto_fill()
        # first selected photo was green and is placed in first frame
        first_frame = canvas.getpixel((100, 100))
        self.assertGreater(first_frame[1], first_frame[0])

    def test_frame_preview_is_non_destructive_until_apply(self):
        self.workflow.select_product("mug.standard_11oz")
        self.workflow.select_photos(self.photos)
        self.workflow.load_template(self.template, self.base)
        self.workflow.auto_fill()
        before = self.workflow.state.template.frames[0].photo_scale
        preview = self.workflow.edit_frame(0, 1.5, 10, 15, preview_only=True)
        self.assertEqual(self.workflow.state.template.frames[0].photo_scale, before)
        self.assertEqual(preview.size, self.base.size)
        self.workflow.edit_frame(0, 1.5, 10, 15, preview_only=False)
        self.assertEqual(self.workflow.state.template.frames[0].photo_scale, 1.5)

    def test_effect_preview_is_non_destructive_and_apply_is_persistent(self):
        self.workflow.select_product("mug.standard_11oz")
        self.workflow.select_photos(self.photos)
        self.workflow.load_template(self.template, self.base)
        self.workflow.auto_fill()
        before = self.workflow.state.current_canvas().tobytes()
        preview = self.workflow.effect_preview(self.workflow.state.current_canvas(), "Warm Light", 80)
        self.assertNotEqual(preview.tobytes(), before)
        self.assertEqual(self.workflow.state.current_canvas().tobytes(), before)
        self.workflow.apply_effect("Warm Light", 80)
        self.assertNotEqual(self.workflow.state.current_canvas().tobytes(), before)

    def test_profile_mirror_rule_drives_final_print_preview(self):
        self.workflow.select_product("mug.standard_11oz")
        self.workflow.select_photos(self.photos)
        self.workflow.load_template(self.template, self.base)
        self.workflow.auto_fill()
        sheet = self.workflow.final_print_preview()
        self.assertEqual(sheet.mode, "RGB")
        self.assertEqual(self.workflow.configured_print_exporter().settings.dpi, 300)
        self.assertTrue(self.workflow.configured_print_exporter().settings.mirror_default)

    def test_mobile_cover_uses_its_profile_defaults(self):
        state = self.workflow.select_product("mobile_cover.iphone_17_pro")
        self.assertEqual(state.profile.category, "Mobile Cover")
        self.assertFalse(state.profile.mirror_required)
        self.assertEqual(state.base_canvas.size, state.profile.canvas_size_px)


if __name__ == "__main__":
    unittest.main(verbosity=2)
