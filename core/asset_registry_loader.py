"""
Asset Registry Loader — Phase 2B

Loads and validates JSON registry files for:
- Templates
- Product profiles
- Assets (backgrounds, effects, clipart, etc.)
- Mobile phone models

Provides scanning, filtering, and search capabilities for the asset workspace.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class AssetRegistryLoader:
    """Main loader for all asset registry files."""
    
    def __init__(self, assets_root: str):
        """
        Initialize asset registry loader.
        
        Args:
            assets_root: Root path to SubliStudioAssets directory
        """
        self.assets_root = Path(assets_root)
        self.registry_dir = self.assets_root / "registry"
        
        # Registry file paths
        self.templates_file = self.registry_dir / "templates.json"
        self.products_file = self.registry_dir / "product-profiles.json"
        self.assets_file = self.registry_dir / "assets.json"
        self.mobile_models_file = self.registry_dir / "mobile-models.json"
        
        # Schema file paths
        self.schemas_dir = self.registry_dir
        
        # Cached data
        self._templates = None
        self._products = None
        self._assets = None
        self._mobile_models = None
    
    def load_json(self, file_path: Path) -> Optional[Dict]:
        """
        Load and parse a JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Parsed JSON data or None if file doesn't exist
        """
        if not file_path.exists():
            print(f"⚠️  Registry file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Count entries
            entry_count = 0
            if 'templates' in data:
                entry_count = len(data['templates'])
            elif 'products' in data:
                entry_count = len(data['products'])
            elif 'assets' in data:
                entry_count = len(data['assets'])
            elif 'models' in data:
                entry_count = len(data['models'])
            
            print(f"✅ Loaded: {file_path.name} ({entry_count} entries)")
            return data
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error in {file_path}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error loading {file_path}: {e}")
            return None
    
    def load_all_registries(self) -> Dict[str, bool]:
        """
        Load all registry files.
        
        Returns:
            Dictionary of registry name -> load success status
        """
        results = {}
        
        print(f"\n📂 Loading asset registries from: {self.assets_root}")
        print("=" * 60)
        
        # Load templates
        templates_data = self.load_json(self.templates_file)
        self._templates = templates_data
        results['templates'] = templates_data is not None
        
        # Load products
        products_data = self.load_json(self.products_file)
        self._products = products_data
        results['products'] = products_data is not None
        
        # Load assets
        assets_data = self.load_json(self.assets_file)
        self._assets = assets_data
        results['assets'] = assets_data is not None
        
        # Load mobile models
        mobile_data = self.load_json(self.mobile_models_file)
        self._mobile_models = mobile_data
        results['mobile_models'] = mobile_data is not None
        
        print("=" * 60)
        success_count = sum(results.values())
        print(f"✅ Loaded {success_count}/{len(results)} registries successfully\n")
        
        return results
    
    # ============ TEMPLATES ============
    
    def get_templates(self) -> List[Dict]:
        """Get all templates."""
        if self._templates is None:
            self.load_json(self.templates_file)
        return self._templates.get('templates', []) if self._templates else []
    
    def get_templates_by_category(self, category: str) -> List[Dict]:
        """Get templates filtered by product category."""
        all_templates = self.get_templates()
        return [t for t in all_templates if t.get('productCategory') == category]
    
    def get_templates_by_frame_count(self, category: str, frame_count: int) -> List[Dict]:
        """Get templates filtered by category and frame count."""
        templates = self.get_templates_by_category(category)
        return [t for t in templates if t.get('frameCount') == frame_count]
    
    def search_templates(self, query: str) -> List[Dict]:
        """Search templates by name, description, or tags."""
        all_templates = self.get_templates()
        query_lower = query.lower()
        
        results = []
        for template in all_templates:
            if query_lower in template.get('name', '').lower():
                results.append(template)
                continue
            if query_lower in template.get('description', '').lower():
                results.append(template)
                continue
            tags = template.get('tags', [])
            if any(query_lower in tag.lower() for tag in tags):
                results.append(template)
                continue
            if query_lower in template.get('theme', '').lower():
                results.append(template)
                continue
            if query_lower in template.get('occasion', '').lower():
                results.append(template)
                continue
        
        return results
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict]:
        """Get a specific template by ID."""
        all_templates = self.get_templates()
        for template in all_templates:
            if template.get('id') == template_id:
                return template
        return None
    
    # ============ PRODUCTS ============
    
    def get_products(self) -> List[Dict]:
        """Get all product profiles."""
        if self._products is None:
            self.load_json(self.products_file)
        return self._products.get('products', []) if self._products else []
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """Get products filtered by category."""
        all_products = self.get_products()
        return [p for p in all_products if p.get('category') == category]
    
    def get_active_products(self) -> List[Dict]:
        """Get only active (available) products."""
        all_products = self.get_products()
        return [p for p in all_products if p.get('isActive', True)]
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Get a specific product by ID."""
        all_products = self.get_products()
        for product in all_products:
            if product.get('id') == product_id:
                return product
        return None
    
    def search_products(self, query: str) -> List[Dict]:
        """Search products by name, description, or tags."""
        all_products = self.get_products()
        query_lower = query.lower()
        
        results = []
        for product in all_products:
            if query_lower in product.get('name', '').lower():
                results.append(product)
                continue
            if query_lower in product.get('description', '').lower():
                results.append(product)
                continue
            tags = product.get('tags', [])
            if any(query_lower in tag.lower() for tag in tags):
                results.append(product)
                continue
            if query_lower in product.get('category', '').lower():
                results.append(product)
                continue
            if query_lower in product.get('subcategory', '').lower():
                results.append(product)
                continue
        
        return results
    
    # ============ ASSETS ============
    
    def get_assets(self) -> List[Dict]:
        """Get all assets."""
        if self._assets is None:
            self.load_json(self.assets_file)
        return self._assets.get('assets', []) if self._assets else []
    
    def get_assets_by_category(self, category: str) -> List[Dict]:
        """Get assets filtered by category."""
        all_assets = self.get_assets()
        return [a for a in all_assets if a.get('category') == category]
    
    def get_assets_by_subcategory(self, category: str, subcategory: str) -> List[Dict]:
        """Get assets filtered by category and subcategory."""
        assets = self.get_assets_by_category(category)
        return [a for a in assets if a.get('subcategory') == subcategory]
    
    def search_assets(self, query: str) -> List[Dict]:
        """Search assets by name, description, tags, or theme."""
        all_assets = self.get_assets()
        query_lower = query.lower()
        
        results = []
        for asset in all_assets:
            if query_lower in asset.get('name', '').lower():
                results.append(asset)
                continue
            if query_lower in asset.get('description', '').lower():
                results.append(asset)
                continue
            tags = asset.get('tags', [])
            if any(query_lower in tag.lower() for tag in tags):
                results.append(asset)
                continue
            if query_lower in asset.get('theme', '').lower():
                results.append(asset)
                continue
            if query_lower in asset.get('occasion', '').lower():
                results.append(asset)
                continue
        
        return results
    
    def get_asset_by_id(self, asset_id: str) -> Optional[Dict]:
        """Get a specific asset by ID."""
        all_assets = self.get_assets()
        for asset in all_assets:
            if asset.get('id') == asset_id:
                return asset
        return None
    
    # ============ MOBILE MODELS ============
    
    def get_mobile_models(self) -> List[Dict]:
        """Get all mobile phone models."""
        if self._mobile_models is None:
            self.load_json(self.mobile_models_file)
        return self._mobile_models.get('models', []) if self._mobile_models else []
    
    def get_mobile_models_by_brand(self, brand: str) -> List[Dict]:
        """Get mobile models filtered by brand."""
        all_models = self.get_mobile_models()
        return [m for m in all_models if m.get('brand') == brand]
    
    def get_active_mobile_models(self) -> List[Dict]:
        """Get only active mobile models."""
        all_models = self.get_mobile_models()
        return [m for m in all_models if m.get('isActive', True)]
    
    def get_popular_mobile_models(self) -> List[Dict]:
        """Get popular/high-demand mobile models."""
        all_models = self.get_mobile_models()
        return [m for m in all_models if m.get('isPopular', False)]
    
    def get_mobile_model_by_id(self, model_id: str) -> Optional[Dict]:
        """Get a specific mobile model by ID."""
        all_models = self.get_mobile_models()
        for model in all_models:
            if model.get('id') == model_id:
                return model
        return None
    
    def search_mobile_models(self, query: str) -> List[Dict]:
        """Search mobile models by name, brand, or tags."""
        all_models = self.get_mobile_models()
        query_lower = query.lower()
        
        results = []
        for model in all_models:
            if query_lower in model.get('modelName', '').lower():
                results.append(model)
                continue
            if query_lower in model.get('brand', '').lower():
                results.append(model)
                continue
            tags = model.get('tags', [])
            if any(query_lower in tag.lower() for tag in tags):
                results.append(model)
                continue
        
        return results
    
    # ============ DIRECTORY SCANNING ============
    
    def scan_directory_structure(self) -> Dict[str, Any]:
        """
        Scan the asset directory structure and report what exists.
        
        Returns:
            Dictionary with directory structure report
        """
        report = {
            'assets_root': str(self.assets_root),
            'exists': self.assets_root.exists(),
            'directories': {},
            'files': {},
            'missing': []
        }
        
        if not self.assets_root.exists():
            report['error'] = f"Assets root directory does not exist: {self.assets_root}"
            return report
        
        # Expected directories
        expected_dirs = [
            'customer_photos/sublimation',
            'customer_photos/mobile',
            'customer_photos/mosaic',
            'customer_photos/caricature',
            'templates/mugs/1-photo',
            'templates/mugs/2-photo',
            'templates/mugs/3-photo',
            'templates/mugs/4-photo',
            'templates/mugs/5-photo',
            'templates/mugs/6-photo',
            'templates/mugs/collage',
            'templates/bottles',
            'templates/tshirts',
            'templates/cushions',
            'templates/tiles',
            'templates/keyrings',
            'templates/mobile',
            'backgrounds',
            'effects/bokeh',
            'effects/light-leaks',
            'effects/glow',
            'clipart',
            'text-presets',
            'mockups',
            'exports/psd',
            'exports/png',
            'exports/jpg',
            'exports/print',
            'registry'
        ]
        
        for dir_path in expected_dirs:
            full_path = self.assets_root / dir_path
            if full_path.exists() and full_path.is_dir():
                report['directories'][dir_path] = {
                    'exists': True,
                    'path': str(full_path),
                    'file_count': len(list(full_path.iterdir()))
                }
            else:
                report['missing'].append(dir_path)
        
        registry_files = [
            'templates.json',
            'product-profiles.json',
            'assets.json',
            'mobile-models.json'
        ]
        
        for file_name in registry_files:
            full_path = self.registry_dir / file_name
            if full_path.exists():
                report['files'][file_name] = {
                    'exists': True,
                    'path': str(full_path),
                    'size_bytes': full_path.stat().st_size
                }
            else:
                report['missing'].append(f'registry/{file_name}')
        
        return report
    
    def _extract_frame_count(self, folder_name: str) -> int:
        """Extract frame count from folder name (e.g., '2-photo' -> 2)."""
        import re
        match = re.search(r'(\d+)', folder_name)
        if match:
            return int(match.group(1))
        return 1
    
    # ============ VALIDATION ============
    
    def validate_templates_schema(self) -> bool:
        """Validate templates.json against schema."""
        return self._validate_schema(self.templates_file, 'templates_schema.json')
    
    def validate_products_schema(self) -> bool:
        """Validate product-profiles.json against schema."""
        return self._validate_schema(self.products_file, 'product_profiles_schema.json')
    
    def validate_assets_schema(self) -> bool:
        """Validate assets.json against schema."""
        return self._validate_schema(self.assets_file, 'assets_schema.json')
    
    def validate_mobile_models_schema(self) -> bool:
        """Validate mobile-models.json against schema."""
        return self._validate_schema(self.mobile_models_file, 'mobile_models_schema.json')
    
    def _validate_schema(self, data_file: Path, schema_file: str) -> bool:
        """Validate a JSON file against its schema."""
        if not data_file.exists():
            print(f"⚠️  File not found: {data_file}")
            return False
        
        schema_path = self.schemas_dir / schema_file
        if not schema_path.exists():
            print(f"⚠️  Schema not found: {schema_path}")
            return False
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            from jsonschema import validate, ValidationError
            validate(instance=data, schema=schema)
            print(f"✅ Validated: {data_file.name} against {schema_file}")
            return True
            
        except ImportError:
            print(f"⚠️  jsonschema not installed. Run: pip3 install jsonschema")
            return True
        except Exception as e:
            print(f"❌ Validation error in {data_file.name}: {e}")
            return False


