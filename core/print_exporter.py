"""
core/print_exporter.py

"Prepare for Print": A4/A3 canvas, mirrored for sublimation, PNG/PDF export.
No PyQt imports.
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
    mirror: bool = True
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

    def _layout_positions(self, sheet_size: Tuple[int, int], design_size: Tuple[int, int]) -> List[Tuple[int, int]]:
        sheet_w, sheet_h = sheet_size
        design_w, design_h = design_size
        px_per_mm = self.settings.dpi / MM_PER_INCH
        margin_px = round(self.settings.margin_mm * px_per_mm)

        n = max(1, self.settings.designs_per_sheet)
        cols = max(1, (sheet_w - margin_px) // (design_w + margin_px))
        cols = max(1, min(cols, n))
        rows = -(-n // cols)

        positions = []
        for i in range(n):
            row, col = divmod(i, cols)
            x = margin_px + col * (design_w + margin_px)
            y = margin_px + row * (design_h + margin_px)
            if x + design_w > sheet_w or y + design_h > sheet_h:
                break
            positions.append((x, y))
        return positions

    def build_print_sheet(self, design: Image.Image) -> Image.Image:
        sheet_w, sheet_h = self._paper_size_px()
        sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))

        prepared = design.convert("RGB")
        if self.settings.mirror:
            prepared = prepared.transpose(Image.FLIP_LEFT_RIGHT)

        max_w = sheet_w - 2 * round(self.settings.margin_mm * self.settings.dpi / MM_PER_INCH)
        max_h = sheet_h
        if prepared.width > max_w or prepared.height > max_h:
            ratio = min(max_w / prepared.width, max_h / prepared.height)
            prepared = prepared.resize(
                (max(1, round(prepared.width * ratio)), max(1, round(prepared.height * ratio))), Image.LANCZOS
            )

        positions = self._layout_positions((sheet_w, sheet_h), prepared.size)
        if not positions:
            positions = [(0, 0)]
        for pos in positions:
            sheet.paste(prepared, pos)

        logger.info("Built print sheet %sx%s px (%s @ %s DPI), %d copies, mirror=%s",
                    sheet_w, sheet_h, self.settings.paper_size, self.settings.dpi, len(positions), self.settings.mirror)
        return sheet

    def export_png(self, design: Image.Image, output_path: str) -> str:
        sheet = self.build_print_sheet(design)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        sheet.save(output_path, "PNG", dpi=(self.settings.dpi, self.settings.dpi))
        return output_path

    def export_pdf(self, design: Image.Image, output_path: str) -> str:
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas as pdf_canvas

        sheet = self.build_print_sheet(design)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        w_mm, h_mm = PAPER_SIZES_MM[self.settings.paper_size]
        page_w_pt = w_mm / MM_PER_INCH * 72
        page_h_pt = h_mm / MM_PER_INCH * 72

        c = pdf_canvas.Canvas(output_path, pagesize=(page_w_pt, page_h_pt))
        c.drawImage(ImageReader(sheet), 0, 0, width=page_w_pt, height=page_h_pt)
        c.showPage()
        c.save()
        return output_path

    def export(self, design: Image.Image, output_dir: str, base_name: str,
               formats: Tuple[str, ...] = ("png",)) -> List[str]:
        outputs = []
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if "png" in formats:
            outputs.append(self.export_png(design, str(out_dir / f"{base_name}.png")))
        if "pdf" in formats:
            outputs.append(self.export_pdf(design, str(out_dir / f"{base_name}.pdf")))
        return outputs
