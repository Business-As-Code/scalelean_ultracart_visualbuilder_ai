from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_cjson_against_registry.py"
SPEC = importlib.util.spec_from_file_location("validate_cjson_against_registry", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _setting(key: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "key": key,
        "declared_type": "string",
        "editor_type": "text",
        "format": None,
        "enum": None,
        "enum_ref": None,
        "values_dynamic": False,
        "multilang": False,
        "breakpoint_enabled": False,
        "conditional": None,
        "is_widget_reference": False,
    }
    value.update(overrides)
    return value


def _registry() -> dict[str, object]:
    return {
        "elements": [
            {
                "type": "row",
                "flags": {"forced_child_type": "column"},
                "placement": {
                    "frontmatter_parents": ["any"],
                    "frontmatter_children": ["column"],
                },
                "settings": [
                    _setting(
                        "width",
                        declared_type="number",
                        enum=[6, 12],
                        breakpoint_enabled=True,
                    ),
                    _setting("target", format="widget-id", is_widget_reference=True),
                    _setting("dynamic", values_dynamic=True),
                    _setting(
                        "dependent",
                        conditional={"key": "mode", "equals": "enabled"},
                    ),
                    _setting("mode"),
                ],
            },
            {
                "type": "column",
                "flags": {"forced_child_type": None},
                "placement": {
                    "frontmatter_parents": ["row"],
                    "frontmatter_children": [],
                },
                "settings": [
                    _setting("copy", multilang=True),
                    _setting("scopedStyles", declared_type="string", format="css"),
                ],
            },
            {
                "type": "text",
                "flags": {"forced_child_type": None},
                "placement": {
                    "frontmatter_parents": ["column"],
                    "frontmatter_children": [],
                },
                "settings": [],
            },
        ],
        "authoring_contract": {
            "node_required_keys": ["id", "type", "config", "childWidgets"],
            "node_allowed_keys": [
                "id",
                "type",
                "config",
                "childWidgets",
                "parentWidgetId",
                "containerId",
            ],
            "node_property_types": {
                "id": "string",
                "type": "string",
                "config": "object",
                "childWidgets": "array",
                "parentWidgetId": "string",
                "containerId": "string",
            },
            "bookkeeping_config_keys": ["hidden", "lock", "inheritGroups"],
            "transient_config_keys": ["modalOpen", "sidepanelOpen", "contextSourceHash"],
            "legacy_config_keys": [{"key": "oldWidth"}],
        },
        "shared_enums": {"icon-library": {"values": ["", "check"]}},
    }


def _valid_tree() -> dict[str, object]:
    return {
        "id": "row-EXAMPLE",
        "type": "row",
        "config": {"width": {"small": 12, "large": 6}},
        "childWidgets": [
            {
                "id": "column-EXAMPLE",
                "type": "column",
                "parentWidgetId": "row-EXAMPLE",
                "config": {"copy": {"ENG": "Example"}},
                "childWidgets": [],
            }
        ],
    }


class ValidateCjsonAgainstRegistryTests(unittest.TestCase):
    def test_accepts_bilateral_forced_child_and_responsive_values(self) -> None:
        result = MODULE.validate_cjson(_valid_tree(), _registry())
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["stats"]["node_count"], 2)
        self.assertEqual(result["scope"], "static_source_validation")
        self.assertIn("native_behavior", result["live_verification_required"])

    def test_rejects_unknown_type_node_key_and_config_key(self) -> None:
        tree = _valid_tree()
        tree["invented"] = True
        tree["config"] = {"unknown": "value"}
        tree["childWidgets"][0]["type"] = "unknown"
        result = MODULE.validate_cjson(tree, _registry())
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("unknown_node_key", codes)
        self.assertIn("unknown_config_key", codes)
        self.assertIn("unknown_element_type", codes)

    def test_rejects_legacy_transient_and_wrong_breakpoint_keys(self) -> None:
        tree = _valid_tree()
        tree["config"] = {
            "oldWidth": 12,
            "modalOpen": True,
            "width": {"small-only": 12},
        }
        result = MODULE.validate_cjson(tree, _registry())
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("legacy_config_key", codes)
        self.assertIn("transient_config_key", codes)
        self.assertIn("invalid_responsive_wrapper", codes)

    def test_rejects_dynamic_value_without_verified_merchant_option(self) -> None:
        tree = _valid_tree()
        tree["config"]["dynamic"] = "merchant-value"
        rejected = MODULE.validate_cjson(tree, _registry())
        accepted = MODULE.validate_cjson(
            tree,
            _registry(),
            verified_dynamic_values={("row", "dynamic"): {"merchant-value"}},
        )
        self.assertIn(
            "unverified_dynamic_value",
            {item["code"] for item in rejected["errors"]},
        )
        self.assertTrue(accepted["valid"], accepted)

    def test_requires_reference_target_or_explicit_external_context(self) -> None:
        tree = _valid_tree()
        tree["config"]["target"] = "external-widget"
        rejected = MODULE.validate_cjson(tree, _registry())
        accepted = MODULE.validate_cjson(
            tree, _registry(), external_ids={"external-widget"}
        )
        self.assertIn(
            "dangling_widget_reference",
            {item["code"] for item in rejected["errors"]},
        )
        self.assertTrue(accepted["valid"], accepted)

    def test_fails_closed_on_unresolved_or_inactive_conditions(self) -> None:
        unresolved_tree = _valid_tree()
        unresolved_tree["config"]["dependent"] = "value"
        unresolved = MODULE.validate_cjson(unresolved_tree, _registry())
        inactive_tree = _valid_tree()
        inactive_tree["config"].update(
            {"dependent": "value", "mode": "disabled"}
        )
        inactive = MODULE.validate_cjson(inactive_tree, _registry())
        existing = MODULE.validate_cjson(
            unresolved_tree, _registry(), mode="existing"
        )

        self.assertIn(
            "unresolved_conditional_setting",
            {item["code"] for item in unresolved["errors"]},
        )
        self.assertIn(
            "inactive_conditional_setting",
            {item["code"] for item in inactive["errors"]},
        )
        self.assertTrue(existing["valid"], existing)

    def test_fails_closed_on_unilateral_or_denied_placement(self) -> None:
        tree = _valid_tree()
        tree["childWidgets"][0]["type"] = "text"
        authoring = MODULE.validate_cjson(tree, _registry())
        existing = MODULE.validate_cjson(tree, _registry(), mode="existing")
        self.assertFalse(authoring["valid"])
        self.assertIn(
            "forced_child_violation",
            {item["code"] for item in authoring["errors"]},
        )
        self.assertIn(
            "placement_denied",
            {item["code"] for item in existing["warnings"]},
        )

    def test_detects_duplicate_ids_and_parent_mismatch(self) -> None:
        tree = _valid_tree()
        tree["childWidgets"][0]["id"] = "row-EXAMPLE"
        tree["childWidgets"][0]["parentWidgetId"] = "wrong-parent"
        result = MODULE.validate_cjson(tree, _registry())
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("duplicate_widget_id", codes)
        self.assertIn("parent_reference_mismatch", codes)

    def test_rejects_invalid_multilang_and_scoped_style_wrappers(self) -> None:
        tree = _valid_tree()
        tree["childWidgets"][0]["config"] = {
            "copy": "not-a-map",
            "scopedStyles": {"mobile": "a { color: red; }"},
        }
        result = MODULE.validate_cjson(tree, _registry())
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("invalid_multilang_wrapper", codes)
        self.assertIn("invalid_scoped_style_breakpoint", codes)

    def test_existing_mode_preserves_legacy_value_shapes_as_warnings(self) -> None:
        tree = _valid_tree()
        tree["config"] = {
            "oldWidth": 12,
            "modalOpen": True,
            "width": {"small-only": "12"},
        }
        tree["childWidgets"][0]["config"] = {"copy": "legacy scalar"}
        result = MODULE.validate_cjson(tree, _registry(), mode="existing")
        warning_codes = {item["code"] for item in result["warnings"]}
        self.assertTrue(result["valid"], result)
        self.assertIn("legacy_config_key", warning_codes)
        self.assertIn("transient_config_key", warning_codes)
        self.assertIn("invalid_responsive_wrapper", warning_codes)
        self.assertIn("invalid_multilang_wrapper", warning_codes)


if __name__ == "__main__":
    unittest.main()
