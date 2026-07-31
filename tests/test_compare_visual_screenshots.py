from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from compare_visual_screenshots import (
    AcceptanceThresholds,
    InputError,
    MaskRectangle,
    compare_images,
    evaluate_thresholds,
    main,
)


class CompareVisualScreenshotsTests(unittest.TestCase):
    def test_metrics_are_normalized_and_pixel_threshold_is_strict(self) -> None:
        reference = Image.new("RGB", (2, 2), (0, 0, 0))
        target = Image.new("RGB", (2, 2), (0, 0, 0))
        target.putdata(
            [
                (255, 0, 0),
                (0, 255, 0),
                (0, 0, 255),
                (0, 0, 0),
            ]
        )

        result = compare_images(reference, target, pixel_delta_threshold=254)

        self.assertAlmostEqual(result.metrics.normalized_mae, 0.25)
        self.assertAlmostEqual(result.metrics.normalized_rmse, 0.5)
        self.assertEqual(result.metrics.maximum_channel_delta, 255)
        self.assertAlmostEqual(result.metrics.percent_pixels_over_threshold, 75.0)
        self.assertEqual(result.compared_pixel_count, 4)
        self.assertEqual(result.masked_pixel_count, 0)

        none_over = compare_images(reference, target, pixel_delta_threshold=255)
        self.assertEqual(none_over.metrics.percent_pixels_over_threshold, 0.0)

    def test_images_are_normalized_to_rgb(self) -> None:
        reference = Image.new("L", (3, 2), 17)
        target = Image.new("RGB", (3, 2), (17, 17, 17))

        result = compare_images(reference, target)

        self.assertEqual(result.metrics.normalized_mae, 0.0)
        self.assertEqual(result.metrics.normalized_rmse, 0.0)
        self.assertEqual(result.metrics.maximum_channel_delta, 0)

    def test_repeatable_overlapping_masks_exclude_pixels_once(self) -> None:
        reference = Image.new("RGB", (3, 1), (0, 0, 0))
        target = Image.new("RGB", (3, 1), (0, 0, 0))
        target.putpixel((0, 0), (255, 255, 255))
        target.putpixel((1, 0), (255, 255, 255))

        result = compare_images(
            reference,
            target,
            masks=(MaskRectangle(0, 0, 1, 1), MaskRectangle(0, 0, 1, 1)),
        )

        self.assertEqual(result.compared_pixel_count, 2)
        self.assertEqual(result.masked_pixel_count, 1)
        self.assertAlmostEqual(result.metrics.normalized_mae, 0.5)
        self.assertAlmostEqual(result.metrics.normalized_rmse, math.sqrt(0.5))
        self.assertEqual(result.metrics.percent_pixels_over_threshold, 50.0)

    def test_threshold_evaluation_uses_inclusive_maximums(self) -> None:
        reference = Image.new("RGB", (1, 1), (0, 0, 0))
        target = Image.new("RGB", (1, 1), (51, 51, 51))
        result = compare_images(reference, target, pixel_delta_threshold=50)
        thresholds = AcceptanceThresholds(
            normalized_mae=0.2,
            normalized_rmse=0.2,
            maximum_channel_delta=51,
            percent_pixels_over_threshold=100.0,
        )

        checks = evaluate_thresholds(result.metrics, thresholds)

        self.assertTrue(all(checks.values()))

    def test_cli_returns_pass_and_mismatch_and_never_echoes_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            reference_path = Path(directory) / "private-reference-customer-918273.png"
            target_path = Path(directory) / "private-target-customer-918273.png"
            Image.new("RGB", (2, 2), (0, 0, 0)).save(reference_path)
            Image.new("RGB", (2, 2), (1, 0, 0)).save(target_path)

            passing_stdout = io.StringIO()
            passing_stderr = io.StringIO()
            with redirect_stdout(passing_stdout), redirect_stderr(passing_stderr):
                passing_code = main(
                    [
                        str(reference_path),
                        str(target_path),
                        "--max-normalized-mae",
                        "0.01",
                        "--max-normalized-rmse",
                        "0.01",
                        "--max-channel-delta",
                        "1",
                        "--max-percent-pixels-over-threshold",
                        "100",
                        "--json",
                    ]
                )

            payload = json.loads(passing_stdout.getvalue())
            output = passing_stdout.getvalue() + passing_stderr.getvalue()
            self.assertEqual(passing_code, 0)
            self.assertTrue(payload["passed"])
            self.assertNotIn(str(reference_path), output)
            self.assertNotIn(str(target_path), output)

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                mismatch_code = main(
                    [str(reference_path), str(target_path), "--json"]
                )
            self.assertEqual(mismatch_code, 1)

    def test_repeatable_cli_masks_can_produce_an_exact_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            reference_path = Path(directory) / "reference.png"
            target_path = Path(directory) / "target.png"
            reference = Image.new("RGB", (3, 2), (20, 30, 40))
            target = reference.copy()
            target.putpixel((0, 0), (255, 255, 255))
            target.putpixel((2, 1), (0, 0, 0))
            reference.save(reference_path)
            target.save(target_path)

            stdout = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(io.StringIO()):
                code = main(
                    [
                        str(reference_path),
                        str(target_path),
                        "--mask",
                        "0,0,1,1",
                        "--mask",
                        "2,1,1,1",
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(payload["masked_pixel_count"], 2)
            self.assertEqual(payload["compared_pixel_count"], 4)
            self.assertEqual(payload["metrics"]["normalized_mae"], 0.0)

    def test_jpeg_is_accepted_and_unsupported_format_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            jpeg_path = Path(directory) / "private-input.jpeg"
            bitmap_path = Path(directory) / "private-input.bmp"
            Image.new("RGB", (2, 2), (90, 100, 110)).save(jpeg_path, format="JPEG")
            Image.new("RGB", (2, 2), (90, 100, 110)).save(bitmap_path, format="BMP")

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                jpeg_code = main([str(jpeg_path), str(jpeg_path)])
                bitmap_code = main([str(bitmap_path), str(bitmap_path)])

        self.assertEqual(jpeg_code, 0)
        self.assertEqual(bitmap_code, 2)

    def test_invalid_inputs_return_generic_error_without_path_echo(self) -> None:
        private_missing = "/private/customer/missing-screenshot-918273.png"
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main([private_missing, private_missing, "--json"])

        output = stdout.getvalue() + stderr.getvalue()
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(stderr.getvalue()), {"error": "input_error"})
        self.assertNotIn(private_missing, output)

    def test_argument_errors_do_not_echo_private_values(self) -> None:
        private_argument = "/private/customer/secret-screenshot-918273.png"
        stderr = io.StringIO()

        with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                main(["reference.png", "target.png", "--unknown", private_argument])

        self.assertEqual(raised.exception.code, 2)
        self.assertNotIn(private_argument, stderr.getvalue())
        self.assertIn("error: invalid arguments", stderr.getvalue())

    def test_dimension_mask_and_all_masked_errors_are_input_errors(self) -> None:
        with self.assertRaises(InputError):
            compare_images(
                Image.new("RGB", (2, 2)),
                Image.new("RGB", (3, 2)),
            )
        with self.assertRaises(InputError):
            compare_images(
                Image.new("RGB", (2, 2)),
                Image.new("RGB", (2, 2)),
                masks=(MaskRectangle(1, 1, 2, 1),),
            )
        with self.assertRaises(InputError):
            compare_images(
                Image.new("RGB", (2, 2)),
                Image.new("RGB", (2, 2)),
                masks=(MaskRectangle(0, 0, 2, 2),),
            )


if __name__ == "__main__":
    unittest.main()
