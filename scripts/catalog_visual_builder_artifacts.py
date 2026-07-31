#!/usr/bin/env python3
"""Build a privacy-safe aggregate catalog from Visual Builder artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from inspect_visual_builder_artifact import Hierarchy, normalize_hierarchy


SCHEMA_VERSION = "1.0"
UNKNOWN_TYPE = "<unknown>"


class CatalogError(Exception):
    """Report an artifact error without retaining or displaying its path."""


def widget_type(node: dict[str, Any]) -> str:
    """Return the schema type used for aggregate catalog keys."""

    value = node.get("type")
    return value if isinstance(value, str) and value else UNKNOWN_TYPE


def load_artifact(path: Path, position: int) -> tuple[bytes, Hierarchy]:
    """Load one artifact and normalize its hierarchy without path disclosure."""

    try:
        source = path.read_bytes()
    except OSError as exc:
        raise CatalogError(f"could not read artifact at input position {position}") from exc

    try:
        document = json.loads(source.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CatalogError(
            f"artifact at input position {position} is not valid UTF-8 JSON"
        ) from exc

    try:
        hierarchy = normalize_hierarchy(document)
    except ValueError as exc:
        raise CatalogError(
            f"artifact at input position {position} is not a supported hierarchy"
        ) from exc
    return source, hierarchy


def add_hierarchy(
    hierarchy: Hierarchy,
    type_instance_counts: Counter[str],
    observed_child_types: dict[str, set[str]],
    config_keys_by_type: dict[str, set[str]],
    edge_counts: Counter[str],
) -> None:
    """Accumulate type-level evidence from one normalized hierarchy."""

    for node in hierarchy.nodes.values():
        current_type = widget_type(node)
        type_instance_counts[current_type] += 1
        config = node.get("config")
        if isinstance(config, dict):
            config_keys_by_type[current_type].update(str(key) for key in config)

    for parent_id, child_ids in hierarchy.children.items():
        parent = hierarchy.nodes.get(parent_id)
        if parent is None:
            continue
        parent_type = widget_type(parent)
        for child_id in child_ids:
            child = hierarchy.nodes.get(child_id)
            if child is None:
                continue
            child_type = widget_type(child)
            observed_child_types[parent_type].add(child_type)
            edge_counts[f"{parent_type}>{child_type}"] += 1


def build_catalog(
    paths: Sequence[Path], *, allow_duplicates: bool = False
) -> dict[str, Any]:
    """Build a deterministic catalog without source paths, IDs, or values."""

    if not paths:
        raise ValueError("at least one artifact is required")

    loaded: list[tuple[str, Hierarchy]] = []
    seen_hashes: set[str] = set()
    duplicate_count = 0

    for position, path in enumerate(paths, start=1):
        source, hierarchy = load_artifact(path, position)
        digest = hashlib.sha256(source).hexdigest()
        if digest in seen_hashes:
            duplicate_count += 1
            if not allow_duplicates:
                continue
        seen_hashes.add(digest)
        loaded.append((digest, hierarchy))

    # Hash ordering makes output independent of command-line path order.
    loaded.sort(key=lambda item: item[0])

    type_instance_counts: Counter[str] = Counter()
    observed_child_types: dict[str, set[str]] = defaultdict(set)
    config_keys_by_type: dict[str, set[str]] = defaultdict(set)
    edge_counts: Counter[str] = Counter()

    widget_count = 0
    root_count = 0
    duplicate_id_count = 0
    missing_id_count = 0
    integrity_error_count = 0

    for _digest, hierarchy in loaded:
        widget_count += len(hierarchy.nodes)
        root_count += len(hierarchy.roots)
        duplicate_id_count += len(hierarchy.duplicate_ids)
        missing_id_count += hierarchy.missing_ids
        integrity_error_count += len(hierarchy.integrity_errors)
        add_hierarchy(
            hierarchy,
            type_instance_counts,
            observed_child_types,
            config_keys_by_type,
            edge_counts,
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "evidence_counts": {
            "input_artifact_count": len(paths),
            "cataloged_artifact_count": len(loaded),
            "duplicate_artifact_count": duplicate_count,
            "widget_instance_count": widget_count,
            "root_count": root_count,
            "duplicate_widget_id_count": duplicate_id_count,
            "missing_widget_id_count": missing_id_count,
            "integrity_error_count": integrity_error_count,
        },
        "artifact_sha256": [digest for digest, _hierarchy in loaded],
        "type_instance_counts": dict(sorted(type_instance_counts.items())),
        "observed_child_types": {
            key: sorted(value) for key, value in sorted(observed_child_types.items())
        },
        "config_key_unions": {
            key: sorted(value) for key, value in sorted(config_keys_by_type.items())
        },
        "parent_to_child_type_edge_counts": dict(sorted(edge_counts.items())),
    }


def render_catalog(catalog: dict[str, Any]) -> str:
    """Serialize a catalog in a stable form."""

    return json.dumps(catalog, indent=2, sort_keys=True) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create an aggregate Visual Builder structure catalog. The output "
            "excludes paths, widget IDs, content values, URLs, and source bytes."
        )
    )
    parser.add_argument(
        "artifacts",
        nargs="+",
        type=Path,
        metavar="ARTIFACT",
        help="explicit CJSON or browser checkpoint path",
    )
    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="count byte-identical artifacts more than once",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write the safe catalog to this path instead of stdout",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        catalog = build_catalog(
            args.artifacts, allow_duplicates=args.allow_duplicates
        )
        rendered = render_catalog(catalog)
        if args.output is None:
            sys.stdout.write(rendered)
        else:
            args.output.write_text(rendered, encoding="utf-8")
    except CatalogError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError:
        print("error: could not write catalog output", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
