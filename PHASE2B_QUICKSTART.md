# Phase 2B — Quick Start Guide

**⏱ 5-minute setup | ✅ Ready to test registries and catalogs**

---

## 1. Set Up Test Directory (2 minutes)

### macOS/Linux
```bash
# Create asset directory structure
mkdir -p ~/SubliStudioAssets/registry
mkdir -p ~/SubliStudioAssets/templates/mugs/1-photo
mkdir -p ~/SubliStudioAssets/templates/mugs/2-photo
mkdir -p ~/SubliStudioAssets/templates/bottles
mkdir -p ~/SubliStudioAssets/backgrounds
mkdir -p ~/SubliStudioAssets/effects
mkdir -p ~/SubliStudioAssets/clipart
mkdir -p ~/SubliStudioAssets/mockups

# Copy registry JSON files from repository
cd mugx/assets/registry
cp templates.json product-profiles.json assets.json mobile-models.json ~/SubliStudioAssets/registry/
```

### Windows (PowerShell)
```powershell
# Create asset directory structure
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\SubliStudioAssets\registry"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\SubliStudioAssets\templates\mugs\1-photo"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\SubliStudioAssets\templates\mugs\2-photo"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\SubliStudioAssets\templates\bottles"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\SubliStudioAssets\backgrounds"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\SubliStudioAssets\effects"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\SubliStudioAssets\clipart"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\SubliStudioAssets\mockups"

# Copy registry JSON files (use File Explorer or robocopy)
robocopy mugx\assets\registry "%USERPROFILE%\SubliStudioAssets\registry" *.json
```

---

## 2. Run Registry Loader Test (1 minute)

```bash
cd mugx/core
python3 asset_registry_loader.py
```

**Expected output:**
```
📂 Loading asset registries from: /home/user/SubliStudioAssets
============================================================
✅ Loaded: templates.json (10 entries)
✅ Loaded: product-profiles.json (9 entries)
✅ Loaded: assets.json (13 entries)
✅ Loaded: mobile-models.json (4 entries)
============================================================
✅ Loaded 4/4 registries successfully

📄 Found 10 templates
📄 Found 5 mug templates
📄 Found 2 2-photo mug templates
📄 Found 3 birthday templates

🛍️  Found 9 products
🛍️  Found 9 active products

🎨 Found 13 assets

📱 Found 4 mobile models
```

---

## 3. Run Product Catalog Test (1 minute)

```bash
python3 product_catalog.py
```

**Expected output:**
```
📊 Loaded 9 products
📦 Categories: ['bottles', 'cushions', 'keyrings', 'mobile', 'mugs', 'tiles', 'tshirts']

☕ Found 2 mug products

🔍 Search 'iphone': 2 results

📄 Print specs for 11oz White Ceramic Mug:
   Canvas: {'width': 2400, 'height': 1038}
   DPI: 300
   Mirror: Yes

================================================================================
🛍️  MUGX PRODUCT CATALOG
================================================================================

📦 BOTTLES
----------------------------------------

  🏷️  500ml
    ✅   500ml Stainless Steel Bottle
       ID: bottle-500ml-steel
       Price: ₹450
       Canvas: 900x2100px @ 300 DPI

📦 MUGS
----------------------------------------

  🏷️  11oz
    ✅   11oz White Ceramic Mug
       ID: mug-11oz-white
       Price: ₹250
       Canvas: 2400x1038px @ 300 DPI
       ⚠️  MIRROR REQUIRED for printing

[... more products ...]
```

---

## 4. Run Template Browser Test (1 minute)

```bash
python3 template_browser.py
```

**Expected output:**
```
📊 Loaded 10 templates
📦 Categories: ['bottles', 'cushions', 'keyrings', 'mobile', 'mugs', 'tiles', 'tshirts']
🖼️  Frame counts: [1, 2, 3, 4, 6]

☕ Found 5 mug templates

🔍 Search 'birthday': 2 results

📄 Layer contract:
   Frames: ['frame_1', 'frame_2']
   Background: background
   Overlays: ['overlay_hearts', 'overlay_text']

✅ Layer validation: {'valid': True, 'missing_layers': [], 'extra_layers': []}

================================================================================
📄 MUGX TEMPLATE BROWSER
================================================================================

📦 MUGS
----------------------------------------

  🖼️  1 Photo
    ⭐  Birthday Cake Mug - Single Photo
       ID: mug-1photo-birthday-cake-001
       Theme: birthday | Occasion: kids-birthday
       Tags: birthday, cake, kids, colorful, balloons
       Frames: frame_1

  🖼️  2 Photos
      Love Hearts Mug - Two Photo
       ID: mug-2photo-love-hearts-001
       Theme: love-romantic | Occasion: anniversary
       Tags: love, hearts, romantic, couple, anniversary
       Frames: frame_1, frame_2

[... more templates ...]
```

