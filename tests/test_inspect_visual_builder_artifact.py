from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from inspect_visual_builder_artifact import (
    normalize_hierarchy,
    summarize,
    validate_expectations,
)


def nested_fixture() -> dict:
    return {
        "id": "container-test",
        "type": "container",
        "config": {},
        "childWidgets": [
            {
                "id": "row-1",
                "type": "row",
                "parentWidgetId": "container-test",
                "config": {"paddingTopSmall": 8, "hidden": "No"},
                "childWidgets": [
                    {
                        "id": "column-1",
                        "type": "column",
                        "parentWidgetId": "row-1",
                        "config": {"gridColumnCountLarge": 12},
                        "childWidgets": [],
                    }
                ],
            }
        ],
    }


class InspectVisualBuilderArtifactTests(unittest.TestCase):
    def test_normalizes_nested_cjson_and_preserves_order(self) -> None:
        hierarchy = normalize_hierarchy(nested_fixture())

        self.assertEqual(hierarchy.roots, ["container-test"])
        self.assertEqual(hierarchy.children["container-test"], ["row-1"])
        self.assertEqual(hierarchy.children["row-1"], ["column-1"])
        self.assertEqual(hierarchy.integrity_errors, [])

    def test_normalizes_browser_checkpoint_widget_map(self) -> None:
        root = nested_fixture()
        row = root["childWidgets"][0]
        column = row["childWidgets"][0]
        checkpoint = {
            "widgets": {
                "container-test": root,
                "row-1": row,
                "column-1": column,
            }
        }

        hierarchy = normalize_hierarchy(checkpoint)

        self.assertEqual(len(hierarchy.nodes), 3)
        self.assertEqual(hierarchy.children["row-1"], ["column-1"])

    def test_normalizes_browser_checkpoint_container_map(self) -> None:
        checkpoint = {"containers": {"container-test": nested_fixture()}}

        hierarchy = normalize_hierarchy(checkpoint)

        self.assertEqual(hierarchy.roots, ["container-test"])
        self.assertEqual(len(hierarchy.nodes), 3)
        self.assertEqual(hierarchy.children["row-1"], ["column-1"])

    def test_reports_responsive_and_visibility_mechanisms(self) -> None:
        report = summarize(normalize_hierarchy(nested_fixture()))

        self.assertEqual(report["widget_count"], 3)
        self.assertEqual(report["type_counts"]["row"], 1)
        self.assertEqual(report["responsive_keys_by_type"]["row"], ["paddingTopSmall"])
        self.assertEqual(report["visibility_keys_by_type"]["row"], ["hidden"])
        self.assertEqual(report["parent_child_type_edge_counts"]["row>column"], 1)
        self.assertEqual(
            report["config_keys_by_type"]["row"],
            ["hidden", "paddingTopSmall"],
        )

    def test_reports_show_on_as_visibility_and_responsive(self) -> None:
        fixture = nested_fixture()
        fixture["config"]["showOn"] = "mobile,tablet"

        report = summarize(normalize_hierarchy(fixture))

        self.assertEqual(report["responsive_keys_by_type"]["container"], ["showOn"])
        self.assertEqual(report["visibility_keys_by_type"]["container"], ["showOn"])

    def test_reference_scan_uses_only_reference_bearing_config_keys(self) -> None:
        fixture = nested_fixture()
        fixture["config"].update(
            {
                "ordinaryCopy": "ordinary-hyphenated-phrase",
                "editModeSelectedTab": "column-1",
                "targetWidgetId": "missing-widget-9",
            }
        )

        report = summarize(normalize_hierarchy(fixture))

        self.assertEqual(
            report["widget_reference_key_counts"],
            {
                "container.editModeSelectedTab": 1,
                "container.targetWidgetId": 1,
            },
        )
        self.assertEqual(report["missing_reference_targets"], ["missing-widget-9"])

    def test_detects_declared_parent_mismatch(self) -> None:
        fixture = nested_fixture()
        fixture["childWidgets"][0]["parentWidgetId"] = "container-other"

        hierarchy = normalize_hierarchy(fixture)

        self.assertEqual(len(hierarchy.integrity_errors), 1)

    def test_detects_cycle_in_widget_map(self) -> None:
        checkpoint = {
            "widgets": {
                "row-1": {
                    "id": "row-1",
                    "type": "row",
                    "parentWidgetId": "column-1",
                    "childWidgets": ["column-1"],
                },
                "column-1": {
                    "id": "column-1",
                    "type": "column",
                    "parentWidgetId": "row-1",
                    "childWidgets": ["row-1"],
                },
            }
        }

        hierarchy = normalize_hierarchy(checkpoint)

        self.assertIn("hierarchy cycle detected", hierarchy.integrity_errors)
        self.assertEqual(hierarchy.roots, [])

    def test_detects_duplicate_and_multiple_parent_references(self) -> None:
        checkpoint = {
            "widgets": {
                "container-1": {
                    "id": "container-1",
                    "type": "container",
                    "childWidgets": ["column-1", "column-1"],
                },
                "container-2": {
                    "id": "container-2",
                    "type": "container",
                    "childWidgets": ["column-1"],
                },
                "column-1": {
                    "id": "column-1",
                    "type": "column",
                    "parentWidgetId": "container-1",
                    "childWidgets": [],
                },
            }
        }

        hierarchy = normalize_hierarchy(checkpoint)

        self.assertTrue(
            any("duplicate child" in error for error in hierarchy.integrity_errors)
        )
        self.assertTrue(
            any("multiple parents" in error for error in hierarchy.integrity_errors)
        )

    def test_detects_map_parent_that_does_not_own_child(self) -> None:
        checkpoint = {
            "widgets": {
                "container-1": {
                    "id": "container-1",
                    "type": "container",
                    "childWidgets": [],
                },
                "column-1": {
                    "id": "column-1",
                    "type": "column",
                    "parentWidgetId": "container-1",
                    "childWidgets": [],
                },
            }
        }

        hierarchy = normalize_hierarchy(checkpoint)

        self.assertTrue(
            any("does not reference it" in error for error in hierarchy.integrity_errors)
        )

    def test_checks_parent_and_exact_order_expectations(self) -> None:
        hierarchy = normalize_hierarchy(nested_fixture())

        failures = validate_expectations(
            hierarchy,
            ["column-1"],
            ["column-1=row-1"],
            ["container-test=row-1"],
        )

        self.assertEqual(failures, [])

    def test_expectation_failure_is_specific(self) -> None:
        hierarchy = normalize_hierarchy(nested_fixture())

        failures = validate_expectations(
            hierarchy,
            ["missing-1"],
            ["column-1=container-test"],
            ["container-test=column-1"],
        )

        self.assertEqual(len(failures), 3)

    def test_checks_type_absence_and_config_values(self) -> None:
        hierarchy = normalize_hierarchy(nested_fixture())

        failures = validate_expectations(
            hierarchy,
            type_relations=["row-1=row"],
            absent_children=["row-1=headline-1"],
            config_expectations=[
                "row-1.paddingTopSmall=8",
                'row-1.hidden="No"',
            ],
        )

        self.assertEqual(failures, [])

    def test_config_expectation_requires_json_value(self) -> None:
        hierarchy = normalize_hierarchy(nested_fixture())

        with self.assertRaises(ValueError):
            validate_expectations(
                hierarchy,
                config_expectations=["row-1.hidden=No"],
            )


if __name__ == "__main__":
    unittest.main()
