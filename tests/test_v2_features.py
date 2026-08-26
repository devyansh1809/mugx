"""
tests/test_v2_features.py

Simulation tests for v2 features: template categorization, round frames,
page-size change, resize-in-frame, extra photo, swap, background+blur,
readymade/3D text, mirror toggles+extra design, mockup variants, auto-save.
"""
import unittest
from pathlib import Path
from PIL import Image
import tempfile
import shutil
import json

from core.models import ProductType, TemplateTheme, FrameShape, FrameInfo, TemplateInfo, PhotoItem, DesignJob
from core.template_manager import TemplateManager
from core.print_exporter import PrintExporter, PrintSettings
from core.mockup_generator import MockupGenerator


class TestV2Features(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.tm = TemplateManager(str(self.tmp / "preview"))
        self.pe = PrintExporter(PrintSettings())
        self.mg = MockupGenerator(str(self.tmp / "mockups"))
        
        self.photo_dir = self.tmp / "photos"
        self.photo_dir.mkdir()
        self.photos = []
        for i, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]):
            p = self.photo_dir / f"photo_{i}.png"
            Image.new("RGB", (200, 200), color).save(p, "PNG")
            self.photos.append(PhotoItem(original_path=str(p), sequence_name=f"{i+1:02d}", index=i))
        
        self.template = TemplateInfo(
            source_path=str(self.tmp / "template.png"),
            display_name="test_template.png",
            width=800, height=600,
            is_psd=False,
            product_type=ProductType.MUG,
            theme=TemplateTheme.COLLAGE_BIRTHDAY,
            frames=[
                FrameInfo(name="frame_1", left=50, top=50, width=200, height=200, shape=FrameShape.RECT),
                FrameInfo(name="frame_round_2", left=300, top=50, width=200, height=200, shape=FrameShape.ROUND),
                FrameInfo(name="frame_3", left=550, top=50, width=200, height=200, shape=FrameShape.RECT),
            ],
            original_physical_width_cm=20.0,
            original_physical_height_cm=15.0,
        )
        
        self.base_canvas = Image.new("RGBA", (800, 600), (240, 240, 240, 255))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_round_frame_detection_from_sidecar(self):
        template_path = self.tmp / "round_template.png"
        Image.new("RGB", (800, 600), (200, 200, 200)).save(template_path, "PNG")
        
        sidecar = self.tmp / "round_template.frames.json"
        sidecar.write_text(json.dumps([
            {"name": "frame_1", "left": 0, "top": 0, "width": 200, "height": 200, "shape": "rect"},
            {"name": "frame_round_2", "left": 250, "top": 0, "width": 200, "height": 200, "shape": "round"},
        ]))
        
        frames = self.tm.detect_frames_sidecar(template_path, (800, 600))
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0].shape, FrameShape.RECT)
        self.assertEqual(frames[1].shape, FrameShape.ROUND)

    def test_change_page_size_rescales_canvas_and_frames(self):
        new_template = self.tm.change_page_size(self.template, new_width_cm=25.0, new_height_cm=18.75)
        self.assertEqual(new_template.width, 1000)
        self.assertEqual(new_template.height, 750)
        self.assertEqual(new_template.frames[0].width, 250)

    def test_resize_photo_in_frame(self):
        filled = self.tm.fill_frames(self.template, self.base_canvas, self.photos[:3])
        resized = self.tm.resize_photo_in_frame(
            self.template, self.base_canvas, self.photos[:3],
            frame_index=0, new_scale=1.5, offset_x=20, offset_y=-10
        )
        self.assertEqual(resized.size, self.base_canvas.size)
        self.assertEqual(self.template.frames[0].photo_scale, 1.5)
        self.assertEqual(self.template.frames[0].photo_offset_x, 20)
        self.assertEqual(self.template.frames[0].photo_offset_y, -10)

    def test_add_extra_photo(self):
        canvas = Image.new("RGBA", (800, 600), (255, 255, 255, 255))
        result = self.tm.add_extra_photo(canvas, self.photos[3], position=(500, 400), border_size=10)
        self.assertEqual(result.size, (800, 600))

    def test_swap_photos_two_select(self):
        filled = self.tm.fill_frames(self.template, self.base_canvas, self.photos[:3])
        swapped = self.tm.swap_photos(self.template, self.base_canvas, self.photos[:3], 0, 2)
        self.assertEqual(self.template.frames[0].photo_index, 2)
        self.assertEqual(self.template.frames[2].photo_index, 0)

    def test_change_background_with_blur(self):
        bg_path = self.tmp / "bg.png"
        Image.new("RGB", (800, 600), (100, 150, 200)).save(bg_path, "PNG")
        design = Image.new("RGBA", (800, 600), (255, 0, 0, 200))
        result_no_blur = self.tm.change_background_with_preview(design, str(bg_path), blur_amount=0)
        result_blur = self.tm.change_background_with_preview(design, str(bg_path), blur_amount=10)
        self.assertEqual(result_no_blur.size, (800, 600))
        self.assertEqual(result_blur.size, (800, 600))

    def test_add_readymade_text(self):
        design = Image.new("RGBA", (800, 600), (0, 0, 0, 255))
        result = self.tm.add_readymade_text(design, "Happy Birthday", position=(100, 100))
        self.assertEqual(result.size, (800, 600))

    def test_generate_3d_text_stub(self):
        text_img = self.tm.generate_3d_text_stub("Test 3D", font_size=60)
        self.assertEqual(text_img.size, (400, 150))
        self.assertEqual(text_img.mode, "RGBA")

    def test_print_export_with_mirror_toggles_and_extra_design(self):
        design = Image.new("RGB", (400, 300), (255, 0, 0))
        extra_design = Image.new("RGB", (300, 200), (0, 255, 0))
        output_path = str(self.tmp / "test_print.png")
        self.pe.export_png(design, output_path, mirror_1=True, mirror_2=False, 
                          extra_design=extra_design, extra_design_rotate=True)
        self.assertTrue(Path(output_path).exists())
        self.assertGreater(Path(output_path).stat().st_size, 0)

    def test_mockup_variants_and_jpg_export(self):
        design = Image.new("RGB", (400, 400), (255, 100, 100))
        variants = self.mg.get_variants("mug")
        self.assertEqual(len(variants), 4)
        mockup = self.mg.render_cylinder_mockup(design, variant=variants[1])
        self.assertEqual(mockup.size, (800, 800))
        jpg_path = str(self.tmp / "mockup_whatsapp.jpg")
        self.mg.export_mockup_jpg(mockup, jpg_path)
        self.assertTrue(Path(jpg_path).exists())

    def test_auto_save_and_load_design_job(self):
        job = DesignJob(
            template=self.template,
            photos=self.photos[:3],
            background_path=None,
            auto_save_enabled=True,
        )
        save_path = job.auto_save(str(self.tmp / "auto_saves"))
        self.assertTrue(Path(save_path).exists())
        loaded_job = DesignJob.load_from_auto_save(save_path)
        self.assertEqual(loaded_job.template.display_name, self.template.display_name)
        self.assertEqual(len(loaded_job.photos), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
