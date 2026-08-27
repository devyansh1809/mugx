# Phase 1 + 2 + 3 Acceptance Checklist

## Phase 1 — User workflow

- [x] Choose a folder then select exact photo thumbnails.
- [x] Select individual image files.
- [x] Preserve selected image order for Auto Fill.
- [x] Load PSD/image templates.
- [x] Auto-fill template frames.
- [x] Show the current design in Design preview.
- [x] Show a live Manual Edit preview with clickable frames.
- [x] Preview frame scale/position before applying it.
- [x] Apply selectable Box/Light effects with intensity.
- [x] Render a Final Print Preview through the production print renderer.
- [x] Export PNG/PDF through that same print renderer.

## Phase 2 — Product-aware workflow

- [x] Product category selector.
- [x] Product model selector populated from `ProductCatalog`.
- [x] Product profile sets native blank canvas dimensions and DPI.
- [x] Profile sets mirror default in Print UI.
- [x] Profile displays bleed and safe-margin information.
- [x] Product template root is displayed and used as the file-picker start path.
- [x] Profile mockup identifiers are displayed in Print workflow for the next mockup phase.
- [x] Controller/integration tests cover product → template directory → selected photos → auto-fill → edit → effect → final print.

## Phase 3 — Mockup preview

- [x] `MockupGenerator` core service that renders a design onto a mockup image.
- [x] Mockup asset definition (JSON) with print-area geometry and transform.
- [x] Mockup preview tab with:
  - product mockup profile display,
  - mockup view selector,
  - refresh and export buttons,
  - live preview of the rendered mockup.
- [x] Mockup widget wired to the same design state as Print/Manual Edit.
- [x] Integration tests for mockup asset loading, rendering, and mirror behavior.

## Verify locally on macOS

```bash
cd /Users/devyanshsingh/Documents/GitHub/mugx/mugx
git switch v2
git pull origin v2
source venv/bin/activate
python -m pip install -r requirements.txt pytest
python -m pytest tests/test_product_catalog.py tests/test_phase12_workflow.py tests/test_phase12_integration.py tests/test_phase3_mockup.py -v
python main.py
```

### Manual smoke test

1. Choose **Mug → 11 oz Ceramic Mug**; confirm the profile panel says 2480 × 1063 px, 300 DPI, mirror on.
2. Choose **Mobile Cover → Apple iPhone 17 Pro Cover**; confirm portrait canvas and mirror off.
3. Choose a photo folder, check exactly two thumbnails, load a two-frame template, and Auto Fill.
4. Open Manual Edit, click a frame, change scale/position; confirm preview changes before Apply.
5. Choose an effect and intensity; confirm preview then Apply.
6. Open Print Preview; confirm it contains the final edited composition and product mirror default.
7. Export PNG and PDF; confirm both files are created.
8. Open **Mockup Preview**; confirm the mug mockup dropdown shows `mug_front`.
9. Select `mug_front` and click **Refresh Mockup**; confirm the preview shows the red design on the mug.
10. Click **Export Mockup PNG**; confirm the file is created in the chosen folder.
