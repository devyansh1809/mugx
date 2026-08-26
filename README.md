# SubliStudio (scaffold)

A macOS desktop app for sublimation print shops — PyQt6 GUI, clean
core/ui separation. This milestone covers photo import, sequential
naming, Auto Enhance, and template loading/preview. Compositing
(auto-fill frames), print export, and mockups are later milestones —
"Prepare for Print" is present but intentionally disabled for now.

## What's implemented in this milestone

- Load a folder of customer photos → sequential naming (01, 02, 03…), stored
  **in memory only** — original files on disk are never renamed
- Thumbnail grid showing each photo's auto-assigned name
- **Auto Enhance checkbox** — mild color correction, smoothing, and
  sharpening (see algorithm details below), with caching so photos aren't
  reprocessed every time the checkbox is toggled or the list redraws
- Product type dropdown (Mug, Bottle, T-shirt, Tile, Cushion, Keyring, Mobile Cover)
- Load a template file (PSD **or** PNG/JPG) → flattened preview render
- "Prepare for Print" button present, disabled (wired up in the next milestone)

## Requirements

- macOS 12+
- Python 3.11+

## Install

```bash
cd subli_studio

# Recommended: virtual environment
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

**Note on OpenCV:** `requirements.txt` installs `opencv-python-headless`,
not `opencv-python`. The regular package bundles its own Qt platform
plugins, which can conflict with PyQt6 on macOS (crashes or "could not
find the Qt platform plugin" errors). Headless has no GUI code of its own,
which is fine since PyQt6 already handles the display.

## Run

```bash
python main.py
```

## Run the tests

```bash
python tests/test_core.py
# or
python -m pytest tests/ -v
```

## Project Structure

```
subli_studio/
├── main.py                        # entry point — creates QApplication, shows MainWindow
├── requirements.txt
│
├── core/                          # framework-free logic (no PyQt imports)
│   ├── models.py                  # PhotoItem, TemplateInfo, ProductType, DesignJob
│   ├── photo_import_service.py    # folder scan, sequential naming, plain thumbnails
│   ├── image_processor.py         # enhance_image() + ImageEnhancementService (caching)
│   └── template_manager.py        # PSD/PNG template loading + preview rendering
│
├── ui/                             # PyQt6 windows and widgets — call into core/, never the reverse
│   ├── main_window.py             # MainWindow: layout + event handlers
│   ├── photo_list_widget.py       # QListWidget subclass for the photo thumbnail grid
│   └── template_preview_widget.py # QLabel subclass for the scaled template preview
│
├── assets/
│   ├── templates/                 # sample_mug_2photo.png — a placeholder 2-slot template
│   └── sample_data/                # 5 generated sample "customer photos" for quick testing
│
└── tests/
    └── test_core.py               # unit tests for the core layer (no PyQt needed to run these)
