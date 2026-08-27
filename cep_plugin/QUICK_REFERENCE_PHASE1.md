# Phase 1: JSX Bridge Layer - Quick Reference

## Function Categories

| Module | Functions | File |
|--------|-----------|------|
| Document | 5 | document_ops.jsx |
| Layer | 10 | layer_ops.jsx |
| Smart Object | 6 | smart_object_ops.jsx |
| Effects | 5 | effects.jsx |
| Export | 4 | export_ops.jsx |
| **Total** | **30** | |

## Most Important Functions

### ⭐⭐⭐ CRITICAL (Phase 2 depends on these)
```javascript
placeImageInSmartObject(layerName, imagePath)  // Fill template frames
getLayersByPattern(pattern)                     // Find frame layers
openDocument(path)                              // Open template PSD
flattenAndExport(format, path)                  // Export preview
getLayerBounds(layerName)                       // Get frame positions
```

### ⭐ HIGH PRIORITY
```javascript
createDocument(widthCm, heightCm, dpi, name, mode)  // Create new doc
getDocumentInfo()                                    // Get doc metadata
duplicateLayer(layerName, newName)                   // Duplicate layer
moveLayer(layerName, x, y)                           // Reposition layer
resizeLayer(layerName, scalePercent)                 // Scale layer
exportLayer(layerName, path, format)                 // Export layer
```

### ⭐ MEDIUM PRIORITY
```javascript
applyCircularMask(layerName, x, y, radius)      // Circular mask
applyGaussianBlur(layerName, radius)            // Blur effect
applyLayerStyle(layerName, style, params)       // Bevel/shadow/glow
mirrorLayer(layerName, axis)                    // Flip layer
applyColorOverlay(layerName, r, g, b, opacity)  // Color overlay
```

## Usage Pattern

```javascript
// 1. Call function via evalScript
csInterface.evalScript("functionName(param1, param2)", function(result) {
  // 2. Parse JSON result
  var data = JSON.parse(result);
  
  // 3. Check success
  if (data.success) {
    console.log("Success:", data.message);
    // Use data...
  } else {
    console.error("Error:", data.error);
  }
});
```

## Common Patterns

### Open document and get info
```javascript
csInterface.evalScript("openDocument('/path/to/file.psd')", function(r) {
  var data = JSON.parse(r);
  if (data.success) {
    console.log("Opened:", data.docName);
  }
});
```

### Find layers and place images
```javascript
csInterface.evalScript("getLayersByPattern('frame_*')", function(r) {
  var layers = JSON.parse(r).layers;
  layers.forEach(function(layer, i) {
    csInterface.evalScript("placeImageInSmartObject('" + layer.name + "', '/photo" + i + ".jpg')");
  });
});
```

### Export preview
```javascript
csInterface.evalScript("flattenAndExport('PNG', '/tmp/preview.png')", function(r) {
  var data = JSON.parse(r);
  if (data.success) {
    document.getElementById("preview").src = "/tmp/preview.png";
  }
});
```

## Error Handling

Always check `success` field:

```javascript
if (data.success) {
  // Success - use data
} else {
  // Error - show data.error
}
```

## Testing

```javascript
// Test all categories
csInterface.evalScript("createDocument(10, 10, 300, 'Test', 'RGB')");
csInterface.evalScript("getLayerList()");
csInterface.evalScript("getLayersByPattern('*')");
csInterface.evalScript("placeImageInSmartObject('Smart Object', '/path.jpg')");
csInterface.evalScript("applyGaussianBlur('Layer 1', 5)");
csInterface.evalScript("flattenAndExport('PNG', '/tmp/test.png')");
```

## Files

- `host/document_ops.jsx` - Document operations
- `host/layer_ops.jsx` - Layer operations
- `host/smart_object_ops.jsx` - Smart object operations ⭐
- `host/effects.jsx` - Effects & filters
- `host/export_ops.jsx` - Export operations
- `host/index.jsx` - Main entry point

**Total**: 6 files, ~35 KB
