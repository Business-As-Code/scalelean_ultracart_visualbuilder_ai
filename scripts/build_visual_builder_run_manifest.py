#!/usr/bin/env python3
"""Build a privacy-safe manifest for one Visual Builder evidence run."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
from typing import Iterable, Sequence


SCHEMA_VERSION = "1.0"
SAFE_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,63})?$")
MAX_VIEWPORT_DIMENSION = 100_000
MAX_DEVICE_PIXEL_RATIO = 100.0
READ_CHUNK_BYTES = 1024 * 1024

ARTIFACT_ARGUMENTS = (
    ("checkpoint", "checkpoint"),
    ("cjson", "cjson"),
    ("vm", "vm"),
    ("rendered_html", "rendered-html"),
    ("screenshot", "screenshot"),
)


class ManifestError(ValueError):
    """Report an input or output problem without exposing private values."""


def validate_label(value: str, *, field: str) -> str:
    """Return a safe label or fail without echoing the supplied value."""

    if not SAFE_LABEL.fullmatch(value):
        raise ManifestError(f"{field} is not safe")
    return value


def utc_timestamp() -> str:
    """Return an unambiguous UTC timestamp for the manifest."""

    return datetime.now(UTC).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def parse_artifact_spec(value: str) -> tuple[str, Path]:
    """Parse ROLE=PATH without placing the path in any diagnostic."""

    if "=" not in value:
        raise ManifestError("artifact role input is invalid")
    role, path_value = value.split("=", 1)
    validate_label(role, field="artifact role")
    if not path_value:
        raise ManifestError("artifact role input is invalid")
    return role, Path(path_value)


def hash_artifact(path: Path) -> tuple[str, int]:
    """Hash one regular file without retaining or returning its bytes."""

    digest = hashlib.sha256()
    byte_count = 0
    try:
        with path.open("rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise ManifestError("artifact input is not a regular file")
            while True:
                chunk = handle.read(READ_CHUNK_BYTES)
                if not chunk:
                    break
                digest.update(chunk)
                byte_count += len(chunk)
            after = os.fstat(handle.fileno())
    except ManifestError:
        raise
    except OSError as error:
        raise ManifestError("artifact input is unavailable") from error

    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
        or byte_count != after.st_size
    ):
        raise ManifestError("artifact input changed while it was read")
    return digest.hexdigest(), byte_count


def parse_viewport(
    width_value: str | None,
    height_value: str | None,
    dpr_value: str | None,
) -> dict[str, int | float] | None:
    """Validate optional viewport metadata."""

    if width_value is None and height_value is None and dpr_value is None:
        return None
    if width_value is None or height_value is None:
        raise ManifestError("viewport width and height must be supplied together")

    try:
        width = int(width_value)
        height = int(height_value)
    except ValueError as error:
        raise ManifestError("viewport dimensions are invalid") from error
    if str(width) != width_value or str(height) != height_value:
        raise ManifestError("viewport dimensions are invalid")
    if not 1 <= width <= MAX_VIEWPORT_DIMENSION:
        raise ManifestError("viewport dimensions are invalid")
    if not 1 <= height <= MAX_VIEWPORT_DIMENSION:
        raise ManifestError("viewport dimensions are invalid")

    viewport: dict[str, int | float] = {
        "height_px": height,
        "width_px": width,
    }
    if dpr_value is not None:
        try:
            dpr = float(dpr_value)
        except ValueError as error:
            raise ManifestError("viewport DPR is invalid") from error
        if (
            not math.isfinite(dpr)
            or dpr <= 0
            or dpr > MAX_DEVICE_PIXEL_RATIO
        ):
            raise ManifestError("viewport DPR is invalid")
        viewport["device_pixel_ratio"] = dpr
    return viewport


def collect_artifacts(
    artifact_values: Iterable[tuple[str, Sequence[str]]],
) -> list[dict[str, object]]:
    """Hash explicit artifact roles and return path-free records."""

    records: list[dict[str, object]] = []
    seen_roles: set[tuple[str, str]] = set()
    for artifact_type, values in artifact_values:
        for value in values:
            role, path = parse_artifact_spec(value)
            identity = (artifact_type, role)
            if identity in seen_roles:
                raise ManifestError("artifact role is duplicated for its type")
            seen_roles.add(identity)
            digest, byte_count = hash_artifact(path)
            records.append(
                {
                    "artifact_type": artifact_type,
                    "byte_count": byte_count,
                    "role": role,
                    "sha256": digest,
                }
            )
    records.sort(key=lambda record: (str(record["artifact_type"]), str(record["role"])))
    return records


def build_manifest(
    *,
    run_label: str,
    artifact_values: Iterable[tuple[str, Sequence[str]]],
    logical_stem: str | None = None,
    viewport: dict[str, int | float] | None = None,
    recorded_at_utc: str | None = None,
) -> dict[str, object]:
    """Build one path-free manifest from explicit evidence artifacts."""

    run: dict[str, str] = {
        "label": validate_label(run_label, field="run label"),
        "recorded_at_utc": recorded_at_utc or utc_timestamp(),
    }
    if logical_stem is not None:
        run["logical_stem"] = validate_label(
            logical_stem, field="logical stem"
        )

    artifacts = collect_artifacts(artifact_values)
    manifest: dict[str, object] = {
        "artifact_role_count": len(artifacts),
        "artifacts": artifacts,
        "run": run,
        "schema_version": SCHEMA_VERSION,
    }
    if viewport is not None:
        manifest["viewport"] = viewport
    return manifest


def render_manifest(manifest: dict[str, object]) -> bytes:
    """Return stable UTF-8 bytes for hashing and exclusive storage."""

    return (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_exclusive(output: Path, content: bytes) -> None:
    """Write a new manifest with mode 0600 and never replace a file."""

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(output, flags, 0o600)
    except FileExistsError as error:
        raise ManifestError("output already exists") from error
    except OSError as error:
        raise ManifestError("manifest output could not be created") from error

    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fchmod(handle.fileno(), 0o600)
            os.fsync(handle.fileno())
    except BaseException as error:
        try:
            output.unlink()
        except OSError:
            pass
        if isinstance(error, ManifestError):
            raise
        raise ManifestError("manifest output could not be written") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Write a privacy-safe Visual Builder evidence manifest. Artifact "
            "paths and source bytes are never included in the output."
        )
    )
    parser.add_argument(
        "--run-label",
        required=True,
        help="safe lowercase run label",
    )
    parser.add_argument(
        "--logical-stem",
        help="optional safe logical CJSON and VM stem",
    )
    parser.add_argument("--viewport-width", help="viewport width in CSS pixels")
    parser.add_argument("--viewport-height", help="viewport height in CSS pixels")
    parser.add_argument("--viewport-dpr", help="optional device pixel ratio")
    for destination, option in ARTIFACT_ARGUMENTS:
        parser.add_argument(
            f"--{option}",
            action="append",
            default=[],
            metavar="ROLE=PATH",
            dest=destination,
            help=f"repeatable named {option} artifact",
        )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="explicit new manifest path",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        viewport = parse_viewport(
            args.viewport_width,
            args.viewport_height,
            args.viewport_dpr,
        )
        artifact_values = (
            (destination, getattr(args, destination))
            for destination, _option in ARTIFACT_ARGUMENTS
        )
        manifest = build_manifest(
            run_label=args.run_label,
            artifact_values=artifact_values,
            logical_stem=args.logical_stem,
            viewport=viewport,
        )
        rendered = render_manifest(manifest)
        write_exclusive(args.output, rendered)
    except ManifestError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    digest = hashlib.sha256(rendered).hexdigest()
    print(
        f"roles={manifest['artifact_role_count']} "
        f"manifest_sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
