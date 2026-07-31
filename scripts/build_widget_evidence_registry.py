#!/usr/bin/env python3
"""Create a privacy-safe widget and settings evidence registry from a catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
DEFAULT_STATUS = "Unknown"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_registry(catalog: dict[str, Any], catalog_hash: str) -> dict[str, Any]:
    """Return an explicit Unknown record for each cataloged type and key."""

    types = catalog.get("type_instance_counts", {})
    keys_by_type = catalog.get("config_key_unions", {})
    if not isinstance(types, dict) or not isinstance(keys_by_type, dict):
        raise ValueError("catalog does not contain type and setting indexes")

    widgets: dict[str, Any] = {}
    for widget_type in sorted(types):
        keys = keys_by_type.get(widget_type, [])
        if not isinstance(keys, list) or not all(isinstance(key, str) for key in keys):
            raise ValueError(f"catalog settings for {widget_type} are invalid")
        widgets[widget_type] = {
            "status": DEFAULT_STATUS,
            "hierarchy": {
                "direct_insertion": DEFAULT_STATUS,
                "child_rule": DEFAULT_STATUS,
                "save_reload": DEFAULT_STATUS,
                "responsive_render": DEFAULT_STATUS,
            },
            "settings": {
                key: {
                    "status": DEFAULT_STATUS,
                    "control": "Unknown",
                    "default": "Unknown",
                    "permitted_values": "Unknown",
                    "dependencies": "Unknown",
                    "responsive_scope": "Unknown",
                    "impact": "Unknown",
                }
                for key in sorted(keys)
            },
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "catalog_sha256": catalog_hash,
        "widgets": widgets,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        catalog = load_json(args.catalog)
        registry = build_registry(catalog, sha256(args.catalog))
        args.output.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
