/* global $, File, Folder, app, Document, Layer, SmartObject, UnitValue */

(function () {
  'use strict';

  // Resolve extension root (folder containing index.jsx)
  var extensionRoot = (function () {
    var scriptPath = $.fileName;
    var f = new File(scriptPath);
    return f.parent.parent; // host/ -> cep_plugin/
  })();

  // ---------- JSON helpers ----------

  function readJSON(relativePath) {
    var fullPath = new File(extensionRoot + '/' + relativePath);
    if (!fullPath.exists) {
      throw new Error('JSON file not found: ' + fullPath.fsName);
    }
    fullPath.open('r');
    var content = fullPath.read();
    fullPath.close();
    return JSON.parse(content);
  }

  var _catalog = null;
  var _registry = null;

  function ensureCatalog() {
    if (!_catalog) {
      _catalog = readJSON('assets/products/catalog.json');
    }
    return _catalog;
  }

  function ensureRegistry() {
    if (!_registry) {
      _registry = readJSON('assets/templates/registry.json');
    }
    return _registry;
  }

  // ---------- Public API ----------

  var MugXHost = {};

  MugXHost.getProducts = function () {
    var catalog = ensureCatalog();
    return catalog.products;
  };

  MugXHost.getProduct = function (productId) {
    var catalog = ensureCatalog();
    for (var i = 0; i < catalog.products.length; i++) {
      var p = catalog.products[i];
      if (p.id === productId) {
        return p;
      }
    }
    return null;
  };

  MugXHost.getTemplates = function (productId, occasion, frameCount) {
    var registry = ensureRegistry();
    var result = [];
    for (var i = 0; i < registry.templates.length; i++) {
      var t = registry.templates[i];
      if (t.product !== productId) {
        continue;
      }
      if (frameCount !== undefined && t.frame_count !== frameCount) {
        continue;
      }
      if (occasion) {
        var hasOccasion = false;
        for (var j = 0; j < t.occasions.length; j++) {
          if (t.occasions[j] === occasion) {
            hasOccasion = true;
            break;
          }
        }
        if (!hasOccasion) {
          continue;
        }
      }
      result.push(t);
    }
    return result;
  };

  // ---------- Existing Photoshop bridge functions ----------

  MugXHost.pingPhotoshop = function () {
    return {
      name: app.name,
      version: app.version,
      language: app.language
    };
  };

  MugXHost.getPhotoshopInfo = function () {
    return {
      name: app.name,
      version: app.version,
      language: app.language,
      build: app.buildNumber
    };
  };

  MugXHost.getDocumentInfo = function () {
    if (!app.documents.length) {
      return null;
    }
    var doc = app.activeDocument;
    return {
      name: doc.name,
      width: doc.width.as('px'),
      height: doc.height.as('px'),
      resolution: doc.resolution.as('px/in'),
      mode: doc.mode.toString(),
      layerCount: doc.layers.length
    };
  };

  MugXHost.getLayerList = function () {
    if (!app.documents.length) {
      return [];
    }
    var doc = app.activeDocument;
    var layers = [];
    for (var i = 0; i < doc.layers.length; i++) {
      var l = doc.layers[i];
      layers.push({
        name: l.name,
        kind: l.kind.toString(),
        visible: l.visible,
        opacity: l.opacity,
        isBackgroundLayer: l.isBackgroundLayer,
        locked: l.allLocked || l.positionLocked
      });
    }
    return layers;
  };

  MugXHost.addTestLayer = function () {
    if (!app.documents.length) {
      return { error: 'No active document' };
    }
    var doc = app.activeDocument;
    var layer = doc.artLayers.add();
    layer.name = 'test_layer_' + new Date().getTime();
    return {
      name: layer.name,
      id: layer.id
    };
  };

  MugXHost.getLayerBounds = function (layerName) {
    if (!app.documents.length) {
      return null;
    }
    var doc = app.activeDocument;
    var layer = null;
    for (var i = 0; i < doc.layers.length; i++) {
      if (doc.layers[i].name === layerName) {
        layer = doc.layers[i];
        break;
      }
    }
    if (!layer) {
      return null;
    }
    var bounds = layer.bounds;
    return {
      left: bounds[0].as('px'),
      top: bounds[1].as('px'),
      right: bounds[2].as('px'),
      bottom: bounds[3].as('px')
    };
  };

  MugXHost.duplicateLayer = function (layerName) {
    if (!app.documents.length) {
      return { error: 'No active document' };
    }
    var doc = app.activeDocument;
    var layer = null;
    for (var i = 0; i < doc.layers.length; i++) {
      if (doc.layers[i].name === layerName) {
        layer = doc.layers[i];
        break;
      }
    }
    if (!layer) {
      return { error: 'Layer not found: ' + layerName };
    }
    var newLayer = layer.duplicate();
    newLayer.name = layerName + '_copy_' + new Date().getTime();
    return {
      name: newLayer.name,
      id: newLayer.id
    };
  };

  MugXHost.createTestRectangle = function () {
    if (!app.documents.length) {
      return { error: 'No active document' };
    }
    var doc = app.activeDocument;
    var layer = doc.artLayers.add();
    layer.name = 'test_rect_' + new Date().getTime();
    return {
      layer: layer.name
    };
  };

  MugXHost.moveLayer = function (layerName, dx, dy) {
    if (!app.documents.length) {
      return { error: 'No active document' };
    }
    var doc = app.activeDocument;
    var layer = null;
    for (var i = 0; i < doc.layers.length; i++) {
      if (doc.layers[i].name === layerName) {
        layer = doc.layers[i];
        break;
      }
    }
    if (!layer) {
      return { error: 'Layer not found: ' + layerName };
    }
    layer.translate(dx, dy);
    return {
      name: layer.name,
      movedBy: { x: dx, y: dy }
    };
  };

  MugXHost.setLayerOpacity = function (layerName, opacity) {
    if (!app.documents.length) {
      return { error: 'No active document' };
    }
    var doc = app.activeDocument;
    var layer = null;
    for (var i = 0; i < doc.layers.length; i++) {
      if (doc.layers[i].name === layerName) {
        layer = doc.layers[i];
        break;
      }
    }
    if (!layer) {
      return { error: 'Layer not found: ' + layerName };
    }
    layer.opacity = opacity;
    return {
      name: layer.name,
      opacity: layer.opacity
    };
  };

  MugXHost.setLayerVisibility = function (layerName, visible) {
    if (!app.documents.length) {
      return { error: 'No active document' };
    }
    var doc = app.activeDocument;
    var layer = null;
    for (var i = 0; i < doc.layers.length; i++) {
      if (doc.layers[i].name === layerName) {
        layer = doc.layers[i];
        break;
      }
    }
    if (!layer) {
      return { error: 'Layer not found: ' + layerName };
    }
    layer.visible = !!visible;
    return {
      name: layer.name,
      visible: layer.visible
    };
  };

  // Expose globally
  this.MugXHost = MugXHost;
}).call(this);