```

## Try it immediately with sample data

1. Run `python main.py`
2. Click **Load Photos** → select `assets/sample_data/` (5 sample photos)
3. Toggle **✨ Auto Enhance** to compare thumbnails with/without enhancement
4. Click **Load Template** → select `assets/templates/sample_mug_2photo.png`
5. You'll see the photo thumbnails on the left and the flattened template
   preview on the right.

(Note: the bundled sample photos are flat placeholder colors, not real
photographs, so the Auto Enhance effect is more visible on your own real
customer photos — noise reduction and sharpening need actual photographic
detail/texture to show clearly.)

## Auto Enhance — algorithm explanation

`enhance_image()` in `core/image_processor.py` applies four steps, in order:

1. **Edge-preserving smoothing** (`cv2.bilateralFilter`) — reduces sensor
   noise/grain without blurring edges, unlike a plain Gaussian blur which
   would soften everything uniformly.
2. **Adaptive local contrast** (CLAHE on the L channel in LAB color space)
   — boosts contrast per-region rather than globally, so a photo that's
   partly in shadow and partly well-lit gets balanced without blowing out
   highlights or crushing shadows. Only the lightness channel is touched;
   color channels (a/b) pass through untouched.
3. **Saturation boost (~12%)** in HSV space — colors "pop" slightly, similar
   to a phone camera's default auto-enhance behavior.
4. **Mild unsharp mask** — restores crispness lost in step 1 and gives
   printed output a sharper look.

**A real tuning issue we caught and fixed:** the first version of this
pipeline used a stronger unsharp mask (weight 1.35/-0.35). Measuring noise
(pixel standard deviation) at each pipeline stage on synthetic noisy input
showed the strong sharpen step was *re-amplifying* noise faster than the
bilateral filter removed it — net result, "enhanced" photos were grainier
than the originals in flat regions. We tuned the bilateral filter stronger
(d=9, sigma=60), the CLAHE gentler (clipLimit=1.0, larger 16×16 tiles — CLAHE
is known to amplify noise in flat regions when tiles are small/aggressive),
and the unsharp mask gentler (1.15/-0.15). The result is roughly noise-neutral
overall while still measurably sharpening real edges — verified with two
regression tests in `tests/test_core.py`
(`test_enhance_does_not_amplify_noise_in_flat_regions` and
`test_enhance_increases_edge_definition`) so this can't silently regress again.

If OpenCV isn't installed, `enhance_image()` falls back to a Pillow-only
version (`ImageEnhance.Contrast` / `.Color` + `ImageFilter.UnsharpMask`) —
weaker (no true edge-preserving smoothing or adaptive contrast) but keeps
the app functional.

### Caching

`ImageEnhancementService` (also in `core/image_processor.py`) wraps
`enhance_image()` with two cache layers:

- **In-memory dict** — instant lookups within the current session (e.g.
  toggling the checkbox on/off repeatedly).
- **Disk cache** (`~/.subli_studio/enhanced_thumbnails/`) — survives app
  restarts. Cache keys are derived from the source file's path + modification
  time + size + requested thumbnail size, so replacing a customer's photo on
  disk automatically invalidates the stale cached version instead of silently
  serving old output.

Toggling Auto Enhance on 5 photos took ~1ms in testing after the first pass
(cache warm); the first pass itself is well under 100ms for typical
thumbnail sizes, so no background threading was needed for this milestone.
Full-resolution enhancement (for the eventual print/compositing pipeline,
not just thumbnails) is measurably slower (~0.25s per 4000×3000px photo) —
that's a background-threading concern for when the compositor is built, not
for thumbnail preview.

## Architecture notes

- **`core/` has zero PyQt imports.** Every service in `core/` takes plain
  paths/dataclasses in and returns plain paths/dataclasses out. This is what
  let us test `PhotoImportService`, `TemplateManager`, and now
  `ImageEnhancementService` fully — including catching the noise-amplification
  bug above — *before* wiring anything into the UI.
- **PSD frame-slot parsing is not yet implemented.** `TemplateManager`
  currently only flattens the PSD for *preview* purposes via
  `psd_tools.PSDImage.composite()`. Extracting individual layer names and
  bounding rectangles (so photos can be auto-fit into named frames) is a
  separate, larger piece of work — planned as `PSDReaderService` per the
  architecture diagram, feeding a `CompositorService` that does the actual
  photo-into-frame compositing with Pillow.
- **Photos are not renamed on disk** during import — only display names/labels
  are sequential, held in the `PhotoItem.sequence_name` field in memory. This
  is deliberate: nothing should mutate a customer's original folder before
  the operator has confirmed a job.
- **Why the "Prepare for Print" button is disabled:** it depends on the
  compositor + print-export services that don't exist yet. Shipping it
  visible-but-disabled keeps the window layout final now and makes it obvious
  where the next milestone plugs in.

## Next milestones (not in this scaffold)

1. `PSDReaderService` — parse PSD layer names/bounds into a template manifest (frame slots)
2. `CompositorService` — Pillow-based auto-fill: fit customer photos into frame slots, swap, background, overlays, text
3. `PrintExportService` — A4 layout, mirror for sublimation, PNG/PDF export
4. `MockupService` — perspective-warp preview onto a product mockup image
5. Wire `DesignCanvas` (interactive `QGraphicsView`) for drag/swap/resize of photos within frames
6. Background threading for full-resolution enhancement once the compositor needs it

