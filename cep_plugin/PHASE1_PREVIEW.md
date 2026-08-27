# Phase 1: JSX Bridge Layer - Preview

## Goal

Build a comprehensive ExtendScript (JSX) API that the JavaScript panel can call for all document and layer operations needed in subsequent phases.

## Functions to Implement

### Document Operations

1. **`openDocument(path)`** - Open a PSD file
2. **`closeDocument(save)`** - Close active document (optionally save)
3. **`createDocument(widthCm, heightCm, dpi, name, colorMode)`** - Create new document
4. **`getDocumentInfo()`** - Get dimensions, color mode, resolution, layer count

### Layer Operations

5. **`getLayersByPattern(namePattern)`** - Find layers matching pattern (e.g., "frame_*")
6. **`getLayerBounds(layerName)`** - Get layer position and size
7. **`getLayerList()`** - Get all layers (already in Phase 0)
8. **`duplicateLayer(layerName, newName)`** - Duplicate a layer
9. **`moveLayer(layerName, x, y)`** - Reposition layer
10. **`resizeLayer(layerName, scalePercent)`** - Scale layer
11. **`rotateLayer(layerName, degrees)`** - Rotate layer
12. **`deleteLayer(layerName)`** - Remove layer

### Smart Object Operations

13. **`placeImageInSmartObject(layerName, imagePath)`** - Replace smart object contents ⭐ CRITICAL
14. **`placeImageAsNewLayer(imagePath, x, y, scale)`** - Place image as new layer
15. **`isSmartObject(layerName)`** - Check if layer is smart object
16. **`getSmartObjectContents()`** - Get linked file path

### Effects & Filters

17. **`applyCircularMask(layerName)`** - Apply circular/elliptical mask
18. **`applyGaussianBlur(layerName, radius)`** - Apply blur filter
19. **`applyLayerStyle(layerName, styleParams)`** - Apply bevel, shadow, etc.

### Export Operations

20. **`flattenAndExport(format, path, options)`** - Export as PNG/JPG/PDF
21. **`exportLayer(layerName, path)`** - Export specific layer
22. **`mirrorLayer(layerName, axis)`** - Flip horizontally/vertically

## Priority Order

1. **Week 1**: Document ops + Smart object replacement (critical for Phase 2)
2. **Week 2**: Layer operations + Export functions
3. **Week 3**: Effects + Filters + Edge cases

## Acceptance Test

From panel JavaScript:
```javascript
// Test smart object replacement
csInterface.evalScript("placeImageInSmartObject('frame_1', '/path/to/photo.jpg')", function(result) {
  console.log("Smart object replaced:", result);
});

// Test layer enumeration
csInterface.evalScript("getLayersByPattern('frame_*')", function(result) {
  var layers = JSON.parse(result);
  console.log("Found", layers.length, "frame layers");
});
```

## Files to Create

- `host/jsx/document_ops.jsx` - Document functions
- `host/jsx/layer_ops.jsx` - Layer functions
- `host/jsx/smart_object_ops.jsx` - Smart object functions ⭐
- `host/jsx/export_ops.jsx` - Export functions
- `host/jsx/effects.jsx` - Filters and effects
- `host/index.jsx` - Update to import all modules

## Timeline

- **Start**: Immediately after Phase 0 acceptance
- **Duration**: 2-3 weeks
- **Blocker**: None (can start now)

---

**Ready to proceed to Phase 1**?
