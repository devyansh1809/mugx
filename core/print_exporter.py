"""
core/print_exporter.py (v2.2)

Fix: mirror_1 and mirror_2 now control independent designs:
  - mirror_1: mirrors the PRIMARY design only.
  - mirror_2: mirrors the EXTRA/secondary design only, independently.
This matches the UI checkboxes and eliminates the cancel-out bug where
applying FLIP_LEFT_RIGHT twice to the same image was a no-op.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image

logger = logging.getLogger("SubliStudio.PrintExporter")

PAPER_SIZES_MM = {
    "A4": (210.0, 297.0),
    "A3": (297.0, 420.0),
    "A5": (148.0, 210.0),
    "Letter": (215.9, 279.4),
}

MM_PER_INCH = 25.4


@dataclass
class PrintSettings:
    paper_size: str = "A4"
    dpi: int = 300
    mirror_default: bool = True
    designs_per_sheet: int = 1
    margin_mm: float = 5.0


class PrintExporter:
    def __init__(self, settings: Optional[PrintSettings] = None):
        self.settings = settings or PrintSettings()

    def _paper_size_px(self) -> Tuple[int, int]:
        if self.settings.paper_size not in PAPER_SIZES_MM:
            raise ValueError(f"Unknown paper size: {self.settings.paper_size}")
        w_mm, h_mm = PAPER_SIZES_MM[self.settings.paper_size]
        px_per_mm = self.settings.dpi / MM_PER_INCH
        return round(w_mm * px_per_mm), round(h_mm * px_per_mm)

    def build_print_sheet(self, design: Image.Image, mirror_1: bool = True,
                          mirror_2: bool = False, extra_design: Optional[Image.Image] = None,
                          extra_design_rotate: bool = False) -> Image.Image:
        sheet_w, sheet_h = self._paper_size_px()
        sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))

        prepared = design.convert("RGB")
        if mirror_1:
            prepared = prepared.transpose(Image.FLIP_LEFT_RIGHT)

        max_w = sheet_w - 2 * round(self.settings.margin_mm * self.settings.dpi / MM_PER_INCH)
        max_h = sheet_h * 0.7
        if prepared.width > max_w or prepared.height > max_h:
            ratio = min(max_w / prepared.width, max_h / prepared.height)
            prepared = prepared.resize(
                (max(1, round(prepared.width * ratio)), max(1, round(prepared.height * ratio))), Image.LANCZOS
            )

        primary_x = round(self.settings.margin_mm * self.settings.dpi / MM_PER_INCH)
        primary_y = primary_x
        sheet.paste(prepared, (primary_x, primary_y))

        if extra_design is not None:
            extra = extra_design.convert("RGB")
            if extra_design_rotate:
                extra = extra.transpose(Image.ROTATE_270)
            if mirror_2:
                extra = extra.transpose(Image.FLIP_LEFT_RIGHT)
            extra_max_w = sheet_w - 2 * primary_x
            extra_max_h = sheet_h * 0.25
            if extra.width > extra_max_w or extra.height > extra_max_h:
                ratio = min(extra_max_w / extra.width, extra_max_h / extra.height)
                extra = extra.resize(
                    (max(1, round(extra.width * ratio)), max(1, round(extra.height * ratio))), Image.LANCZOS
                )
            extra_x = primary_x
            extra_y = sheet_h - extra.height - primary_x
            sheet.paste(extra, (extra_x, extra_y))

        return sheet

    def export_png(self, design: Image.Image, output_path: str, mirror_1: bool = True,
                   mirror_2: bool = False, extra_design: Optional[Image.Image] = None,
                   extra_design_rotate: bool = False) -> str:
        sheet = self.build_print_sheet(design, mirror_1, mirror_2, extra_design, extra_design_rotate)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        sheet.save(output_path, "PNG", dpi=(self.settings.dpi, self.settings.dpi))
        return output_path

    def export_pdf(self, design: Image.Image, output_path: str, mirror_1: bool = True,
                   mirror_2: bool = False, extra_design: Optional[Image.Image] = None,
                   extra_design_rotate: bool = False) -> str:
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas as pdf_canvas

        sheet = self.build_print_sheet(design, mirror_1, mirror_2, extra_design, extra_design_rotate)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        w_mm, h_mm = PAPER_SIZES_MM[self.settings.paper_size]
        page_w_pt = w_mm / MM_PER_INCH * 72
        page_h_pt = h_mm / MM_PER_INCH * 72

        c = pdf_canvas.Canvas(output_path, pagesize=(page_w_pt, page_h_pt))
        c.drawImage(ImageReader(sheet), 0, 0, width=page_w_pt, height=page_h_pt)
        c.showPage()
        c.save()
        return output_path

    def export(self, design: Image.Image, output_dir: str, base_name: str, mirror_1: bool = True,
               mirror_2: bool = False, extra_design: Optional[Image.Image] = None,
               extra_design_rotate: bool = False,
               formats: Tuple[str, ...] = ("png",)) -> List[str]:
        outputs = []
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if "png" in formats:
            outputs.append(self.export_png(design, str(out_dir / f"{base_name}.png"),
                                          mirror_1, mirror_2, extra_design, extra_design_rotate))
        if "pdf" in formats:
            outputs.append(self.export_pdf(design, str(out_dir / f"{base_name}.pdf"),
                                          mirror_1, mirror_2, extra_design, extra_design_rotate))
        return outputs
