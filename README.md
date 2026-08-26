# SubliStudio

A macOS desktop app for sublimation print shops -- PyQt6 GUI, clean
core/ui separation. Inspired by tools like "Mug-x Print Plugin Pro":
load customer photos, auto-fill them into product templates (mug,
bottle, T-shirt, tile, cushion, keyring, mobile cover), tweak the
design, and export a print-ready sublimation file.

## What's implemented

- **Photo import** -- load a folder of customer photos -> sequential naming
  (01, 02, 03...), stored in memory only; original files on disk are never renamed.
- **Auto Enhance** -- mild color correction, smoothing, and sharpening, with
  two-tier (memory + disk) caching.
- **Template loading + frame detection** -- PSD (via psd-tools) frame layers
  named `frame_1`, `frame_2`, ... are auto-detected; PNG/JPG templates use an
  optional `<name>.frames.json` sidecar, or default to one full-canvas frame.
  Detected frames render as clickable overlay rectangles on the preview.
- **Auto Fill** -- fills the first N frames with the first N loaded photos
  (cover or fit/crop logic); N chosen via spinbox.
- **Swap photos** -- click a frame, then double-click a photo, to replace
  just that frame without disturbing the rest of the design.
- **Change Background** -- pick any image; scaled to fill the canvas, design
  composited on top.
- **Effects** -- PNG overlay library (glow, box light, vignette); drop more
  PNGs into `assets/effects/` to extend, no code changes needed.
- **Add Text** -- text, font size, color, position (0-1 canvas ratio).
- **Prepare for Print** -- A4/A3/A5/Letter canvas at configurable DPI
  (default 300), mirrored horizontally for sublimation, optional multiple
  copies per sheet, exports PNG and/or PDF.
- **3D Preview (proof of concept)** -- dependency-light 2.5D cylindrical mug
  mockup (Pillow + numpy only). A Smart-Object PSD mockup path also exists in
  `core/mockup_generator.py` for when a validated mockup PSD is available; it
  raises `NotImplementedError` otherwise rather than producing a wrong render.

## Requirements

- macOS 12+ (development also works on Windows/Linux; only `PACKAGING.md`'s
  steps are macOS-specific)
- Python 3.11+

## Install

```bash
cd subli_studio
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**OpenCV note:** `requirements.txt` installs `opencv-python-headless`, not
`opencv-python` -- the regular package bundles its own Qt plugins that can
conflict with PyQt6 on macOS. If it's missing entirely, `image_processor.py`
falls back to a Pillow-only enhancement pipeline automatically.

**psd-tools note:** only required for PSD/PSB templates and the
smart-object mockup path -- PNG/JPG templates and the 2.5D mockup work
without it.

## Run

```bash
python main.py
```

## Run the tests

```bash
python -m pytest tests/ -v
```

All 28 tests in `tests/test_core.py` exercise `core/` only (zero PyQt
dependency by design), so they run headless / in CI without a display.

## Project Structure

```
subli_studio/
├── main.py
├── requirements.txt
├── core/                          # framework-free logic (no PyQt imports)
│   ├── models.py                  # PhotoItem, FrameInfo, TemplateInfo, ProductType, DesignJob
│   ├── photo_import_service.py    # folder scan, sequential naming, plain thumbnails
│   ├── image_processor.py         # enhance_image() + ImageEnhancementService (caching)
│   ├── template_manager.py        # frame detection, fill/swap/background/overlay/text
│   ├── print_exporter.py          # A4/A3 layout, mirroring, PNG/PDF export
│   └── mockup_generator.py        # 2.5D cylinder mockup + smart-object path
├── ui/                             # PyQt6 windows/widgets -- call core/, never the reverse
│   ├── main_window.py
│   ├── photo_list_widget.py
│   ├── template_preview_widget.py  # scaled preview + clickable frame overlays
│   ├── print_settings_dialog.py
│   ├── text_tool_dialog.py
│   └── mockup_preview_dialog.py
├── assets/
│   ├── templates/                  # sample templates + .frames.json sidecars
│   ├── sample_data/                 # sample "customer photos"
│   ├── backgrounds/                 # sample background images
│   └── effects/                     # PNG overlay effects
└── tests/
    └── test_core.py
