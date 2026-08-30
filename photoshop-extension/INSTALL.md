# MugX Photoshop Extension - Installation Guide

## Prerequisites

- Adobe Photoshop 2026 (version 27.9.1)
- macOS 10.15+ or Windows 10+
- Node.js 16+ (for development)

---

## Quick Install

### 1. Enable Developer Mode

**macOS:**
```bash
defaults write com.adobe.CSXS.9 PlayerDebugMode 1
```

**Windows:**
1. Open Registry Editor (`regedit`)
2. Navigate to: `HKEY_CURRENT_USER\Software\Adobe\CSXS.9`
3. Create new String Value: `PlayerDebugMode`
4. Set value to: `1`

### 2. Copy Extension Files

**macOS:**
```bash
# Create extensions folder if it doesn't exist
mkdir -p "~/Library/Application Support/Adobe/CEP/extensions"

# Copy the photoshop-extension folder
cp -r photoshop-extension "~/Library/Application Support/Adobe/CEP/extensions/mugx-photoshop"
```

**Windows:**
```bash
# Create extensions folder if it doesn't exist
mkdir "%APPDATA%\Adobe\CEP\extensions"

# Copy the photoshop-extension folder (use File Explorer or robocopy)
robocopy photoshop-extension "%APPDATA%\Adobe\CEP\extensions\mugx-photoshop" /E
```

### 3. Restart Photoshop

1. Close Photoshop completely (Cmd+Q / Alt+F4)
2. Reopen Photoshop
3. Go to **Window → Extensions → MugX Panel**

---

## Verification

### Panel Should Appear
- Title: "MugX Photoshop Bridge"
- Status indicator at top
- Five test buttons enabled
- Result display area at bottom

### Test Connectivity
1. Click **"Ping Photoshop"**
2. Should show:
   ```json
   {
     "success": true,
     "appName": "Adobe Photoshop",
     "version": "27.9.1"
   }
   ```
3. Status should turn green: "Connected"

---

## Troubleshooting

### Panel Not Appearing

**Check extension folder:**
```bash
# macOS
ls -la "~/Library/Application Support/Adobe/CEP/extensions/mugx-photoshop"

# Windows
dir "%APPDATA%\Adobe\CEP\extensions\mugx-photoshop"
```

Should contain:
- `CSXS/manifest.xml`
- `host/index.jsx`
- `client/index.html`

**Check Developer Mode:**
```bash
# macOS
defaults read com.adobe.CSXS.9 PlayerDebugMode
# Should return: 1

# Windows (PowerShell)
Get-ItemProperty -Path "HKCU:\Software\Adobe\CSXS.9" -Name PlayerDebugMode
# Should return: 1
```

### "EvalScript error." in Console

This indicates ExtendScript execution failed. Check:
1. `host/index.jsx` syntax is valid
2. `#target photoshop` is present
3. No unsupported Photoshop APIs

**Debug in Photoshop:**
1. Open Photoshop
2. Press `Cmd+Opt+Shift+I` (macOS) or `Ctrl+Alt+Shift+I` (Windows)
3. Check JavaScript console for errors

### Panel Shows but Buttons Disabled

- Panel is still connecting
- Wait 2-3 seconds for initialization
- Check Photoshop is fully loaded
- Try closing and reopening panel

### Version Mismatch

If manifest targets 27.9.1 but you have different version:

**Edit `CSXS/manifest.xml`:**
```xml
<Host Name="PHXS" Version="[27.0,28.0)" />
```

This allows any 27.x version.

---

## Development

### Debug Mode

Enable CEP debugging:

**macOS:**
```bash
defaults write com.adobe.CSXS.9 DebugMode 1
```

**Windows:**
```reg
HKEY_CURRENT_USER\Software\Adobe\CSXS.9
"DebugMode"="1"
```

### View Panel Logs

**macOS:**
```bash
# CEP logs
log show --predicate 'process == "Adobe CEP"' --last 1h

# Or check Console.app
```

**Windows:**
```
%LOCALAPPDATA%\Temp\cep_logs
```

### Hot Reload

For development, you can modify files and reload:

1. Edit `client/index.html` or `host/index.jsx`
2. In Photoshop: Window → Extensions → MugX Panel
3. Close panel
4. Reopen panel (Window → Extensions → MugX Panel)

---

## Uninstall

**macOS:**
```bash
rm -rf "~/Library/Application Support/Adobe/CEP/extensions/mugx-photoshop"
```

**Windows:**
```bash
rmdir /s "%APPDATA%\Adobe\CEP\extensions\mugx-photoshop"
```

Disable developer mode:

**macOS:**
```bash
defaults write com.adobe.CSXS.9 PlayerDebugMode 0
```

**Windows:**
```reg
HKEY_CURRENT_USER\Software\Adobe\CSXS.9
"PlayerDebugMode"="0"
```

---

## Support

For issues or questions:
1. Check `PHASE2A_ACCEPTANCE.md` for test procedures
2. Review `README_PHASE2A.md` for bridge documentation
3. Check Photoshop JavaScript console for errors
4. Verify extension folder structure matches expected layout

---

## File Structure

```
mugx-photoshop/
├── CSXS/
│   └── manifest.xml          # CEP manifest
├── host/
│   └── index.jsx             # ExtendScript bridge
├── client/
│   ├── index.html            # Panel UI
│   └── CSInterface.js        # CEP library
├── main.js                   # Error handling
├── README_PHASE2A.md         # Documentation
└── INSTALL.md                # This file
```

---

## License

Part of MugX project - Custom printing solution for retail entrepreneurs.
