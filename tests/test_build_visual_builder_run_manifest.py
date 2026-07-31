from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
from io import StringIO
import json
from pathlib import Path
import stat
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_visual_builder_run_manifest import main, parse_viewport, validate_label


FIXED_TIMESTAMP = "2026-07-31T12:34:56.123456Z"
PRIVATE_MARKER = "private-session-token-do-not-emit"


class BuildVisualBuilderRunManifestTests(unittest.TestCase):
    def run_main(self, argv: list[str]) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with (
            patch(
                "build_visual_builder_run_manifest.utc_timestamp",
                return_value=FIXED_TIMESTAMP,
            ),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            result = main(argv)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_writes_path_free_manifest_for_all_repeatable_roles(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = {
                "checkpoint_before": root / "private-checkpoint-before.json",
                "checkpoint_after": root / "private-checkpoint-after.json",
                "cjson": root / "item-display.cjson",
                "vm": root / "item-display.vm",
                "html": root / "rendered-product.html",
                "screenshot": root / "editor-product.png",
            }
            for index, path in enumerate(artifacts.values(), start=1):
                path.write_bytes(
                    f"{PRIVATE_MARKER}-{index}-https://private.invalid/path".encode()
                )
            output = root / "run-manifest.json"

            result, stdout, stderr = self.run_main(
                [
                    "--run-label",
                    "product-save-001",
                    "--logical-stem",
                    "item-display",
                    "--viewport-width",
                    "1440",
                    "--viewport-height",
                    "1100",
                    "--viewport-dpr",
                    "2",
                    "--checkpoint",
                    f"before={artifacts['checkpoint_before']}",
                    "--checkpoint",
                    f"after={artifacts['checkpoint_after']}",
                    "--cjson",
                    f"saved={artifacts['cjson']}",
                    "--vm",
                    f"saved={artifacts['vm']}",
                    "--rendered-html",
                    f"public={artifacts['html']}",
                    "--screenshot",
                    f"desktop={artifacts['screenshot']}",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(result, 0)
            self.assertEqual(stderr, "")
            raw_manifest = output.read_bytes()
            manifest = json.loads(raw_manifest)
            self.assertEqual(manifest["schema_version"], "1.0")
            self.assertEqual(manifest["artifact_role_count"], 6)
            self.assertEqual(
                manifest["run"],
                {
                    "label": "product-save-001",
                    "logical_stem": "item-display",
                    "recorded_at_utc": FIXED_TIMESTAMP,
                },
            )
            self.assertEqual(
                manifest["viewport"],
                {
                    "device_pixel_ratio": 2.0,
                    "height_px": 1100,
                    "width_px": 1440,
                },
            )

            records = {
                (record["artifact_type"], record["role"]): record
                for record in manifest["artifacts"]
            }
            self.assertEqual(
                set(records),
                {
                    ("checkpoint", "after"),
                    ("checkpoint", "before"),
                    ("cjson", "saved"),
                    ("rendered_html", "public"),
                    ("screenshot", "desktop"),
                    ("vm", "saved"),
                },
            )
            for key, path in (
                (("checkpoint", "before"), artifacts["checkpoint_before"]),
                (("checkpoint", "after"), artifacts["checkpoint_after"]),
                (("cjson", "saved"), artifacts["cjson"]),
                (("vm", "saved"), artifacts["vm"]),
                (("rendered_html", "public"), artifacts["html"]),
                (("screenshot", "desktop"), artifacts["screenshot"]),
            ):
                source = path.read_bytes()
                self.assertEqual(records[key]["byte_count"], len(source))
                self.assertEqual(
                    records[key]["sha256"], hashlib.sha256(source).hexdigest()
                )

            manifest_hash = hashlib.sha256(raw_manifest).hexdigest()
            self.assertEqual(
                stdout,
                f"roles=6 manifest_sha256={manifest_hash}\n",
            )
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)

            exposed = raw_manifest.decode() + stdout + stderr
            self.assertNotIn(PRIVATE_MARKER, exposed)
            self.assertNotIn("https://", exposed)
            for path in artifacts.values():
                self.assertNotIn(str(path), exposed)
                self.assertNotIn(path.name, exposed)
            self.assertNotIn(str(output), exposed)

    def test_refuses_existing_output_without_overwriting(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "private.cjson"
            artifact.write_bytes(b"private artifact")
            output = root / "manifest.json"
            output.write_text("existing private manifest", encoding="utf-8")

            result, stdout, stderr = self.run_main(
                [
                    "--run-label",
                    "existing-output-test",
                    "--cjson",
                    f"saved={artifact}",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(result, 2)
            self.assertEqual(stdout, "")
            self.assertEqual(stderr, "error: output already exists\n")
            self.assertEqual(output.read_text(encoding="utf-8"), "existing private manifest")
            self.assertNotIn(str(output), stderr)
            self.assertNotIn(str(artifact), stderr)

    def test_rejects_unsafe_labels_without_echo_or_output(self) -> None:
        unsafe_values = (
            ("run", "https://private.invalid/run"),
            ("stem", "../private-item"),
            ("role", "private role=/private/artifact.cjson"),
        )
        for kind, unsafe in unsafe_values:
            with self.subTest(kind=kind), TemporaryDirectory() as directory:
                root = Path(directory)
                artifact = root / "private.cjson"
                artifact.write_bytes(b"private artifact")
                output = root / "manifest.json"
                argv = [
                    "--run-label",
                    "safe-run",
                    "--cjson",
                    f"saved={artifact}",
                    "--output",
                    str(output),
                ]
                if kind == "run":
                    argv[1] = unsafe
                elif kind == "stem":
                    argv[2:2] = ["--logical-stem", unsafe]
                else:
                    argv[3] = unsafe

                result, stdout, stderr = self.run_main(argv)

                self.assertEqual(result, 2)
                self.assertEqual(stdout, "")
                self.assertFalse(output.exists())
                self.assertNotIn(unsafe, stderr)
                self.assertNotIn(str(artifact), stderr)

    def test_missing_artifact_is_path_safe_and_creates_no_output(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            missing = root / "customer-session-private.cjson"
            output = root / "manifest.json"

            result, stdout, stderr = self.run_main(
                [
                    "--run-label",
                    "missing-input-test",
                    "--cjson",
                    f"saved={missing}",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(result, 2)
            self.assertEqual(stdout, "")
            self.assertEqual(stderr, "error: artifact input is unavailable\n")
            self.assertNotIn(str(missing), stderr)
            self.assertFalse(output.exists())

    def test_rejects_duplicate_role_within_artifact_type(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.vm"
            second = root / "second.vm"
            first.write_bytes(b"first")
            second.write_bytes(b"second")
            output = root / "manifest.json"

            result, stdout, stderr = self.run_main(
                [
                    "--run-label",
                    "duplicate-role-test",
                    "--vm",
                    f"saved={first}",
                    "--vm",
                    f"saved={second}",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(result, 2)
            self.assertEqual(stdout, "")
            self.assertEqual(
                stderr,
                "error: artifact role is duplicated for its type\n",
            )
            self.assertFalse(output.exists())

    def test_zero_artifacts_is_a_valid_metadata_only_manifest(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "manifest.json"

            result, stdout, stderr = self.run_main(
                [
                    "--run-label",
                    "metadata-only",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(result, 0)
            self.assertEqual(stderr, "")
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(manifest["artifacts"], [])
            self.assertEqual(manifest["artifact_role_count"], 0)
            self.assertRegex(
                stdout,
                r"^roles=0 manifest_sha256=[0-9a-f]{64}\n$",
            )

    def test_viewport_and_label_contracts(self) -> None:
        self.assertEqual(validate_label("item-page_1", field="label"), "item-page_1")
        self.assertEqual(
            parse_viewport("1440", "900", "1.5"),
            {
                "height_px": 900,
                "width_px": 1440,
                "device_pixel_ratio": 1.5,
            },
        )
        for unsafe in ("", "Upper", "has space", ".hidden", "a" * 65):
            with self.subTest(unsafe=unsafe):
                with self.assertRaises(ValueError):
                    validate_label(unsafe, field="label")
        for width, height, dpr in (
            ("1440", None, None),
            (None, "900", None),
            (None, None, "2"),
            ("0", "900", None),
            ("01440", "900", None),
            ("1440", "900", "nan"),
            ("1440", "900", "0"),
        ):
            with self.subTest(width=width, height=height, dpr=dpr):
                with self.assertRaises(ValueError):
                    parse_viewport(width, height, dpr)


if __name__ == "__main__":
    unittest.main()
