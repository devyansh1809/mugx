"""
Phase 5: Asset Library - Test Suite
"""

import pytest
import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.layer_models import Document, TextLayer
from core.layer_engine import LayerEngine


class TestAssetBrowser:
    def test_asset_creation(self):
        from core.asset_browser import Asset, AssetType
        asset = Asset(id="test_1", name="Test Asset", type=AssetType.CLIP_ART, path="/path/to/asset.png", category="test", tags=["test", "sample"])
        assert asset.id == "test_1" and asset.name == "Test Asset" and asset.type == AssetType.CLIP_ART and len(asset.tags) == 2
    
    def test_asset_serialization(self):
        from core.asset_browser import Asset, AssetType
        asset = Asset(id="test_2", name="Test", type=AssetType.BACKGROUND, path="/test.png", category="backgrounds", is_favorite=True, usage_count=5)
        data = asset.to_dict()
        restored = Asset.from_dict(data)
        assert restored.id == "test_2" and restored.type == AssetType.BACKGROUND and restored.is_favorite == True and restored.usage_count == 5
    
    def test_asset_browser_search(self):
        from core.asset_browser import AssetBrowser, Asset, AssetType
        with tempfile.TemporaryDirectory() as tmpdir:
            browser = AssetBrowser(tmpdir)
            asset1 = Asset(id="asset_1", name="Red Flower", type=AssetType.CLIP_ART, path="/flower.png", category="nature", tags=["flower", "red", "nature"])
            asset2 = Asset(id="asset_2", name="Blue Sky", type=AssetType.BACKGROUND, path="/sky.png", category="nature", tags=["sky", "blue", "nature"])
            browser.assets["asset_1"] = asset1
            browser.assets["asset_2"] = asset2
            results = browser.search_assets("flower")
            assert len(results) == 1 and results[0].id == "asset_1"
            results = browser.search_assets("nature")
            assert len(results) == 2
    
    def test_asset_browser_favorites(self):
        from core.asset_browser import AssetBrowser, Asset, AssetType
        with tempfile.TemporaryDirectory() as tmpdir:
            browser = AssetBrowser(tmpdir)
            asset = Asset(id="fav_1", name="Test", type=AssetType.CLIP_ART, path="/test.png", category="test")
            browser.assets["fav_1"] = asset
            browser.toggle_favorite("fav_1")
            assert asset.is_favorite == True
            favorites = browser.get_favorites()
            assert len(favorites) == 1
    
    def test_asset_browser_recent(self):
        from core.asset_browser import AssetBrowser, Asset, AssetType
        with tempfile.TemporaryDirectory() as tmpdir:
            browser = AssetBrowser(tmpdir)
            for i in range(5):
                asset = Asset(id=f"recent_{i}", name=f"Asset {i}", type=AssetType.CLIP_ART, path=f"/asset{i}.png", category="test")
                browser.assets[f"recent_{i}"] = asset
                browser.add_to_recent(f"recent_{i}")
            recent = browser.get_recent(3)
            assert len(recent) == 3 and recent[0].id == "recent_4"
    
    def test_asset_browser_popular(self):
        from core.asset_browser import AssetBrowser, Asset, AssetType
        with tempfile.TemporaryDirectory() as tmpdir:
            browser = AssetBrowser(tmpdir)
            asset1 = Asset(id="pop_1", name="Popular 1", type=AssetType.CLIP_ART, path="/1.png", category="test", usage_count=10)
            asset2 = Asset(id="pop_2", name="Popular 2", type=AssetType.CLIP_ART, path="/2.png", category="test", usage_count=50)
            asset3 = Asset(id="pop_3", name="Popular 3", type=AssetType.CLIP_ART, path="/3.png", category="test", usage_count=30)
            browser.assets["pop_1"] = asset1
            browser.assets["pop_2"] = asset2
            browser.assets["pop_3"] = asset3
            popular = browser.get_popular(limit=2)
            assert len(popular) == 2 and popular[0].id == "pop_2" and popular[1].id == "pop_3"


