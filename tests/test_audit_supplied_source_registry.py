from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
BUILD_SPEC = importlib.util.spec_from_file_location(
    "build_supplied_source_registry_test_support",
    ROOT / "scripts" / "build_supplied_source_registry.py",
)
assert BUILD_SPEC and BUILD_SPEC.loader
BUILD = importlib.util.module_from_spec(BUILD_SPEC)
BUILD_SPEC.loader.exec_module(BUILD)

TEST_SUPPORT_SPEC = importlib.util.spec_from_file_location(
    "build_supplied_source_registry_fixture_support",
    ROOT / "tests" / "test_build_supplied_source_registry.py",
)
assert TEST_SUPPORT_SPEC and TEST_SUPPORT_SPEC.loader
TEST_SUPPORT = importlib.util.module_from_spec(TEST_SUPPORT_SPEC)
TEST_SUPPORT_SPEC.loader.exec_module(TEST_SUPPORT)

AUDIT_SPEC = importlib.util.spec_from_file_location(
    "audit_supplied_source_registry",
    ROOT / "scripts" / "audit_supplied_source_registry.py",
)
assert AUDIT_SPEC and AUDIT_SPEC.loader
AUDIT = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(AUDIT)


class AuditSuppliedSourceRegistryTests(unittest.TestCase):
    def test_audits_integrity_counts_and_supplied_example(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = TEST_SUPPORT._make_bundle(root)
            intake = root / "intake.json"
            TEST_SUPPORT._intake_manifest(bundle, intake)
            registry = BUILD.build_registry(bundle, intake)
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            example = {
                "id": "row-example",
                "type": "row",
                "config": {},
                "childWidgets": [
                    {
                        "id": "column-example",
                        "type": "column",
                        "parentWidgetId": "row-example",
                        "config": {},
                        "childWidgets": [],
                    }
                ],
            }
            (bundle / "examples").mkdir()
            (bundle / "examples" / "valid.cjson").write_text(
                json.dumps(example), encoding="utf-8"
            )
            TEST_SUPPORT._intake_manifest(bundle, intake)
            registry = BUILD.build_registry(bundle, intake)
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            result = AUDIT.audit_registry(bundle, intake, registry_path)

        self.assertTrue(result["valid"], result)
        self.assertEqual(result["catalog"]["element_count"], 2)
        self.assertEqual(result["supplied_examples"]["valid_count"], 1)
        self.assertEqual(result["source_integrity"]["status"], "verified")
        self.assertNotIn(str(root), json.dumps(result))
        receipt = AUDIT.public_receipt(result)
        self.assertEqual(receipt["supplied_examples"]["example_count"], 1)
        self.assertNotIn("results", receipt["supplied_examples"])
        self.assertNotIn("label", json.dumps(receipt))

    def test_rejects_registry_catalog_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = TEST_SUPPORT._make_bundle(root)
            intake = root / "intake.json"
            TEST_SUPPORT._intake_manifest(bundle, intake)
            registry = BUILD.build_registry(bundle, intake)
            registry["catalog"]["element_count"] = 99
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            result = AUDIT.audit_registry(bundle, intake, registry_path)

        self.assertFalse(result["valid"])
        self.assertIn(
            "registry catalog counts do not match normalized content",
            result["failures"],
        )


if __name__ == "__main__":
    unittest.main()
