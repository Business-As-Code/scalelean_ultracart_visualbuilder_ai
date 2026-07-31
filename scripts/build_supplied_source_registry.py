#!/usr/bin/env python3
"""Build a normalized private registry from an UltraCart SFVB agent bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


REGISTRY_KIND = "ultracart_visual_builder_source_registry"
REGISTRY_SCHEMA_VERSION = 1
RESPONSIVE_KEYS = ("small", "medium", "large")
SCOPED_STYLE_KEYS = (
    "all",
    "small-only",
    "medium-only",
    "medium-up",
    "large-only",
    "xlarge-up",
    "xxlarge-up",
)
BOOKKEEPING_CONFIG_KEYS = ("hidden", "lock", "inheritGroups")
TRANSIENT_CONFIG_KEYS = ("modalOpen", "sidepanelOpen", "contextSourceHash")
EXPECTED_DOC_SECTIONS = (
    "Identity",
    "Purpose & when to use",
    "Placement",
    "Configuration",
    "Runtime behavior",
    "Rendering & CSS",
    "Interactions with sibling elements",
    "Recipes",
    "Gotchas & degradation",
    "See also",
)
REFERENCE_FORMATS = {"widget-id"}
REFERENCE_EDITOR_TYPES = {"parentWidget", "widget", "widgets"}
GENERATED_SCHEMA_BLOCK = re.compile(
    r"<!-- BEGIN GENERATED SCHEMA:.*?<!-- END GENERATED SCHEMA:.*?-->",
    re.DOTALL,
)
SECTION_HEADING = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
PLACEMENT_LINE = re.compile(
    r"^-\s+`?(allowedUnder|allowedChild)`?\s*:\s*(.+?)\s*$",
    re.MULTILINE,
)
CONTEXT_SENTENCE = re.compile(
    r"[^.\n]*(?:context|inside|within|ancestor|parent|child|runtime|server-rendered)[^.\n]*\.",
    re.IGNORECASE,
)


class RegistryBuildError(Exception):
    """Report a source packet or registry construction failure."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise RegistryBuildError("a required bundle file could not be read") from exc


def _load_json(path: Path) -> tuple[bytes, Any]:
    raw = _read_bytes(path)
    try:
        return raw, json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RegistryBuildError("a required bundle JSON file is invalid") from exc


def _json_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _matches_declared_type(value: Any, declared: Any) -> bool:
    declared_types = declared if isinstance(declared, list) else [declared]
    for candidate in declared_types:
        if candidate == "null" and value is None:
            return True
        if candidate == "boolean" and isinstance(value, bool):
            return True
        if candidate == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if candidate == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if candidate == "string" and isinstance(value, str):
            return True
        if candidate == "array" and isinstance(value, list):
            return True
        if candidate == "object" and isinstance(value, dict):
            return True
    return False


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "null":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [
            item.strip().strip("'\"")
            for item in inner.split(",")
            if item.strip()
        ]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value.strip("'\"")


def _parse_frontmatter(source: str) -> tuple[dict[str, Any], str]:
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    if not source.startswith("---\n"):
        raise RegistryBuildError("an element document has no YAML front matter")
    end = source.find("\n---\n", 4)
    if end < 0:
        raise RegistryBuildError("an element document has unterminated YAML front matter")
    frontmatter: dict[str, Any] = {}
    for line in source[4:end].splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator or not key.strip():
            raise RegistryBuildError("an element document has invalid YAML front matter")
        frontmatter[key.strip()] = _parse_scalar(value)
    return frontmatter, source[end + 5 :]


