#!/usr/bin/env python3
"""Audit a private SFVB registry and supplied examples without exposing source."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from build_supplied_source_registry import _validate_intake_manifest, validate_registry
from validate_cjson_against_registry import validate_cjson


class RegistryAuditError(Exception):
    """Report an unreadable or unsafe audit input."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RegistryAuditError("an audit input could not be read") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise RegistryAuditError("an audit input could not be hashed") from exc
    return digest.hexdigest()


def _require_private(path: Path, private_root: Path) -> None:
    try:
        path.resolve().relative_to(private_root.resolve())
    except ValueError as exc:
        raise RegistryAuditError("audit paths must stay inside the private artifact root") from exc


def _count_anomalies(registry: Mapping[str, Any]) -> dict[str, int]:
    records = registry.get("anomalies", {}).get("records", [])
    if not isinstance(records, list):
        return {}
    counts = Counter(
        record.get("kind")
        for record in records
        if isinstance(record, dict) and isinstance(record.get("kind"), str)
    )
    return dict(sorted(counts.items()))


def audit_registry(
    bundle_root: Path,
    intake_manifest: Path,
    registry_path: Path,
) -> dict[str, Any]:
    registry = _load_json(registry_path)
    if not isinstance(registry, dict):
        raise RegistryAuditError("registry root must be an object")

    intake = _validate_intake_manifest(bundle_root, intake_manifest)
    source = registry.get("source", {})
    catalog = registry.get("catalog", {})
    elements = registry.get("elements", [])
    if not isinstance(source, dict) or not isinstance(catalog, dict) or not isinstance(elements, list):
        raise RegistryAuditError("registry structure is invalid")

    failures = list(validate_registry(registry))
    if source.get("intake_integrity") != intake:
        failures.append("registry intake receipt does not match the current bundle")
    actual_element_count = len(elements)
    actual_setting_count = sum(
        len(element.get("settings", []))
        for element in elements
        if isinstance(element, dict) and isinstance(element.get("settings"), list)
    )
    actual_unique_setting_keys = len(
        {
            setting.get("key")
            for element in elements
            if isinstance(element, dict)
            for setting in element.get("settings", [])
            if isinstance(setting, dict) and isinstance(setting.get("key"), str)
        }
    )
    expected_catalog = {
        "element_count": actual_element_count,
        "friendly_name_count": len(
            {
                element.get("friendly_name")
                for element in elements
                if isinstance(element, dict) and element.get("friendly_name")
            }
        ),
        "setting_instance_count": actual_setting_count,
        "unique_setting_key_count": actual_unique_setting_keys,
    }
    if catalog != expected_catalog:
        failures.append("registry catalog counts do not match normalized content")

    actual_anomalies = _count_anomalies(registry)
    declared_anomalies = registry.get("anomalies", {}).get("counts", {})
    if declared_anomalies != actual_anomalies:
        failures.append("registry anomaly counts do not match anomaly records")

    source_hash_coverage = Counter()
    description_provenance = Counter()
    placement_status = Counter()
    for element in elements:
        if not isinstance(element, dict):
            continue
        hashes = element.get("source_hashes", {})
        if isinstance(hashes, dict):
            source_hash_coverage.update(key for key, value in hashes.items() if value)
        placement = element.get("placement", {})
        if isinstance(placement, dict):
            placement_status.update([str(placement.get("child_model", "missing"))])
        for setting in element.get("settings", []):
            if isinstance(setting, dict):
                description_provenance.update(
                    [str(setting.get("description_source", "missing"))]
                )

    examples_dir = bundle_root / "examples"
    example_results = []
    warning_codes = Counter()
    error_codes = Counter()
    for example_path in sorted(examples_dir.glob("*.cjson")):
        result = validate_cjson(_load_json(example_path), registry, mode="existing")
        warning_codes.update(issue["code"] for issue in result["warnings"])
        error_codes.update(issue["code"] for issue in result["errors"])
        example_results.append(
            {
                "label": example_path.stem,
                "valid": result["valid"],
                "node_count": result["stats"]["node_count"],
                "error_count": len(result["errors"]),
                "warning_count": len(result["warnings"]),
            }
        )
        if not result["valid"]:
            failures.append("a supplied example failed existing-content validation")

    try:
        registry_bytes = registry_path.stat().st_size
    except OSError as exc:
        raise RegistryAuditError("registry could not be inspected") from exc

    return {
        "kind": "ultracart_visual_builder_source_registry_audit",
        "schema_version": 1,
        "valid": not failures,
        "failures": sorted(set(failures)),
        "registry": {
            "sha256": _sha256(registry_path),
            "bytes": registry_bytes,
            "kind": registry.get("kind"),
            "schema_version": registry.get("schema_version"),
        },
        "source_integrity": intake,
        "catalog": expected_catalog,
        "source_hash_coverage": dict(sorted(source_hash_coverage.items())),
        "description_provenance": dict(sorted(description_provenance.items())),
        "placement_child_models": dict(sorted(placement_status.items())),
        "source_anomalies": actual_anomalies,
        "unresolved_placement_token_count": len(
            registry.get("anomalies", {}).get("unresolved_placement_tokens", [])
        ),
        "supplied_examples": {
            "count": len(example_results),
            "valid_count": sum(item["valid"] for item in example_results),
            "error_codes": dict(sorted(error_codes.items())),
            "warning_codes": dict(sorted(warning_codes.items())),
            "results": example_results,
        },
        "static_validator_scope": {
            "proves": "source-shape, type, setting, reference, and placement checks",
            "does_not_prove": [
                "editor_save_reload",
                "generated_vm",
                "non_editor_render",
                "responsive_render",
                "native_behavior",
            ],
        },
    }


