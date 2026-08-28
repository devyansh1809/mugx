# Phase 2A — Quick Start Guide

**⏱ 5-minute setup | ✅ Ready to test in Photoshop 27.9.1**

---

## 1. Install (2 minutes)

### macOS
```bash
# Enable developer mode
defaults write com.adobe.CSXS.9 PlayerDebugMode 1

# Copy extension
mkdir -p "~/Library/Application Support/Adobe/CEP/extensions"
cp -r photoshop-extension "~/Library/Application Support/Adobe/CEP/extensions/mugx-photoshop"
```

### Windows
```powershell
# Enable developer mode (PowerShell as Administrator)
New-ItemProperty -Path "HKCU:\Software\Adobe\CSXS.9" -Name "PlayerDebugMode" -Value "1" -Force

# Copy extension (use File Explorer or robocopy)
robocopy photoshop-extension "%APPDATA%\Adobe\CEP\extensions\mugx-photoshop" /E
```

---

## 2. Test (3 minutes)

1. **Restart Photoshop** (close completely, reopen)

2. **Open panel:**
   - Window → Extensions → MugX Panel

3. **Click test buttons:**
   - ✅ **Ping Photoshop** → Should show green "Connected"
   - ✅ **Get PS Info** → Shows Photoshop details
   - ✅ **Get Doc Info** → Shows document info (open a PSD first)
   - ✅ **Get Layers** → Lists all layers
   - ✅ **Add Test Layer** → Creates layer in Photoshop

4. **Test error handling:**
   - Close all documents
   - Click "Get Doc Info"
   - Should show **error** (not false success) ✅

---

## 3. Verify (1 minute)

### Expected Results

| Test | Expected Result |
|------|----------------|
| Panel opens | ✅ No errors |
| Ping Photoshop | ✅ Green "Connected" status |
| Get PS Info | ✅ Shows version 27.9.1 |
| Get Doc Info | ✅ Shows document details |
| Get Layers | ✅ Lists layers correctly |
| Add Test Layer | ✅ New layer appears in Photoshop |
| Error handling | ✅ Shows error, not false success |

### If All Pass ✅

**Phase 2A is complete!** Next steps:

1. Complete full acceptance test: `PHASE2A_ACCEPTANCE.md`
2. Merge to `v2` branch
3. Begin Phase 2B: Template Browser

---

## Troubleshooting

### Panel not appearing?
```bash
# macOS - verify install
ls -la "~/Library/Application Support/Adobe/CEP/extensions/mugx-photoshop"

# Should contain: CSXS/, host/, client/
```

### "EvalScript error." in console?
- Check `host/index.jsx` syntax
- Verify `#target photoshop` is present
- Restart Photoshop

### Buttons disabled?
- Wait 2-3 seconds for initialization
- Check Photoshop is fully loaded
- Close and reopen panel

### Need more help?
- Full guide: `photoshop-extension/INSTALL.md`
- API docs: `photoshop-extension/README_PHASE2A.md`
- Acceptance test: `PHASE2A_ACCEPTANCE.md`

---

## Bridge API Reference

### pingPhotoshop()
```javascript
{
  success: true,
  timestamp: 1724847000000,
  appName: "Adobe Photoshop",
  version: "27.9.1",
  build: "27.9.1"
}
```

### getDocumentInfo()
```javascript
{
  success: true,
  documentCount: 1,
  name: "design.psd",
  width: 3000,
  height: 3000,
  resolution: 300,
  mode: "RGBM",
  layerCount: 5,
  activeLayer: "Background"
}
```

### getLayerList()
```javascript
{
  success: true,
  layerCount: 5,
  layers: [
    { index: 0, name: "Layer 1", kind: "artLayer", visible: true }
  ]
}
```

### addTestLayer()
```javascript
{
  success: true,
  layerName: "MugX Test Layer",
  layerIndex: 5,
  message: "Test layer added successfully"
}
```

---

## Files at a Glance

| File | What It Does |
|------|-------------|
| `CSXS/manifest.xml` | CEP manifest (targets PS 27.9.1) |
| `host/index.jsx` | 7 bridge functions (no JSON.stringify) |
| `client/index.html` | Panel UI with test buttons |
| `main.js` | **Critical fix:** EvalScript error = FAILURE |
| `PHASE2A_ACCEPTANCE.md` | Full acceptance checklist |
| `INSTALL.md` | Detailed installation guide |

---

## Success! ✅

When you see:
- ✅ Green "Connected" status
- ✅ All buttons working
- ✅ Test layer created in Photoshop
- ✅ Errors shown correctly (no false success)

**Phase 2A is validated and ready to merge!**

---

**Branch:** `phase2a-bridge-stabilize`  
**Base:** `v2`  
**Status:** Ready for testing  
**Next:** Acceptance test → Merge → Phase 2B
