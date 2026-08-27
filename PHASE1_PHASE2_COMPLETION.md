# Phase 1 + Phase 2 Completion

This update closes the previously identified gaps between the Phase 1 UI workflow and the Phase 2 product catalog.

## Phase 1 verified behaviors

- Customer photos are selected explicitly and selection order is preserved.
- Auto-fill places photos according to selected order.
- Frame edits can be rendered as previews without mutating the saved state.
- Applied frame edits persist in the design state.
- Background and visual-effect operations have non-destructive preview paths.
- Applied effects persist in the final design canvas.
- Final print preview is built through the same `PrintExporter.build_print_sheet()` path used by production export.

## Phase 2 integrated behaviors

- A selected ProductProfile creates the correct physical/DPI canvas.
- Product template folder is resolved by `profile.template_path`.
- Product DPI and default mirror rules configure the print exporter.
- Product mockup identifiers are retained and exposed for the product mockup layer.
- Mobile-cover profiles default to portrait/non-mirrored output; mug profiles default to mirrored output.

## Test commands

```bash
python -m pip install pytest
python -m pytest tests/test_product_catalog.py tests/test_phase12_workflow.py -v
```

The Phase 1/2 workflow tests run without PyQt because the controller is GUI-independent. This makes them suitable for CI and protects the core workflow even while the UI evolves.
