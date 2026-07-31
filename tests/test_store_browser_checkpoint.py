from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
from io import StringIO
import json
import stat
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from store_browser_checkpoint import main, validate_label


def checkpoint_document() -> dict:
    return {
        "containers": {
            "container-test": {
                "id": "container-test",
                "type": "container",
                "config": {"privateCopy": "do not disclose this content"},
                "childWidgets": [
                    {
                        "id": "row-1",
                        "type": "row",
                        "parentWidgetId": "container-test",
                        "config": {},
                        "childWidgets": [
                            {
                                "id": "column-1",
                                "type": "column",
                                "parentWidgetId": "row-1",
                                "config": {},
                                "childWidgets": [],
                            }
                        ],
                    }
                ],
            }
        }
    }


class StoreBrowserCheckpointTests(unittest.TestCase):
    def run_main(
        self,
        private_root: Path,
        argv: list[str],
    ) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with (
            patch(
                "store_browser_checkpoint.load_config",
                return_value={"UVB_PRIVATE_ARTIFACT_ROOT": str(private_root)},
            ),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            result = main(argv)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_stores_exact_bytes_with_private_modes_and_safe_output(self) -> None:
        with (
            TemporaryDirectory() as private_directory,
            TemporaryDirectory() as source_directory,
        ):
            private_root = Path(private_directory)
            source = Path(source_directory) / "private-checkpoint.json"
            raw_bytes = (
                json.dumps(checkpoint_document(), separators=(", ", ": ")) + "\n"
            ).encode()
            source.write_bytes(raw_bytes)

            result, stdout, stderr = self.run_main(
                private_root,
                [str(source), "--label", "product-hero"],
            )

            self.assertEqual(result, 0)
            self.assertEqual(stderr, "")
            checkpoint_root = private_root / "browser-checkpoints"
            stored = list(checkpoint_root.iterdir())
            self.assertEqual(len(stored), 1)
            self.assertIn("product-hero", stored[0].name)
            self.assertEqual(stored[0].read_bytes(), raw_bytes)
            self.assertEqual(stat.S_IMODE(checkpoint_root.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(stored[0].stat().st_mode), 0o600)
            self.assertEqual(
                stdout,
                "widgets=3 roots=1 "
                f"sha256={hashlib.sha256(raw_bytes).hexdigest()}\n",
            )
            self.assertNotIn(str(source), stdout + stderr)
            self.assertNotIn(str(private_root), stdout + stderr)
            self.assertNotIn("do not disclose", stdout + stderr)

    def test_collision_safe_naming_does_not_overwrite(self) -> None:
        with (
            TemporaryDirectory() as private_directory,
            TemporaryDirectory() as source_directory,
        ):
            private_root = Path(private_directory)
            source = Path(source_directory) / "checkpoint.json"
            raw_bytes = json.dumps(checkpoint_document()).encode()
            source.write_bytes(raw_bytes)

            with patch(
                "store_browser_checkpoint.timestamp_token",
                return_value="20260731T120000000000Z",
            ):
                first, _, _ = self.run_main(
                    private_root, [str(source), "--label", "test"]
                )
                second, _, _ = self.run_main(
                    private_root, [str(source), "--label", "test"]
                )

            self.assertEqual((first, second), (0, 0))
            stored = sorted((private_root / "browser-checkpoints").iterdir())
            self.assertEqual(len(stored), 2)
            self.assertNotEqual(stored[0].name, stored[1].name)
            self.assertEqual(
                [path.read_bytes() for path in stored],
                [raw_bytes, raw_bytes],
            )

    def test_rejects_invalid_hierarchy_without_disclosing_input(self) -> None:
        with (
            TemporaryDirectory() as private_directory,
            TemporaryDirectory() as source_directory,
        ):
            private_root = Path(private_directory)
            source = Path(source_directory) / "private-broken.json"
            document = checkpoint_document()
            document["containers"]["container-test"]["childWidgets"][0][
                "parentWidgetId"
            ] = "secret-wrong-parent"
            source.write_text(json.dumps(document), encoding="utf-8")

            result, stdout, stderr = self.run_main(private_root, [str(source)])

            self.assertEqual(result, 2)
            self.assertEqual(stdout, "")
            self.assertIn("input validation failed", stderr)
            self.assertNotIn(str(source), stderr)
            self.assertNotIn(str(private_root), stderr)
            self.assertNotIn("secret-wrong-parent", stderr)
            self.assertFalse((private_root / "browser-checkpoints").exists())

    def test_rejects_malformed_hierarchy_shape_without_traceback(self) -> None:
        with (
            TemporaryDirectory() as private_directory,
            TemporaryDirectory() as source_directory,
        ):
            private_root = Path(private_directory)
            source = Path(source_directory) / "malformed.json"
            source.write_text(
                json.dumps(
                    {
                        "id": "container-test",
                        "type": "container",
                        "childWidgets": 17,
                    }
                ),
                encoding="utf-8",
            )

            result, stdout, stderr = self.run_main(private_root, [str(source)])

            self.assertEqual(result, 2)
            self.assertEqual(stdout, "")
            self.assertEqual(
                stderr,
                "Checkpoint not stored: input validation failed.\n",
            )
            self.assertFalse((private_root / "browser-checkpoints").exists())

    def test_rejects_unsafe_label_before_reading_or_storing(self) -> None:
        with TemporaryDirectory() as private_directory:
            private_root = Path(private_directory)
            missing_source = private_root / "not-present.json"

            result, stdout, stderr = self.run_main(
                private_root,
                [str(missing_source), "--label", "../escape"],
            )

            self.assertEqual(result, 2)
            self.assertEqual(stdout, "")
            self.assertIn("label is not safe", stderr)
            self.assertNotIn("../escape", stderr)
            self.assertFalse((private_root / "browser-checkpoints").exists())

    def test_safe_label_contract(self) -> None:
        self.assertEqual(validate_label("item-page_1"), "item-page_1")
        for unsafe in ("", "Upper", "has space", ".hidden", "a" * 49):
            with self.subTest(unsafe=unsafe):
                with self.assertRaises(ValueError):
                    validate_label(unsafe)


if __name__ == "__main__":
    unittest.main()
