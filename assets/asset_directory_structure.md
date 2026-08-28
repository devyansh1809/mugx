# SubliStudio Asset Directory Structure

## Overview

This document defines the standard asset directory structure for SubliStudio/MugX application.
All assets are organized under a root `SubliStudioAssets/` directory.

---

## Directory Tree

```
SubliStudioAssets/
├── customer_photos/
│   ├── sublimation/          # Sublimation print photos
│   ├── mobile/               # Mobile cover photos
│   ├── mosaic/               # Mosaic/collage photos
│   └── caricature/           # Caricature/cartoon photos
│
├── templates/
│   ├── mugs/
│   │   ├── 1-photo/          # Single photo mug templates
│   │   ├── 2-photo/          # Two photo mug templates
│   │   ├── 3-photo/          # Three photo mug templates
│   │   ├── 4-photo/          # Four photo mug templates
│   │   ├── 5-photo/          # Five photo mug templates
│   │   ├── 6-photo/          # Six photo mug templates
│   │   └── collage/          # Collage-style mug templates
│   ├── bottles/
│   │   ├── 1-photo/
│   │   ├── 2-photo/
│   │   └── collage/
│   ├── tshirts/
│   │   ├── front-only/
│   │   ├── back-only/
│   │   ├── front-back/
│   │   └── full-wrap/
│   ├── cushions/
│   │   ├── square-16x16/
│   │   ├── rectangular-12x20/
│   │   └── round/
│   ├── tiles/
│   │   ├── 4x4/
│   │   ├── 6x6/
│   │   ├── 8x8/
│   │   └── rectangular/
│   ├── keyrings/
│   │   ├── round/
│   │   ├── square/
│   │   └── custom-shape/
│   └── mobile/
│       ├── iphone-15/
│       ├── iphone-15-pro/
│       ├── samsung-s24/
│       └── oneplus-12/
│
├── backgrounds/
│   ├── solid-colors/
│   ├── gradients/
│   ├── patterns/
│   ├── textures/
│   └── themed/
│       ├── birthday/
│       ├── anniversary/
│       ├── wedding/
│       ├── love-romantic/
│       ├── kids/
│       └── festival/
│
├── effects/
│   ├── bokeh/
│   ├── light-leaks/
│   ├── glow/
│   ├── vignette/
│   ├── blur/
│   └── filters/
│
├── clipart/
│   ├── birthday/
│   ├── anniversary/
│   ├── wedding/
│   ├── love-hearts/
│   ├── kids-cartoons/
│   ├── flowers/
│   ├── animals/
│   ├── religious/
│   └── text-bubbles/
│
├── text-presets/
│   ├── birthday-wishes/
│   ├── anniversary-messages/
│   ├── love-quotes/
│   ├── motivational/
│   ├── funny/
│   └── custom-fonts/
│
├── mockups/
│   ├── mugs/
│   │   ├── white-mug-front.jpg
│   │   ├── white-mug-angle.jpg
│   │   ├── magic-mug-before.jpg
│   │   └── magic-mug-after.jpg
│   ├── bottles/
│   │   ├── steel-bottle-front.jpg
│   │   └── steel-bottle-angle.jpg
│   ├── tshirts/
│   │   ├── tshirt-front-mockup.jpg
│   │   ├── tshirt-back-mockup.jpg
│   │   └── tshirt-full-wrap.jpg
│   ├── cushions/
│   │   ├── square-cushion-mockup.jpg
│   │   └── rectangular-cushion-mockup.jpg
│   ├── tiles/
│   │   ├── tile-4x4-mockup.jpg
│   │   └── tile-8x8-mockup.jpg
│   └── mobile/
│       ├── iphone-15-mockup.jpg
│       └── samsung-s24-mockup.jpg
│
├── exports/
│   ├── psd/                  # Exported PSD files
│   ├── png/                  # Exported PNG files (transparent)
│   ├── jpg/                  # Exported JPG files (customer approval)
│   └── print/                # Print-ready files (mirrored, bleed)
│
└── registry/
    ├── templates.json        # Template registry
    ├── product-profiles.json # Product catalog with specs
    ├── assets.json           # Asset library index
    └── mobile-models.json    # Mobile phone model database
```

---

## Directory Purposes

