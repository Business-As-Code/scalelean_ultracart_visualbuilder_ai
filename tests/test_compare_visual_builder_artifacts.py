from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from compare_visual_builder_artifacts import (
    compare_hierarchies,
    main,
    render_text,
    select_reference_hierarchy,
)
from inspect_visual_builder_artifact import normalize_hierarchy


def node(
    widget_id: str,
    widget_type: str,
    *,
    parent: str | None = None,
    config: dict | None = None,
    children: list[dict] | None = None,
) -> dict:
    result = {
        "id": widget_id,
        "type": widget_type,
        "config": {} if config is None else config,
        "childWidgets": [] if children is None else children,
    }
    if parent is not None:
        result["parentWidgetId"] = parent
    return result


def simple_fixture(*, secret: str = "reference") -> dict:
    first = node(
        "column-private-first",
        "column",
        parent="row-private-main",
        config={"gridColumnCountLarge": 6},
    )
    second = node(
        "column-private-second",
        "column",
        parent="row-private-main",
        config={"gridColumnCountLarge": 6},
    )
    row = node(
        "row-private-main",
        "row",
        parent="container-private-root",
        config={
            "privateCopy": secret,
            "privateImage": "https://private.example.test/asset.png",
            "paddingTopLarge": 24,
        },
        children=[first, second],
    )
    return node("container-private-root", "container", children=[row])


def write_json(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document), encoding="utf-8")


