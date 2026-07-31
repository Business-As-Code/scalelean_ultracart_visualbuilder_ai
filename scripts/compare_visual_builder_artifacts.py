#!/usr/bin/env python3
"""Compare Visual Builder hierarchies without exposing private artifact data."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence

from inspect_visual_builder_artifact import Hierarchy, normalize_hierarchy


MAX_ARTIFACT_BYTES = 128 * 1024 * 1024
MAX_SAFE_SCHEMA_TOKEN_LENGTH = 128
SAFE_SCHEMA_TOKEN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")


class InputError(ValueError):
    """Report an input problem without retaining private data in the message."""


@dataclass(frozen=True)
class LoadedArtifact:
    """A normalized artifact and its decoded top-level document."""

    document: dict[str, Any]
    hierarchy: Hierarchy


def _reject_json_constant(_value: str) -> None:
    raise ValueError("non-finite JSON number")


def load_artifact(path: Path, role: str) -> LoadedArtifact:
    """Read and normalize one artifact without exposing its path or bytes."""

    try:
        with path.open("rb") as handle:
            source = handle.read(MAX_ARTIFACT_BYTES + 1)
    except OSError as error:
        raise InputError(f"{role} artifact is unavailable") from error
    if len(source) > MAX_ARTIFACT_BYTES:
        raise InputError(f"{role} artifact is too large")
    try:
        document = json.loads(
            source.decode("utf-8-sig"), parse_constant=_reject_json_constant
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise InputError(f"{role} artifact is not valid UTF-8 JSON") from error
    try:
        hierarchy = normalize_hierarchy(document)
    except ValueError as error:
        raise InputError(f"{role} artifact is not a supported hierarchy") from error
    _validate_hierarchy(hierarchy, role)
    return LoadedArtifact(document=document, hierarchy=hierarchy)


def _validate_hierarchy(hierarchy: Hierarchy, role: str) -> None:
    """Reject structural ambiguity without exposing affected widget IDs."""

    missing_parent_count = sum(
        1
        for node in hierarchy.nodes.values()
        if node.get("parentWidgetId")
        and node.get("parentWidgetId") not in hierarchy.nodes
    )
    invalid_config_count = sum(
        1
        for node in hierarchy.nodes.values()
        if node.get("config") is not None and not isinstance(node.get("config"), dict)
    )
    invalid_type_count = sum(
        1
        for node in hierarchy.nodes.values()
        if not isinstance(node.get("type"), str) or not node.get("type")
    )
    if (
        hierarchy.duplicate_ids
        or hierarchy.missing_ids
        or hierarchy.integrity_errors
        or missing_parent_count
        or invalid_config_count
        or invalid_type_count
    ):
        raise InputError(f"{role} artifact has invalid hierarchy structure")


def select_reference_hierarchy(
    hierarchy: Hierarchy, reference_root: str | None
) -> Hierarchy:
    """Select exactly one reference root and return only its reachable subtree."""

    if not hierarchy.roots:
        raise InputError("reference artifact has no hierarchy root")
    if reference_root is None:
        if len(hierarchy.roots) != 1:
            raise InputError(
                "reference artifact has multiple roots; --reference-root is required"
            )
        selected_root = hierarchy.roots[0]
    else:
        if reference_root not in hierarchy.roots:
            raise InputError("selected reference root is unavailable or is not a root")
        selected_root = reference_root

    reachable: set[str] = set()
    pending = [selected_root]
    while pending:
        node_id = pending.pop()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        pending.extend(hierarchy.children.get(node_id, []))

    nodes = {node_id: hierarchy.nodes[node_id] for node_id in reachable}
    children = {
        node_id: list(hierarchy.children.get(node_id, []))
        for node_id in reachable
    }
    selected = Hierarchy(
        nodes=nodes,
        children=children,
        roots=[selected_root],
        duplicate_ids=[],
        missing_ids=0,
        integrity_errors=[],
    )
    _validate_hierarchy(selected, "selected reference")
    return selected


def select_target_hierarchy(hierarchy: Hierarchy) -> Hierarchy:
    """Require the target CJSON to describe one hierarchy root."""

    if len(hierarchy.roots) != 1:
        raise InputError("target artifact must contain exactly one hierarchy root")
    return hierarchy


def _parent_map(hierarchy: Hierarchy) -> dict[str, str]:
    parents: dict[str, str] = {}
    for parent_id, child_ids in hierarchy.children.items():
        for child_id in child_ids:
            parents[child_id] = parent_id
    return parents


def _safe_schema_token(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    if not value or len(value) > MAX_SAFE_SCHEMA_TOKEN_LENGTH:
        return None
    if not SAFE_SCHEMA_TOKEN.fullmatch(value):
        return None
    return value


def _count_types(
    node_ids: set[str], nodes: Mapping[str, dict[str, Any]]
) -> tuple[dict[str, int], int]:
    counts: Counter[str] = Counter()
    unreported = 0
    for node_id in node_ids:
        token = _safe_schema_token(nodes[node_id].get("type"))
        if token is None:
            unreported += 1
        else:
            counts[token] += 1
    return dict(sorted(counts.items())), unreported


def _drop_null_mapping_entries(value: Any) -> Any:
    """Recursively make a missing object key equivalent to an explicit null."""

    if isinstance(value, dict):
        return {
            key: _drop_null_mapping_entries(item)
            for key, item in value.items()
            if item is not None
        }
    if isinstance(value, list):
        return [_drop_null_mapping_entries(item) for item in value]
    return value


def _config_for_node(
    node: dict[str, Any],
    ignored_keys: set[str],
    treat_missing_null_equal: bool,
) -> dict[str, Any]:
    raw = node.get("config")
    config = dict(raw) if isinstance(raw, dict) else {}
    for key in ignored_keys:
        config.pop(key, None)
    if treat_missing_null_equal:
        return _drop_null_mapping_entries(config)
    return config


def _exact_json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without Python's bool-to-number coercion."""

    options = {"ensure_ascii": False, "separators": (",", ":"), "sort_keys": True}
    return json.dumps(left, **options) == json.dumps(right, **options)


