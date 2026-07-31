from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_widget_evidence_registry import build_registry
from validate_widget_evidence_registry import unsafe_artifacts, validate


CATALOG = {
    "type_instance_counts": {"column": 1, "row": 1},
    "config_key_unions": {"column": ["width"], "row": ["gap", "width"]},
}


class WidgetEvidenceRegistryTests(unittest.TestCase):
    def test_generated_registry_covers_types_and_keys(self) -> None:
        registry = build_registry(CATALOG, "catalog-hash")
        self.assertEqual(validate(CATALOG, registry, "catalog-hash"), [])
        self.assertEqual(registry["widgets"]["row"]["settings"]["gap"]["status"], "Unknown")

    def test_fails_for_stale_hash_and_missing_setting(self) -> None:
        registry = build_registry(CATALOG, "old-hash")
        del registry["widgets"]["row"]["settings"]["gap"]
        errors = validate(CATALOG, registry, "new-hash")
        self.assertIn("evidence registry catalog hash is stale", errors)
        self.assertIn("undocumented setting key: row.gap", errors)

    def test_fails_for_invalid_status(self) -> None:
        registry = build_registry(CATALOG, "catalog-hash")
        modified = copy.deepcopy(registry)
        modified["widgets"]["column"]["status"] = "Hypothesis"
        self.assertIn("widget status missing or invalid: column", validate(CATALOG, modified, "catalog-hash"))

    def test_detects_unsafe_public_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "safe.md").write_text("safe", encoding="utf-8")
            (root / "source.cjson").write_text("{}", encoding="utf-8")
            (root / ".env").write_text("secret", encoding="utf-8")
            self.assertEqual(unsafe_artifacts(root), [".env", "source.cjson"])


if __name__ == "__main__":
    unittest.main()
