#!/usr/bin/env python3
"""Validate a CJSON tree against the normalized private SFVB source registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


class CjsonValidationError(Exception):
    """Report an unreadable registry or CJSON document."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CjsonValidationError("a validation input could not be read") from exc


def _matches_type(value: Any, declared: Any) -> bool:
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


def _issue(code: str, path: str, detail: str) -> dict[str, str]:
    return {"code": code, "path": path, "detail": detail}


def _element_map(registry: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    elements = registry.get("elements")
    if not isinstance(elements, list):
        raise CjsonValidationError("the source registry has no element list")
    result: dict[str, Mapping[str, Any]] = {}
    for element in elements:
        if not isinstance(element, dict) or not isinstance(element.get("type"), str):
            raise CjsonValidationError("the source registry contains an invalid element")
        result[element["type"]] = element
    return result


def _setting_map(element: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    settings = element.get("settings")
    if not isinstance(settings, list):
        return {}
    return {
        setting["key"]: setting
        for setting in settings
        if isinstance(setting, dict) and isinstance(setting.get("key"), str)
    }


def _conditional_met(conditional: Mapping[str, Any], config: Mapping[str, Any]) -> bool | None:
    key = conditional.get("key")
    if not isinstance(key, str) or key not in config:
        return None
    actual = config[key]
    if "equals" in conditional:
        expected = conditional["equals"]
        if isinstance(expected, list):
            return actual in expected
        return actual == expected
    if "notEquals" in conditional:
        expected = conditional["notEquals"]
        if isinstance(expected, list):
            return actual not in expected
        return actual != expected
    return None


def _base_values(
    setting: Mapping[str, Any], value: Any, path: str
) -> tuple[list[tuple[str, Any]], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    if setting.get("key") == "scopedStyles" and isinstance(value, dict):
        allowed = {
            "all",
            "small-only",
            "medium-only",
            "medium-up",
            "large-only",
            "xlarge-up",
            "xxlarge-up",
        }
        unknown = sorted(set(value) - allowed)
        if unknown:
            errors.append(
                _issue(
                    "invalid_scoped_style_breakpoint",
                    path,
                    "scopedStyles contains an unsupported breakpoint key",
                )
            )
        return [(f"{path}.{key}", item) for key, item in value.items()], errors
    if setting.get("multilang"):
        if not isinstance(value, dict) or not value:
            errors.append(
                _issue(
                    "invalid_multilang_wrapper",
                    path,
                    "multilingual settings require a nonempty language map",
                )
            )
            return [], errors
        invalid = [key for key in value if not isinstance(key, str) or len(key) != 3]
        if invalid:
            errors.append(
                _issue(
                    "invalid_multilang_key",
                    path,
                    "multilingual language keys must contain three characters",
                )
            )
        return [(f"{path}.{key}", item) for key, item in value.items()], errors
    if setting.get("breakpoint_enabled") and isinstance(value, dict):
        allowed = {"small", "medium", "large"}
        if not value or set(value) - allowed:
            errors.append(
                _issue(
                    "invalid_responsive_wrapper",
                    path,
                    "responsive settings allow only sparse small, medium, and large keys",
                )
            )
        return [(f"{path}.{key}", item) for key, item in value.items()], errors
    return [(path, value)], errors


def _validate_setting_value(
    setting: Mapping[str, Any],
    value: Any,
    path: str,
    registry: Mapping[str, Any],
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    values, wrapper_errors = _base_values(setting, value, path)
    errors.extend(wrapper_errors)
    declared = setting.get("declared_type")
    enum = setting.get("enum")
    enum_ref = setting.get("enum_ref")
    if enum_ref == "_icon-library.json":
        enum = (
            registry.get("shared_enums", {})
            .get("icon-library", {})
            .get("values", [])
        )
    for value_path, candidate in values:
        if declared is not None and not _matches_type(candidate, declared):
            errors.append(
                _issue(
                    "invalid_setting_type",
                    value_path,
                    "setting value does not match its declared source type",
                )
            )
        if isinstance(enum, list) and candidate not in enum:
            errors.append(
                _issue(
                    "invalid_setting_enum",
                    value_path,
                    "setting value is not in the source enum",
                )
            )
    return errors


def classify_placement(
    parent: Mapping[str, Any], child: Mapping[str, Any]
) -> str:
    parent_type = parent.get("type")
    child_type = child.get("type")
    parent_children = parent.get("placement", {}).get("frontmatter_children", [])
    child_parents = child.get("placement", {}).get("frontmatter_parents", [])
    parent_allows = "any" in parent_children or child_type in parent_children
    child_allows = "any" in child_parents or parent_type in child_parents
    parent_silent = not parent_children
    child_silent = not child_parents
    if parent_allows and child_allows:
        return "bilateral"
    if parent_allows or child_allows:
        if (parent_allows and child_silent) or (child_allows and parent_silent):
            return "unilateral"
        return "contradicted"
    if parent_silent or child_silent:
        return "unknown"
    return "denied"


def validate_cjson(
    document: Any,
    registry: Mapping[str, Any],
    *,
    mode: str = "authoring",
    external_ids: Iterable[str] = (),
    verified_dynamic_values: Mapping[tuple[str, str], set[Any]] | None = None,
) -> dict[str, Any]:
    if mode not in {"authoring", "existing"}:
        raise CjsonValidationError("validation mode must be authoring or existing")
    elements = _element_map(registry)
    contract = registry.get("authoring_contract")
    if not isinstance(contract, dict):
        raise CjsonValidationError("the source registry has no authoring contract")
    allowed_node_keys = set(contract.get("node_allowed_keys", []))
    required_node_keys = set(contract.get("node_required_keys", []))
    node_types = contract.get("node_property_types", {})
    bookkeeping = set(contract.get("bookkeeping_config_keys", []))
    transient = set(contract.get("transient_config_keys", []))
    legacy = {
        item.get("key")
        for item in contract.get("legacy_config_keys", [])
        if isinstance(item, dict)
    }
    external = set(external_ids)
    dynamic_values = verified_dynamic_values or {}
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    nodes: list[tuple[Mapping[str, Any], str, Mapping[str, Any] | None]] = []
    ids: set[str] = set()
    duplicate_ids: set[str] = set()

    def walk(node: Any, path: str, parent: Mapping[str, Any] | None) -> None:
        if not isinstance(node, dict):
            errors.append(_issue("invalid_node", path, "node must be an object"))
            return
        nodes.append((node, path, parent))
        missing = sorted(required_node_keys - set(node))
        unknown = sorted(set(node) - allowed_node_keys)
        if missing:
            errors.append(_issue("missing_node_key", path, "node is missing a required key"))
        if unknown:
            errors.append(_issue("unknown_node_key", path, "node contains an unsupported key"))
        for key, declared in node_types.items():
            if key in node and declared is not None and not _matches_type(node[key], declared):
                errors.append(
                    _issue("invalid_node_key_type", f"{path}.{key}", "node key has the wrong type")
                )
        node_id = node.get("id")
        if isinstance(node_id, str):
            if node_id in ids:
                duplicate_ids.add(node_id)
            ids.add(node_id)
        children = node.get("childWidgets")
        if isinstance(children, list):
            for index, child in enumerate(children):
                walk(child, f"{path}.childWidgets[{index}]", node)

    walk(document, "$", None)
    if duplicate_ids:
        errors.append(_issue("duplicate_widget_id", "$", "widget ids must be unique"))

    references: list[tuple[str, str]] = []
    root_container = document.get("containerId") if isinstance(document, dict) else None
    for node, path, parent in nodes:
        element_type = node.get("type")
        element = elements.get(element_type) if isinstance(element_type, str) else None
        if element is None:
            errors.append(_issue("unknown_element_type", f"{path}.type", "type is not in the closed catalog"))
            continue
        config = node.get("config")
        if not isinstance(config, dict):
            continue
        settings = _setting_map(element)
        for key, value in config.items():
            setting_path = f"{path}.config.{key}"
            if key in transient:
                issue = _issue(
                    "transient_config_key",
                    setting_path,
                    "transient editor state must not be authored",
                )
                (warnings if mode == "existing" else errors).append(issue)
                continue
            if key in legacy:
                issue = _issue("legacy_config_key", setting_path, "legacy settings must not be emitted")
                (warnings if mode == "existing" else errors).append(issue)
                continue
            if key in bookkeeping:
                if key == "hidden" and value not in {"Yes", "No"}:
                    issue = _issue(
                        "invalid_hidden_value", setting_path, "hidden must be Yes or No"
                    )
                    (warnings if mode == "existing" else errors).append(issue)
                if key == "inheritGroups":
                    if not isinstance(value, dict) or any(
                        not isinstance(group_value, dict) for group_value in value.values()
                    ):
                        errors.append(
                            _issue(
                                "invalid_inherit_groups",
                                setting_path,
                                "inheritGroups must be a two-level object",
                            )
                        )
                    else:
                        warnings.append(
                            _issue(
                                "inherit_group_semantics_unverified",
                                setting_path,
                                "effective inherited settings require descendant context",
                            )
                        )
                continue
            setting = settings.get(key)
            if setting is None:
                issue = _issue(
                    "unknown_config_key",
                    setting_path,
                    "config key is absent from the selected element schema",
                )
                (warnings if mode == "existing" else errors).append(issue)
                continue
            value_issues = _validate_setting_value(setting, value, setting_path, registry)
            (warnings if mode == "existing" else errors).extend(value_issues)
            conditional = setting.get("conditional")
            if isinstance(conditional, dict):
                condition_status = _conditional_met(conditional, config)
                if condition_status is False:
                    issue = _issue(
                        "inactive_conditional_setting",
                        setting_path,
                        "setting is present while its editor condition is unmet",
                    )
                    (warnings if mode == "existing" else errors).append(issue)
                elif condition_status is None:
                    issue = _issue(
                        "unresolved_conditional_setting",
                        setting_path,
                        "setting condition cannot be resolved from local config",
                    )
                    (warnings if mode == "existing" else errors).append(issue)
            if setting.get("values_dynamic"):
                allowed = dynamic_values.get((str(element_type), key))
                if allowed is None or value not in allowed:
                    issue = _issue(
                        "unverified_dynamic_value",
                        setting_path,
                        "runtime-computed option values must come from current merchant data",
                    )
                    (warnings if mode == "existing" else errors).append(issue)
            if setting.get("is_widget_reference"):
                if isinstance(value, str):
                    references.append((setting_path, value))
                elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                    references.extend((setting_path, item) for item in value)
                else:
                    errors.append(
                        _issue(
                            "invalid_widget_reference",
                            setting_path,
                            "widget reference must be a string or string list",
                        )
                    )
        if parent is not None:
            parent_type = parent.get("type")
            parent_element = elements.get(parent_type) if isinstance(parent_type, str) else None
            if parent_element is not None:
                forced = parent_element.get("flags", {}).get("forced_child_type")
                if forced is not None and element_type != forced:
                    issue = _issue(
                        "forced_child_violation",
                        path,
                        "child type does not match the parent's forced child type",
                    )
                    (warnings if mode == "existing" else errors).append(issue)
                placement = classify_placement(parent_element, element)
                if placement != "bilateral":
                    issue = _issue(
                        f"placement_{placement}",
                        path,
                        "source placement signals do not bilaterally prove this edge",
                    )
                    (warnings if mode == "existing" else errors).append(issue)
            parent_id = parent.get("id")
            if "parentWidgetId" in node and node.get("parentWidgetId") != parent_id:
                errors.append(
                    _issue(
                        "parent_reference_mismatch",
                        f"{path}.parentWidgetId",
                        "parentWidgetId does not match the containing node",
                    )
                )
        elif isinstance(node.get("parentWidgetId"), str) and node["parentWidgetId"] not in external:
            issue = _issue(
                "external_parent_unresolved",
                f"{path}.parentWidgetId",
                "root parent reference requires full target-page context",
            )
            (warnings if mode == "existing" else errors).append(issue)
        if root_container is not None and "containerId" in node and node.get("containerId") != root_container:
            errors.append(
                _issue(
                    "container_reference_mismatch",
                    f"{path}.containerId",
                    "containerId differs within the tree",
                )
            )

    for path, target in references:
        if target not in ids and target not in external:
            issue = _issue(
                "dangling_widget_reference",
                path,
                "widget reference target is unavailable in the tree or external context",
            )
            (warnings if mode == "existing" else errors).append(issue)

    errors.sort(key=lambda item: (item["path"], item["code"]))
    warnings.sort(key=lambda item: (item["path"], item["code"]))
    return {
        "valid": not errors,
        "mode": mode,
        "scope": "static_source_validation",
        "live_verification_required": [
            "editor_save_reload",
            "generated_vm",
            "non_editor_render",
            "responsive_render",
            "native_behavior",
        ],
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "node_count": len(nodes),
            "unique_id_count": len(ids),
            "reference_count": len(references),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    parser.add_argument("cjson", type=Path)
    parser.add_argument("--mode", choices=("authoring", "existing"), default="authoring")
    parser.add_argument(
        "--external-id-file",
        type=Path,
        help="Private newline-delimited external widget ids",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    external_ids: list[str] = []
    if args.external_id_file:
        try:
            external_ids = [
                line.strip()
                for line in args.external_id_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except OSError as exc:
            raise SystemExit("external id file could not be read") from exc
    result = validate_cjson(
        _load_json(args.cjson),
        _load_json(args.registry),
        mode=args.mode,
        external_ids=external_ids,
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            f"valid={str(result['valid']).lower()} "
            f"errors={len(result['errors'])} warnings={len(result['warnings'])} "
            f"nodes={result['stats']['node_count']}"
        )
        for issue in result["errors"] + result["warnings"]:
            print(f"{issue['code']} {issue['path']}: {issue['detail']}")
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
