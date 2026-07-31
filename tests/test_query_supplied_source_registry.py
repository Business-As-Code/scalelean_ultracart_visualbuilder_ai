from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "query_supplied_source_registry.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("query_supplied_source_registry", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _registry() -> dict[str, object]:
    return {
        "authoring_contract": {
            "responsive_value_keys": ["small", "medium", "large"],
            "scoped_style_keys": ["all", "small-only"],
        },
        "anomalies": {
            "records": [
                {"kind": "unmapped_setting_type", "element": "row", "setting": "size"}
            ]
        },
        "elements": [
            {
                "type": "row",
                "friendly_name": "Row",
                "widget_group": "grid",
                "status": "stable",
                "tags": ["layout"],
                "flags": {"forced_child_type": "column"},
                "placement": {
                    "child_model": "forced",
                    "frontmatter_parents": ["any"],
                    "frontmatter_children": ["column"],
                    "allowed_under_signals": ["any element"],
                    "allowed_child_signals": ["column only"],
                    "other_rules": "",
                    "context_sentences": [],
                },
                "settings_count": 1,
                "settings": [{"key": "size", "declared_type": "number"}],
                "reference_setting_keys": [],
                "source_hashes": {"schema_sha256": "a" * 64},
                "documentation": {"selected_sections": {"purpose": "Layout."}},
                "supplier_warnings": [],
            },
            {
                "type": "column",
                "friendly_name": "Column",
                "widget_group": "grid",
                "status": "stable",
                "tags": ["layout"],
                "flags": {"forced_child_type": None},
                "placement": {
                    "child_model": "leaf",
                    "frontmatter_parents": ["row"],
                    "frontmatter_children": [],
                },
                "settings_count": 0,
                "settings": [],
                "reference_setting_keys": [],
                "source_hashes": {"schema_sha256": "b" * 64},
                "documentation": {"selected_sections": {}},
                "supplier_warnings": [],
            },
        ],
    }


class QuerySuppliedSourceRegistryTests(unittest.TestCase):
    def test_element_summary_is_compact_and_counts_anomalies(self) -> None:
        summary = MODULE.element_summary(_registry(), "row")
        self.assertEqual(summary["settings_count"], 1)
        self.assertEqual(summary["setting_keys"], ["size"])
        self.assertEqual(summary["source_anomaly_counts"], {"unmapped_setting_type": 1})
        self.assertNotIn("documentation", summary)

    def test_setting_summary_includes_responsive_contract(self) -> None:
        summary = MODULE.setting_summary(_registry(), "row", "size")
        self.assertEqual(summary["setting"]["declared_type"], "number")
        self.assertEqual(summary["responsive_value_keys"], ["small", "medium", "large"])

    def test_placement_query_separates_bilateral_from_other_signals(self) -> None:
        result = MODULE.placement_candidates(_registry(), "row", direction="children")
        self.assertEqual(result["candidates"]["bilateral"], ["column"])
        self.assertIn("row", result["candidates"]["contradicted"])
        self.assertIn("bilateral only", result["authoring_rule"])

    def test_search_uses_type_name_group_and_tags(self) -> None:
        result = MODULE.search_elements(_registry(), "layout")
        self.assertEqual(result["match_count"], 2)

    def test_unknown_element_and_setting_fail_closed(self) -> None:
        with self.assertRaises(MODULE.RegistryQueryError):
            MODULE.element_summary(_registry(), "missing")
        with self.assertRaises(MODULE.RegistryQueryError):
            MODULE.setting_summary(_registry(), "row", "missing")


if __name__ == "__main__":
    unittest.main()
