# Phase 2 — Product Catalog

Phase 2 introduces a data-driven product catalog in `assets/products/catalog.json` and the `core.product_catalog` service.

## What a profile controls

Each product model specifies:

- Product ID, name, category, tags, description
- Physical print width/height in millimeters
- Production DPI
- Bleed and safe-margin measurements
- Pixel canvas dimensions calculated from mm and DPI
- Default mirror rule
- Orientation
- Product-specific template directory
- Product-specific mockup identifiers

## Catalog workflow

```text
Product category → Product model/profile → Canvas + print defaults
                                      ├→ template folder
                                      ├→ mockup profiles
                                      └→ bleed/safe/mirror production settings
```

## Example

`mug.standard_11oz` resolves to a 210 × 90 mm, 300 DPI, mirrored mug wrap. Its native design canvas is 2480 × 1063 pixels and templates belong in:

```text
assets/products/mugs/standard_11oz/templates/
```

## Adding a new product

Add an entry to `assets/products/catalog.json`; no Python code change is needed. For example, add a new phone cover with its own print size, camera/cutout template directory, mirror rule, and mockup profile.

## Validation

Run:

```bash
python -m pytest tests/test_product_catalog.py -v
```