if __name__ == '__main__':
    assets_root = Path.home() / 'SubliStudioAssets'
    loader = AssetRegistryLoader(assets_root)
    results = loader.load_all_registries()
    
    templates = loader.get_templates()
    print(f"\n📄 Found {len(templates)} templates")
    
    mug_templates = loader.get_templates_by_category('mugs')
    print(f"📄 Found {len(mug_templates)} mug templates")
    
    mug_2photo = loader.get_templates_by_frame_count('mugs', 2)
    print(f"📄 Found {len(mug_2photo)} 2-photo mug templates")
    
    birthday_templates = loader.search_templates('birthday')
    print(f"📄 Found {len(birthday_templates)} birthday templates")
    
    products = loader.get_products()
    print(f"\n🛍️  Found {len(products)} products")
    
    active_products = loader.get_active_products()
    print(f"🛍️  Found {len(active_products)} active products")
    
    assets = loader.get_assets()
    print(f"\n🎨 Found {len(assets)} assets")
    
    mobile_models = loader.get_mobile_models()
    print(f"\n📱 Found {len(mobile_models)} mobile models")
    
    scan_report = loader.scan_directory_structure()
    print(f"\n📂 Directory scan:")
    print(f"   Assets root exists: {scan_report['exists']}")
    print(f"   Directories found: {len(scan_report['directories'])}")
    print(f"   Missing directories: {len(scan_report['missing'])}")