def _record_config_key_change(
    destination: Counter[str], key: str
) -> int:
    token = _safe_schema_token(key)
    if token is None:
        return 1
    destination[token] += 1
    return 0


def compare_hierarchies(
    reference: Hierarchy,
    target: Hierarchy,
    *,
    ignore_config_keys: Sequence[str] = (),
    treat_missing_null_equal: bool = False,
) -> dict[str, Any]:
    """Return only aggregate and validated schema-key change counts."""

    ignored_keys = set(ignore_config_keys)
    reference_ids = set(reference.nodes)
    target_ids = set(target.nodes)
    missing_ids = reference_ids - target_ids
    excess_ids = target_ids - reference_ids
    common_ids = reference_ids & target_ids

    missing_type_counts, unreported_missing_types = _count_types(
        missing_ids, reference.nodes
    )
    excess_type_counts, unreported_excess_types = _count_types(
        excess_ids, target.nodes
    )

    type_transitions: Counter[str] = Counter()
    type_change_count = 0
    unreported_type_transition_count = 0
    for node_id in common_ids:
        reference_type = reference.nodes[node_id].get("type")
        target_type = target.nodes[node_id].get("type")
        if reference_type == target_type:
            continue
        type_change_count += 1
        safe_reference_type = _safe_schema_token(reference_type)
        safe_target_type = _safe_schema_token(target_type)
        if safe_reference_type is None or safe_target_type is None:
            unreported_type_transition_count += 1
        else:
            type_transitions[f"{safe_reference_type}>{safe_target_type}"] += 1

    reference_parents = _parent_map(reference)
    target_parents = _parent_map(target)
    parent_link_change_count = sum(
        reference_parents.get(node_id) != target_parents.get(node_id)
        for node_id in common_ids
    )
    child_order_change_count = sum(
        reference.children.get(node_id, []) != target.children.get(node_id, [])
        for node_id in common_ids
    )

    config_key_additions: Counter[str] = Counter()
    config_key_removals: Counter[str] = Counter()
    config_value_changes: Counter[str] = Counter()
    unreported_config_key_change_count = 0
    config_key_addition_count = 0
    config_key_removal_count = 0
    config_value_change_count = 0
    widgets_with_config_changes = 0

    for node_id in common_ids:
        reference_config = _config_for_node(
            reference.nodes[node_id], ignored_keys, treat_missing_null_equal
        )
        target_config = _config_for_node(
            target.nodes[node_id], ignored_keys, treat_missing_null_equal
        )
        changed_widget = False
        for key in set(reference_config) | set(target_config):
            if key not in reference_config:
                config_key_addition_count += 1
                changed_widget = True
                unreported_config_key_change_count += _record_config_key_change(
                    config_key_additions, key
                )
            elif key not in target_config:
                config_key_removal_count += 1
                changed_widget = True
                unreported_config_key_change_count += _record_config_key_change(
                    config_key_removals, key
                )
            elif not _exact_json_equal(reference_config[key], target_config[key]):
                config_value_change_count += 1
                changed_widget = True
                unreported_config_key_change_count += _record_config_key_change(
                    config_value_changes, key
                )
        if changed_widget:
            widgets_with_config_changes += 1

    aggregate = {
        "child_order_changes": child_order_change_count,
        "config_key_additions": config_key_addition_count,
        "config_key_removals": config_key_removal_count,
        "config_value_changes": config_value_change_count,
        "excess_nodes": len(excess_ids),
        "missing_nodes": len(missing_ids),
        "parent_link_changes": parent_link_change_count,
        "type_changes": type_change_count,
        "widgets_with_config_changes": widgets_with_config_changes,
    }
    matched = not any(
        aggregate[key]
        for key in (
            "child_order_changes",
            "config_key_additions",
            "config_key_removals",
            "config_value_changes",
            "excess_nodes",
            "missing_nodes",
            "parent_link_changes",
            "type_changes",
        )
    )
    return {
        "aggregate_change_counts": aggregate,
        "matched": matched,
        "normalization": {
            "ignored_config_key_count": len(ignored_keys),
            "treat_missing_null_equal": treat_missing_null_equal,
        },
        "unreported_change_counts": {
            "config_key_changes": unreported_config_key_change_count,
            "excess_node_types": unreported_excess_types,
            "missing_node_types": unreported_missing_types,
            "type_transitions": unreported_type_transition_count,
        },
        "validated_config_key_change_counts": {
            "added": dict(sorted(config_key_additions.items())),
            "removed": dict(sorted(config_key_removals.items())),
            "value_changed": dict(sorted(config_value_changes.items())),
        },
        "validated_type_change_counts": {
            "excess_nodes": excess_type_counts,
            "missing_nodes": missing_type_counts,
            "transitions": dict(sorted(type_transitions.items())),
        },
    }