---

## 5. Verify Key Features (1 minute)

### ✅ Registry Loading
- [ ] All 4 registries load successfully
- [ ] Templates: 10 entries
- [ ] Products: 9 entries
- [ ] Assets: 13 entries
- [ ] Mobile models: 4 entries

### ✅ Filtering
- [ ] Mug templates: 5 found
- [ ] 2-photo mug templates: 1 found
- [ ] Mug products: 2 found
- [ ] iPhone products: 2 found

### ✅ Search
- [ ] Search "birthday": 2+ templates found
- [ ] Search "iphone": 2 products found

### ✅ Layer Contracts
- [ ] Layer contract retrieved successfully
- [ ] Frames: ['frame_1', 'frame_2']
- [ ] Background: 'background'
- [ ] Validation passes

### ✅ Print Specs
- [ ] Canvas size: 2400x1038px
- [ ] DPI: 300
- [ ] Mirror rule: True for mugs

---

## Quick Python API Test

```python
from pathlib import Path
from core.asset_registry_loader import AssetRegistryLoader
from core.product_catalog import ProductCatalog
from core.template_browser import TemplateBrowser

# Initialize
assets_root = Path.home() / 'SubliStudioAssets'
loader = AssetRegistryLoader(assets_root)
loader.load_all_registries()

# Test templates
templates = loader.get_templates_by_category('mugs')
print(f"Mug templates: {len(templates)}")

mug_2photo = loader.get_templates_by_frame_count('mugs', 2)
print(f"2-photo mug templates: {len(mug_2photo)}")

# Test products
catalog = ProductCatalog(loader)
catalog.load()

mugs = catalog.filter_by_category('mugs')
print(f"Mug products: {len(mugs)}")

specs = catalog.get_print_specs('mug-11oz-white')
print(f"Canvas: {specs['canvas_size']['width']}x{specs['canvas_size']['height']}px")
print(f"Mirror: {specs['print_mirror_rule']}")

# Test templates
browser = TemplateBrowser(loader)
browser.load()

contract = browser.get_layer_contract('mug-2photo-love-hearts-001')
print(f"Layer frames: {contract['frames']}")

validation = browser.validate_layer_names(
    'mug-2photo-love-hearts-001',
    ['frame_1', 'frame_2', 'background']
)
print(f"Validation: {validation['valid']}")
```

**Expected output:**
```
Mug templates: 5
2-photo mug templates: 1
Mug products: 2
Canvas: 2400x1038px
Mirror: True
Layer frames: ['frame_1', 'frame_2']
Validation: True
```

---

## Troubleshooting

### Registry files not found?
```bash
# Check if files exist
ls -la ~/SubliStudioAssets/registry/

# Should show:
# templates.json
# product-profiles.json
# assets.json
# mobile-models.json
```

### Python import errors?
```bash
# Make sure you're in mugx/core directory
cd mugx/core

# Or add parent directory to path
export PYTHONPATH="..:$PYTHONPATH"
```

### JSON parse errors?
```bash
# Validate JSON syntax
python3 -m json.tool ~/SubliStudioAssets/registry/templates.json > /dev/null && echo "Valid JSON"
```

---

## Success! ✅

When you see:
- ✅ All 4 registries load successfully
- ✅ Filtering works (category, frame count)
- ✅ Search finds templates and products
- ✅ Layer contracts retrieved correctly
- ✅ Print specs show correct canvas size and mirror rule
- ✅ Layer validation passes

**Phase 2B is validated and ready to merge!**

---

## Next Steps

1. **Complete full acceptance test:** `PHASE2B_ACCEPTANCE.md`
2. **Merge to v2 branch:**
   ```bash
   git checkout v2
   git merge phase2b-asset-catalog
   git push origin v2
   ```
3. **Begin Phase 3:** Asset Library UI
   - Asset browser widget
   - Thumbnail previews
   - Drag-and-drop

---

**Branch:** `phase2b-asset-catalog`  
**Base:** `phase2a-bridge-stabilize`  
**Status:** Ready for testing  
**Next:** Acceptance test → Merge → Phase 3