```

## PSD template layer naming convention

`TemplateManager.detect_frames_psd()` walks all layers (incl. nested groups)
and matches names against `frame[_-\s]*\d+` (case-insensitive) -- so
`frame_1`, `Frame-2`, `FRAME 3`, `frame4` are all recognized, then sorted by
the trailing number (layer order in the PSD doesn't matter).

For PNG/JPG templates, add `<template-name>.frames.json` next to the
template file:

```json
[
  {"name": "frame_1", "left": 40, "top": 60, "width": 300, "height": 300},
  {"name": "frame_2", "left": 400, "top": 60, "width": 300, "height": 300}
]
```

No sidecar -> the whole canvas is treated as a single `frame_1`.

## Try it immediately with sample data

1. `python main.py`
2. **Load Photos** -> `assets/sample_data/`
3. Toggle **Auto Enhance** to compare thumbnails
4. **Load Template** -> a file from `assets/templates/`
5. Check **Show frame overlays** to see detected frames
6. Set **Photos to use** and click **Auto Fill**
7. Click a frame, then double-click a different photo, to swap it in
8. Try **Change Background**, an **Effect**, and **Add Text**
9. Click **3D Preview** for a quick mockup sanity check
10. Click **Prepare for Print**, choose settings + output folder --
    you get a print-ready PNG and PDF

## Auto Enhance -- algorithm

`enhance_image()` applies, in order: (1) edge-preserving bilateral
smoothing, (2) CLAHE adaptive contrast on LAB's L channel only, (3) a ~12%
HSV saturation boost, (4) a mild unsharp mask (1.15/-0.15).

**Tuning fix on record:** an earlier stronger unsharp mask (1.35/-0.35)
re-amplified sensor noise faster than smoothing removed it -- verified with
`test_enhance_does_not_amplify_noise_in_flat_regions` and
`test_enhance_increases_or_maintains_edge_definition` in `tests/test_core.py`,
which now guard against that regression. The Pillow-only fallback (used when
OpenCV isn't installed) is tuned the same way (smooth first, sharpen gently)
to avoid the same failure mode.

Caching: `ImageEnhancementService` uses an in-memory dict plus a disk cache
under `~/.subli_studio/enhanced_thumbnails/`, keyed on path + mtime + size +
thumbnail size, so replacing a photo on disk invalidates stale entries.

## Fill / swap / background / effects / text

`fill_frames()` pastes photos into detected frames in order via
`fit_photo_to_frame()` (`cover` crops to fill exactly; `fit` preserves the
whole photo with transparent padding). Fewer photos than frames just leaves
the rest showing the base template -- no crash. `swap_photo()` re-runs
`fill_frames()` with every other frame's current assignment preserved.
`change_background()`, `add_overlay()`, and `add_text()` each return a new
composited RGBA image rather than mutating state, so the design pipeline
stays easy to reason about and test.

## Prepare for Print

`PrintExporter` computes sheet pixel size from paper size (mm) + DPI, mirrors
the design if requested (sublimation transfer paper prints mirrored), tiles
`designs_per_sheet` copies in a grid respecting `margin_mm`, and exports PNG
(`export_png`) and/or PDF (`export_pdf`, via reportlab). Supported sizes:
A4, A3, A5, Letter (extend `PAPER_SIZES_MM` for more).

## 3D mockup preview

`render_cylinder_mockup()` is the default: cosine-shaped horizontal squeeze +
matching shading gradient over a neutral studio background -- no pre-made
mockup file required, works for any design immediately.

`render_smart_object_mockup()` is the "correct" long-term path (swap a
pre-made mockup PSD's Smart Object with the current design for photoreal
results), but psd-tools' write support for arbitrary Smart Objects is
limited/version-dependent, so it raises a clear `NotImplementedError` rather
than silently producing a wrong render. To add a real mockup product: author
a PSD with one Smart Object per product, validate psd-tools can read+rewrite
it in your target version, then wire it in.

## Architecture notes

- **`core/` has zero PyQt imports** -- every service takes plain
  paths/dataclasses/PIL images in, returns the same out. This is what let us
  fully unit-test everything (28 tests) without a display or PyQt installed.
- **`ui/` calls into `core/`, never the reverse.**
- **Photos are never renamed on disk** -- only in-memory display labels.
- **Frame-fill state lives on `FrameInfo.photo_index`**, so swaps can
  reconstruct "what's in every frame" without a separate state object.

## Next milestones

1. **Collage layouts** for 7-18 photos (a `CollageLayoutService` generating
   `FrameInfo` lists programmatically).
2. **Batch processing** across a folder of templates x a folder of photo sets.
3. **SQLite database** for customers/orders/templates (stdlib `sqlite3`,
   no new dependency).
4. **Real Smart-Object mockups** once a validated PSD + psd-tools pairing
   is confirmed.
5. **Background threading** for full-resolution (print-time, not thumbnail)
   enhancement.

See `PACKAGING.md` for building a standalone macOS `.app`.
