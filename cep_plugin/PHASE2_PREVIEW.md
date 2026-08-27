# Phase 2: Template Engine - Preview

## Goal

Build the template browser and auto-fill engine that drives Photoshop's PSD templates via the Phase 1 JSX bridge.

## Components

### 1. Template Metadata (JSON)

Port existing Python template schema to JSON:

```json
{
  "templates": [
    {
      "id": "mug_4frame_001",
      "name": "4-Frame Mug Template",
      "productType": "MUG",
      "frameCount": 4,
      "theme": "birthday",
      "thumbnailPath": "assets/templates/mug_4frame_001_thumb.jpg",
      "psdPath": "assets/templates/mug_4frame_001.psd",
      "framePattern": "frame_*",
      "tags": ["mug", "4-frame", "birthday"]
    }
  ]
}
```

### 2. Template Browser UI (HTML/CSS/JS)

- Grid of template thumbnails
- Filters: product type, frame count, theme
- Search by name/tags
- Preview on hover
- Click to select

### 3. Auto-Fill Engine (JS)

```javascript
function autoFillTemplate(template, photos) {
  // 1. Open template PSD
  csInterface.evalScript("openDocument('" + template.psdPath + "')", function() {
    // 2. Get frame layers
    csInterface.evalScript("getLayersByPattern('" + template.framePattern + "')", function(result) {
      var layers = JSON.parse(result).layers;
      
      // 3. Place each photo in corresponding frame
      for (var i = 0; i < photos.length && i < layers.length; i++) {
        csInterface.evalScript("placeImageInSmartObject('" + layers[i].name + "', '" + photos[i] + "')");
      }
      
      // 4. Export preview
      csInterface.evalScript("flattenAndExport('PNG', '/tmp/preview.png')", function() {
        // 5. Show preview in panel
        document.getElementById("preview").src = "/tmp/preview.png";
      });
    });
  });
}
```

### 4. Live Preview

- Show flattened PNG in panel
- Update on every change
- Click to open in Photoshop

### 5. Integration with Phase 1

Uses these Phase 1 functions:
- `openDocument(path)` - Open template PSD
- `getLayersByPattern(pattern)` - Find frame layers
- `placeImageInSmartObject(layerName, imagePath)` - Fill frames
- `flattenAndExport(format, path)` - Generate preview
- `getLayerBounds(layerName)` - Calculate positions

## Acceptance Test

1. Select 4 photos from folder
2. Choose 4-frame template from browser
3. Click "Auto Fill"
4. Photoshop opens template PSD
5. All 4 frames filled with photos
6. Preview shown in panel
7. Click preview → opens in Photoshop as editable PSD

## Timeline

- **Week 1**: Template browser UI + JSON loader
- **Week 2**: Auto-fill engine + live preview
- **Week 3**: Testing + edge cases

## Files to Create

- `js/template_loader.js` - Load template JSON
- `js/template_browser.js` - Browser UI logic
- `js/auto_fill_engine.js` - Auto-fill logic
- `templates/templates.json` - Template metadata
- `css/template_browser.css` - Browser styling
- `template_browser.html` - Browser UI (or integrate into index.html)

---

**Ready to proceed to Phase 2**?
