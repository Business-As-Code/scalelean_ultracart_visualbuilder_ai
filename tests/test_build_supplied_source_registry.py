from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_supplied_source_registry.py"
SPEC = importlib.util.spec_from_file_location("build_supplied_source_registry", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


SECTIONS = (
    "Identity",
    "Purpose & when to use",
    "Placement",
    "Configuration",
    "Runtime behavior",
    "Rendering & CSS",
    "Interactions with sibling elements",
    "Recipes",
    "Gotchas & degradation",
    "See also",
)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _doc(element: str, parents: list[str], children: list[str]) -> str:
    frontmatter = f"""---
element: {element}
friendlyName: {element}
widgetGroup: test
status: stable
schema: ./schema/{element}.schema.json
designFile: src/js/{element}.js
runtimeFile: null
cssFile: null
serverRender: false
causesClones: false
consumesItemContext: false
parents: [{', '.join(parents)}]
children: [{', '.join(children)}]
relatedElements: []
tags: [test]
---

# {element}
"""
    bodies = []
    for section in SECTIONS:
        if section == "Placement":
            body = "- `allowedUnder`: documented parent.\n- `allowedChild`: documented child."
        elif section == "Configuration":
            body = f"<!-- BEGIN GENERATED SCHEMA: {element} -->\nignored\n<!-- END GENERATED SCHEMA: {element} -->\n\n### Notes\nUseful notes."
        else:
            body = "None."
        bodies.append(f"## {section}\n\n{body}\n")
    return frontmatter + "\n".join(bodies)


def _make_bundle(root: Path) -> Path:
    bundle = root / "bundle"
    catalog = []
    for element, parents, children, forced in (
        ("row", ["any"], ["column"], "column"),
        ("column", ["row"], [], None),
    ):
        catalog.append(
            {
                "element": element,
                "friendlyName": element,
                "widgetGroup": "test",
                "source": f"src/js/{element}.js",
                "settings": 1,
                "hasDoc": True,
            }
        )
        properties = {
            "size": {
                "type": "number",
                "x-sfvb-type": "number",
                "x-sfvb-title": "Size",
                "x-sfvb-breakpoints": True,
                "default": "wrong-type" if element == "row" else 12,
                "enum": [6, 12],
                "description": "Size",
                "x-sfvb-needsDescription": element == "row",
            }
        }
        _write_json(
            bundle / "elements" / "schema" / f"{element}.schema.json",
            {
                "$schema": "http://json-schema.org/draft-04/schema#",
                "$id": element,
                "title": element,
                "type": "object",
                "properties": properties,
                "x-sfvb-friendlyName": element,
                "x-sfvb-widgetGroup": "test",
                "x-sfvb-flags": {
                    "serverRender": False,
                    "causesClones": False,
                    "consumesItemContext": False,
                    "allowAddChildren": element == "row",
                    "addChildForceType": forced,
                },
                "x-sfvb-groups": [],
                "x-sfvb-breakpointNames": list(MODULE.SCOPED_STYLE_KEYS),
                "x-sfvb-warnings": [],
            },
        )
        if element == "column":
            _write_json(
                bundle / "elements" / "schema" / f"{element}.descriptions.json",
                {"size": "Column size."},
            )
        (bundle / "elements" / f"{element}.md").parent.mkdir(parents=True, exist_ok=True)
        (bundle / "elements" / f"{element}.md").write_text(
            _doc(element, parents, children), encoding="utf-8"
        )
    _write_json(
        bundle / "elements" / "schema" / "_index.json",
        {"count": 2, "elements": catalog, "x-sfvb-generated": True},
    )
    _write_json(
        bundle / "elements" / "schema" / "_icon-library.json",
        {"$id": "icons", "enum": ["", "check"], "x-sfvb-generated": True},
    )
    _write_json(
        bundle / "cjson-node.schema.json",
        {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string"},
                "config": {"type": "object"},
                "childWidgets": {"type": "array"},
                "parentWidgetId": {"type": "string"},
                "containerId": {"type": "string"},
            },
            "required": ["id", "type", "config", "childWidgets"],
            "additionalProperties": False,
        },
    )
    _write_json(
        bundle / "manifest.json",
        {
            "bundle": "test-bundle",
            "generated": "2026-07-31T00:00:00Z",
            "generator": "test",
            "elementCount": 2,
            "fileCount": 9,
            "totalBytes": 1,
            "legacyConfigKeys": {"keys": [{"key": "oldSize"}]},
        },
    )
    return bundle


def _intake_manifest(bundle: Path, path: Path) -> None:
    records = []
    for candidate in sorted(value for value in bundle.rglob("*") if value.is_file()):
        raw = candidate.read_bytes()
        records.append(
            {
                "relative_path": candidate.relative_to(bundle).as_posix(),
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    _write_json(path, {"files": records})


class BuildSuppliedSourceRegistryTests(unittest.TestCase):
    def test_builds_normalized_registry_and_preserves_anomalies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = _make_bundle(root)
            intake = root / "intake.json"
            _intake_manifest(bundle, intake)
            registry = MODULE.build_registry(bundle, intake)

        self.assertEqual(registry["catalog"]["element_count"], 2)
        self.assertEqual(registry["source"]["intake_integrity"]["status"], "verified")
        row = {item["type"]: item for item in registry["elements"]}["row"]
        self.assertEqual(row["flags"]["forced_child_type"], "column")
        self.assertEqual(row["placement"]["child_model"], "forced")
        self.assertEqual(row["settings"][0]["description_source"], "generated_fallback")
        self.assertEqual(
            registry["anomalies"]["counts"],
            {"default_type_mismatch": 1, "enum_default_mismatch": 1},
        )
        self.assertEqual(MODULE.validate_registry(registry), [])

    def test_rejects_changed_bundle_after_intake(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = _make_bundle(root)
            intake = root / "intake.json"
            _intake_manifest(bundle, intake)
            (bundle / "elements" / "row.md").write_text("changed", encoding="utf-8")
            with self.assertRaises(MODULE.RegistryBuildError):
                MODULE.build_registry(bundle, intake)

    def test_accepts_crlf_element_documents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = _make_bundle(Path(directory))
            path = bundle / "elements" / "row.md"
            path.write_bytes(path.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))
            registry = MODULE.build_registry(bundle)
        self.assertEqual(registry["catalog"]["element_count"], 2)

    def test_rejects_unknown_forced_child_type(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = _make_bundle(Path(directory))
            registry = MODULE.build_registry(bundle)
        registry["elements"][0]["flags"]["forced_child_type"] = "missing"
        self.assertIn(
            "registry forced child references an unknown type",
            MODULE.validate_registry(registry),
        )


if __name__ == "__main__":
    unittest.main()
