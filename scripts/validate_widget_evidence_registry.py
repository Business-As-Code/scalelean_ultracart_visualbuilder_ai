#!/usr/bin/env python3
"""Fail closed when the public Visual Builder evidence registry is incomplete."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ALLOWED_STATUS = {"Verified", "Contradicted", "Unknown"}
UNSAFE_SUFFIXES = {".cjson", ".vm", ".env", ".har"}
UNSAFE_NAMES = {".env", "cookies.json", "storage-state.json"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(catalog: dict[str, Any], registry: dict[str, Any], catalog_hash: str) -> list[str]:
    errors: list[str] = []
    if registry.get("schema_version") != "1.0":
        errors.append("unsupported evidence registry schema")
    if registry.get("catalog_sha256") != catalog_hash:
        errors.append("evidence registry catalog hash is stale")
    widgets = registry.get("widgets")
    if not isinstance(widgets, dict):
        return errors + ["evidence registry widgets must be an object"]
    catalog_types = set(catalog.get("type_instance_counts", {}))
    registry_types = set(widgets)
    for widget_type in sorted(catalog_types - registry_types):
        errors.append(f"undocumented widget type: {widget_type}")
    for widget_type in sorted(registry_types - catalog_types):
        errors.append(f"widget type absent from catalog: {widget_type}")
    for widget_type in sorted(catalog_types & registry_types):
        entry = widgets[widget_type]
        if not isinstance(entry, dict):
            errors.append(f"widget record is invalid: {widget_type}")
            continue
        if entry.get("status") not in ALLOWED_STATUS:
            errors.append(f"widget status missing or invalid: {widget_type}")
        hierarchy = entry.get("hierarchy")
        if not isinstance(hierarchy, dict):
            errors.append(f"hierarchy evidence missing: {widget_type}")
        else:
            for field in ("direct_insertion", "child_rule", "save_reload", "responsive_render"):
                if hierarchy.get(field) not in ALLOWED_STATUS:
                    errors.append(f"hierarchy status missing or invalid: {widget_type}.{field}")
        settings = entry.get("settings")
        if not isinstance(settings, dict):
            errors.append(f"settings registry missing: {widget_type}")
            continue
        catalog_keys = set(catalog.get("config_key_unions", {}).get(widget_type, []))
        for key in sorted(catalog_keys - set(settings)):
            errors.append(f"undocumented setting key: {widget_type}.{key}")
        for key in sorted(set(settings) - catalog_keys):
            errors.append(f"setting key absent from catalog: {widget_type}.{key}")
        for key in sorted(catalog_keys & set(settings)):
            setting = settings[key]
            if not isinstance(setting, dict) or setting.get("status") not in ALLOWED_STATUS:
                errors.append(f"setting status missing or invalid: {widget_type}.{key}")
                continue
            for field in ("control", "default", "permitted_values", "dependencies", "responsive_scope", "impact"):
                if field not in setting:
                    errors.append(f"setting field missing: {widget_type}.{key}.{field}")
    return errors


def unsafe_artifacts(root: Path) -> list[str]:
    """Return tracked or publishable files that violate the public boundary.

    Ignored local credentials are intentionally outside the public repository
    contract. In a Git worktree, use Git's publishable file set. The recursive
    fallback keeps the function useful for isolated tests and exported trees.
    """

    findings: list[str] = []
    ignored = {".git", ".venv", "__pycache__"}
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-co", "--exclude-standard"],
            check=True,
            capture_output=True,
            text=True,
        )
        candidates = [root / line for line in result.stdout.splitlines() if line]
    except (OSError, subprocess.CalledProcessError):
        candidates = list(root.rglob("*"))
    for path in candidates:
        if not path.is_file() or any(part in ignored for part in path.parts):
            continue
        if path.name in UNSAFE_NAMES or path.suffix.lower() in UNSAFE_SUFFIXES:
            findings.append(path.relative_to(root).as_posix())
    return sorted(findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--repository-root", type=Path)
    args = parser.parse_args()
    try:
        errors = validate(load_json(args.catalog), load_json(args.registry), digest(args.catalog))
    except (OSError, json.JSONDecodeError) as error:
        errors = [f"could not read registry inputs: {error}"]
    if args.repository_root:
        errors.extend(f"unsafe public artifact: {path}" for path in unsafe_artifacts(args.repository_root))
    if errors:
        print("validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 2
    print("Widget evidence registry is complete and safe for the supplied catalog.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
