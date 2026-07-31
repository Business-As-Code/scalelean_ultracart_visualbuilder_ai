from __future__ import annotations

import json
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from capture_ftps_candidates import (
    REQUIRED,
    candidate_remote_paths,
    main,
    resolve_tree_manifest,
    select_candidates,
)


class CaptureFtpsCandidatesTests(unittest.TestCase):
    def test_selects_explicit_manifest_filename(self) -> None:
        with TemporaryDirectory() as directory:
            private_root = Path(directory)
            manifest = private_root / "ftps-tree-explicit.json"
            manifest.write_text("{}\n", encoding="utf-8")

            selected, used_fallback = resolve_tree_manifest(
                private_root,
                manifest.name,
            )

            self.assertEqual(selected, manifest.resolve())
            self.assertFalse(used_fallback)

    def test_selects_explicit_absolute_manifest_within_root(self) -> None:
        with TemporaryDirectory() as directory:
            private_root = Path(directory)
            nested = private_root / "captures"
            nested.mkdir()
            manifest = nested / "tree.json"
            manifest.write_text("{}\n", encoding="utf-8")

            selected, used_fallback = resolve_tree_manifest(
                private_root,
                str(manifest),
            )

            self.assertEqual(selected, manifest.resolve())
            self.assertFalse(used_fallback)

    def test_rejects_manifest_path_outside_private_root(self) -> None:
        with TemporaryDirectory() as root_directory, TemporaryDirectory() as other:
            private_root = Path(root_directory)
            outside_manifest = Path(other) / "ftps-tree-outside.json"
            outside_manifest.write_text("{}\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                resolve_tree_manifest(private_root, str(outside_manifest))

    def test_latest_tree_fallback_prints_warning(self) -> None:
        with TemporaryDirectory() as directory:
            private_root = Path(directory)
            manifest = private_root / "ftps-tree-20260101T000000Z.json"
            manifest.write_text(
                json.dumps({"directories": []}) + "\n",
                encoding="utf-8",
            )
            config = {name: "test" for name in REQUIRED}
            config["UVB_FILE_PROTOCOL"] = "ftpes"
            stderr = StringIO()

            with (
                patch(
                    "capture_ftps_candidates.load_config",
                    return_value=config,
                ),
                patch(
                    "capture_ftps_candidates.private_directory",
                    return_value=private_root,
                ),
                redirect_stdout(StringIO()),
                redirect_stderr(stderr),
            ):
                result = main([])

            self.assertEqual(result, 0)
            self.assertIn("Warning: --tree-manifest was not supplied", stderr.getvalue())

    def test_rejects_selection_mode_conflict(self) -> None:
        with self.assertRaises(ValueError):
            select_candidates(
                ["/theme/item-display.cjson"],
                ["item-display.cjson"],
                ["/theme/item-display.cjson"],
            )

    def test_filters_by_exact_remote_path(self) -> None:
        tree = {
            "directories": [
                {
                    "path": "/theme/a",
                    "entries": ["item-display.cjson", "item-display.vm"],
                },
                {
                    "path": "/theme/b",
                    "entries": ["item-display.cjson", "item-display.vm"],
                },
            ]
        }
        candidates = candidate_remote_paths(tree)

        selected = select_candidates(
            candidates,
            [],
            ["/theme/b/item-display.cjson", "/theme/b/item-display.vm"],
        )

        self.assertEqual(
            selected,
            ["/theme/b/item-display.cjson", "/theme/b/item-display.vm"],
        )

    def test_exact_remote_path_must_exist_in_selected_tree(self) -> None:
        with self.assertRaises(ValueError):
            select_candidates(
                ["/theme/item-display.cjson"],
                [],
                ["/other/item-display.cjson"],
            )


if __name__ == "__main__":
    unittest.main()
