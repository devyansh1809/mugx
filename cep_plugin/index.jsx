/* global $, File, Folder, app, Document, Layer, SmartObject, UnitValue */

(function () {
  'use strict';

  var extensionRoot = (function () {
    var scriptPath = $.fileName;
    var f = new File(scriptPath);
    return f.parent;
  })();

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

  var MugXHost = {};

  MugXHost.getProducts = function () {
    return ensureCatalog().products;
  };

  MugXHost.getProduct = function (productId) {
    var products = ensureCatalog().products;
    for (var i = 0; i < products.length; i++) {
      if (products[i].id === productId) {
        return products[i];
      }
    }
    return null;
  };

  MugXHost.getTemplates = function (productId, occasion, frameCount) {
    var templates = ensureRegistry().templates;
    var result = [];
    for (var i = 0; i < templates.length; i++) {
      var template = templates[i];
      if (template.product !== productId) {
        continue;
      }
      if (frameCount !== undefined && frameCount !== null && frameCount !== '' && template.frame_count !== Number(frameCount)) {
        continue;
      }
      if (occasion) {
        var hasOccasion = false;
        for (var j = 0; j < template.occasions.length; j++) {
          if (template.occasions[j] === occasion) {
            hasOccasion = true;
            break;
          }
        }
        if (!hasOccasion) {
          continue;
        }
      }
      result.push(template);
    }
    return result;
  };

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
      var layer = doc.layers[i];
      layers.push({
        name: layer.name,
        kind: layer.kind.toString(),
        visible: layer.visible,
        opacity: layer.opacity,
        isBackgroundLayer: layer.isBackgroundLayer,
        locked: layer.allLocked || layer.positionLocked
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
    return { name: layer.name, id: layer.id };
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
    var copy = layer.duplicate();
    copy.name = layerName + '_copy_' + new Date().getTime();
    return { name: copy.name, id: copy.id };
  };

  MugXHost.createTestRectangle = function () {
    if (!app.documents.length) {
      return { error: 'No active document' };
    }
    var doc = app.activeDocument;
    var layer = doc.artLayers.add();
    layer.name = 'test_rect_' + new Date().getTime();
    return { layer: layer.name };
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
    return { name: layer.name, movedBy: { x: dx, y: dy } };
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
    return { name: layer.name, opacity: layer.opacity };
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
    return { name: layer.name, visible: layer.visible };
  };

  this.MugXHost = MugXHost;
}).call(this);
