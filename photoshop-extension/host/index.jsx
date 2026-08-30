// MugX Photoshop Bridge - Phase 2A Stabilized (Fix: safe string-serialized JSON)
// Every bridge function returns a JSON STRING (built with a custom encoder,
// not JSON.stringify) so CSInterface.evalScript() can hand the panel a
// parseable string instead of "[object Object]".
// Compatible with Photoshop 27.9.1

#target photoshop

// ---------- Custom JSON encoder (no JSON.stringify) ----------
function jsonEscape(str) {
    str = String(str);
    var out = "";
    for (var i = 0; i < str.length; i++) {
        var c = str.charAt(i);
        var code = str.charCodeAt(i);
        if (c === '"') { out += '\\"'; }
        else if (c === '\\') { out += '\\\\'; }
        else if (c === '\n') { out += '\\n'; }
        else if (c === '\r') { out += '\\r'; }
        else if (c === '\t') { out += '\\t'; }
        else if (code < 0x20) { out += ''; }
        else { out += c; }
    }
    return out;
}

function toJSON(value) {
    if (value === null || value === undefined) {
        return "null";
    }
    var t = typeof value;
    if (t === "number") {
        if (!isFinite(value)) return "null";
        return String(value);
    }
    if (t === "boolean") {
        return value ? "true" : "false";
    }
    if (t === "string") {
        return '"' + jsonEscape(value) + '"';
    }
    if (value && value.constructor && value.constructor.name === "Array") {
        var parts = [];
        for (var i = 0; i < value.length; i++) {
            parts.push(toJSON(value[i]));
        }
        return "[" + parts.join(",") + "]";
    }
    if (t === "object") {
        var pairs = [];
        for (var key in value) {
            if (value.hasOwnProperty(key)) {
                var v = value[key];
                if (typeof v === "function") { continue; }
                pairs.push('"' + jsonEscape(key) + '":' + toJSON(v));
            }
        }
        return "{" + pairs.join(",") + "}";
    }
    return '"' + jsonEscape(String(value)) + '"';
}

// Global error handler wrapper - always returns a JSON STRING
function safeExecute(fn) {
    try {
        var result = fn();
        return toJSON(result);
    } catch (e) {
        return toJSON({
            _error: true,
            success: false,
            name: e.name || "UnknownError",
            message: e.message || String(e),
            line: e.line || null
        });
    }
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
            platform: String(app.platform),
            language: String(app.language),
            path: String(app.path),
            preferencesFolder: String(app.preferencesFolder),
            systemInformation: String(app.systemInformation)
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
            resolution: doc.resolution,
            mode: String(doc.mode),
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
                    kind: String(layer.typename === "LayerSet" ? "layerSet" : "artLayer"),
                    visible: layer.visible,
                    opacity: layer.opacity,
                    isBackgroundLayer: !!layer.isBackgroundLayer,
                    locked: !!(layer.allLocked || layer.positionLocked),
                    parentIndex: parentIndex
                };

                layers.push(layerInfo);

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
            for (var i = 0; i < doc.layers.length; i++) {
                if (doc.layers[i].name === layerName) {
                    targetLayer = doc.layers[i];
                    break;
                }
            }
        } else {
            targetLayer = doc.activeLayer;
        }

        if (!targetLayer) {
            return {
                success: false,
                error: "Layer not found: " + (layerName || "active layer")
            };
        }

        var bounds = targetLayer.bounds;
        var left = bounds[0].as("px");
        var top = bounds[1].as("px");
        var right = bounds[2].as("px");
        var bottom = bounds[3].as("px");

        return {
            success: true,
            layerName: targetLayer.name,
            bounds: {
                left: left,
                top: top,
                right: right,
                bottom: bottom
            },
            width: right - left,
            height: bottom - top
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
            for (var i = 0; i < doc.layers.length; i++) {
                if (doc.layers[i].name === layerName) {
                    targetLayer = doc.layers[i];
                    break;
                }
            }
        } else {
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
