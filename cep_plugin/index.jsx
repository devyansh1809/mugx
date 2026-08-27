#target photoshop

function escapeJsonString(value) {
    return String(value)
        .replace(/\\/g, "\\\\")
        .replace(/"/g, '\\"')
        .replace(/\r/g, "\\r")
        .replace(/\n/g, "\\n");
}

function pingPhotoshop() {
    try {
        return '{"success":true,"version":"' +
            escapeJsonString(app.version) +
            '","name":"' +
            escapeJsonString(app.name) +
            '"}';
    } catch (e) {
        return '{"success":false,"error":"' +
            escapeJsonString(e) +
            '"}';
    }
}

function getPhotoshopInfo() {
    try {
        var output = '{"success":true';
        output += ',"version":"' + escapeJsonString(app.version) + '"';
        output += ',"name":"' + escapeJsonString(app.name) + '"';
        output += ',"documents":' + app.documents.length;

        if (app.documents.length > 0) {
            var doc = app.activeDocument;
            output += ',"document":"' + escapeJsonString(doc.name) + '"';
            output += ',"widthPx":' + doc.width.as("px");
            output += ',"heightPx":' + doc.height.as("px");
            output += ',"resolution":' + doc.resolution;
        }

        output += '}';
        return output;
    } catch (e) {
        return '{"success":false,"error":"' +
            escapeJsonString(e) +
            '"}';
    }
}

function getDocumentInfo() {
    try {
        if (app.documents.length === 0) {
            return '{"success":false,"error":"No document open"}';
        }

        var doc = app.activeDocument;

        return '{"success":true' +
            ',"name":"' + escapeJsonString(doc.name) + '"' +
            ',"widthPx":' + doc.width.as("px") +
            ',"heightPx":' + doc.height.as("px") +
            ',"resolution":' + doc.resolution +
            '}';
    } catch (e) {
        return '{"success":false,"error":"' +
            escapeJsonString(e) + '"}';
    }
}

function getLayerList() {
    try {
        if (app.documents.length === 0) {
            return '{"success":false,"error":"No document open"}';
        }

        var doc = app.activeDocument;
        var output = '{"success":true,"count":' + doc.layers.length + ',"layers":[';

        for (var i = 0; i < doc.layers.length; i++) {
            if (i > 0) {
                output += ',';
            }

            output += '{"index":' + i +
                ',"name":"' + escapeJsonString(doc.layers[i].name) + '"' +
                ',"visible":' + (doc.layers[i].visible ? 'true' : 'false') +
                '}';
        }

        output += ']}';
        return output;
    } catch (e) {
        return '{"success":false,"error":"' +
            escapeJsonString(e) +
            '"}';
    }
}

function addTestLayer(layerName) {
    try {
        if (app.documents.length === 0) {
            return '{"success":false,"error":"No document open"}';
        }

        var doc = app.activeDocument;
        var layer = doc.artLayers.add();
        layer.name = layerName || "SubliStudio Test Layer";

        return '{"success":true,"name":"' +
            escapeJsonString(layer.name) +
            '","index":' + layer.itemIndex + '}';
    } catch (e) {
        return '{"success":false,"error":"' +
            escapeJsonString(e) +
            '"}';
    }
}

function getLayerBounds(layerName) {
    try {
        if (app.documents.length === 0) {
            return '{"success":false,"error":"No document open"}';
        }

        var doc = app.activeDocument;
        var layer = doc.layers.getByName(layerName);
        var b = layer.bounds;

        return '{"success":true,"name":"' +
            escapeJsonString(layer.name) +
            '","left":' + b[0].as("px") +
            ',"top":' + b[1].as("px") +
            ',"right":' + b[2].as("px") +
            ',"bottom":' + b[3].as("px") +
            ',"width":' + (b[2].as("px") - b[0].as("px")) +
            ',"height":' + (b[3].as("px") - b[1].as("px")) +
            '}';
    } catch (e) {
        return '{"success":false,"error":"' +
            escapeJsonString(e) +
            '"}';
    }
}

function duplicateLayer(layerName, newName) {
    try {
        if (app.documents.length === 0) {
            return '{"success":false,"error":"No document open"}';
        }

        var doc = app.activeDocument;
        var source = doc.layers.getByName(layerName);
        var copy = source.duplicate();

        if (newName && newName !== "") {
            copy.name = newName;
        }

        return '{"success":true,"source":"' +
            escapeJsonString(source.name) +
            '","copy":"' +
            escapeJsonString(copy.name) +
            '"}';
    } catch (e) {
        return '{"success":false,"error":"' +
            escapeJsonString(e) +
            '"}';
    }
}

function createTestRectangle(layerName, left, top, width, height, red, green, blue) {
    try {
        if (app.documents.length === 0) {
            return '{"success":false,"error":"No document open"}';
        }

        var doc = app.activeDocument;
        var layer = doc.artLayers.add();
        layer.name = layerName || "Test Rectangle";

        var color = new SolidColor();
        color.rgb.red = red;
        color.rgb.green = green;
        color.rgb.blue = blue;

        doc.selection.select([
            [left, top],
            [left + width, top],
            [left + width, top + height],
            [left, top + height]
        ]);

        doc.selection.fill(color);
        doc.selection.deselect();

        return '{"success":true,"name":"' +
            escapeJsonString(layer.name) +
            '","left":' + left +
            ',"top":' + top +
            ',"width":' + width +
            ',"height":' + height +
            '}';
    } catch (e) {
        return '{"success":false,"error":"' +
            escapeJsonString(e) +
            '"}';
    }
}

function moveLayer(layerName, targetLeft, targetTop) {
    try {
        if (app.documents.length === 0) {
            return '{"success":false,"error":"No document open"}';
        }

        var doc = app.activeDocument;
        var layer = doc.layers.getByName(layerName);
        var bounds = layer.bounds;

        var currentLeft = bounds[0].as("px");
        var currentTop = bounds[1].as("px");

        layer.translate(
            targetLeft - currentLeft,
            targetTop - currentTop
        );

        return getLayerBounds(layerName);
    } catch (e) {
        return '{"success":false,"error":"' +
            escapeJsonString(e) +
            '"}';
    }
}

function setLayerOpacity(layerName, opacity) {
    try {
        if (app.documents.length === 0) {
            return '{"success":false,"error":"No document open"}';
        }

        if (opacity < 0 || opacity > 100) {
            return '{"success":false,"error":"Opacity must be between 0 and 100"}';
        }

        var layer = app.activeDocument.layers.getByName(layerName);
        layer.opacity = opacity;

        return '{"success":true,"name":"' +
            escapeJsonString(layer.name) +
            '","opacity":' + layer.opacity +
            '}';
    } catch (e) {
        return '{"success":false,"error":"' +
            escapeJsonString(e) +
            '"}';
    }
}

function setLayerVisibility(layerName, visible) {
    try {
        if (app.documents.length === 0) {
            return '{"success":false,"error":"No document open"}';
        }

        var layer = app.activeDocument.layers.getByName(layerName);
        layer.visible = visible;

        return '{"success":true,"name":"' +
            escapeJsonString(layer.name) +
            '","visible":' + (layer.visible ? 'true' : 'false') +
            '}';
    } catch (e) {
        return '{"success":false,"error":"' +
            escapeJsonString(e) +
            '"}';
    }
}
