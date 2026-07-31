#!/usr/bin/env python3
"""Run one pinned, read-only FTPS root listing without exposing file names."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from urllib.parse import quote


ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
REQUIRED = (
    "UVB_FILE_PROTOCOL",
    "UVB_FILE_HOST",
    "UVB_FILE_PORT",
    "UVB_FILE_USERNAME",
    "UVB_FILE_PASSWORD",
    "UVB_FILE_ROOT",
    "UVB_FILE_PINNED_PUBKEY",
)


def parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        name, separator, value = line.partition("=")
        if not separator:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[name.strip()] = value
    return values


def curl_quote(value: str) -> str:
    return (
        '"'
        + value.replace("\\", "\\\\").replace('"', '\\"')
        + '"'
    )


def main() -> int:
    config = parse_dotenv(ENV_PATH)
    missing = [name for name in REQUIRED if not config.get(name, "").strip()]
    if missing:
        print("Probe not run: incomplete configuration: " + ", ".join(missing))
        return 2
    if config["UVB_FILE_PROTOCOL"].strip().lower() not in {
        "ftpes",
        "ftps-explicit",
        "explicit-ftps",
    }:
        print("Probe not run: the configured protocol is not explicit FTPS.")
        return 2

    root = "/" + config["UVB_FILE_ROOT"].strip("/") + "/"
    url = (
        "ftp://"
        + config["UVB_FILE_HOST"].strip()
        + ":"
        + config["UVB_FILE_PORT"].strip()
        + quote(root, safe="/")
    )
    curl_config = "\n".join(
        (
            "url = " + curl_quote(url),
            "user = "
            + curl_quote(
                config["UVB_FILE_USERNAME"] + ":" + config["UVB_FILE_PASSWORD"]
            ),
            "ssl-reqd",
            "insecure",
            "pinnedpubkey = " + curl_quote(config["UVB_FILE_PINNED_PUBKEY"]),
            "list-only",
            "disable-epsv",
            "connect-timeout = 20",
            "max-time = 30",
            "silent",
        )
    ) + "\n"

    try:
        result = subprocess.run(
            ["curl", "--config", "-"],
            input=curl_config.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=35,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        print("Pinned FTPS probe could not run. No files were displayed.")
        return 2

    if result.returncode == 0:
        entry_count = len([line for line in result.stdout.splitlines() if line.strip()])
        print(
            "Pinned FTPS probe passed: authentication, configured root access, "
            f"and listing completed ({entry_count} entries)."
        )
        return 0
    if result.returncode == 90:
        print("Pinned FTPS probe failed: server public key did not match the pin.")
        return 1
    if result.returncode == 67:
        print("Pinned FTPS probe failed: UltraCart rejected the login.")
        return 1
    if result.returncode == 9:
        print("Pinned FTPS probe failed: configured-root access was not accepted.")
        return 1
    print("Pinned FTPS probe did not complete. No files were displayed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