### customer_photos/
Stores customer-uploaded photos organized by product type.
- **sublimation/**: Photos for sublimation printing (mugs, bottles, tiles)
- **mobile/**: Photos for mobile cover printing
- **mosaic/**: Photos for mosaic/collage products
- **caricature/**: Cartoon/caricature style photos

### templates/
PSD template files organized by product category and frame count.
- Each folder contains PSD files with standardized layer naming
- Templates include smart objects for photo placement
- Layer naming convention: `frame_1`, `frame_2`, `background`, `overlay_*`

### backgrounds/
Background images and patterns for design composition.
- **solid-colors/**: Single color backgrounds (RGB/CMYK values in filename)
- **gradients/**: Gradient backgrounds
- **patterns/**: Repeating patterns (stripes, polka dots, etc.)
- **textures/**: Paper, fabric, wood textures
- **themed/**: Occasion-specific backgrounds

### effects/
Overlay effects for enhancing designs.
- **bokeh/**: Bokeh light effects
- **light-leaks/**: Light leak overlays
- **glow/**: Glow and aura effects
- **vignette/**: Vignette overlays
- **blur/**: Blur effects
- **filters/**: Color grading filters

### clipart/
Vector and raster clipart organized by theme.
- All clipart should be PNG with transparency
- Minimum 300 DPI for print quality
- Organized by occasion and subject

### text-presets/
Pre-designed text styles and messages.
- **birthday-wishes/**: "Happy Birthday" styles
- **anniversary-messages/**: Anniversary greetings
- **love-quotes/**: Romantic quotes
- **motivational/**: Inspirational text
- **funny/**: Humorous messages
- **custom-fonts/**: Special font files (.ttf, .otf)

### mockups/
Product mockup images for customer approval.
- High-resolution JPG files (minimum 2000px width)
- Multiple angles where applicable
- Before/after for magic mugs
- Used for customer approval exports

### exports/
Output directory for generated files.
- **psd/**: Layered PSD files for editing
- **png/**: Transparent PNG for web/digital
- **jpg/**: JPG for customer approval (email/WhatsApp)
- **print/**: Print-ready files (mirrored, with bleed)

### registry/
JSON registry files for application indexing.
- **templates.json**: All template metadata
- **product-profiles.json**: Product specifications
- **assets.json**: Asset library index
- **mobile-models.json**: Mobile phone dimensions database

---

## Naming Conventions

### Files
- Use lowercase with hyphens: `birthday-cake-clipart.png`
- Include dimensions: `background-gradient-1920x1080.jpg`
- Include version if applicable: `template-mug-1photo-v2.psd`

### Templates
- Format: `{product}-{framecount}-{theme}.psd`
- Example: `mug-1photo-birthday.psd`, `mug-2photo-love.psd`

### Products
- Format: `{category}-{size}-{variant}`
- Example: `mug-11oz-white`, `bottle-500ml-steel`

---

## Asset Metadata

All assets should include metadata in corresponding registry JSON:
- `name`: Display name
- `path`: Relative path from SubliStudioAssets root
- `category`: Asset category
- `tags`: Search tags
- `dimensions`: Width x Height in pixels
- `dpi`: Resolution (for print assets)
- `created`: Creation date
- `updated`: Last modified date
- `thumbnail`: Path to thumbnail image

---

## Registry Files

See individual schema documents:
- `templates_schema.json` — Template registry schema
- `product_profiles_schema.json` — Product catalog schema
- `assets_schema.json` — Asset library schema
- `mobile_models_schema.json` — Mobile models schema

---

## Version Control

- Registry JSON files are version-controlled
- Large assets (PSD, JPG, PNG) stored externally or in `.gitignore`
- Use `assets/README.md` to document external asset locations

---

## Backup Strategy

- `registry/` folder: Git version control
- `templates/` folder: External backup (large PSD files)
- `mockups/` folder: External backup (high-res images)
- `customer_photos/` folder: Customer data backup (separate system)

---

## Migration Notes

For existing installations:
1. Create `SubliStudioAssets/` root directory
2. Run asset scanner to detect existing files
3. Generate registry JSON files from scan results
4. Update application config to point to new root

---

**Document Version:** 1.0  
**Last Updated:** August 28, 2026  
**Maintained By:** MugX Development Team
