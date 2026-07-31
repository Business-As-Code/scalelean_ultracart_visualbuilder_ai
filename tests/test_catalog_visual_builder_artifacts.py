from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_visual_builder_artifacts import build_catalog, main, render_catalog


def private_fixture(label: str = "first") -> dict:
    return {
        "id": f"container-private-{label}",
        "type": "container",
        "config": {"internalNote": f"secret content {label}"},
        "childWidgets": [
            {
                "id": f"row-private-{label}",
                "type": "row",
                "parentWidgetId": f"container-private-{label}",
                "config": {
                    "backgroundImage": "https://private.example.test/asset.png",
                    "paddingTopLarge": 24,
                },
                "childWidgets": [
                    {
                        "id": f"column-private-{label}",
                        "type": "column",
                        "parentWidgetId": f"row-private-{label}",
                        "config": {"gridColumnCountLarge": 12},
                        "childWidgets": [
                            {
                                "id": f"headline-private-{label}",
                                "type": "headline",
                                "parentWidgetId": f"column-private-{label}",
                                "config": {
                                    "html": f"customer secret {label}",
                                    "remotePath": f"/private/{label}/source.cjson",
                                    "buttonShowThese": [f"widget-private-{label}"],
                                },
                                "childWidgets": [],
                            }
                        ],
                    }
                ],
            }
        ],
    }


def write_json(path: Path, document: dict) -> None:
    path.write_text(
        json.dumps(document, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )


class CatalogVisualBuilderArtifactsTests(unittest.TestCase):
    def test_catalog_excludes_private_values_ids_urls_and_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "private-client-source.cjson"
            write_json(source, private_fixture("needle-918273"))

            rendered = render_catalog(build_catalog([source]))

        self.assertNotIn("private-client-source.cjson", rendered)
        self.assertNotIn("needle-918273", rendered)
        self.assertNotIn("customer secret", rendered)
        self.assertNotIn("https://private.example.test", rendered)
        self.assertNotIn("/private/", rendered)
        self.assertNotIn("container-private", rendered)
        self.assertIn('"html"', rendered)
        self.assertIn('"headline"', rendered)

    def test_deduplicates_identical_artifacts_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.cjson"
            second = Path(directory) / "second.cjson"
            fixture = private_fixture()
            write_json(first, fixture)
            write_json(second, fixture)

            catalog = build_catalog([first, second])
            repeated = build_catalog([first, second], allow_duplicates=True)

        self.assertEqual(catalog["evidence_counts"]["input_artifact_count"], 2)
        self.assertEqual(catalog["evidence_counts"]["cataloged_artifact_count"], 1)
        self.assertEqual(catalog["evidence_counts"]["duplicate_artifact_count"], 1)
        self.assertEqual(catalog["type_instance_counts"]["row"], 1)
        self.assertEqual(len(catalog["artifact_sha256"]), 1)
        self.assertEqual(repeated["evidence_counts"]["cataloged_artifact_count"], 2)
        self.assertEqual(repeated["type_instance_counts"]["row"], 2)
        self.assertEqual(len(repeated["artifact_sha256"]), 2)

    def test_reports_child_types_edges_and_config_key_unions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.cjson"
            write_json(source, private_fixture())

            catalog = build_catalog([source])

        self.assertEqual(catalog["type_instance_counts"], {
            "column": 1,
            "container": 1,
            "headline": 1,
            "row": 1,
        })
        self.assertEqual(catalog["observed_child_types"], {
            "column": ["headline"],
            "container": ["row"],
            "row": ["column"],
        })
        self.assertEqual(catalog["parent_to_child_type_edge_counts"], {
            "column>headline": 1,
            "container>row": 1,
            "row>column": 1,
        })
        self.assertEqual(
            catalog["config_key_unions"]["row"],
            ["backgroundImage", "paddingTopLarge"],
        )

    def test_output_is_deterministic_for_reversed_input_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.cjson"
            second = Path(directory) / "second.cjson"
            write_json(first, private_fixture("alpha"))
            write_json(second, private_fixture("beta"))

            forward = render_catalog(build_catalog([first, second]))
            reverse = render_catalog(build_catalog([second, first]))

        self.assertEqual(forward, reverse)

    def test_main_defaults_to_stdout_and_can_write_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.cjson"
            output = Path(directory) / "catalog.json"
            write_json(source, private_fixture())
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                stdout_status = main([str(source)])
            output_status = main([str(source), "--output", str(output)])

            stdout_catalog = json.loads(stdout.getvalue())
            output_catalog = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(stdout_status, 0)
        self.assertEqual(output_status, 0)
        self.assertEqual(stdout_catalog, output_catalog)


if __name__ == "__main__":
    unittest.main()
