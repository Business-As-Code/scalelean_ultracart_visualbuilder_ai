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

from compare_ftps_captures import main, resolve_capture_directory


PAIR_PATHS = (
    "/private/theme/item-display.cjson",
    "/private/theme/item-display.vm",
)


def write_tree(private_root: Path, name: str, remote_root: str = "/storefront") -> str:
    tree_name = f"tree-{name}.json"
    (private_root / tree_name).write_text(
        json.dumps({"root": remote_root}) + "\n",
        encoding="utf-8",
    )
    return tree_name


def write_capture(
    private_root: Path,
    name: str,
    tree_manifest: str,
    hashes: dict[str, str],
) -> Path:
    capture = private_root / name
    capture.mkdir()
    captured = [
        {
            "path": candidate_path,
            "extension": Path(candidate_path).suffix,
            "sha256": content_hash,
            "local_name": f"private-{index}{Path(candidate_path).suffix}",
        }
        for index, (candidate_path, content_hash) in enumerate(hashes.items())
    ]
    (capture / "manifest.json").write_text(
        json.dumps(
            {
                "tree_manifest": tree_manifest,
                "captured": captured,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return capture


def paired_hashes(cjson_hash: str, vm_hash: str) -> dict[str, str]:
    return {
        PAIR_PATHS[0]: cjson_hash,
        PAIR_PATHS[1]: vm_hash,
    }


class CompareFtpsCapturesTests(unittest.TestCase):
    def run_main(
        self,
        private_root: Path,
        argv: list[str],
    ) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with (
            patch(
                "compare_ftps_captures.load_config",
                return_value={"UVB_PRIVATE_ARTIFACT_ROOT": str(private_root)},
            ),
            patch(
                "compare_ftps_captures.private_directory",
                return_value=private_root,
            ),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            result = main(argv)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_resolves_bare_and_absolute_capture_selectors(self) -> None:
        with TemporaryDirectory() as directory:
            private_root = Path(directory)
            tree = write_tree(private_root, "shared")
            capture = write_capture(
                private_root,
                "ftps-candidates-before",
                tree,
                paired_hashes("a", "a"),
            )

            self.assertEqual(
                resolve_capture_directory(private_root, capture.name),
                capture.resolve(),
            )
            self.assertEqual(
                resolve_capture_directory(private_root, str(capture)),
                capture.resolve(),
            )

    def test_rejects_capture_selector_escape(self) -> None:
        with TemporaryDirectory() as directory, TemporaryDirectory() as other:
            private_root = Path(directory)
            outside_root = Path(other)
            tree = write_tree(outside_root, "outside")
            outside = write_capture(
                outside_root,
                "ftps-candidates-outside",
                tree,
                paired_hashes("a", "a"),
            )

            with self.assertRaises(ValueError):
                resolve_capture_directory(private_root, str(outside))
            with self.assertRaises(ValueError):
                resolve_capture_directory(private_root, "../ftps-candidates-outside")

    def test_requires_before_and_after_together(self) -> None:
        with redirect_stdout(StringIO()):
            result = main(["--before", "ftps-candidates-before"])

        self.assertEqual(result, 2)

    def test_newest_two_fallback_prints_compatibility_warning(self) -> None:
        with TemporaryDirectory() as directory:
            private_root = Path(directory)
            tree = write_tree(private_root, "shared")
            write_capture(
                private_root,
                "ftps-candidates-20260101T000000Z",
                tree,
                paired_hashes("a", "a"),
            )
            write_capture(
                private_root,
                "ftps-candidates-20260101T000001Z",
                tree,
                paired_hashes("b", "b"),
            )

            result, _, stderr = self.run_main(private_root, [])

            self.assertEqual(result, 0)
            self.assertIn("Warning: --before and --after were not supplied", stderr)
            self.assertNotIn("ftps-candidates-", stderr)

    def test_rejects_mismatched_ftps_roots_without_disclosing_them(self) -> None:
        with TemporaryDirectory() as directory:
            private_root = Path(directory)
            before_tree = write_tree(private_root, "before", "/first-private-root")
            after_tree = write_tree(private_root, "after", "/second-private-root")
            before = write_capture(
                private_root,
                "ftps-candidates-before",
                before_tree,
                paired_hashes("a", "a"),
            )
            after = write_capture(
                private_root,
                "ftps-candidates-after",
                after_tree,
                paired_hashes("b", "b"),
            )

            result, stdout, _ = self.run_main(
                private_root,
                ["--before", before.name, "--after", after.name],
            )

            self.assertEqual(result, 2)
            self.assertIn("different FTPS roots", stdout)
            self.assertNotIn("/first-private-root", stdout)
            self.assertNotIn("/second-private-root", stdout)

    def test_explicit_pair_reports_expected_cjson_and_vm_change(self) -> None:
        with TemporaryDirectory() as directory:
            private_root = Path(directory)
            tree = write_tree(private_root, "shared")
            before = write_capture(
                private_root,
                "ftps-candidates-before",
                tree,
                paired_hashes("a", "a"),
            )
            after = write_capture(
                private_root,
                "ftps-candidates-after",
                tree,
                paired_hashes("b", "b"),
            )

            result, stdout, stderr = self.run_main(
                private_root,
                [
                    "--before",
                    str(before),
                    "--after",
                    after.name,
                    "--expect-stem",
                    "item-display",
                ],
            )

            self.assertEqual(result, 0)
            self.assertEqual(stderr, "")
            self.assertIn("1 CJSON changed, 1 VM changed", stdout)
            self.assertIn("Expected logical CJSON/VM pair changed: yes.", stdout)
            self.assertNotIn("/private/theme", stdout)

    def test_three_state_rollback_reports_saved_changes_and_restoration(self) -> None:
        with TemporaryDirectory() as directory:
            private_root = Path(directory)
            tree = write_tree(private_root, "shared")
            before = write_capture(
                private_root,
                "ftps-candidates-before",
                tree,
                paired_hashes("baseline-cjson", "baseline-vm"),
            )
            after = write_capture(
                private_root,
                "ftps-candidates-after",
                tree,
                paired_hashes("saved-cjson", "saved-vm"),
            )
            rollback = write_capture(
                private_root,
                "ftps-candidates-rollback",
                tree,
                paired_hashes("baseline-cjson", "baseline-vm"),
            )

            result, stdout, _ = self.run_main(
                private_root,
                [
                    "--before",
                    before.name,
                    "--after",
                    after.name,
                    "--rollback",
                    rollback.name,
                    "--expect-stem",
                    "item-display",
                ],
            )

            self.assertEqual(result, 0)
            self.assertIn("1 CJSON changed, 1 VM changed", stdout)
            self.assertIn("2 matching candidates, 0 content mismatches", stdout)
            self.assertIn("Expected rollback matches baseline: yes.", stdout)

    def test_three_state_rollback_returns_nonzero_on_content_mismatch(self) -> None:
        with TemporaryDirectory() as directory:
            private_root = Path(directory)
            tree = write_tree(private_root, "shared")
            before = write_capture(
                private_root,
                "ftps-candidates-before",
                tree,
                paired_hashes("baseline-cjson", "baseline-vm"),
            )
            after = write_capture(
                private_root,
                "ftps-candidates-after",
                tree,
                paired_hashes("saved-cjson", "saved-vm"),
            )
            rollback = write_capture(
                private_root,
                "ftps-candidates-rollback",
                tree,
                paired_hashes("baseline-cjson", "not-restored"),
            )

            result, stdout, _ = self.run_main(
                private_root,
                [
                    "--before",
                    before.name,
                    "--after",
                    after.name,
                    "--rollback",
                    rollback.name,
                ],
            )

            self.assertEqual(result, 1)
            self.assertIn("1 CJSON changed, 1 VM changed", stdout)
            self.assertIn("Expected rollback matches baseline: no.", stdout)


if __name__ == "__main__":
    unittest.main()
