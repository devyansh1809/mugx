// MugX Photoshop Bridge - Phase 2A Stabilized
// Returns safe JSON-compatible objects without JSON.stringify
// Compatible with Photoshop 27.9.1

#target photoshop

// Global error handler wrapper
function safeExecute(fn) {
    try {
        return fn();
    } catch (e) {
        return {
            _error: true,
            name: e.name || "UnknownError",
            message: e.message || String(e),
            line: e.line || null
        };
    }
}

// Convert Photoshop objects to plain JS objects ( ExtendScript compatible)
function toPlainObject(obj) {
    if (obj === null || obj === undefined) {
        return null;
    }
    
    var result = {};
    for (var key in obj) {
        if (obj.hasOwnProperty(key)) {
            try {
                var value = obj[key];
                if (typeof value === "function") {
                    continue;
                } else if (typeof value === "object" && value !== null) {
                    // Skip complex nested objects
                    result[key] = String(value);
                } else {
                    result[key] = value;
                }
            } catch (e) {
                result[key] = "<error>";
            }
        }
    }
    return result;
}

// 1. pingPhotoshop - Basic connectivity test
function pingPhotoshop() {
    return safeExecute(function() {
        return {
            success: true,
            timestamp: new Date().getTime(),
            appName: app.name,
            version: app.version,
            build: app.build
        };
    });
}

// 2. getPhotoshopInfo - Detailed application information
function getPhotoshopInfo() {
    return safeExecute(function() {
        return {
            success: true,
            name: app.name,
            version: app.version,
            build: app.build,
            platform: app.platform,
            language: app.language,
            path: app.path,
            preferencesFolder: app.preferencesFolder,
            systemInformation: app.systemInformation
        };
    });
}

// 3. getDocumentInfo - Current document details
function getDocumentInfo() {
    return safeExecute(function() {
        if (!app.documents.length) {
            return {
                success: false,
                error: "No open documents",
                documentCount: 0
            };
        }
        
        var doc = app.activeDocument;
        return {
            success: true,
            documentCount: app.documents.length,
            name: doc.name,
            width: doc.width.as("px"),
            height: doc.height.as("px"),
            resolution: doc.resolution.as("pixels/inch"),
            mode: doc.mode.toString(),
            colorSpace: doc.mode,
            bitDepth: doc.bitsPerChannel,
            layerCount: doc.layers.length,
            activeLayer: doc.activeLayer ? doc.activeLayer.name : null,
            filePath: doc.path ? doc.path.fsName : null
        };
    });
}

// 4. getLayerList - List all layers in current document
function getLayerList() {
    return safeExecute(function() {
        if (!app.documents.length) {
            return {
                success: false,
                error: "No open documents",
                layers: []
            };
        }
        
        var doc = app.activeDocument;
        var layers = [];
        
        function collectLayers(layerSet, parentIndex) {
            for (var i = 0; i < layerSet.layers.length; i++) {
                var layer = layerSet.layers[i];
                var layerInfo = {
                    index: i,
                    name: layer.name,
                    kind: layer.kind,
                    visible: layer.visible,
                    opacity: layer.opacity,
                    isBackgroundLayer: layer.isBackgroundLayer,
                    locked: layer.allLocked || layer.positionLocked,
                    parentIndex: parentIndex
                };
                
                layers.push(layerInfo);
                
                // Handle layer sets (groups)
                if (layer.typename === "LayerSet") {
                    collectLayers(layer, i);
                }
            }
        }
        
        collectLayers(doc, -1);
        
        return {
            success: true,
            layerCount: layers.length,
            layers: layers
        };
    });
}

// 5. addTestLayer - Add a test layer to verify write access
function addTestLayer() {
    return safeExecute(function() {
        if (!app.documents.length) {
            return {
                success: false,
                error: "No open documents"
            };
        }
        
        var doc = app.activeDocument;
        var testLayer = doc.artLayers.add();
        testLayer.name = "MugX Test Layer";
        
        return {
            success: true,
            layerName: testLayer.name,
            layerIndex: doc.layers.length - 1,
            message: "Test layer added successfully"
        };
    });
}

// 6. getLayerBounds - Get bounds of active or specified layer
function getLayerBounds(layerName) {
    return safeExecute(function() {
        if (!app.documents.length) {
            return {
                success: false,
                error: "No open documents"
            };
        }
        
        var doc = app.activeDocument;
        var targetLayer = null;
        
        if (layerName) {
            // Find layer by name
            for (var i = 0; i < doc.layers.length; i++) {
                if (doc.layers[i].name === layerName) {
                    targetLayer = doc.layers[i];
                    break;
                }
            }
        } else {
            // Use active layer
            targetLayer = doc.activeLayer;
        }
        
        if (!targetLayer) {
            return {
                success: false,
                error: "Layer not found: " + (layerName || "active layer")
            };
        }
        
        var bounds = targetLayer.bounds;
        return {
            success: true,
            layerName: targetLayer.name,
            bounds: {
                left: bounds[0].as("px"),
                top: bounds[1].as("px"),
                right: bounds[2].as("px"),
                bottom: bounds[3].as("px")
            },
            width: bounds[2].as("px") - bounds[0].as("px"),
            height: bounds[3].as("px") - bounds[1].as("px")
        };
    });
}

// 7. duplicateLayer - Duplicate the active or specified layer
function duplicateLayer(layerName) {
    return safeExecute(function() {
        if (!app.documents.length) {
            return {
                success: false,
                error: "No open documents"
            };
        }
        
        var doc = app.activeDocument;
        var targetLayer = null;
        
        if (layerName) {
            // Find layer by name
            for (var i = 0; i < doc.layers.length; i++) {
                if (doc.layers[i].name === layerName) {
                    targetLayer = doc.layers[i];
                    break;
                }
            }
        } else {
            // Use active layer
            targetLayer = doc.activeLayer;
        }
        
        if (!targetLayer) {
            return {
                success: false,
                error: "Layer not found: " + (layerName || "active layer")
            };
        }
        
        var duplicated = targetLayer.duplicate();
        
        return {
            success: true,
            originalLayer: targetLayer.name,
            duplicatedLayer: duplicated.name,
            message: "Layer duplicated successfully"
        };
    });
}

// Export all functions for CEP bridge
var MugXBridge = {
    pingPhotoshop: pingPhotoshop,
    getPhotoshopInfo: getPhotoshopInfo,
    getDocumentInfo: getDocumentInfo,
    getLayerList: getLayerList,
    addTestLayer: addTestLayer,
    getLayerBounds: getLayerBounds,
    duplicateLayer: duplicateLayer
};

// IIFE wrapper for CEP evalScript compatibility
(function() {
    // Bridge is ready
    return MugXBridge;
})();