def _parse_sections(body: str) -> dict[str, str]:
    matches = list(SECTION_HEADING.finditer(body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[match.group(1)] = body[start:end].strip()
    return sections


def _without_generated_schema(value: str) -> str:
    return GENERATED_SCHEMA_BLOCK.sub("", value).strip()


def _extract_configuration_notes(value: str) -> str:
    value = _without_generated_schema(value)
    match = re.search(r"^### Notes\s*$", value, re.MULTILINE)
    return value[match.end() :].strip() if match else value


def _extract_placement(placement: str) -> dict[str, Any]:
    signals: dict[str, list[str]] = {"allowed_under": [], "allowed_child": []}
    for name, value in PLACEMENT_LINE.findall(placement):
        key = "allowed_under" if name == "allowedUnder" else "allowed_child"
        signals[key].append(value.strip())
    other_rules = PLACEMENT_LINE.sub("", placement).strip()
    return {
        **signals,
        "other_rules": other_rules,
        "context_sentences": [
            match.group(0).strip() for match in CONTEXT_SENTENCE.finditer(placement)
        ],
    }


def _validate_intake_manifest(
    bundle_root: Path, intake_manifest: Path | None
) -> dict[str, Any]:
    if intake_manifest is None:
        return {
            "status": "not_checked",
            "manifest_sha256": None,
            "file_count": None,
            "total_bytes": None,
        }
    raw, document = _load_json(intake_manifest)
    files = document.get("files") if isinstance(document, dict) else None
    if not isinstance(files, list):
        raise RegistryBuildError("the private intake manifest has no file list")
    seen: set[str] = set()
    for record in files:
        if not isinstance(record, dict):
            raise RegistryBuildError("the private intake manifest has an invalid record")
        relative = record.get("relative_path")
        expected_bytes = record.get("bytes")
        expected_sha256 = record.get("sha256")
        if (
            not isinstance(relative, str)
            or relative in seen
            or not isinstance(expected_bytes, int)
            or not isinstance(expected_sha256, str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256)
        ):
            raise RegistryBuildError("the private intake manifest has an invalid record")
        seen.add(relative)
        candidate = (bundle_root / relative).resolve()
        try:
            candidate.relative_to(bundle_root.resolve())
        except ValueError as exc:
            raise RegistryBuildError("the private intake manifest escapes the bundle") from exc
        value = _read_bytes(candidate)
        if len(value) != expected_bytes or _sha256_bytes(value) != expected_sha256:
            raise RegistryBuildError("the supplied bundle does not match its intake manifest")
    actual = {
        path.relative_to(bundle_root).as_posix()
        for path in bundle_root.rglob("*")
        if path.is_file()
    }
    if actual != seen:
        raise RegistryBuildError("the supplied bundle file set does not match its intake manifest")
    return {
        "status": "verified",
        "manifest_sha256": _sha256_bytes(raw),
        "file_count": len(files),
        "total_bytes": sum(int(record["bytes"]) for record in files),
    }


def _setting_record(
    element_type: str,
    key: str,
    schema: Mapping[str, Any],
    authored_descriptions: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    anomalies: list[dict[str, Any]] = []
    default_present = "default" in schema
    default = schema.get("default")
    declared_type = schema.get("type")
    enum = schema.get("enum")
    if default_present and declared_type is not None and not _matches_declared_type(default, declared_type):
        anomalies.append(
            {
                "kind": "default_type_mismatch",
                "element": element_type,
                "setting": key,
                "declared_type": declared_type,
                "actual_type": _json_type_name(default),
            }
        )
    if default_present and isinstance(enum, list) and default not in enum:
        anomalies.append(
            {
                "kind": "enum_default_mismatch",
                "element": element_type,
                "setting": key,
            }
        )
    conditional = schema.get("x-sfvb-conditional")
    record = {
        "key": key,
        "declared_type": declared_type,
        "editor_type": schema.get("x-sfvb-type"),
        "format": schema.get("x-sfvb-format"),
        "title": schema.get("x-sfvb-title"),
        "default_present": default_present,
        "default": default if default_present else None,
        "enum": enum,
        "enum_ref": schema.get("x-sfvb-enumRef"),
        "value_labels": schema.get("x-sfvb-valueLabels"),
        "values_dynamic": bool(schema.get("x-sfvb-valuesDynamic", False)),
        "multilang": bool(schema.get("x-sfvb-multilang", False)),
        "breakpoint_enabled": bool(schema.get("x-sfvb-breakpoints", False)),
        "conditional": conditional,
        "conditional_reference_status": None,
        "widget_type": schema.get("x-sfvb-widgetType"),
        "unmapped_type": schema.get("x-sfvb-unmapped-type"),
        "description": schema.get("description"),
        "description_source": (
            "supplier_sidecar" if key in authored_descriptions else "generated_fallback"
        ),
        "needs_description": bool(schema.get("x-sfvb-needsDescription", False)),
        "is_widget_reference": (
            schema.get("x-sfvb-format") in REFERENCE_FORMATS
            or schema.get("x-sfvb-type") in REFERENCE_EDITOR_TYPES
        ),
    }
    return record, anomalies


def _element_record(bundle_root: Path, catalog_entry: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    element_type = catalog_entry.get("element")
    if not isinstance(element_type, str) or not element_type:
        raise RegistryBuildError("the element catalog contains an invalid type")
    schema_path = bundle_root / "elements" / "schema" / f"{element_type}.schema.json"
    doc_path = bundle_root / "elements" / f"{element_type}.md"
    descriptions_path = bundle_root / "elements" / "schema" / f"{element_type}.descriptions.json"
    schema_raw, schema = _load_json(schema_path)
    doc_raw = _read_bytes(doc_path)
    try:
        doc_source = doc_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RegistryBuildError("an element document is not UTF-8") from exc
    if descriptions_path.is_file():
        descriptions_raw, descriptions = _load_json(descriptions_path)
        if not isinstance(descriptions, dict):
            raise RegistryBuildError("an element description sidecar is invalid")
        descriptions_hash = _sha256_bytes(descriptions_raw)
        descriptions_present = True
    else:
        descriptions = {}
        descriptions_hash = None
        descriptions_present = False
    if not isinstance(schema, dict) or not isinstance(schema.get("properties"), dict):
        raise RegistryBuildError("an element schema is invalid")
    frontmatter, body = _parse_frontmatter(doc_source)
    sections = _parse_sections(body)
    settings: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = []
    for key, property_schema in sorted(schema["properties"].items()):
        if not isinstance(property_schema, dict):
            raise RegistryBuildError("an element setting schema is invalid")
        record, setting_anomalies = _setting_record(
            element_type, key, property_schema, descriptions
        )
        conditional = record["conditional"]
        if isinstance(conditional, dict):
            target = conditional.get("key")
            if isinstance(target, str):
                status = "resolved" if target in schema["properties"] else "unresolved"
            else:
                status = "invalid"
            record["conditional_reference_status"] = status
            if status != "resolved":
                anomalies.append(
                    {
                        "kind": "conditional_reference_unresolved",
                        "element": element_type,
                        "setting": key,
                    }
                )
        if record["unmapped_type"] is not None:
            anomalies.append(
                {"kind": "unmapped_setting_type", "element": element_type, "setting": key}
            )
        settings.append(record)
        anomalies.extend(setting_anomalies)
    extra_descriptions = sorted(set(descriptions) - set(schema["properties"]))
    anomalies.extend(
        {
            "kind": "description_without_active_setting",
            "element": element_type,
            "setting": key,
        }
        for key in extra_descriptions
    )
    flags = schema.get("x-sfvb-flags")
    if not isinstance(flags, dict):
        raise RegistryBuildError("an element schema has invalid flags")
    placement = _extract_placement(sections.get("Placement", ""))
    frontmatter_children = frontmatter.get("children")
    if not isinstance(frontmatter_children, list):
        frontmatter_children = []
    allow_children = bool(flags.get("allowAddChildren", False))
    forced_child = flags.get("addChildForceType")
    if forced_child:
        child_model = "forced"
    elif allow_children and frontmatter_children:
        child_model = "constrained_or_general"
    elif allow_children:
        child_model = "undocumented"
    elif frontmatter_children:
        child_model = "contextual_or_runtime"
    else:
        child_model = "leaf"
    selected_sections = {
        "purpose": sections.get("Purpose & when to use", ""),
        "placement": sections.get("Placement", ""),
        "configuration_notes": _extract_configuration_notes(
            sections.get("Configuration", "")
        ),
        "runtime_behavior": sections.get("Runtime behavior", ""),
        "interactions": sections.get("Interactions with sibling elements", ""),
        "recipes": sections.get("Recipes", ""),
        "gotchas": sections.get("Gotchas & degradation", ""),
    }
    return {
        "type": element_type,
        "friendly_name": schema.get("x-sfvb-friendlyName"),
        "widget_group": schema.get("x-sfvb-widgetGroup"),
        "status": frontmatter.get("status"),
        "flags": {
            "server_render": bool(flags.get("serverRender", False)),
            "causes_clones": bool(flags.get("causesClones", False)),
            "consumes_item_context": bool(flags.get("consumesItemContext", False)),
            "allow_add_children": allow_children,
            "forced_child_type": forced_child,
        },
        "breakpoint_names": schema.get("x-sfvb-breakpointNames", []),
        "setting_groups": schema.get("x-sfvb-groups", []),
        "settings_count": len(settings),
        "settings": settings,
        "reference_setting_keys": [
            setting["key"] for setting in settings if setting["is_widget_reference"]
        ],
        "placement": {
            "frontmatter_parents": frontmatter.get("parents", []),
            "frontmatter_children": frontmatter_children,
            "allowed_under_signals": placement["allowed_under"],
            "allowed_child_signals": placement["allowed_child"],
            "other_rules": placement["other_rules"],
            "context_sentences": placement["context_sentences"],
            "child_model": child_model,
        },
        "related_elements": frontmatter.get("relatedElements", []),
        "tags": frontmatter.get("tags", []),
        "documentation": {
            "section_names": list(sections),
            "section_contract_complete": tuple(sections) == EXPECTED_DOC_SECTIONS,
            "selected_sections": selected_sections,
        },
        "source_hashes": {
            "schema_sha256": _sha256_bytes(schema_raw),
            "document_sha256": _sha256_bytes(doc_raw),
            "descriptions_sha256": descriptions_hash,
        },
        "description_sidecar_present": descriptions_present,
        "supplier_warnings": schema.get("x-sfvb-warnings", []),
    }, anomalies


def build_registry(bundle: Path, intake_manifest: Path | None = None) -> dict[str, Any]:
    bundle_root = bundle.resolve()
    if not bundle_root.is_dir():
        raise RegistryBuildError("the supplied bundle directory does not exist")
    integrity = _validate_intake_manifest(bundle_root, intake_manifest)
    manifest_raw, manifest = _load_json(bundle_root / "manifest.json")
    node_schema_raw, node_schema = _load_json(bundle_root / "cjson-node.schema.json")
    index_raw, index = _load_json(bundle_root / "elements" / "schema" / "_index.json")
    icon_library_raw, icon_library = _load_json(
        bundle_root / "elements" / "schema" / "_icon-library.json"
    )
    if not isinstance(manifest, dict) or not isinstance(index, dict):
        raise RegistryBuildError("the supplied bundle metadata is invalid")
    catalog = index.get("elements")
    if not isinstance(catalog, list):
        raise RegistryBuildError("the supplied element catalog is invalid")
    elements: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = []
    for entry in sorted(catalog, key=lambda item: item.get("element", "")):
        if not isinstance(entry, dict):
            raise RegistryBuildError("the supplied element catalog is invalid")
        element, element_anomalies = _element_record(bundle_root, entry)
        elements.append(element)
        anomalies.extend(element_anomalies)
    element_types = [element["type"] for element in elements]
    if len(element_types) != len(set(element_types)):
        raise RegistryBuildError("the supplied element catalog has duplicate types")
    declared_count = manifest.get("elementCount")
    if declared_count != len(elements) or index.get("count") != len(elements):
        raise RegistryBuildError("the supplied element counts do not reconcile")
    known_types = set(element_types)
    unresolved_placement_tokens: list[dict[str, str]] = []
    for element in elements:
        for direction, values in (
            ("parent", element["placement"]["frontmatter_parents"]),
            ("child", element["placement"]["frontmatter_children"]),
        ):
            if not isinstance(values, list):
                continue
            for value in values:
                if value not in known_types and value != "any":
                    unresolved_placement_tokens.append(
                        {"element": element["type"], "direction": direction, "token": value}
                    )
    anomaly_counts: dict[str, int] = {}
    for anomaly in anomalies:
        key = str(anomaly["kind"])
        anomaly_counts[key] = anomaly_counts.get(key, 0) + 1
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "kind": REGISTRY_KIND,
        "source": {
            "bundle": manifest.get("bundle"),
            "generated_at": manifest.get("generated"),
            "generator": manifest.get("generator"),
            "manifest_sha256": _sha256_bytes(manifest_raw),
            "catalog_sha256": _sha256_bytes(index_raw),
            "node_schema_sha256": _sha256_bytes(node_schema_raw),
            "declared_file_count": manifest.get("fileCount"),
            "declared_total_bytes": manifest.get("totalBytes"),
            "intake_integrity": integrity,
        },
        "authoring_contract": {
            "node_required_keys": node_schema.get("required", []),
            "node_allowed_keys": sorted(node_schema.get("properties", {})),
            "node_property_types": {
                key: value.get("type")
                for key, value in sorted(node_schema.get("properties", {}).items())
                if isinstance(value, dict)
            },
            "bookkeeping_config_keys": list(BOOKKEEPING_CONFIG_KEYS),
            "transient_config_keys": list(TRANSIENT_CONFIG_KEYS),
            "legacy_config_keys": manifest.get("legacyConfigKeys", {}).get("keys", []),
            "responsive_value_keys": list(RESPONSIVE_KEYS),
            "scoped_style_keys": list(SCOPED_STYLE_KEYS),
            "inheritance_max_depth": 30,
        },
        "shared_enums": {
            "icon-library": {
                "values": icon_library.get("enum", []),
                "source_sha256": _sha256_bytes(icon_library_raw),
            }
        },
        "catalog": {
            "element_count": len(elements),
            "friendly_name_count": len(
                {element["friendly_name"] for element in elements}
            ),
            "setting_instance_count": sum(
                int(element["settings_count"]) for element in elements
            ),
            "unique_setting_key_count": len(
                {
                    setting["key"]
                    for element in elements
                    for setting in element["settings"]
                }
            ),
        },
        "elements": elements,
        "anomalies": {
            "counts": dict(sorted(anomaly_counts.items())),
            "records": sorted(
                anomalies,
                key=lambda item: (
                    str(item.get("kind", "")),
                    str(item.get("element", "")),
                    str(item.get("setting", "")),
                ),
            ),
            "unresolved_placement_tokens": sorted(
                unresolved_placement_tokens,
                key=lambda item: (item["element"], item["direction"], item["token"]),
            ),
        },
    }


def validate_registry(registry: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if registry.get("kind") != REGISTRY_KIND:
        errors.append("registry kind is invalid")
    elements = registry.get("elements")
    if not isinstance(elements, list):
        return errors + ["registry element list is invalid"]
    types = [element.get("type") for element in elements if isinstance(element, dict)]
    if len(types) != len(elements) or any(not isinstance(value, str) for value in types):
        errors.append("registry contains an invalid element type")
    if len(types) != len(set(types)):
        errors.append("registry contains duplicate element types")
    catalog = registry.get("catalog")
    if not isinstance(catalog, dict) or catalog.get("element_count") != len(elements):
        errors.append("registry catalog count does not reconcile")
    known_types = set(types)
    for element in elements:
        if not isinstance(element, dict):
            continue
        flags = element.get("flags")
        settings = element.get("settings")
        if not isinstance(flags, dict):
            errors.append("registry element flags are invalid")
            continue
        forced = flags.get("forced_child_type")
        if forced is not None and forced not in known_types:
            errors.append("registry forced child references an unknown type")
        if not isinstance(settings, list) or element.get("settings_count") != len(settings):
            errors.append("registry setting count does not reconcile")
            continue
        setting_keys = [setting.get("key") for setting in settings if isinstance(setting, dict)]
        if len(setting_keys) != len(settings) or len(setting_keys) != len(set(setting_keys)):
            errors.append("registry contains invalid or duplicate setting keys")
        hashes = element.get("source_hashes")
        if not isinstance(hashes, dict):
            errors.append("registry element source hashes are invalid")
        else:
            for key in ("schema_sha256", "document_sha256"):
                if not re.fullmatch(r"[0-9a-f]{64}", str(hashes.get(key, ""))):
                    errors.append("registry element source hash is invalid")
        placement = element.get("placement")
        if not isinstance(placement, dict) or placement.get("child_model") not in {
            "forced",
            "constrained_or_general",
            "undocumented",
            "contextual_or_runtime",
            "leaf",
        }:
            errors.append("registry element child model is invalid")
    return sorted(set(errors))


def _require_private_path(path: Path, private_root: Path) -> None:
    try:
        path.resolve().relative_to(private_root.resolve())
    except ValueError as exc:
        raise RegistryBuildError("bundle, manifest, and output must stay in the private root") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="Private supplied bundle directory")
    parser.add_argument("--intake-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    private_root_value = os.environ.get("UVB_PRIVATE_ARTIFACT_ROOT")
    if not private_root_value:
        raise SystemExit("UVB_PRIVATE_ARTIFACT_ROOT is required")
    private_root = Path(private_root_value)
    for path in (args.bundle, args.intake_manifest, args.output):
        _require_private_path(path, private_root)
    registry = build_registry(args.bundle, args.intake_manifest)
    errors = validate_registry(registry)
    if errors:
        raise SystemExit("registry validation failed: " + "; ".join(errors))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        "Built private registry: "
        f"{registry['catalog']['element_count']} elements, "
        f"{registry['catalog']['setting_instance_count']} setting instances, "
        f"{sum(registry['anomalies']['counts'].values())} source anomalies"
    )


if __name__ == "__main__":
    main()
