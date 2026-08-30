from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from .config import MugXConfig

@dataclass
class TemplateMetadata:
    path: str
    product: str  # 'mug', 'bottle', 'collage'
    photo_count: int
    category: str = ''
    name: str = ''

class TemplateManager:
    def __init__(self, config: MugXConfig | None = None):
        self.config = config or MugXConfig.from_env()
        self.template_base = self.config.templates
        self.metadata_file = self.template_base / 'templates.json'

    def get_template_folders(self, product: str = 'mug') -> List[Path]:
        """Get all template folders for a product (e.g., Mug/1 Photo, Mug/2 Photo, etc.)."""
        base = self.template_base / product.capitalize()
        if not base.exists():
            return []
        return [d for d in base.iterdir() if d.is_dir()]

    def get_templates_by_photo_count(self, product: str, photo_count: int) -> List[Path]:
        """Get all templates for a product with specific photo count."""
        folder = self.template_base / product.capitalize() / f"{photo_count} Photo"
        if folder.exists():
            return list(folder.glob('*.psd'))
        return []

    def get_collage_templates(self, category: str = '') -> List[Path]:
        """Get collage templates, optionally filtered by category."""
        base = self.template_base / 'Collage'
        if not base.exists():
            return []
        if category:
            cat_folder = base / category
            return list(cat_folder.glob('*.psd')) if cat_folder.exists() else []
        return list(base.rglob('*.psd'))

    def detect_frame_count(self, psd_path: Path) -> int:
        """Detect frame count from PSD filename or metadata file."""
        # Try to read from metadata file first
        metadata = self._load_metadata()
        if psd_path.as_posix() in metadata:
            return metadata[psd_path.as_posix()].get('photo_count', 0)
        # Fallback: parse from filename (e.g., "Mug_6Photo_Design01.psd" -> 6)
        import re
        match = re.search(r'(\d+)\s*Photo', psd_path.stem, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0

    def get_smart_object_names(self, psd_path: Path) -> List[str]:
        """Get list of smart object layer names from metadata or convention."""
        # In production, this would parse the PSD or read a sidecar JSON
        # For now, use convention: Photo_01, Photo_02, ..., Photo_NN
        count = self.detect_frame_count(psd_path)
        return [f"Photo_{i:02d}" for i in range(1, count + 1)]

    def save_metadata(self, templates: List[TemplateMetadata]) -> None:
        """Save template metadata to JSON file."""
        self.template_base.mkdir(parents=True, exist_ok=True)
        data = {t.path: asdict(t) for t in templates}
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load template metadata from JSON file."""
        if not self.metadata_file.exists():
            return {}
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def scan_templates(self) -> List[TemplateMetadata]:
        """Scan all template folders and build metadata list."""
        metadata = []
        for product in ('mug', 'bottle'):
            for folder in self.get_template_folders(product):
                photo_count = self._parse_photo_count(folder.name)
                for psd in folder.glob('*.psd'):
                    metadata.append(TemplateMetadata(
                        path=psd.as_posix(),
                        product=product,
                        photo_count=photo_count,
                        category=folder.parent.name if folder.parent != self.template_base / product.capitalize() else '',
                        name=psd.stem
                    ))
        # Scan collages
        collage_base = self.template_base / 'Collage'
        if collage_base.exists():
            for folder in collage_base.iterdir():
                if folder.is_dir():
                    for psd in folder.glob('*.psd'):
                        metadata.append(TemplateMetadata(
                            path=psd.as_posix(),
                            product='collage',
                            photo_count=0,  # Collages have variable counts
                            category=folder.name,
                            name=psd.stem
                        ))
        self.save_metadata(metadata)
        return metadata

    def _parse_photo_count(self, folder_name: str) -> int:
        """Parse photo count from folder name (e.g., '1 Photo' -> 1)."""
        import re
        match = re.match(r'(\d+)\s*Photo', folder_name, re.IGNORECASE)
        return int(match.group(1)) if match else 0

    def list_templates(self, product: Optional[str] = None, photo_count: Optional[int] = None) -> List[TemplateMetadata]:
        """List templates with optional filters."""
        metadata = self._load_metadata()
        results = []
        for path, data in metadata.items():
            if product and data.get('product') != product:
                continue
            if photo_count and data.get('photo_count') != photo_count:
                continue
            results.append(TemplateMetadata(**data))
        return results
