#!/usr/bin/env python3
"""Validate the safe configuration shape without printing secret values."""

from __future__ import annotations

import os
import sys

from capture_ftps_listing import load_config


REQUIRED_BASE = ("UVB_ACCOUNT", "UVB_STOREFRONT_URL")
FILE_TRANSFER_FIELDS = (
    "UVB_FILE_PROTOCOL",
    "UVB_FILE_HOST",
    "UVB_FILE_PORT",
    "UVB_FILE_USERNAME",
    "UVB_FILE_PASSWORD",
    "UVB_FILE_ROOT",
    "UVB_FILE_PINNED_PUBKEY",
    "UVB_PRIVATE_ARTIFACT_ROOT",
)


def effective_config() -> dict[str, str]:
    config = load_config()
    config.update({key: value for key, value in os.environ.items() if value})
    return config


def configured(config: dict[str, str], name: str) -> bool:
    return bool(config.get(name, "").strip())


def main() -> int:
    config = effective_config()
    missing_base = [name for name in REQUIRED_BASE if not configured(config, name)]
    if missing_base:
        print("Missing required configuration: " + ", ".join(missing_base))
        return 1

    configured_transfer = [
        name for name in FILE_TRANSFER_FIELDS if configured(config, name)
    ]
    if configured_transfer and len(configured_transfer) != len(FILE_TRANSFER_FIELDS):
        missing_transfer = [
            name for name in FILE_TRANSFER_FIELDS if not configured(config, name)
        ]
        print("Incomplete file-transfer configuration: " + ", ".join(missing_transfer))
        return 1

    if configured_transfer:
        print("Base and file-transfer configuration are present. Values not displayed.")
    else:
        print("Base configuration is present. File-transfer configuration is intentionally unset.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
