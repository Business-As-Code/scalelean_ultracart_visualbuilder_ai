#!/usr/bin/env python3
"""Compare two explicit screenshots without exposing image content or paths."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import sys
from typing import Sequence
import warnings

from PIL import Image, ImageChops, ImageDraw, UnidentifiedImageError


SUPPORTED_FORMATS = frozenset({"JPEG", "PNG"})
MAX_IMAGE_PIXELS = 100_000_000


class InputError(ValueError):
    """Report invalid input without retaining or displaying private data."""


class PrivacySafeArgumentParser(argparse.ArgumentParser):
    """Reject malformed CLI input without echoing user-supplied values."""

    def error(self, message: str) -> None:
        del message
        self.print_usage(sys.stderr)
        self.exit(2, "error: invalid arguments\n")


@dataclass(frozen=True)
class MaskRectangle:
    """One zero-based rectangle excluded from comparison metrics."""

    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class ScreenshotMetrics:
    """Aggregate, normalized difference metrics for unmasked pixels."""

    normalized_mae: float
    normalized_rmse: float
    maximum_channel_delta: int
    percent_pixels_over_threshold: float


@dataclass(frozen=True)
class AcceptanceThresholds:
    """Maximum accepted values for every reported difference metric."""

    normalized_mae: float = 0.0
    normalized_rmse: float = 0.0
    maximum_channel_delta: int = 0
    percent_pixels_over_threshold: float = 0.0


@dataclass(frozen=True)
class ComparisonResult:
    """A privacy-safe screenshot comparison result."""

    width: int
    height: int
    compared_pixel_count: int
    masked_pixel_count: int
    pixel_delta_threshold: int
    metrics: ScreenshotMetrics


def _parse_mask(value: str) -> MaskRectangle:
    parts = value.split(",")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("mask must be x,y,width,height")
    try:
        values = tuple(int(part, 10) for part in parts)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "mask must contain four base-10 integers"
        ) from error
    rectangle = MaskRectangle(*values)
    if rectangle.x < 0 or rectangle.y < 0:
        raise argparse.ArgumentTypeError("mask coordinates must be non-negative")
    if rectangle.width <= 0 or rectangle.height <= 0:
        raise argparse.ArgumentTypeError("mask dimensions must be positive")
    return rectangle


def _unit_interval(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("value must be a number from 0 to 1") from error
    if not math.isfinite(parsed) or not 0.0 <= parsed <= 1.0:
        raise argparse.ArgumentTypeError("value must be a number from 0 to 1")
    return parsed


def _percentage(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("value must be a number from 0 to 100") from error
    if not math.isfinite(parsed) or not 0.0 <= parsed <= 100.0:
        raise argparse.ArgumentTypeError("value must be a number from 0 to 100")
    return parsed


def _channel_delta(value: str) -> int:
    try:
        parsed = int(value, 10)
    except ValueError as error:
        raise argparse.ArgumentTypeError("value must be an integer from 0 to 255") from error
    if not 0 <= parsed <= 255:
        raise argparse.ArgumentTypeError("value must be an integer from 0 to 255")
    return parsed


def _read_image(path_value: str) -> Image.Image:
    path = Path(path_value)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                if image.format not in SUPPORTED_FORMATS:
                    raise InputError("input image format is unsupported")
                width, height = image.size
                if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
                    raise InputError("input image dimensions are unsupported")
                image.load()
                return image.convert("RGB")
    except InputError:
        raise
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        UnidentifiedImageError,
        ValueError,
    ) as error:
        raise InputError("input image is unavailable or invalid") from error


def _comparison_mask(
    size: tuple[int, int], masks: Sequence[MaskRectangle]
) -> tuple[Image.Image, int, int]:
    width, height = size
    included = Image.new("L", size, color=255)
    draw = ImageDraw.Draw(included)
    for rectangle in masks:
        if (
            rectangle.x < 0
            or rectangle.y < 0
            or rectangle.width <= 0
            or rectangle.height <= 0
            or rectangle.x + rectangle.width > width
            or rectangle.y + rectangle.height > height
        ):
            raise InputError("mask rectangle is outside the image dimensions")
        draw.rectangle(
            (
                rectangle.x,
                rectangle.y,
                rectangle.x + rectangle.width - 1,
                rectangle.y + rectangle.height - 1,
            ),
            fill=0,
        )

    mask_histogram = included.histogram()
    compared_pixel_count = mask_histogram[255]
    if compared_pixel_count == 0:
        raise InputError("masks exclude every image pixel")
    total_pixel_count = width * height
    return included, compared_pixel_count, total_pixel_count - compared_pixel_count


def compare_images(
    reference: Image.Image,
    target: Image.Image,
    *,
    masks: Sequence[MaskRectangle] = (),
    pixel_delta_threshold: int = 0,
) -> ComparisonResult:
    """Compare two same-size images and return aggregate metrics only."""

    if not 0 <= pixel_delta_threshold <= 255:
        raise InputError("pixel delta threshold is outside the valid range")
    if reference.size != target.size:
        raise InputError("input image dimensions do not match")
    width, height = reference.size
    if width <= 0 or height <= 0:
        raise InputError("input image dimensions are unsupported")

    reference_rgb = reference.convert("RGB")
    target_rgb = target.convert("RGB")
    included, compared_pixel_count, masked_pixel_count = _comparison_mask(
        reference_rgb.size, masks
    )
    difference = ImageChops.difference(reference_rgb, target_rgb)
    channel_histogram = difference.histogram(mask=included)

    absolute_sum = 0
    squared_sum = 0
    for band in range(3):
        offset = band * 256
        for delta in range(256):
            count = channel_histogram[offset + delta]
            absolute_sum += delta * count
            squared_sum += delta * delta * count

    red, green, blue = difference.split()
    maximum_per_pixel = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    pixel_histogram = maximum_per_pixel.histogram(mask=included)
    maximum_channel_delta = next(
        (delta for delta in range(255, -1, -1) if pixel_histogram[delta]),
        0,
    )
    pixels_over_threshold = sum(pixel_histogram[pixel_delta_threshold + 1 :])

    channel_count = compared_pixel_count * 3
    metrics = ScreenshotMetrics(
        normalized_mae=absolute_sum / channel_count / 255.0,
        normalized_rmse=math.sqrt(squared_sum / channel_count) / 255.0,
        maximum_channel_delta=maximum_channel_delta,
        percent_pixels_over_threshold=(
            pixels_over_threshold / compared_pixel_count * 100.0
        ),
    )
    return ComparisonResult(
        width=width,
        height=height,
        compared_pixel_count=compared_pixel_count,
        masked_pixel_count=masked_pixel_count,
        pixel_delta_threshold=pixel_delta_threshold,
        metrics=metrics,
    )


def compare_files(
    reference_path: str,
    target_path: str,
    *,
    masks: Sequence[MaskRectangle] = (),
    pixel_delta_threshold: int = 0,
) -> ComparisonResult:
    """Read and compare two explicit PNG or JPEG screenshots."""

    reference = _read_image(reference_path)
    target = _read_image(target_path)
    return compare_images(
        reference,
        target,
        masks=masks,
        pixel_delta_threshold=pixel_delta_threshold,
    )


def evaluate_thresholds(
    metrics: ScreenshotMetrics, thresholds: AcceptanceThresholds
) -> dict[str, bool]:
    """Evaluate all acceptance thresholds with inclusive maximums."""

    return {
        "maximum_channel_delta": (
            metrics.maximum_channel_delta <= thresholds.maximum_channel_delta
        ),
        "normalized_mae": metrics.normalized_mae <= thresholds.normalized_mae,
        "normalized_rmse": metrics.normalized_rmse <= thresholds.normalized_rmse,
        "percent_pixels_over_threshold": (
            metrics.percent_pixels_over_threshold
            <= thresholds.percent_pixels_over_threshold
        ),
    }


def _rounded(value: float) -> float:
    return round(value, 12)


def _payload(
    result: ComparisonResult,
    thresholds: AcceptanceThresholds,
    checks: dict[str, bool],
) -> dict[str, object]:
    return {
        "acceptance_thresholds": {
            "maximum_channel_delta": thresholds.maximum_channel_delta,
            "normalized_mae": _rounded(thresholds.normalized_mae),
            "normalized_rmse": _rounded(thresholds.normalized_rmse),
            "percent_pixels_over_threshold": _rounded(
                thresholds.percent_pixels_over_threshold
            ),
        },
        "checks": checks,
        "compared_pixel_count": result.compared_pixel_count,
        "dimensions": {"height": result.height, "width": result.width},
        "masked_pixel_count": result.masked_pixel_count,
        "metrics": {
            "maximum_channel_delta": result.metrics.maximum_channel_delta,
            "normalized_mae": _rounded(result.metrics.normalized_mae),
            "normalized_rmse": _rounded(result.metrics.normalized_rmse),
            "percent_pixels_over_threshold": _rounded(
                result.metrics.percent_pixels_over_threshold
            ),
        },
        "passed": all(checks.values()),
        "pixel_delta_threshold": result.pixel_delta_threshold,
    }


def render_text(payload: dict[str, object]) -> str:
    """Render only dimensions, aggregate metrics, thresholds, and results."""

    dimensions = payload["dimensions"]
    metrics = payload["metrics"]
    thresholds = payload["acceptance_thresholds"]
    checks = payload["checks"]
    lines = [
        "Visual screenshot comparison",
        f"dimensions: {dimensions['width']}x{dimensions['height']}",
        f"compared pixels: {payload['compared_pixel_count']}",
        f"masked pixels: {payload['masked_pixel_count']}",
        f"pixel delta threshold: {payload['pixel_delta_threshold']}",
        f"normalized MAE: {metrics['normalized_mae']:.12f}",
        f"normalized RMSE: {metrics['normalized_rmse']:.12f}",
        f"maximum channel delta: {metrics['maximum_channel_delta']}",
        "percent pixels over threshold: "
        f"{metrics['percent_pixels_over_threshold']:.12f}",
        "acceptance thresholds:",
        f"  normalized MAE: {thresholds['normalized_mae']:.12f}",
        f"  normalized RMSE: {thresholds['normalized_rmse']:.12f}",
        f"  maximum channel delta: {thresholds['maximum_channel_delta']}",
        "  percent pixels over threshold: "
        f"{thresholds['percent_pixels_over_threshold']:.12f}",
        "checks:",
    ]
    for name in (
        "normalized_mae",
        "normalized_rmse",
        "maximum_channel_delta",
        "percent_pixels_over_threshold",
    ):
        lines.append(f"  {name}: " + ("PASS" if checks[name] else "FAIL"))
    lines.append("result: " + ("pass" if payload["passed"] else "mismatch"))
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = PrivacySafeArgumentParser(
        description=(
            "Compare two explicit same-size PNG or JPEG screenshots using "
            "privacy-safe aggregate metrics."
        )
    )
    parser.add_argument("reference_image", metavar="REFERENCE_IMAGE")
    parser.add_argument("target_image", metavar="TARGET_IMAGE")
    parser.add_argument(
        "--mask",
        action="append",
        default=[],
        type=_parse_mask,
        metavar="X,Y,WIDTH,HEIGHT",
        help="exclude a zero-based rectangle; repeat for multiple masks",
    )
    parser.add_argument(
        "--pixel-delta-threshold",
        type=_channel_delta,
        default=0,
        metavar="0..255",
        help="count a pixel when any RGB channel delta is greater than this value",
    )
    parser.add_argument(
        "--max-normalized-mae",
        type=_unit_interval,
        default=0.0,
        metavar="0..1",
    )
    parser.add_argument(
        "--max-normalized-rmse",
        type=_unit_interval,
        default=0.0,
        metavar="0..1",
    )
    parser.add_argument(
        "--max-channel-delta",
        type=_channel_delta,
        default=0,
        metavar="0..255",
    )
    parser.add_argument(
        "--max-percent-pixels-over-threshold",
        type=_percentage,
        default=0.0,
        metavar="0..100",
    )
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    thresholds = AcceptanceThresholds(
        normalized_mae=args.max_normalized_mae,
        normalized_rmse=args.max_normalized_rmse,
        maximum_channel_delta=args.max_channel_delta,
        percent_pixels_over_threshold=args.max_percent_pixels_over_threshold,
    )
    try:
        result = compare_files(
            args.reference_image,
            args.target_image,
            masks=args.mask,
            pixel_delta_threshold=args.pixel_delta_threshold,
        )
    except InputError:
        if args.json:
            print(json.dumps({"error": "input_error"}, sort_keys=True), file=sys.stderr)
        else:
            print("error: screenshot comparison input is invalid", file=sys.stderr)
        return 2

    checks = evaluate_thresholds(result.metrics, thresholds)
    payload = _payload(result, thresholds, checks)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(payload))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
