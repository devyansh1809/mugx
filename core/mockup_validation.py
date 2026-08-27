"""Phase 3 catalog-to-mockup-asset validation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from core.mockup_asset_registry import MockupAssetRegistry
from core.product_catalog import ProductCatalog


@dataclass
class MockupValidationReport:
    installed: Dict[str, List[str]] = field(default_factory=dict)
    missing: Dict[str, List[str]] = field(default_factory=dict)
    invalid: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def production_ready(self) -> bool:
        return not self.missing and not self.invalid

    def as_text(self) -> str:
        lines = []
        for product_id, views in sorted(self.installed.items()):
            lines.append(f"READY {product_id}: {', '.join(views)}")
        for product_id, views in sorted(self.missing.items()):
            lines.append(f"MISSING {product_id}: {', '.join(views)}")
        for product_id, errors in sorted(self.invalid.items()):
            lines.append(f"INVALID {product_id}: {'; '.join(errors)}")
        return "\n".join(lines) or "No product mockup mappings declared."


def validate_mockup_coverage(catalog: ProductCatalog, registry: MockupAssetRegistry) -> MockupValidationReport:
    report = MockupValidationReport()
    for category in catalog.categories():
        for profile in catalog.by_category(category):
            expected = list(profile.mockup_profiles)
            declared = registry.declared_views(profile.id)
            missing = [view for view in expected if view not in declared]
            installed: List[str] = []
            invalid: List[str] = []
            for view in expected:
                record = registry.record(profile.id, view)
                if record is None:
                    continue
                errors = registry.validate_record(record)
                if errors:
                    invalid.append(f"{view}: {', '.join(errors)}")
                elif record.is_installed:
                    installed.append(view)
                else:
                    missing.append(view)
            if installed:
                report.installed[profile.id] = installed
            if missing:
                report.missing[profile.id] = sorted(set(missing))
            if invalid:
                report.invalid[profile.id] = invalid
    return report