def public_receipt(result: Mapping[str, Any]) -> dict[str, Any]:
    """Return the fixed aggregate subset that is safe to version in Git."""

    supplied_examples = result.get("supplied_examples", {})
    results = supplied_examples.get("results", [])
    return {
        "catalog": result.get("catalog", {}),
        "description_provenance": result.get("description_provenance", {}),
        "kind": "ultracart_visual_builder_source_registry_public_receipt",
        "placement_child_models": result.get("placement_child_models", {}),
        "registry": result.get("registry", {}),
        "schema_version": 1,
        "source_anomalies": result.get("source_anomalies", {}),
        "source_hash_coverage": result.get("source_hash_coverage", {}),
        "source_integrity": result.get("source_integrity", {}),
        "static_validator_scope": result.get("static_validator_scope", {}),
        "supplied_examples": {
            "error_count": sum(
                int(item.get("error_count", 0))
                for item in results
                if isinstance(item, dict)
            ),
            "example_count": supplied_examples.get("count", 0),
            "valid_count": supplied_examples.get("valid_count", 0),
            "warning_count": sum(
                int(item.get("warning_count", 0))
                for item in results
                if isinstance(item, dict)
            ),
        },
        "unresolved_placement_token_count": result.get(
            "unresolved_placement_token_count", 0
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_root", type=Path)
    parser.add_argument("intake_manifest", type=Path)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--public-receipt",
        type=Path,
        help="Optional path for the fixed path-free aggregate receipt",
    )
    args = parser.parse_args()

    private_root_value = os.environ.get("UVB_PRIVATE_ARTIFACT_ROOT")
    if not private_root_value:
        raise SystemExit("UVB_PRIVATE_ARTIFACT_ROOT is required")
    private_root = Path(private_root_value)
    for path in (args.bundle_root, args.intake_manifest, args.registry, args.output.parent):
        _require_private(path, private_root)

    result = audit_registry(args.bundle_root, args.intake_manifest, args.registry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        args.output.chmod(0o600)
    except OSError as exc:
        raise SystemExit("private audit receipt could not be written") from exc
    if args.public_receipt:
        try:
            args.public_receipt.parent.mkdir(parents=True, exist_ok=True)
            args.public_receipt.write_text(
                json.dumps(public_receipt(result), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            raise SystemExit("public aggregate receipt could not be written") from exc
    print(
        f"valid={str(result['valid']).lower()} "
        f"elements={result['catalog']['element_count']} "
        f"settings={result['catalog']['setting_instance_count']} "
        f"examples={result['supplied_examples']['valid_count']}/{result['supplied_examples']['count']} "
        f"registry_sha256={result['registry']['sha256']}"
    )
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
