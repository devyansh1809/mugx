/**
 * MugX Photoshop Extension - Main Entry Point
 * Phase 2A: Stabilized bridge with proper error handling
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 400,
        height: 650,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    mainWindow.loadFile(path.join(__dirname, 'client', 'index.html'));

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// Handle bridge calls from panel
ipcMain.handle('callBridge', async (event, functionName, args) => {
    try {
        // In a real CEP extension, this would use CSInterface.evalScript
        // For Electron testing, we simulate the bridge
        const result = await simulateBridgeCall(functionName, args);
        return { success: true, data: result };
    } catch (error) {
        return { 
            success: false, 
            error: error.message,
            isEvalScriptError: error.message.includes('EvalScript error.')
        };
    }
});

// Simulated bridge for testing (replace with actual CEP calls in production)
async function simulateBridgeCall(functionName, args) {
    // This is a placeholder - in production, use actual CSInterface.evalScript
    return new Promise((resolve, reject) => {
        // Simulate bridge response
        if (functionName === 'pingPhotoshop') {
            resolve({
                success: true,
                timestamp: Date.now(),
                appName: 'Adobe Photoshop',
                version: '27.9.1',
                build: '27.9.1'
            });
        } else {
            reject(new Error('Function not implemented in simulation'));
        }
    });
}

// CRITICAL: Proper error handling for EvalScript
// "EvalScript error." must be treated as FAILURE, not success
function handleEvalScriptResult(result, callback) {
    if (result === 'EvalScript error.') {
        // This is a FAILURE - do NOT treat as success
        callback({
            success: false,
            error: 'EvalScript error.',
            isEvalScriptError: true,
            message: 'ExtendScript execution failed. Check Photoshop console for details.'
        });
        return;
    }
    
    try {
        // Parse the returned object
        const parsed = eval('(' + result + ')');
        
        if (parsed && parsed._error) {
            // Bridge-level error
            callback({
                success: false,
                error: parsed.name || 'BridgeError',
                message: parsed.message,
                line: parsed.line
            });
        } else {
            // Success
            callback({
                success: true,
                data: parsed
            });
        }
    } catch (e) {
        // Parse error
        callback({
            success: false,
            error: 'ParseError',
            message: 'Failed to parse ExtendScript result: ' + e.message,
            rawResult: result
        });
    }
}

app.whenReady().then(() => {
    createWindow();
    
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// Export for testing
module.exports = { handleEvalScriptResult, simulateBridgeCall };
