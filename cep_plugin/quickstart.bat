@echo off
echo SubliStudio CEP Plugin - Quick Start
echo ====================================
echo.
echo [1/4] Enabling PlayerDebugMode (Windows)...
reg add "HKEY_CURRENT_USER\Software\Adobe\CSXS.7" /v PlayerDebugMode /t REG_SZ /d 1 /f
echo   Done
echo.
echo [2/4] Downloading CSInterface.js...
if exist "js\CSInterface.js" (
    echo   Already exists
) else (
    curl -o "js\CSInterface.js" "https://raw.githubusercontent.com/Adobe-CEP/CEP-Resources/master/CEP_9.x/Documentation/CSInterface.js"
    if %ERRORLEVEL% EQU 0 (
        echo   Downloaded
    ) else (
        echo   Failed - download manually from GitHub
    )
)
echo.
echo [3/4] Installing to CEP extensions folder...
echo   Copy cep_plugin folder to: %APPDATA%\Adobe\CEP\extensions\com.sublistudio.cep
echo.
echo [4/4] Opening Chrome debugger...
echo   Navigate to: http://localhost:8888
start "" "http://localhost:8888"
echo.
echo ====================================
echo Setup complete!
echo.
echo Next steps:
echo   1. Open Photoshop
echo   2. Window ^> Extensions ^> SubliStudio CEP
echo   3. Click 'Test Connection' button
echo   4. Check Chrome debugger for console logs
echo.
pause