class CompareVisualBuilderArtifactsTests(unittest.TestCase):
    def test_identical_artifacts_match_with_no_changes(self) -> None:
        hierarchy = normalize_hierarchy(simple_fixture())

        report = compare_hierarchies(hierarchy, hierarchy)

        self.assertTrue(report["matched"])
        self.assertTrue(
            all(value == 0 for value in report["aggregate_change_counts"].values())
        )

    def test_compares_all_required_dimensions_and_reports_only_safe_counts(self) -> None:
        reference = simple_fixture(secret="customer private reference")
        target = simple_fixture(secret="customer private target")
        reference_row = reference["childWidgets"][0]
        target_row = target["childWidgets"][0]

        removed = target_row["childWidgets"].pop(1)
        target_row["childWidgets"].reverse()
        target_panel = node(
            "panel-private-new",
            "panel",
            parent="container-private-root",
            children=[target_row["childWidgets"].pop(0)],
        )
        target_panel["childWidgets"][0]["parentWidgetId"] = "panel-private-new"
        target["childWidgets"].append(target_panel)
        target_row["type"] = "panel"
        target_row["config"] = {
            "privateCopy": "customer private target",
            "addedSetting": 7,
            "paddingTopLarge": 30,
        }
        del removed

        report = compare_hierarchies(
            normalize_hierarchy(reference), normalize_hierarchy(target)
        )
        rendered = json.dumps(report, sort_keys=True) + render_text(report)

        aggregate = report["aggregate_change_counts"]
        self.assertEqual(aggregate["missing_nodes"], 1)
        self.assertEqual(aggregate["excess_nodes"], 1)
        self.assertEqual(aggregate["type_changes"], 1)
        self.assertEqual(aggregate["parent_link_changes"], 1)
        self.assertGreaterEqual(aggregate["child_order_changes"], 1)
        self.assertEqual(aggregate["config_key_additions"], 1)
        self.assertEqual(aggregate["config_key_removals"], 1)
        self.assertEqual(aggregate["config_value_changes"], 2)
        self.assertEqual(
            report["validated_type_change_counts"]["transitions"],
            {"row>panel": 1},
        )
        self.assertEqual(
            report["validated_config_key_change_counts"]["value_changed"],
            {"paddingTopLarge": 1, "privateCopy": 1},
        )
        for private_value in (
            "container-private-root",
            "row-private-main",
            "column-private-first",
            "panel-private-new",
            "customer private reference",
            "customer private target",
            "https://private.example.test",
        ):
            self.assertNotIn(private_value, rendered)

    def test_exact_child_order_is_a_required_dimension(self) -> None:
        reference = simple_fixture()
        target = simple_fixture()
        target["childWidgets"][0]["childWidgets"].reverse()

        report = compare_hierarchies(
            normalize_hierarchy(reference), normalize_hierarchy(target)
        )

        self.assertFalse(report["matched"])
        self.assertEqual(report["aggregate_change_counts"]["child_order_changes"], 1)

    def test_config_ignore_and_missing_null_normalization_are_declared(self) -> None:
        reference = simple_fixture(secret="reference secret")
        target = simple_fixture(secret="target secret")
        target["childWidgets"][0]["config"]["nullableSetting"] = None
        reference_hierarchy = normalize_hierarchy(reference)
        target_hierarchy = normalize_hierarchy(target)

        strict = compare_hierarchies(reference_hierarchy, target_hierarchy)
        normalized = compare_hierarchies(
            reference_hierarchy,
            target_hierarchy,
            ignore_config_keys=["privateCopy"],
            treat_missing_null_equal=True,
        )

        self.assertFalse(strict["matched"])
        self.assertTrue(normalized["matched"])
        self.assertEqual(normalized["normalization"]["ignored_config_key_count"], 1)
        self.assertTrue(normalized["normalization"]["treat_missing_null_equal"])

    def test_missing_null_normalization_applies_inside_object_values(self) -> None:
        reference = simple_fixture()
        target = simple_fixture()
        reference["childWidgets"][0]["config"]["responsive"] = {"large": 12}
        target["childWidgets"][0]["config"]["responsive"] = {
            "large": 12,
            "small": None,
        }

        strict = compare_hierarchies(
            normalize_hierarchy(reference), normalize_hierarchy(target)
        )
        normalized = compare_hierarchies(
            normalize_hierarchy(reference),
            normalize_hierarchy(target),
            treat_missing_null_equal=True,
        )

        self.assertFalse(strict["matched"])
        self.assertTrue(normalized["matched"])

    def test_bool_and_number_config_values_are_not_equal(self) -> None:
        reference = simple_fixture()
        target = simple_fixture()
        reference["config"]["enabled"] = True
        target["config"]["enabled"] = 1

        report = compare_hierarchies(
            normalize_hierarchy(reference), normalize_hierarchy(target)
        )

        self.assertFalse(report["matched"])
        self.assertEqual(report["aggregate_change_counts"]["config_value_changes"], 1)

    def test_multiple_reference_roots_require_an_explicit_selection(self) -> None:
        checkpoint = {
            "containers": {
                "container-private-first": simple_fixture(),
                "container-private-second": node(
                    "container-private-second", "container"
                ),
            }
        }
        hierarchy = normalize_hierarchy(checkpoint)

        with self.assertRaisesRegex(ValueError, "multiple roots"):
            select_reference_hierarchy(hierarchy, None)
        selected = select_reference_hierarchy(hierarchy, "container-private-root")

        self.assertEqual(len(selected.nodes), 4)
        self.assertEqual(selected.roots, ["container-private-root"])

    def test_cli_selects_reference_root_and_uses_required_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            reference_path = Path(directory) / "private-reference-checkpoint.json"
            target_path = Path(directory) / "private-target.cjson"
            checkpoint = {
                "containers": {
                    "container-private-root": simple_fixture(),
                    "container-private-other": node(
                        "container-private-other", "container"
                    ),
                }
            }
            write_json(reference_path, checkpoint)
            write_json(target_path, simple_fixture())
            stdout = io.StringIO()
            stderr = io.StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                missing_selection = main(
                    [str(reference_path), str(target_path), "--json"]
                )
            self.assertEqual(missing_selection, 2)
            self.assertNotIn(str(reference_path), stderr.getvalue())
            stderr.seek(0)
            stderr.truncate(0)
            stdout.seek(0)
            stdout.truncate(0)
            with redirect_stdout(stdout), redirect_stderr(stderr):
                matched = main(
                    [
                        str(reference_path),
                        str(target_path),
                        "--reference-root",
                        "container-private-root",
                        "--json",
                    ]
                )

        self.assertEqual(matched, 0)
        self.assertTrue(json.loads(stdout.getvalue())["matched"])
        self.assertNotIn("container-private-root", stdout.getvalue())

    def test_cli_returns_one_for_mismatch_and_two_for_private_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            reference_path = Path(directory) / "reference-secret-client.cjson"
            target_path = Path(directory) / "target-secret-client.cjson"
            write_json(reference_path, simple_fixture())
            changed = simple_fixture()
            changed["config"]["paddingTopLarge"] = 99
            write_json(target_path, changed)
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                mismatch = main([str(reference_path), str(target_path), "--json"])

            bad_path = Path(directory) / "do-not-disclose-private-path.cjson"
            bad_path.write_text("{private invalid json", encoding="utf-8")
            stdout.seek(0)
            stdout.truncate(0)
            with redirect_stdout(stdout), redirect_stderr(stderr):
                invalid = main([str(bad_path), str(target_path), "--json"])

        self.assertEqual(mismatch, 1)
        self.assertEqual(invalid, 2)
        self.assertNotIn("do-not-disclose-private-path", stderr.getvalue())
        self.assertNotIn("private invalid json", stderr.getvalue())

    def test_cli_applies_repeatable_ignores_and_missing_null_equivalence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            reference_path = Path(directory) / "reference.cjson"
            target_path = Path(directory) / "target.cjson"
            reference = simple_fixture(secret="first private value")
            target = simple_fixture(secret="second private value")
            reference["config"]["volatileToken"] = "private alpha"
            target["config"].update(
                {
                    "nullableSetting": None,
                    "volatileToken": "private beta",
                }
            )
            write_json(reference_path, reference)
            write_json(target_path, target)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                status = main(
                    [
                        str(reference_path),
                        str(target_path),
                        "--ignore-config-key",
                        "privateCopy",
                        "--ignore-config-key",
                        "volatileToken",
                        "--treat-missing-null-equal",
                        "--json",
                    ]
                )

        report = json.loads(stdout.getvalue())
        self.assertEqual(status, 0)
        self.assertTrue(report["matched"])
        self.assertEqual(report["normalization"]["ignored_config_key_count"], 2)

    def test_unsafe_schema_tokens_are_counted_but_never_output(self) -> None:
        reference = simple_fixture()
        target = simple_fixture()
        reference["childWidgets"][0]["type"] = "https://private.example/type"
        target["childWidgets"][0]["type"] = "private type target"
        reference["config"]["/private/config/key"] = "old private value"
        target["config"]["/private/config/key"] = "new private value"

        report = compare_hierarchies(
            normalize_hierarchy(reference), normalize_hierarchy(target)
        )
        rendered = json.dumps(report, sort_keys=True) + render_text(report)

        self.assertEqual(
            report["unreported_change_counts"]["type_transitions"], 1
        )
        self.assertEqual(
            report["unreported_change_counts"]["config_key_changes"], 1
        )
        self.assertNotIn("https://private.example/type", rendered)
        self.assertNotIn("private type target", rendered)
        self.assertNotIn("/private/config/key", rendered)
        self.assertNotIn("old private value", rendered)
        self.assertNotIn("new private value", rendered)


if __name__ == "__main__":
    unittest.main()
