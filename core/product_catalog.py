"""
Product Catalog — Phase 2B

Provides product catalog functionality with:
- Product profiles with specifications
- Filtering by category, subcategory, price
- Search functionality
- Print specifications (dimensions, DPI, bleed, safe area, mirror rules)
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from .asset_registry_loader import AssetRegistryLoader


class ProductCatalog:
    """Product catalog manager with filtering and search capabilities."""
    
    def __init__(self, loader: AssetRegistryLoader):
        """
        Initialize product catalog.
        
        Args:
            loader: AssetRegistryLoader instance
        """
        self.loader = loader
        self._products = []
        self._categories = set()
        self._subcategories = set()
    
    def load(self) -> int:
        """
        Load products from registry.
        
        Returns:
            Number of products loaded
        """
        self._products = self.loader.get_products()
        
        # Extract unique categories and subcategories
        for product in self._products:
            self._categories.add(product.get('category'))
            self._subcategories.add(product.get('subcategory'))
        
        return len(self._products)
    
    def get_all_products(self) -> List[Dict]:
        """Get all products."""
        return self._products
    
    def get_categories(self) -> List[str]:
        """Get all product categories."""
        return sorted(list(self._categories))
    
    def get_subcategories(self) -> List[str]:
        """Get all product subcategories."""
        return sorted(list(self._subcategories))
    
    def filter_by_category(self, category: str) -> List[Dict]:
        """Filter products by category."""
        return [p for p in self._products if p.get('category') == category]
    
    def filter_by_subcategory(self, subcategory: str) -> List[Dict]:
        """Filter products by subcategory."""
        return [p for p in self._products if p.get('subcategory') == subcategory]
    
    def filter_by_price_range(self, min_price: float, max_price: float) -> List[Dict]:
        """Filter products by price range."""
        return [
            p for p in self._products
            if min_price <= p.get('basePrice', 0) <= max_price
        ]
    
    def filter_active(self) -> List[Dict]:
        """Get only active products."""
        return [p for p in self._products if p.get('isActive', True)]
    
    def filter_premium(self) -> List[Dict]:
        """Get only premium products."""
        return [p for p in self._products if p.get('isPremium', False)]
    
    def search(self, query: str) -> List[Dict]:
        """Search products by name, description, tags, or category."""
        return self.loader.search_products(query)
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """Get a specific product by ID."""
        return self.loader.get_product_by_id(product_id)
    
    def get_print_specs(self, product_id: str) -> Optional[Dict]:
        """
        Get print specifications for a product.
        
        Args:
            product_id: Product ID
            
        Returns:
            Dictionary with print specifications or None
        """
        product = self.get_product(product_id)
        if not product:
            return None
        
        return {
            'product_id': product.get('id'),
            'product_name': product.get('name'),
            'canvas_size': product.get('canvasSize'),
            'dpi': product.get('dpi'),
            'print_area': product.get('printArea'),
            'bleed': product.get('bleed'),
            'safe_area': product.get('safeArea'),
            'print_mirror_rule': product.get('printMirrorRule'),
            'print_mirror_note': product.get('printMirrorNote'),
            'psd_template_path': product.get('psdTemplatePath'),
            'mockup_path': product.get('mockupPath')
        }
    
    def get_product_tree(self) -> Dict[str, Any]:
        """
        Get product catalog as a hierarchical tree.
        
        Returns:
            Nested dictionary: category -> subcategory -> products
        """
        tree = {}
        
        for product in self._products:
            category = product.get('category', 'unknown')
            subcategory = product.get('subcategory', 'general')
            
            if category not in tree:
                tree[category] = {}
            
            if subcategory not in tree[category]:
                tree[category][subcategory] = []
            
            tree[category][subcategory].append(product)
        
        return tree
    
    def print_catalog(self):
        """Print formatted product catalog."""
        tree = self.get_product_tree()
        
        print("\n" + "=" * 80)
        print("🛍️  MUGX PRODUCT CATALOG")
        print("=" * 80)
        
        for category in sorted(tree.keys()):
            print(f"\n📦 {category.upper()}")
            print("-" * 40)
            
            for subcategory in sorted(tree[category].keys()):
                print(f"\n  🏷️  {subcategory}")
                
                for product in tree[category][subcategory]:
                    price = product.get('basePrice', 0)
                    active = "✅" if product.get('isActive', True) else "❌"
                    premium = "⭐" if product.get('isPremium', False) else "  "
                    
                    print(f"    {active}{premium} {product.get('name')}")
                    print(f"       ID: {product.get('id')}")
                    print(f"       Price: ₹{price}")
                    
                    # Print specs
                    canvas = product.get('canvasSize', {})
                    dpi = product.get('dpi', 300)
                    print(f"       Canvas: {canvas.get('width', 0)}x{canvas.get('height', 0)}px @ {dpi} DPI")
                    
                    # Print mirror rule
                    if product.get('printMirrorRule'):
                        print(f"       ⚠️  MIRROR REQUIRED for printing")
        
        print("\n" + "=" * 80)


# ============ USAGE EXAMPLE ============

if __name__ == '__main__':
    # Example usage
    assets_root = Path.home() / 'SubliStudioAssets'
    loader = AssetRegistryLoader(assets_root)
    
    # Load all registries
    loader.load_all_registries()
    
    # Create product catalog
    catalog = ProductCatalog(loader)
    product_count = catalog.load()
    
    print(f"\n📊 Loaded {product_count} products")
    
    # Get categories
    categories = catalog.get_categories()
    print(f"📦 Categories: {categories}")
    
    # Filter by category
    mugs = catalog.filter_by_category('mugs')
    print(f"\n☕ Found {len(mugs)} mug products")
    
    # Search
    results = catalog.search('iphone')
    print(f"\n🔍 Search 'iphone': {len(results)} results")
    
    # Get print specs
    specs = catalog.get_print_specs('mug-11oz-white')
    if specs:
        print(f"\n📄 Print specs for {specs['product_name']}:")
        print(f"   Canvas: {specs['canvas_size']}")
        print(f"   DPI: {specs['dpi']}")
        print(f"   Mirror: {'Yes' if specs['print_mirror_rule'] else 'No'}")
    
    # Print full catalog
    catalog.print_catalog()
