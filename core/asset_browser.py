"""
Phase 5: Asset Library - Asset Browser Engine
"""

import os
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class AssetType(Enum):
    CLIP_ART = "clip_art"
    BACKGROUND = "background"
    PATTERN = "pattern"
    TEXT_PRESET = "text_preset"
    EFFECT = "effect"
    COLLAGE_THEME = "collage_theme"


@dataclass
class Asset:
    id: str
    name: str
    type: AssetType
    path: str
    category: str
    tags: List[str] = field(default_factory=list)
    thumbnail_path: Optional[str] = None
    is_favorite: bool = False
    usage_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "type": self.type.value, "path": self.path, "category": self.category, "tags": self.tags, "thumbnail_path": self.thumbnail_path, "is_favorite": self.is_favorite, "usage_count": self.usage_count, "metadata": self.metadata}
    
    @classmethod
    def from_dict(cls, data: dict) -> "Asset":
        return cls(id=data.get("id", ""), name=data.get("name", ""), type=AssetType(data.get("type", "clip_art")), path=data.get("path", ""), category=data.get("category", ""), tags=data.get("tags", []), thumbnail_path=data.get("thumbnail_path"), is_favorite=data.get("is_favorite", False), usage_count=data.get("usage_count", 0), metadata=data.get("metadata", {}))


class AssetBrowser:
    def __init__(self, assets_root: str):
        self.assets_root = Path(assets_root)
        self.assets: Dict[str, Asset] = {}
        self.categories: Dict[str, List[str]] = {}
        self.recent_assets: List[str] = []
        self.max_recent = 20
        self._index_assets()
    
    def _index_assets(self) -> None:
        type_dirs = {AssetType.CLIP_ART: "clip_art", AssetType.BACKGROUND: "backgrounds", AssetType.PATTERN: "patterns", AssetType.TEXT_PRESET: "text_presets", AssetType.EFFECT: "effects", AssetType.COLLAGE_THEME: "collage_themes"}
        for asset_type, dir_name in type_dirs.items():
            type_path = self.assets_root / dir_name
            if type_path.exists(): self._index_asset_type(type_path, asset_type)
    
    def _index_asset_type(self, path: Path, asset_type: AssetType) -> None:
        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".svg", ".json", ".txt"]:
                if "thumb" in file_path.name or file_path.name.startswith("."): continue
                asset_id = f"{asset_type.value}_{file_path.stem}"
                category = file_path.parent.name if file_path.parent != path else "uncategorized"
                metadata = {}
                json_path = file_path.with_suffix(".json")
                if json_path.exists():
                    try:
                        with open(json_path, "r") as f: metadata = json.load(f)
                    except: pass
                asset = Asset(id=asset_id, name=file_path.stem.replace("_", " ").title(), type=asset_type, path=str(file_path), category=category, tags=metadata.get("tags", []), thumbnail_path=str(file_path.with_name(f"thumb_{file_path.name}")) if file_path.with_name(f"thumb_{file_path.name}").exists() else None, metadata=metadata)
                self.assets[asset_id] = asset
                if category not in self.categories: self.categories[category] = []
                if asset_id not in self.categories[category]: self.categories[category].append(asset_id)
    
    def get_assets(self, asset_type: Optional[AssetType] = None, category: Optional[str] = None) -> List[Asset]:
        assets = list(self.assets.values())
        if asset_type: assets = [a for a in assets if a.type == asset_type]
        if category: assets = [a for a in assets if a.category == category]
        return assets
    
    def search_assets(self, query: str, asset_type: Optional[AssetType] = None) -> List[Asset]:
        query = query.lower()
        results = []
        for asset in self.assets.values():
            if asset_type and asset.type != asset_type: continue
            if query in asset.name.lower() or query in asset.category.lower() or any(query in tag.lower() for tag in asset.tags): results.append(asset)
        return results
    
    def get_categories(self, asset_type: Optional[AssetType] = None) -> List[str]:
        if asset_type:
            categories = set()
            for asset in self.assets.values():
                if asset.type == asset_type: categories.add(asset.category)
            return sorted(list(categories))
        return sorted(list(self.categories.keys()))
    
    def get_asset(self, asset_id: str) -> Optional[Asset]: return self.assets.get(asset_id)
    
    def toggle_favorite(self, asset_id: str) -> bool:
        asset = self.assets.get(asset_id)
        if not asset: return False
        asset.is_favorite = not asset.is_favorite
        return True
    
    def get_favorites(self, asset_type: Optional[AssetType] = None) -> List[Asset]:
        favorites = [a for a in self.assets.values() if a.is_favorite]
        if asset_type: favorites = [a for a in favorites if a.type == asset_type]
        return favorites
    
    def add_to_recent(self, asset_id: str) -> None:
        if asset_id in self.recent_assets: self.recent_assets.remove(asset_id)
        self.recent_assets.insert(0, asset_id)
        if len(self.recent_assets) > self.max_recent: self.recent_assets.pop()
    
    def get_recent(self, limit: int = 10) -> List[Asset]:
        recent = []
        for asset_id in self.recent_assets[:limit]:
            asset = self.assets.get(asset_id)
            if asset: recent.append(asset)
        return recent
    
    def increment_usage(self, asset_id: str) -> None:
        if asset_id in self.assets: self.assets[asset_id].usage_count += 1
    
    def get_popular(self, asset_type: Optional[AssetType] = None, limit: int = 10) -> List[Asset]:
        assets = list(self.assets.values())
        if asset_type: assets = [a for a in assets if a.type == asset_type]
        assets.sort(key=lambda a: a.usage_count, reverse=True)
        return assets[:limit]
    
    def get_thumbnails(self, asset_ids: List[str]) -> Dict[str, str]:
        thumbnails = {}
        for asset_id in asset_ids:
            asset = self.assets.get(asset_id)
            if asset: thumbnails[asset_id] = asset.thumbnail_path or asset.path
        return thumbnails
    
    def get_asset_count(self, asset_type: Optional[AssetType] = None) -> int:
        if asset_type: return len([a for a in self.assets.values() if a.type == asset_type])
        return len(self.assets)
    
    def get_all_tags(self, asset_type: Optional[AssetType] = None) -> List[str]:
        tags = set()
        for asset in self.assets.values():
            if asset_type and asset.type != asset_type: continue
            tags.update(asset.tags)
        return sorted(list(tags))