def render_text(report: dict[str, Any]) -> str:
    aggregate = report["aggregate_change_counts"]
    type_counts = report["validated_type_change_counts"]
    config_counts = report["validated_config_key_change_counts"]
    unreported = report["unreported_change_counts"]

    def format_counts(values: Mapping[str, int]) -> str:
        if not values:
            return "none"
        return ", ".join(f"{key}={value}" for key, value in values.items())

    lines = ["Visual Builder artifact comparison"]
    for key in (
        "missing_nodes",
        "excess_nodes",
        "type_changes",
        "parent_link_changes",
        "child_order_changes",
        "config_key_additions",
        "config_key_removals",
        "config_value_changes",
        "widgets_with_config_changes",
    ):
        lines.append(f"{key.replace('_', ' ').capitalize()}: {aggregate[key]}")
    lines.extend(
        [
            "Validated missing-node type counts: "
            + format_counts(type_counts["missing_nodes"]),
            "Validated excess-node type counts: "
            + format_counts(type_counts["excess_nodes"]),
            "Validated type-transition counts: "
            + format_counts(type_counts["transitions"]),
            "Validated added config-key counts: "
            + format_counts(config_counts["added"]),
            "Validated removed config-key counts: "
            + format_counts(config_counts["removed"]),
            "Validated changed config-key counts: "
            + format_counts(config_counts["value_changed"]),
            "Unreported schema-key change count: " + str(sum(unreported.values())),
            "Ignored config-key count: "
            + str(report["normalization"]["ignored_config_key_count"]),
            "Missing-null equivalence: "
            + ("enabled" if report["normalization"]["treat_missing_null_equal"] else "disabled"),
            "Matched: " + ("yes" if report["matched"] else "no"),
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare an explicit Visual Builder reference checkpoint or CJSON "
            "with an explicit target CJSON. Output excludes paths, widget IDs, "
            "content, URLs, and configuration values."
        )
    )
    parser.add_argument("reference", type=Path, metavar="REFERENCE")
    parser.add_argument("target", type=Path, metavar="TARGET")
    parser.add_argument(
        "--reference-root",
        help="select one root when the reference checkpoint has multiple roots",
    )
    parser.add_argument(
        "--ignore-config-key",
        action="append",
        default=[],
        metavar="KEY",
        help="ignore an exact top-level config key; repeat as needed",
    )
    parser.add_argument(
        "--treat-missing-null-equal",
        action="store_true",
        help="treat missing object keys and explicit null values as equal",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if any(not key for key in args.ignore_config_key):
            raise InputError("ignored config keys must be non-empty")
        reference = load_artifact(args.reference, "reference")
        target = load_artifact(args.target, "target")
        selected_reference = select_reference_hierarchy(
            reference.hierarchy, args.reference_root
        )
        selected_target = select_target_hierarchy(target.hierarchy)
        report = compare_hierarchies(
            selected_reference,
            selected_target,
            ignore_config_keys=args.ignore_config_key,
            treat_missing_null_equal=args.treat_missing_null_equal,
        )
    except InputError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0 if report["matched"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
