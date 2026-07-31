#!/usr/bin/env python3
"""Validate and privately store an exact Visual Builder browser checkpoint."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Sequence

from capture_ftps_listing import load_config, private_directory
from inspect_visual_builder_artifact import Hierarchy, normalize_hierarchy


SAFE_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,47})?$")
CHECKPOINT_DIRECTORY = "browser-checkpoints"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a Visual Builder CJSON or browser checkpoint and copy its "
            "exact bytes into configured private storage."
        )
    )
    parser.add_argument("artifact", type=Path)
    parser.add_argument(
        "--label",
        help=(
            "Optional lowercase label using only letters, digits, hyphens, "
            "or underscores."
        ),
    )
    return parser.parse_args(argv)


def validate_label(value: str | None) -> str | None:
    if value is None:
        return None
    if not SAFE_LABEL.fullmatch(value):
        raise ValueError("label is not safe")
    return value


def validate_hierarchy(raw_bytes: bytes) -> Hierarchy:
    try:
        document = json.loads(raw_bytes)
        hierarchy = normalize_hierarchy(document)
    except (
        AttributeError,
        KeyError,
        TypeError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
        RecursionError,
    ) as error:
        raise ValueError("checkpoint validation failed") from error

    if (
        not hierarchy.nodes
        or not hierarchy.roots
        or hierarchy.duplicate_ids
        or hierarchy.missing_ids
        or hierarchy.integrity_errors
    ):
        raise ValueError("checkpoint validation failed")
    return hierarchy


def timestamp_token() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def checkpoint_directory(private_root: Path) -> Path:
    resolved_root = private_root.resolve()
    directory = resolved_root / CHECKPOINT_DIRECTORY
    if directory.exists():
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("private checkpoint directory is invalid")
    else:
        directory.mkdir(mode=0o700)
    if directory.resolve() != directory or directory.parent != resolved_root:
        raise ValueError("private checkpoint directory is invalid")
    directory.chmod(0o700)
    return directory


def destination_name(label: str | None, collision: int = 0) -> str:
    parts = ["browser-checkpoint", timestamp_token()]
    if label:
        parts.append(label)
    if collision:
        parts.append(f"{collision:03d}")
    return "-".join(parts) + ".json"


def store_exact_bytes(directory: Path, raw_bytes: bytes, label: str | None) -> Path:
    collision = 0
    while True:
        destination = directory / destination_name(label, collision)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(destination, flags, 0o600)
        except FileExistsError:
            collision += 1
            continue
        try:
            with os.fdopen(descriptor, "wb") as output:
                output.write(raw_bytes)
                output.flush()
                os.fsync(output.fileno())
            destination.chmod(0o600)
        except BaseException:
            try:
                destination.unlink()
            except OSError:
                pass
            raise
        return destination


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        label = validate_label(args.label)
    except ValueError:
        print("Checkpoint not stored: label is not safe.", file=sys.stderr)
        return 2

    config = load_config()
    if not config.get("UVB_PRIVATE_ARTIFACT_ROOT", "").strip():
        print(
            "Checkpoint not stored: private artifact storage is not configured.",
            file=sys.stderr,
        )
        return 2

    try:
        raw_bytes = args.artifact.read_bytes()
        hierarchy = validate_hierarchy(raw_bytes)
    except (OSError, ValueError):
        print("Checkpoint not stored: input validation failed.", file=sys.stderr)
        return 2

    try:
        private_root = private_directory(config)
        directory = checkpoint_directory(private_root)
        store_exact_bytes(directory, raw_bytes, label)
    except (OSError, ValueError):
        print("Checkpoint not stored: private storage failed.", file=sys.stderr)
        return 1

    digest = hashlib.sha256(raw_bytes).hexdigest()
    print(
        f"widgets={len(hierarchy.nodes)} roots={len(hierarchy.roots)} "
        f"sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
