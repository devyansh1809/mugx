# SubliStudio CEP Plugin - Phase 0: Foundation

## Overview

This is Phase 0 of converting SubliStudio from a standalone Python/PyQt app to a native Adobe Photoshop CEP (Common Extensibility Platform) plugin.

**Status**: ✅ Phase 0 Complete - Basic panel loads in Photoshop and can communicate via ExtendScript

## Folder Structure

```
mugx/
└── cep_plugin/
    ├── CSXS/
    │   └── manifest.xml      # CEP extension manifest
    ├── .debug                 # Chrome remote debugger config
    ├── index.html             # Main panel UI
    ├── css/
    │   └── style.css          # Panel styling
    ├── js/
    │   ├── main.js            # Panel JavaScript
    │   └── CSInterface.js     # Adobe's bridge library (download required)
    └── host/
        └── index.jsx          # ExtendScript host functions
```

## Installation & Testing

### Step 1: Download CSInterface.js

CSInterface.js is Adobe's official JavaScript library for CEP panels. Download it from:

```bash
curl -o js/CSInterface.js "https://raw.githubusercontent.com/Adobe-CEP/CEP-Resources/master/CEP_9.x/Documentation/CSInterface.js"
```

Or manually download from:
https://github.com/Adobe-CEP/CEP-Resources/blob/master/CEP_9.x/Documentation/CSInterface.js

### Step 2: Enable PlayerDebugMode (for development)

CEP extensions must be code-signed for production, but for development you can enable unsigned extensions:

**macOS:**
```bash
defaults write com.adobe.CSXS.7 PlayerDebugMode 1
```

**Windows:**
```cmd
reg add "HKEY_CURRENT_USER\Software\Adobe\CSXS.7" /v PlayerDebugMode /t REG_SZ /d 1 /f
```

**Note:** Replace `7` with your CEP version (7 for CC 2019, 8 for CC 2020, 9 for CC 2021, etc.)

### Step 3: Install Extension

**Option A: Copy to CEP extensions folder**

**macOS:**
```bash
cp -r cep_plugin ~/Library/Application Support/Adobe/CEP/extensions/com.sublistudio.cep
```

**Windows:**
```cmd
xcopy /E /I cep_plugin "%APPDATA%\Adobe\CEP\extensions\com.sublistudio.cep"
```

**Option B: Use .zxp installer (recommended for production)**

Use ZXPSignCmd to sign and package as .zxp, then install via Adobe Exchange or Extension Manager.

### Step 4: Load in Photoshop

1. Open Photoshop CC (2019 or later recommended)
2. Go to **Window > Extensions > SubliStudio CEP**
3. Panel should open showing "Connecting to Photoshop..."
4. Click **Test Connection** button
5. You should see Photoshop version info in the result box

### Step 5: Debug with Chrome (optional but recommended)

The `.debug` file enables Chrome remote debugging:

1. Open Chrome
2. Navigate to: `http://localhost:8888`
3. You'll see your panel's DOM and can debug JavaScript
4. Console logs from the panel appear in Chrome DevTools

## Features

### Phase 0 Features (Complete ✅)

- ✅ Panel loads in Photoshop
- ✅ Connection status indicator
- ✅ Test button calls ExtendScript function
- ✅ Returns Photoshop version and document info
- ✅ Styled UI with module navigation placeholders
- ✅ Error handling and logging

### ExtendScript Functions Available

From `host/index.jsx`:

1. **`getPhotoshopInfo()`** - Returns JSON with:
   - Photoshop version
   - Application name
   - Active document info (name, size, resolution, color mode)

2. **`pingPhotoshop()`** - Simple connectivity test

3. **`createTestDocument()`** - Creates a test document

4. **`getLayerList()`** - Lists all layers in active document

## Testing

### Manual Test

1. Open Photoshop
2. Open a document (any PSD or create new)
3. Window > Extensions > SubliStudio CEP
4. Click "Test Connection"
5. Verify you see:
   - ✓ Green status indicator
   - ✓ Photoshop version displayed
   - ✓ Document info (if document is open)

### JavaScript Console Test

Open Chrome debugger (http://localhost:8888) and run:

```javascript
csInterface.evalScript("pingPhotoshop()", function(result) {
  console.log("Ping result:", result);
});

csInterface.evalScript("getPhotoshopInfo()", function(result) {
  console.log("Photoshop info:", JSON.parse(result));
});
```

## Troubleshooting

### Panel doesn't appear in Window > Extensions menu

- Check manifest.xml Host version range matches your Photoshop version
- Verify PlayerDebugMode is enabled
- Check CEP extensions folder path is correct
- Restart Photoshop after copying files

### Panel appears but shows "Connection failed"

- Make sure Photoshop is fully loaded
- Check Chrome debugger console for errors
- Verify CSInterface.js is loaded (check Network tab)
- Try `pingPhotoshop()` function first

### Test button doesn't work

- Check browser console for JavaScript errors
- Verify event listeners are attached (check main.js init function)
- Make sure CSInterface is initialized

## Next Phases

### Phase 1: JSX Bridge Layer (Next)

Build comprehensive ExtendScript API for:
- Document operations (open, close, create)
- Layer operations (get, create, move, resize, delete)
- Smart object manipulation
- Export functions

### Phase 2: Template Engine

Port template browser and auto-fill logic from Python to JS/JSX

### Phase 3: Manual Editing Tools

Port manual edit tools (swap, resize, background, text)

### Phase 4: Mobile Panel

Build device picker and mobile cover design tools

### Phase 5: 3D Mockup Preview

Port mockup generator to use Photoshop smart objects

### Phase 6: Print Exporter

Build print sheet layout and export

### Phase 7: Magic Modules

Implement caricature, mosaic, and QR label generators

### Phase 8: Asset Library, Licensing, Packaging

Complete asset management, licensing system, and signed distribution

## Resources

- **Adobe CEP Documentation**: https://github.com/Adobe-CEP/CEP-Resources
- **ExtendScript Toolkit**: https://www.adobe.com/devnet/scripting.html
- **Photoshop Scripting Guide**: https://www.adobe.com/devnet/photoshop/scripting.html
- **ZXPSignCmd**: https://github.com/Adobe-CEP/ZXPSignCmd (for signing extensions)

## License

Part of the SubliStudio project. See main repository for license details.
