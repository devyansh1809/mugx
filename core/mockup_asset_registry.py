"""Registry for local, licensed Phase 3 mockup assets.

No third-party images are bundled.  This registry discovers assets installed in
assets/mockups and resolves their accompanying JSON metadata.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class MockupAssetRecord:
    product_id: str
    view_id: str
    image_path: Path
    metadata_path: Path
    metadata: Dict[str, Any]

    @property
    def is_installed(self) -> bool:
        return self.image_path.is_file() and self.metadata_path.is_file()


class MockupAssetRegistry:
    def __init__(self, asset_dir: Optional[str] = None):
        root = Path(asset_dir) if asset_dir else Path(__file__).resolve().parent.parent / "assets" / "mockups"
        self.asset_dir = root
        self.manifest_path = self.asset_dir / "manifest.json"
        self._manifest = self._read_manifest()

    def _read_manifest(self) -> Dict[str, Any]:
        if not self.manifest_path.is_file():
            return {"version": 1, "assets": []}
        try:
            with self.manifest_path.open(encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return {"version": 1, "assets": []}
        return payload if isinstance(payload, dict) else {"version": 1, "assets": []}

    def declared_views(self, product_id: str) -> List[str]:
        return [str(item.get("view_id", "")) for item in self._manifest.get("assets", [])
                if isinstance(item, dict) and item.get("product_id") == product_id and item.get("view_id")]

    def record(self, product_id: str, view_id: str) -> Optional[MockupAssetRecord]:
        entry = next((item for item in self._manifest.get("assets", [])
                      if isinstance(item, dict) and item.get("product_id") == product_id
                      and item.get("view_id") == view_id), None)
        if not entry:
            return None
        image_path = self.asset_dir / str(entry.get("image", ""))
        metadata_path = self.asset_dir / str(entry.get("metadata", ""))
        metadata: Dict[str, Any] = {}
        if metadata_path.is_file():
            try:
                with metadata_path.open(encoding="utf-8") as handle:
                    loaded = json.load(handle)
                if isinstance(loaded, dict):
                    metadata = loaded
            except (OSError, json.JSONDecodeError):
                metadata = {}
        return MockupAssetRecord(product_id, view_id, image_path, metadata_path, metadata)

    def installed_views(self, product_id: str) -> List[str]:
        result = []
        for view_id in self.declared_views(product_id):
            record = self.record(product_id, view_id)
            if record and record.is_installed and record.metadata:
                result.append(view_id)
        return result

    def validate_record(self, record: MockupAssetRecord) -> List[str]:
        errors: List[str] = []
        if not record.metadata_path.is_file():
            errors.append("metadata JSON is missing")
        if not record.image_path.is_file():
            errors.append("base image is missing")
        data = record.metadata
        if not data and record.metadata_path.is_file():
            errors.append("metadata JSON is invalid")
            return errors
        required = ("width_px", "height_px", "print_region")
        for key in required:
            if key not in data:
                errors.append(f"metadata field '{key}' is missing")
        region = data.get("print_region")
        if isinstance(region, dict):
            mode = region.get("mode", "rectangle")
            if mode not in {"rectangle", "polygon"}:
                errors.append("print_region.mode must be rectangle or polygon")
            if mode == "rectangle":
                for key in ("x", "y", "width", "height"):
                    if not isinstance(region.get(key), (int, float)):
                        errors.append(f"print_region.{key} must be numeric")
            if mode == "polygon":
                points = region.get("points")
                if not isinstance(points, list) or len(points) < 3:
                    errors.append("polygon print region needs at least three points")
        elif data:
            errors.append("print_region must be an object")
        return errors

    def all_records(self) -> Iterable[MockupAssetRecord]:
        for entry in self._manifest.get("assets", []):
            if isinstance(entry, dict) and entry.get("product_id") and entry.get("view_id"):
                record = self.record(str(entry["product_id"]), str(entry["view_id"]))
                if record:
                    yield record
