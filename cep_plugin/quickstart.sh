#!/bin/bash
echo "SubliStudio CEP Plugin - Quick Start"
echo "===================================="
echo ""
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "[1/4] Enabling PlayerDebugMode (macOS)..."
    defaults write com.adobe.CSXS.7 PlayerDebugMode 1
    echo "  ✓ Done"
else
    echo "[1/4] Windows: Run this command manually:"
    echo '  reg add "HKEY_CURRENT_USER\\Software\\Adobe\\CSXS.7" /v PlayerDebugMode /t REG_SZ /d 1 /f'
fi
echo ""
echo "[2/4] Downloading CSInterface.js..."
if [ -f "js/CSInterface.js" ]; then
    echo "  ✓ Already exists"
else
    curl -o js/CSInterface.js "https://raw.githubusercontent.com/Adobe-CEP/CEP-Resources/master/CEP_9.x/Documentation/CSInterface.js"
    if [ $? -eq 0 ]; then
        echo "  ✓ Downloaded"
    else
        echo "  ✗ Failed - download manually from GitHub"
    fi
fi
echo ""
echo "[3/4] Installing to CEP extensions folder..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    CEP_DIR="$HOME/Library/Application Support/Adobe/CEP/extensions"
    mkdir -p "$CEP_DIR"
    cp -r . "$CEP_DIR/com.sublistudio.cep"
    echo "  ✓ Installed to: $CEP_DIR/com.sublistudio.cep"
else
    echo "  Windows: Copy cep_plugin folder to: %APPDATA%\\Adobe\\CEP\\extensions\\com.sublistudio.cep"
fi
echo ""
echo "[4/4] Opening Chrome debugger..."
echo "  Navigate to: http://localhost:8888"
open "http://localhost:8888" 2>/dev/null || echo "  Open manually in Chrome"
echo ""
echo "===================================="
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Open Photoshop"
echo "  2. Window > Extensions > SubliStudio CEP"
echo "  3. Click 'Test Connection' button"
echo "  4. Check Chrome debugger for console logs"
echo ""
