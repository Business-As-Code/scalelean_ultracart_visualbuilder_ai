#!/usr/bin/env python3
"""Query the private normalized SFVB registry without exposing source files."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Mapping

from validate_cjson_against_registry import classify_placement


class RegistryQueryError(Exception):
    """Report a missing or malformed source-registry query."""


def _element_map(registry: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    elements = registry.get("elements")
    if not isinstance(elements, list):
        raise RegistryQueryError("registry element list is invalid")
    result: dict[str, Mapping[str, Any]] = {}
    for element in elements:
        if not isinstance(element, dict) or not isinstance(element.get("type"), str):
            raise RegistryQueryError("registry contains an invalid element")
        result[element["type"]] = element
    return result


def _get_element(registry: Mapping[str, Any], element_type: str) -> Mapping[str, Any]:
    element = _element_map(registry).get(element_type)
    if element is None:
        raise RegistryQueryError("element type is not in the closed registry")
    return element


def element_summary(registry: Mapping[str, Any], element_type: str) -> dict[str, Any]:
    element = _get_element(registry, element_type)
    placement = element.get("placement", {})
    settings = element.get("settings", [])
    anomalies = registry.get("anomalies", {}).get("records", [])
    return {
        "type": element_type,
        "friendly_name": element.get("friendly_name"),
        "widget_group": element.get("widget_group"),
        "status": element.get("status"),
        "flags": element.get("flags"),
        "child_model": placement.get("child_model"),
        "documented_parents": placement.get("frontmatter_parents", []),
        "documented_children": placement.get("frontmatter_children", []),
        "settings_count": element.get("settings_count"),
        "setting_keys": [
            setting.get("key") for setting in settings if isinstance(setting, dict)
        ],
        "reference_setting_keys": element.get("reference_setting_keys", []),
        "source_anomaly_counts": _anomaly_counts(anomalies, element_type),
        "source_hashes": element.get("source_hashes"),
    }


def _anomaly_counts(records: Any, element_type: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not isinstance(records, list):
        return counts
    for record in records:
        if not isinstance(record, dict) or record.get("element") != element_type:
            continue
        kind = record.get("kind")
        if isinstance(kind, str):
            counts[kind] = counts.get(kind, 0) + 1
    return dict(sorted(counts.items()))


def setting_summary(
    registry: Mapping[str, Any], element_type: str, setting_key: str
) -> dict[str, Any]:
    element = _get_element(registry, element_type)
    settings = element.get("settings")
    if not isinstance(settings, list):
        raise RegistryQueryError("element setting list is invalid")
    setting = next(
        (
            item
            for item in settings
            if isinstance(item, dict) and item.get("key") == setting_key
        ),
        None,
    )
    if setting is None:
        raise RegistryQueryError("setting is not defined for the selected element")
    return {
        "element_type": element_type,
        "setting": setting,
        "responsive_value_keys": registry.get("authoring_contract", {}).get(
            "responsive_value_keys", []
        ),
        "scoped_style_keys": registry.get("authoring_contract", {}).get(
            "scoped_style_keys", []
        ),
    }


def placement_candidates(
    registry: Mapping[str, Any],
    element_type: str,
    *,
    direction: str,
) -> dict[str, Any]:
    if direction not in {"children", "parents"}:
        raise RegistryQueryError("placement direction must be children or parents")
    elements = _element_map(registry)
    selected = elements.get(element_type)
    if selected is None:
        raise RegistryQueryError("element type is not in the closed registry")
    groups: dict[str, list[str]] = {
        "bilateral": [],
        "unilateral": [],
        "contradicted": [],
        "unknown": [],
        "denied": [],
    }
    for candidate_type, candidate in elements.items():
        if direction == "children":
            status = classify_placement(selected, candidate)
        else:
            status = classify_placement(candidate, selected)
        groups[status].append(candidate_type)
    return {
        "type": element_type,
        "direction": direction,
        "candidates": {
            status: sorted(values) for status, values in groups.items() if values
        },
        "counts": {status: len(values) for status, values in groups.items()},
        "authoring_rule": "bilateral only; all other statuses require reconciliation",
    }


def search_elements(registry: Mapping[str, Any], query: str) -> dict[str, Any]:
    normalized = query.casefold().strip()
    if not normalized:
        raise RegistryQueryError("search query must not be empty")
    matches = []
    for element in _element_map(registry).values():
        fields = [
            element.get("type"),
            element.get("friendly_name"),
            element.get("widget_group"),
            *(element.get("tags") or []),
        ]
        haystack = " ".join(str(value) for value in fields if value is not None).casefold()
        if normalized in haystack:
            matches.append(
                {
                    "type": element.get("type"),
                    "friendly_name": element.get("friendly_name"),
                    "widget_group": element.get("widget_group"),
                    "child_model": element.get("placement", {}).get("child_model"),
                    "settings_count": element.get("settings_count"),
                }
            )
    return {"query": query, "match_count": len(matches), "matches": matches}


def prose_summary(registry: Mapping[str, Any], element_type: str) -> dict[str, Any]:
    element = _get_element(registry, element_type)
    return {
        "type": element_type,
        "placement_signals": {
            "allowed_under": element.get("placement", {}).get(
                "allowed_under_signals", []
            ),
            "allowed_child": element.get("placement", {}).get(
                "allowed_child_signals", []
            ),
            "other_rules": element.get("placement", {}).get("other_rules", ""),
            "context_sentences": element.get("placement", {}).get(
                "context_sentences", []
            ),
        },
        "selected_documentation": element.get("documentation", {}).get(
            "selected_sections", {}
        ),
        "supplier_warnings": element.get("supplier_warnings", []),
    }


def _load_registry(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RegistryQueryError("private registry could not be read") from exc
    if not isinstance(value, dict):
        raise RegistryQueryError("private registry root is invalid")
    return value


def _require_private_registry(path: Path) -> None:
    private_root_value = os.environ.get("UVB_PRIVATE_ARTIFACT_ROOT")
    if not private_root_value:
        raise RegistryQueryError("UVB_PRIVATE_ARTIFACT_ROOT is required")
    try:
        path.resolve().relative_to(Path(private_root_value).resolve())
    except ValueError as exc:
        raise RegistryQueryError("registry must stay inside the private artifact root") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    element_parser = subparsers.add_parser("element")
    element_parser.add_argument("element_type")
    setting_parser = subparsers.add_parser("setting")
    setting_parser.add_argument("element_type")
    setting_parser.add_argument("setting_key")
    children_parser = subparsers.add_parser("children")
    children_parser.add_argument("element_type")
    parents_parser = subparsers.add_parser("parents")
    parents_parser.add_argument("element_type")
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    prose_parser = subparsers.add_parser("prose")
    prose_parser.add_argument("element_type")
    args = parser.parse_args()
    _require_private_registry(args.registry)
    registry = _load_registry(args.registry)
    if args.command == "element":
        result = element_summary(registry, args.element_type)
    elif args.command == "setting":
        result = setting_summary(registry, args.element_type, args.setting_key)
    elif args.command == "children":
        result = placement_candidates(registry, args.element_type, direction="children")
    elif args.command == "parents":
        result = placement_candidates(registry, args.element_type, direction="parents")
    elif args.command == "search":
        result = search_elements(registry, args.query)
    else:
        result = prose_summary(registry, args.element_type)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
