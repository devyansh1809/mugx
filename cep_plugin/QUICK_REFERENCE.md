# CEP Plugin Quick Reference

## Install (macOS)
```bash
defaults write com.adobe.CSXS.7 PlayerDebugMode 1
cp -r cep_plugin ~/Library/Application\ Support/Adobe/CEP/extensions/com.sublistudio.cep
```

## Install (Windows)
```cmd
reg add "HKEY_CURRENT_USER\Software\Adobe\CSXS.7" /v PlayerDebugMode /t REG_SZ /d 1 /f
xcopy /E /I cep_plugin "%APPDATA%\Adobe\CEP\extensions\com.sublistudio.cep"
```

## Test
1. Open Photoshop
2. Window > Extensions > SubliStudio CEP
3. Click "Test Connection"
4. See Photoshop version

## Debug
- Chrome: http://localhost:8888
- Console: Chrome DevTools
- JSX errors: Photoshop's JavaScript console

## ExtendScript Functions
```javascript
getPhotoshopInfo()      // Returns JSON with version, doc info
pingPhotoshop()         // Simple connectivity test
createTestDocument()    // Creates new document
getLayerList()          // Lists all layers
```

## Panel Functions
```javascript
csInterface.evalScript("getPhotoshopInfo()", callback)
csInterface.getSystemPath("extension")
csInterface.openURLInDefaultBrowser("https://...")
```

## Common Issues
- Panel not showing? → Check PlayerDebugMode, restart Photoshop
- Connection failed? → Wait for Photoshop to fully load
- Test button not working? → Check Chrome console for errors
