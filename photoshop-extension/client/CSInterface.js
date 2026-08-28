/**
 * CSInterface - Adobe CEP CSInterface library
 * Simplified version for MugX extension
 */

function CSInterface() {
    this.hostEnvironment = null;
}

CSInterface.prototype.evalScript = function(script, callback) {
    if (window.__adobe_cep__ && window.__adobe_cep__.evalScript) {
        window.__adobe_cep__.evalScript(script, callback);
    } else if (window.cep && window.cep.evalScript) {
        window.cep.evalScript(script, callback);
    } else {
        // Fallback for testing
        console.log('evalScript called:', script);
        if (callback) {
            callback('{"success": false, "error": "CEP runtime not available"}');
        }
    }
};

CSInterface.prototype.getSystemPath = function(pathType) {
    if (window.cep && window.cep.util) {
        return window.cep.util.getSystemPath(pathType);
    }
    return null;
};

CSInterface.prototype.openURLInDefaultBrowser = function(url) {
    if (window.cep && window.cep.util) {
        window.cep.util.openURLInDefaultBrowser(url);
    } else {
        window.open(url, '_blank');
    }
};

// Path types
CSInterface.prototype.SYSTEM_PATH_EXTENSION = 'extension';
CSInterface.prototype.SYSTEM_PATH_USER_DATA = 'userData';
CSInterface.prototype.SYSTEM_PATH_COMMON_FILES = 'commonFiles';
CSInterface.prototype.SYSTEM_PATH_MY_DOCUMENTS = 'myDocuments';
CSInterface.prototype.SYSTEM_PATH_APPLICATION = 'application';
CSInterface.prototype.SYSTEM_PATH_TEMP = 'temp';
