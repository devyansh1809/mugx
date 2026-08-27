# Phase 3 Mockup Assets

Install only assets whose licence permits customer-facing commercial use. Keep third-party PSD/PNG source assets local unless their licence explicitly permits repository redistribution.

Put each licensed pair in `assets/mockups/` and retain the matching entry in `manifest.json`:

```text
assets/mockups/bottle_front.png
assets/mockups/bottle_front.json
```

Metadata supports a rectangular or polygon print region, cylinder wrapping, optional texture/shadow/highlight overlays, and PSD smart-object metadata.

```json
{
  "width_px": 2400,
  "height_px": 2400,
  "print_region": {"mode":"rectangle","x":630,"y":560,"width":1140,"height":1050,"surface":"cylinder","curve":0.30},
  "texture":"bottle_front_texture.png",
  "texture_strength":0.18,
  "shadow":"bottle_front_shadow.png",
  "highlight":"bottle_front_highlight.png",
  "source_psd":"bottle_front.psd",
  "smart_object_layer":"YOUR_DESIGN"
}
```

Verify with:

```bash
python -m pytest tests/test_phase3_mockup.py tests/test_phase3_asset_pipeline.py -v
python main.py
```

The app exports an explicitly labelled `ILLUSTRATIVE FALLBACK` when a licensed PNG/JSON pair is not installed.
