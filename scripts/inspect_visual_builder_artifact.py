#!/usr/bin/env python3
"""Inspect an UltraCart Visual Builder hierarchy without exposing content values."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable


RESPONSIVE_KEY = re.compile(r"(?:Small|Medium|Large)$", re.IGNORECASE)
WIDGET_ID = re.compile(r"^[a-z][a-z0-9_-]*-[a-z0-9_-]+$", re.IGNORECASE)
REFERENCE_CONFIG_KEY = re.compile(
    r"(?:"
    r"(?:parent|child|source|target|clone)?widget(?:id|ids|ref|refs|reference|references)?"
    r"|childwidgets"
    r"|editmodeselected(?:tab|slide)"
    r"|clone(?:root|source)(?:id)?"
    r")$",
    re.IGNORECASE,
)
VISIBILITY_KEYS = {
    "hidden",
    "hideAncestorIfEmpty",
    "buttonHideThese",
    "buttonShowThese",
    "showOn",
}


@dataclass(frozen=True)
class Hierarchy:
    nodes: dict[str, dict[str, Any]]
    children: dict[str, list[str]]
    roots: list[str]
    duplicate_ids: list[str]
    missing_ids: int
    integrity_errors: list[str]


def child_id(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and isinstance(value.get("id"), str):
        return value["id"]
    return None


def _graph_integrity_errors(
    nodes: dict[str, dict[str, Any]],
    children: dict[str, list[str]],
) -> tuple[list[str], dict[str, set[str]]]:
    errors: list[str] = []
    referenced_parents: dict[str, set[str]] = defaultdict(set)

    for parent_id, child_ids in children.items():
        seen: set[str] = set()
        for item in child_ids:
            if item in seen:
                errors.append(f"{parent_id} contains duplicate child {item}")
            seen.add(item)
            if item in nodes:
                referenced_parents[item].add(parent_id)

    for node_id, parent_ids in referenced_parents.items():
        if len(parent_ids) > 1:
            errors.append(
                f"{node_id} is referenced by multiple parents: "
                + ", ".join(sorted(parent_ids))
            )

    for node_id, node in nodes.items():
        declared_parent = node.get("parentWidgetId")
        actual_parents = referenced_parents.get(node_id, set())
        if declared_parent and declared_parent in nodes:
            if declared_parent not in actual_parents:
                errors.append(
                    f"{node_id} declares parent {declared_parent!r}, but that parent "
                    "does not reference it"
                )
        if len(actual_parents) == 1 and declared_parent:
            actual_parent = next(iter(actual_parents))
            if declared_parent != actual_parent:
                errors.append(
                    f"{node_id} declares parent {declared_parent!r}, "
                    f"expected {actual_parent!r}"
                )

    state: dict[str, int] = {}

    def visit(node_id: str) -> None:
        current_state = state.get(node_id, 0)
        if current_state == 1:
            errors.append("hierarchy cycle detected")
            return
        if current_state == 2:
            return
        state[node_id] = 1
        for item in children.get(node_id, []):
            if item in nodes:
                visit(item)
        state[node_id] = 2

    for node_id in nodes:
        visit(node_id)
    return sorted(set(errors)), referenced_parents


def _from_widget_map(widget_map: dict[str, Any]) -> Hierarchy:
    nodes: dict[str, dict[str, Any]] = {}
    children: dict[str, list[str]] = {}
    errors: list[str] = []
    missing_ids = 0

    for map_id, raw_node in widget_map.items():
        if not isinstance(raw_node, dict):
            errors.append(f"widget map entry {map_id!r} is not an object")
            continue
        node_id = raw_node.get("id")
        if not isinstance(node_id, str) or not node_id:
            missing_ids += 1
            continue
        if node_id != map_id:
            errors.append(f"widget map key {map_id!r} does not match id {node_id!r}")
        nodes[node_id] = raw_node
        child_ids = [child_id(item) for item in raw_node.get("childWidgets") or []]
        children[node_id] = [item for item in child_ids if item]

    for parent_id, child_ids in children.items():
        for item in child_ids:
            if item not in nodes:
                errors.append(f"{parent_id} references missing child {item}")

    graph_errors, referenced_parents = _graph_integrity_errors(nodes, children)
    errors.extend(graph_errors)
    roots = sorted(
        node_id
        for node_id in nodes
        if not referenced_parents.get(node_id)
    )
    return Hierarchy(nodes, children, roots, [], missing_ids, sorted(set(errors)))


def _from_nested_roots(roots_to_walk: list[dict[str, Any]]) -> Hierarchy:
    nodes: dict[str, dict[str, Any]] = {}
    children: dict[str, list[str]] = defaultdict(list)
    duplicate_ids: list[str] = []
    errors: list[str] = []
    missing_ids = 0

    def walk(node: Any, traversal_parent: str | None) -> None:
        nonlocal missing_ids
        if not isinstance(node, dict):
            errors.append("childWidgets contains a non-object child")
            return
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id:
            missing_ids += 1
            return
        if node_id in nodes:
            duplicate_ids.append(node_id)
            return
        nodes[node_id] = node
        declared_parent = node.get("parentWidgetId")
        if traversal_parent and declared_parent not in {None, traversal_parent}:
            errors.append(
                f"{node_id} declares parent {declared_parent!r}, expected {traversal_parent!r}"
            )
        for raw_child in node.get("childWidgets") or []:
            item = child_id(raw_child)
            if item:
                children[node_id].append(item)
            walk(raw_child, node_id)

    roots: list[str] = []
    for root in roots_to_walk:
        root_id = root.get("id")
        if isinstance(root_id, str) and root_id:
            roots.append(root_id)
        walk(root, None)
    graph_errors, referenced_parents = _graph_integrity_errors(nodes, dict(children))
    errors.extend(graph_errors)
    inferred_roots = sorted(
        node_id for node_id in nodes if not referenced_parents.get(node_id)
    )
    if sorted(set(roots)) != inferred_roots:
        errors.append("declared roots do not match the traversed hierarchy")
    return Hierarchy(
        nodes,
        dict(children),
        roots,
        sorted(set(duplicate_ids)),
        missing_ids,
        sorted(set(errors)),
    )


def normalize_hierarchy(document: Any) -> Hierarchy:
    if not isinstance(document, dict):
        raise ValueError("artifact root must be a JSON object")
    widget_map = document.get("widgets")
    if isinstance(widget_map, dict):
        return _from_widget_map(widget_map)
    container_map = document.get("containers")
    if isinstance(container_map, dict):
        roots = [value for value in container_map.values() if isinstance(value, dict)]
        if len(roots) != len(container_map):
            raise ValueError("containers checkpoint contains a non-object root")
        return _from_nested_roots(roots)
    if isinstance(document.get("id"), str):
        return _from_nested_roots([document])
    raise ValueError(
        "artifact is neither a nested CJSON root nor a browser hierarchy checkpoint"
    )


def visibility_keys(config: dict[str, Any]) -> set[str]:
    return {
        key
        for key in config
        if key in VISIBILITY_KEYS or key.lower().startswith(("hideif", "showif"))
    }


def referenced_widget_ids(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        for token in re.split(r"[\s,;]+", value):
            if WIDGET_ID.fullmatch(token):
                yield token
    elif isinstance(value, list):
        for item in value:
            yield from referenced_widget_ids(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from referenced_widget_ids(item)


def summarize(hierarchy: Hierarchy) -> dict[str, Any]:
    type_counts = Counter(str(node.get("type") or "<unknown>") for node in hierarchy.nodes.values())
    observed_child_bearing = Counter(
        str(hierarchy.nodes[node_id].get("type") or "<unknown>")
        for node_id, child_ids in hierarchy.children.items()
        if child_ids and node_id in hierarchy.nodes
    )
    parent_child_edges: Counter[str] = Counter()
    for parent_id, child_ids in hierarchy.children.items():
        parent = hierarchy.nodes.get(parent_id)
        if parent is None:
            continue
        parent_type = str(parent.get("type") or "<unknown>")
        for item in child_ids:
            child = hierarchy.nodes.get(item)
            if child is None:
                continue
            child_type = str(child.get("type") or "<unknown>")
            parent_child_edges[f"{parent_type}>{child_type}"] += 1
    responsive: dict[str, set[str]] = defaultdict(set)
    visibility: dict[str, set[str]] = defaultdict(set)
    references: dict[str, set[str]] = defaultdict(set)
    config_keys: dict[str, set[str]] = defaultdict(set)

    for node_id, node in hierarchy.nodes.items():
        widget_type = str(node.get("type") or "<unknown>")
        config = node.get("config") or {}
        if not isinstance(config, dict):
            continue
        config_keys[widget_type].update(config)
        responsive[widget_type].update(
            key for key in config if key == "showOn" or RESPONSIVE_KEY.search(key)
        )
        visibility[widget_type].update(visibility_keys(config))
        for key, value in config.items():
            if not REFERENCE_CONFIG_KEY.search(str(key)):
                continue
            targets = set(referenced_widget_ids(value))
            if targets:
                references[f"{widget_type}.{key}"].update(targets)

    missing_parent_targets = sorted(
        {
            str(node.get("parentWidgetId"))
            for node in hierarchy.nodes.values()
            if node.get("parentWidgetId")
            and node.get("parentWidgetId") not in hierarchy.nodes
        }
    )
    referenced_ids = sorted({target for targets in references.values() for target in targets})
    missing_reference_targets = sorted(set(referenced_ids) - set(hierarchy.nodes))

    return {
        "widget_count": len(hierarchy.nodes),
        "root_ids": hierarchy.roots,
        "type_counts": dict(sorted(type_counts.items())),
        "observed_child_bearing_type_counts": dict(
            sorted(observed_child_bearing.items())
        ),
        "parent_child_type_edge_counts": dict(sorted(parent_child_edges.items())),
        "config_keys_by_type": {
            key: sorted(value) for key, value in sorted(config_keys.items())
        },
        "responsive_keys_by_type": {
            key: sorted(value) for key, value in sorted(responsive.items()) if value
        },
        "visibility_keys_by_type": {
            key: sorted(value) for key, value in sorted(visibility.items()) if value
        },
        "widget_reference_key_counts": {
            key: len(value) for key, value in sorted(references.items())
        },
        "duplicate_ids": hierarchy.duplicate_ids,
        "missing_id_count": hierarchy.missing_ids,
        "missing_parent_targets": missing_parent_targets,
        "missing_reference_targets": missing_reference_targets,
        "integrity_errors": hierarchy.integrity_errors,
    }


def parse_relation(value: str, option: str) -> tuple[str, str]:
    if "=" not in value:
        raise ValueError(f"{option} must use CHILD=PARENT")
    left, right = value.split("=", 1)
    if not left or not right:
        raise ValueError(f"{option} must use non-empty identifiers")
    return left, right


def validate_expectations(
    hierarchy: Hierarchy,
    present: list[str] | None = None,
    parent_relations: list[str] | None = None,
    exact_orders: list[str] | None = None,
    type_relations: list[str] | None = None,
    absent_children: list[str] | None = None,
    config_expectations: list[str] | None = None,
) -> list[str]:
    failures: list[str] = []
    for node_id in present or []:
        if node_id not in hierarchy.nodes:
            failures.append(f"expected widget is absent: {node_id}")
    for relation in parent_relations or []:
        child, parent = parse_relation(relation, "--expect-parent")
        node = hierarchy.nodes.get(child)
        if node is None:
            failures.append(f"expected child is absent: {child}")
        elif node.get("parentWidgetId") != parent:
            failures.append(
                f"expected {child} parent {parent}, found {node.get('parentWidgetId')!r}"
            )
    for relation in exact_orders or []:
        parent, csv = parse_relation(relation, "--expect-order")
        expected = [item for item in csv.split(",") if item]
        actual = hierarchy.children.get(parent, [])
        if actual != expected:
            failures.append(f"expected {parent} order {expected}, found {actual}")
    for relation in type_relations or []:
        node_id, expected_type = parse_relation(relation, "--expect-type")
        node = hierarchy.nodes.get(node_id)
        if node is None:
            failures.append(f"expected typed widget is absent: {node_id}")
        elif node.get("type") != expected_type:
            failures.append(
                f"expected {node_id} type {expected_type}, found {node.get('type')!r}"
            )
    for relation in absent_children or []:
        parent, prohibited_child = parse_relation(relation, "--expect-absent-child")
        if prohibited_child in hierarchy.children.get(parent, []):
            failures.append(f"expected {parent} not to contain {prohibited_child}")
    for expectation in config_expectations or []:
        target, raw_expected = parse_relation(expectation, "--expect-config")
        widget_id, separator, config_key = target.partition(".")
        if not separator or not widget_id or not config_key:
            raise ValueError("--expect-config must use WIDGET.KEY=JSON_VALUE")
        try:
            expected_value = json.loads(raw_expected)
        except json.JSONDecodeError as error:
            raise ValueError(
                "--expect-config value must be valid JSON, including quotes for strings"
            ) from error
        node = hierarchy.nodes.get(widget_id)
        if node is None:
            failures.append(f"expected configured widget is absent: {widget_id}")
            continue
        config = node.get("config") or {}
        actual_value = config.get(config_key) if isinstance(config, dict) else None
        if actual_value != expected_value:
            failures.append(
                f"expected {widget_id}.{config_key}={expected_value!r}, "
                f"found {actual_value!r}"
            )
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize a private Visual Builder CJSON or browser checkpoint. "
            "Content values are never printed."
        )
    )
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--expect-present", action="append", default=[])
    parser.add_argument(
        "--expect-parent",
        action="append",
        default=[],
        metavar="CHILD=PARENT",
    )
    parser.add_argument(
        "--expect-order",
        action="append",
        default=[],
        metavar="PARENT=CHILD1,CHILD2",
    )
    parser.add_argument(
        "--expect-type",
        action="append",
        default=[],
        metavar="WIDGET=TYPE",
    )
    parser.add_argument(
        "--expect-absent-child",
        action="append",
        default=[],
        metavar="PARENT=CHILD",
    )
    parser.add_argument(
        "--expect-config",
        action="append",
        default=[],
        metavar="WIDGET.KEY=JSON_VALUE",
    )
    return parser.parse_args()


def human_summary(summary: dict[str, Any], failures: list[str]) -> str:
    lines = [
        f"Widgets: {summary['widget_count']}",
        "Roots: " + (", ".join(summary["root_ids"]) or "none"),
        f"Widget types: {len(summary['type_counts'])}",
        "Observed child-bearing types: "
        + (", ".join(summary["observed_child_bearing_type_counts"]) or "none"),
        f"Observed parent-to-child type edges: {len(summary['parent_child_type_edge_counts'])}",
        "Responsive types: "
        + (", ".join(summary["responsive_keys_by_type"]) or "none"),
        "Visibility mechanisms: "
        + (", ".join(summary["visibility_keys_by_type"]) or "none"),
    ]
    integrity_count = (
        len(summary["duplicate_ids"])
        + summary["missing_id_count"]
        + len(summary["missing_parent_targets"])
        + len(summary["integrity_errors"])
    )
    lines.append(f"Hierarchy integrity failures: {integrity_count}")
    lines.append(f"Expectation failures: {len(failures)}")
    lines.extend(f"FAIL: {failure}" for failure in failures)
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        document = json.loads(args.artifact.read_text(encoding="utf-8"))
        hierarchy = normalize_hierarchy(document)
        report = summarize(hierarchy)
        failures = validate_expectations(
            hierarchy,
            args.expect_present,
            args.expect_parent,
            args.expect_order,
            args.expect_type,
            args.expect_absent_child,
            args.expect_config,
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Inspection failed: {error}", file=sys.stderr)
        return 2

    if args.json:
        report["expectation_failures"] = failures
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(human_summary(report, failures))
    has_integrity_failure = bool(
        report["duplicate_ids"]
        or report["missing_id_count"]
        or report["missing_parent_targets"]
        or report["integrity_errors"]
    )
    return 1 if has_integrity_failure or failures else 0


if __name__ == "__main__":
    sys.exit(main())
