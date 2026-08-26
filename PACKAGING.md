# Packaging SubliStudio as a standalone macOS app

## 1. Prerequisites

- macOS (PyInstaller does not cross-compile a `.app` from Linux/Windows)
- Project venv active with `pip install -r requirements.txt`
- `pip install pyinstaller`

## 2. Generate a spec file

```bash
cd subli_studio
pyi-makespec --windowed --name SubliStudio main.py
```

Edit `SubliStudio.spec` to bundle assets and pick up psd-tools data files:

```python
from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['main.py'],
    datas=[('assets', 'assets')] + collect_data_files('psd_tools'),
    hiddenimports=['PyQt6.sip'],
)

app = BUNDLE(
    exe, name='SubliStudio.app', icon=None,
    bundle_identifier='com.yourcompany.substudio',
    info_plist={'NSHighResolutionCapable': 'True', 'CFBundleShortVersionString': '0.1.0'},
)
```

## 3. Build

```bash
pyinstaller SubliStudio.spec
```

`dist/SubliStudio.app` is the result. Run from Terminal to see console
output while debugging:

```bash
./dist/SubliStudio.app/Contents/MacOS/SubliStudio
```

## 4. Signing / notarization (optional)

```bash
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAMID)" dist/SubliStudio.app

ditto -c -k --keepParent dist/SubliStudio.app SubliStudio.zip

xcrun notarytool submit SubliStudio.zip \
  --apple-id "you@example.com" --team-id TEAMID --password "app-specific-password" --wait

xcrun stapler staple dist/SubliStudio.app
```

Without this, the app runs fine on your own Mac; on other Macs, Gatekeeper
shows an "unidentified developer" warning users can bypass manually.

## 5. Distributing

- Simplest: zip `dist/SubliStudio.app` (use `ditto` to preserve metadata).
- Nicer: build a `.dmg` with `create-dmg` (`brew install create-dmg`):

```bash
create-dmg --volname "SubliStudio" --window-size 500 300 --icon-size 100 \
  dist/SubliStudio.dmg dist/SubliStudio.app
```

## Troubleshooting

- **"could not find the Qt platform plugin 'cocoa'"** -- `opencv-python`
  (not headless) is installed and its bundled Qt plugins conflict with
  PyQt6. Use `opencv-python-headless` only.
- **Builds but crashes silently** -- run from Terminal to see the
  traceback; usually a missing `hiddenimports` entry for something
  lazily imported (e.g. psd_tools internals).
- **Templates/effects "not found" only in the packaged app** -- resolve
  asset paths relative to `sys._MEIPASS` at runtime, not the source tree:
  ```python
  import sys
  from pathlib import Path
  BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
  ```
- **App is large (100s of MB)** -- normal for PyQt6 + OpenCV + numpy bundled
  together.
- **Gatekeeper blocks the app** -- expected without notarization; notarize
  for distribution, or tell users to right-click -> Open the first time.