class TestTextPresetManager:
    def test_text_preset_creation(self):
        from core.text_preset_manager import TextPreset
        preset = TextPreset(id="test_preset", name="Test Preset", font_family="Arial", font_size=32.0, font_weight="bold", color="#FF0000", category="custom", tags=["test", "red"])
        assert preset.id == "test_preset" and preset.font_size == 32.0 and preset.color == "#FF0000"
    
    def test_text_preset_serialization(self):
        from core.text_preset_manager import TextPreset
        preset = TextPreset(id="serialize_test", name="Test", font_family="Georgia", font_size=24.0, color="#0000FF", shadow=True, shadow_color="#808080")
        data = preset.to_dict()
        restored = TextPreset.from_dict(data)
        assert restored.id == "serialize_test" and restored.font_family == "Georgia" and restored.shadow == True
    
    def test_preset_manager_builtin(self):
        from core.text_preset_manager import TextPresetManager
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TextPresetManager(tmpdir)
            assert len(manager.presets) > 0
            categories = manager.get_categories()
            assert "basic" in categories or "effects" in categories
    
    def test_preset_manager_search(self):
        from core.text_preset_manager import TextPresetManager
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TextPresetManager(tmpdir)
            results = manager.search_presets("bold")
            assert len(results) > 0


class TestAssetLayerIntegration:
    def test_create_clip_art_layer(self):
        from core.asset_layer_integration import AssetLayerFactory
        from core.asset_browser import Asset, AssetType
        asset = Asset(id="clip_1", name="Test Clip Art", type=AssetType.CLIP_ART, path="/clip.png", category="test")
        doc = Document(canvas_width=1000, canvas_height=1000)
        layer = AssetLayerFactory.create_layer_from_asset(asset, doc, x=50, y=50, scale=1.5)
        assert layer is not None and layer.type == "clip_art" and layer.asset_path == "/clip.png" and layer.transform.x == 50 and layer.transform.y == 50 and layer.transform.scale == 1.5
    
    def test_create_background_layer(self):
        from core.asset_layer_integration import AssetLayerFactory
        from core.asset_browser import Asset, AssetType
        asset = Asset(id="bg_1", name="Test Background", type=AssetType.BACKGROUND, path="/bg.png", category="backgrounds", metadata={"blur_radius": 5.0})
        doc = Document(canvas_width=1000, canvas_height=1000)
        layer = AssetLayerFactory.create_layer_from_asset(asset, doc)
        assert layer is not None and layer.type == "background" and layer.image_path == "/bg.png" and layer.blur_radius == 5.0
    
    def test_apply_text_preset(self):
        from core.asset_layer_integration import AssetLayerFactory
        from core.text_preset_manager import TextPreset
        preset = TextPreset(id="preset_1", name="Bold Red", font_family="Arial Black", font_size=36.0, font_weight="bold", color="#FF0000")
        text_layer = TextLayer(text="Test", font_family="Arial", font_size=24.0, color="#000000")
        AssetLayerFactory.apply_text_preset(text_layer, preset)
        assert text_layer.font_family == "Arial Black" and text_layer.font_size == 36.0 and text_layer.font_weight == "bold" and text_layer.color == "#FF0000"
    
    def test_create_text_from_preset(self):
        from core.asset_layer_integration import AssetLayerFactory
        from core.text_preset_manager import TextPreset
        preset = TextPreset(id="preset_2", name="Elegant", font_family="Georgia", font_size=32.0, font_style="italic", color="#4A4A4A")
        layer = AssetLayerFactory.create_text_layer_from_preset(preset, text="Hello World", x=100, y=200)
        assert layer.type == "text" and layer.text == "Hello World" and layer.font_family == "Georgia" and layer.font_size == 32.0 and layer.font_style == "italic" and layer.transform.x == 100 and layer.transform.y == 200
    
    def test_add_asset_to_document(self):
        from core.asset_layer_integration import add_asset_to_document
        from core.asset_browser import Asset, AssetType
        asset = Asset(id="add_test", name="Test Asset", type=AssetType.CLIP_ART, path="/test.png", category="test")
        doc = Document(canvas_width=1000, canvas_height=1000)
        engine = LayerEngine(doc)
        layer = add_asset_to_document(asset, doc, engine, x=50, y=50)
        assert layer is not None and engine.get_layer_count() == 1 and engine.can_undo() == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
