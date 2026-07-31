from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from capture_ftps_tree import safe_relative_path


class CaptureFtpsTreeTests(unittest.TestCase):
    def test_accepts_a_relative_storefront_subtree(self) -> None:
        self.assertEqual(
            safe_relative_path("storefront/theme/containers"),
            "storefront/theme/containers",
        )

    def test_rejects_parent_traversal(self) -> None:
        with self.assertRaises(ValueError):
            safe_relative_path("storefront/../other")

    def test_rejects_an_absolute_path(self) -> None:
        with self.assertRaises(ValueError):
            safe_relative_path("/storefront/theme")
