"""
Template Browser — Phase 2B

Provides template browsing functionality with:
- Filtering by product category and frame count
- Search by theme, occasion, tags
- Template preview and metadata
- Layer naming contract validation
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from .asset_registry_loader import AssetRegistryLoader


class TemplateBrowser:
    """Template browser with filtering and search capabilities."""
    
    def __init__(self, loader: AssetRegistryLoader):
        """
        Initialize template browser.
        
        Args:
            loader: AssetRegistryLoader instance
        """
        self.loader = loader
        self._templates = []
        self._categories = set()
        self._frame_counts = set()
        self._themes = set()
    
    def load(self) -> int:
        """
        Load templates from registry.
        
        Returns:
            Number of templates loaded
        """
        self._templates = self.loader.get_templates()
        
        # Extract unique categories, frame counts, and themes
        for template in self._templates:
            self._categories.add(template.get('productCategory'))
            self._frame_counts.add(template.get('frameCount'))
            self._themes.add(template.get('theme'))
        
        return len(self._templates)
    
    def get_all_templates(self) -> List[Dict]:
        """Get all templates."""
        return self._templates
    
    def get_categories(self) -> List[str]:
        """Get all template categories."""
        return sorted(list(self._categories))
    
    def get_frame_counts(self) -> List[int]:
        """Get all frame counts."""
        return sorted(list(self._frame_counts))
    
    def get_themes(self) -> List[str]:
        """Get all themes."""
        return sorted(list(self._themes))
    
    def filter_by_category(self, category: str) -> List[Dict]:
        """Filter templates by product category."""
        return [t for t in self._templates if t.get('productCategory') == category]
    
    def filter_by_frame_count(self, frame_count: int) -> List[Dict]:
        """Filter templates by frame count."""
        return [t for t in self._templates if t.get('frameCount') == frame_count]
    
    def filter_by_category_and_frames(self, category: str, frame_count: int) -> List[Dict]:
        """Filter templates by both category and frame count."""
        return [
            t for t in self._templates
            if t.get('productCategory') == category and t.get('frameCount') == frame_count
        ]
    
    def filter_by_theme(self, theme: str) -> List[Dict]:
        """Filter templates by theme."""
        return [t for t in self._templates if t.get('theme') == theme]
    
    def filter_by_occasion(self, occasion: str) -> List[Dict]:
        """Filter templates by occasion."""
        return [t for t in self._templates if t.get('occasion') == occasion]
    
    def filter_premium(self) -> List[Dict]:
        """Get only premium templates."""
        return [t for t in self._templates if t.get('isPremium', False)]
    
    def search(self, query: str) -> List[Dict]:
        """Search templates by name, description, tags, theme, or occasion."""
        return self.loader.search_templates(query)
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get a specific template by ID."""
        return self.loader.get_template_by_id(template_id)
    
    def get_template_tree(self) -> Dict[str, Any]:
        """
        Get template catalog as a hierarchical tree.
        
        Returns:
            Nested dictionary: category -> frame_count -> templates
        """
        tree = {}
        
        for template in self._templates:
            category = template.get('productCategory', 'unknown')
            frame_count = template.get('frameCount', 0)
            
            if category not in tree:
                tree[category] = {}
            
            if frame_count not in tree[category]:
                tree[category][frame_count] = []
            
            tree[category][frame_count].append(template)
        
        return tree
    
    def get_layer_contract(self, template_id: str) -> Optional[Dict]:
        """
        Get layer naming contract for a template.
        
        Args:
            template_id: Template ID
            
        Returns:
            Layer naming contract or None
        """
        template = self.get_template(template_id)
        if not template:
            return None
        
        return template.get('layerNamingContract')
    
    def validate_layer_names(self, template_id: str, actual_layers: List[str]) -> Dict[str, Any]:
        """
        Validate actual Photoshop layer names against template contract.
        
        Args:
            template_id: Template ID
            actual_layers: List of actual layer names from Photoshop
            
        Returns:
            Validation result with missing/extra layers
        """
        contract = self.get_layer_contract(template_id)
        if not contract:
            return {
                'valid': False,
                'error': 'Template not found or no layer contract'
            }
        
        expected_frames = set(contract.get('frames', []))
        actual_frames = set(actual_layers)
        
        missing = expected_frames - actual_frames
        extra = actual_frames - expected_frames
        
        return {
            'valid': len(missing) == 0,
            'missing_layers': list(missing),
            'extra_layers': list(extra),
            'expected_frames': list(expected_frames),
            'background_layer': contract.get('background'),
            'overlay_layers': contract.get('overlays', [])
        }
    
    def print_browser(self):
        """Print formatted template browser."""
        tree = self.get_template_tree()
        
        print("\n" + "=" * 80)
        print("📄 MUGX TEMPLATE BROWSER")
        print("=" * 80)
        
        for category in sorted(tree.keys()):
            print(f"\n📦 {category.upper()}")
            print("-" * 40)
            
            for frame_count in sorted(tree[category].keys()):
                print(f"\n  🖼️  {frame_count} Photo{'s' if frame_count > 1 else ''}")
                
                for template in tree[category][frame_count]:
                    premium = "⭐" if template.get('isPremium', False) else "  "
                    theme = template.get('theme', 'general')
                    occasion = template.get('occasion', '')
                    
                    print(f"    {premium} {template.get('name')}")
                    print(f"       ID: {template.get('id')}")
                    print(f"       Theme: {theme} | Occasion: {occasion}")
                    print(f"       Tags: {', '.join(template.get('tags', []))}")
                    
                    # Print layer contract
                    contract = template.get('layerNamingContract', {})
                    frames = contract.get('frames', [])
                    print(f"       Frames: {', '.join(frames)}")
        
        print("\n" + "=" * 80)


# ============ USAGE EXAMPLE ============

if __name__ == '__main__':
    # Example usage
    assets_root = Path.home() / 'SubliStudioAssets'
    loader = AssetRegistryLoader(assets_root)
    
    # Load all registries
    loader.load_all_registries()
    
    # Create template browser
    browser = TemplateBrowser(loader)
    template_count = browser.load()
    
    print(f"\n📊 Loaded {template_count} templates")
    
    # Get categories
    categories = browser.get_categories()
    print(f"📦 Categories: {categories}")
    
    # Get frame counts
    frame_counts = browser.get_frame_counts()
    print(f"🖼️  Frame counts: {frame_counts}")
    
    # Filter by category and frames
    mug_2photo = browser.filter_by_category_and_frames('mugs', 2)
    print(f"\n☕ Found {len(mug_2photo)} 2-photo mug templates")
    
    # Search
    results = browser.search('birthday')
    print(f"\n🔍 Search 'birthday': {len(results)} results")
    
    # Get layer contract
    contract = browser.get_layer_contract('mug-2photo-love-hearts-001')
    if contract:
        print(f"\n📄 Layer contract:")
        print(f"   Frames: {contract.get('frames')}")
        print(f"   Background: {contract.get('background')}")
        print(f"   Overlays: {contract.get('overlays')}")
    
    # Validate layers
    validation = browser.validate_layer_names(
        'mug-2photo-love-hearts-001',
        ['frame_1', 'frame_2', 'background', 'overlay_hearts']
    )
    print(f"\n✅ Layer validation: {validation}")
    
    # Print full browser
    browser.print_browser()
