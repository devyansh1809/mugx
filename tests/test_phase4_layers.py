"""
Phase 4: Layer Editor - Test Suite
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.layer_models import Document, PhotoLayer, TextLayer, BackgroundLayer, ClipArtLayer, OverlayLayer, LayerTransform, LayerProperties, create_photo_layer, create_text_layer, create_background_layer
from core.layer_engine import LayerEngine


class TestLayerModels:
    def test_create_photo_layer(self):
        layer = create_photo_layer("/path/to/photo.jpg", x=100, y=50, scale=1.5)
        assert layer.type == "photo"
        assert layer.image_path == "/path/to/photo.jpg"
        assert layer.transform.x == 100
        assert layer.transform.y == 50
        assert layer.transform.scale == 1.5
        assert layer.properties.visible == True
    
    def test_create_text_layer(self):
        layer = create_text_layer("Hello World", x=200, y=100, font_size=36, color="#FF0000")
        assert layer.type == "text"
        assert layer.text == "Hello World"
        assert layer.font_size == 36
        assert layer.color == "#FF0000"
        assert layer.transform.x == 200
    
    def test_create_background_layer(self):
        layer = create_background_layer(color="#0000FF")
        assert layer.type == "background"
        assert layer.color == "#0000FF"
    
    def test_layer_transform(self):
        transform = LayerTransform(x=50, y=75, scale=2.0, rotation=45)
        data = transform.to_dict()
        assert data["x"] == 50 and data["y"] == 75 and data["scale"] == 2.0 and data["rotation"] == 45
        restored = LayerTransform.from_dict(data)
        assert restored.x == 50 and restored.rotation == 45
    
    def test_document_add_layer(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        photo = create_photo_layer("/photo.jpg")
        text = create_text_layer("Test")
        doc.add_layer(photo)
        doc.add_layer(text)
        assert len(doc.layers) == 2
        assert doc.active_layer_id == text.id
    
    def test_document_remove_layer(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        photo = create_photo_layer("/photo.jpg")
        doc.add_layer(photo)
        removed = doc.remove_layer(photo.id)
        assert removed is not None
        assert len(doc.layers) == 0
        assert doc.active_layer_id is None
    
    def test_document_move_layer(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        layer1 = create_photo_layer("/1.jpg")
        layer2 = create_text_layer("Text")
        layer3 = create_photo_layer("/2.jpg")
        doc.add_layer(layer1)
        doc.add_layer(layer2)
        doc.add_layer(layer3)
        doc.move_layer(layer1.id, 2)
        assert doc.layers[2].id == layer1.id
    
    def test_document_serialization(self):
        doc = Document(canvas_width=800, canvas_height=600, name="Test Doc")
        doc.add_layer(create_photo_layer("/test.jpg", x=50, y=50))
        doc.add_layer(create_text_layer("Hello", x=100, y=100))
        data = doc.to_dict()
        restored = Document.from_dict(data)
        assert restored.canvas_width == 800 and restored.canvas_height == 600 and restored.name == "Test Doc"
        assert len(restored.layers) == 2
        assert restored.layers[0].type == "photo" and restored.layers[1].type == "text"


class TestLayerEngine:
    def test_engine_add_layer(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        engine = LayerEngine(doc)
        layer = create_photo_layer("/test.jpg")
        engine.add_layer(layer)
        assert len(doc.layers) == 1 and engine.can_undo() == True
    
    def test_engine_undo_add(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        engine = LayerEngine(doc)
        layer = create_photo_layer("/test.jpg")
        engine.add_layer(layer)
        engine.undo()
        assert len(doc.layers) == 0 and engine.can_undo() == False and engine.can_redo() == True
    
    def test_engine_redo(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        engine = LayerEngine(doc)
        layer = create_photo_layer("/test.jpg")
        engine.add_layer(layer)
        engine.undo()
        engine.redo()
        assert len(doc.layers) == 1
    
    def test_engine_move_layer(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        engine = LayerEngine(doc)
        layer = create_photo_layer("/test.jpg", x=0, y=0)
        engine.add_layer(layer)
        engine.move_layer(layer.id, 50, 100)
        assert layer.transform.x == 50 and layer.transform.y == 100
    
    def test_engine_undo_move(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        engine = LayerEngine(doc)
        layer = create_photo_layer("/test.jpg", x=0, y=0)
        engine.add_layer(layer)
        engine.move_layer(layer.id, 50, 100)
        engine.undo()
        assert layer.transform.x == 0 and layer.transform.y == 0
    
    def test_engine_scale_layer(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        engine = LayerEngine(doc)
        layer = create_photo_layer("/test.jpg", scale=1.0)
        engine.add_layer(layer)
        engine.scale_layer(layer.id, 1.5)
        assert layer.transform.scale == 1.5
    
    def test_engine_rotate_layer(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        engine = LayerEngine(doc)
        layer = create_photo_layer("/test.jpg")
        engine.add_layer(layer)
        engine.rotate_layer(layer.id, 45)
        assert layer.transform.rotation == 45
    
    def test_engine_bring_to_front(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        engine = LayerEngine(doc)
        layer1 = create_photo_layer("/1.jpg")
        layer2 = create_photo_layer("/2.jpg")
        engine.add_layer(layer1)
        engine.add_layer(layer2)
        engine.bring_to_front(layer1.id)
        assert doc.layers[-1].id == layer1.id
    
    def test_engine_send_to_back(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        engine = LayerEngine(doc)
        layer1 = create_photo_layer("/1.jpg")
        layer2 = create_photo_layer("/2.jpg")
        engine.add_layer(layer1)
        engine.add_layer(layer2)
        engine.send_to_back(layer2.id)
        assert doc.layers[0].id == layer2.id
    
    def test_engine_duplicate_layer(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        engine = LayerEngine(doc)
        layer = create_photo_layer("/test.jpg", x=100, y=100)
        engine.add_layer(layer)
        new_layer = engine.duplicate_layer(layer.id)
        assert new_layer is not None and new_layer.id != layer.id
        assert new_layer.image_path == layer.image_path and len(doc.layers) == 2
    
    def test_engine_set_visibility(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        engine = LayerEngine(doc)
        layer = create_photo_layer("/test.jpg")
        engine.add_layer(layer)
        engine.set_layer_visibility(layer.id, False)
        assert layer.properties.visible == False and engine.can_undo() == True
    
    def test_engine_set_opacity(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        engine = LayerEngine(doc)
        layer = create_photo_layer("/test.jpg")
        engine.add_layer(layer)
        engine.set_layer_opacity(layer.id, 0.5)
        assert layer.properties.opacity == 0.5
    
    def test_engine_clear_history(self):
        doc = Document(canvas_width=1000, canvas_height=1000)
        engine = LayerEngine(doc)
        layer = create_photo_layer("/test.jpg")
        engine.add_layer(layer)
        engine.move_layer(layer.id, 10, 10)
        assert engine.can_undo() == True
        engine.clear_history()
        assert engine.can_undo() == False and engine.can_redo() == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
