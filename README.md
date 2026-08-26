# SubliStudio v2

A macOS desktop app for sublimation printing, inspired by "Mug-x Print Plugin Pro 6.0" but built as a standalone native app (not a Photoshop plugin).

## What's New in v2 (vs v1)

- Multi-panel UI: Design | Manual Edit | Text | Print | Mockup tabs
- Photo import UX: Last-used folder persistence, per-photo sequence name override
- Template categorization: Product-type filter, frame-count filter (1-6+), theme filter
- Round frame detection: frame_round_* layers recognized and rendered with circular masks
- Resize photo in frame: Post-fill scale + offset adjustment
- Extra Photo tool: Auto-bordered frames for photos beyond template's frame count
- Change Page Size: cm/inch canvas rescale for odd-sized physical blanks
- Background preview + blur: Blur toggle before committing background change
- Readymade Text presets: Themed captions
- 3D Text Generator: Stub implementation for 3D-styled text layers
- Swap Photos (two-select UX): Select two frames, swap their photos
- Mirror 1 / Mirror 2 toggle: Manual mirroring control per job
- Add Extra Design: Fill leftover A4 space with second design, 90-degree rotate option
- Auto-save: Every design state auto-saved to manual_psd/ as JSON sidecars
- 3D Mockup variants: Multiple angle options
- Mockup JPG export: WhatsApp/email-optimized export
- QR Code Generator stub, Caricature/Mosaic stubs (Step 10 extension points)

## Requirements

- macOS 12+ (dev also works on Windows/Linux)
- Python 3.11+

## Install

```bash
cd subli_studio
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Run Tests

```bash
python -m pytest tests/ -v
```

See IMPLEMENTATION_SUMMARY.md for the full v1-to-v2 gap analysis and test results.

## Next Steps (Step 10)

1. Populate asset library (backgrounds, effects, text presets, collage themes)
2. Collage layouts (7-18 photos)
3. Batch processing
4. SQLite database
5. Mosaic module
6. Caricature module
7. QR Code Generator panel

See PACKAGING.md for building a standalone macOS .app.
