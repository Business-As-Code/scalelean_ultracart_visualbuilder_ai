#!/usr/bin/env python3
"""Capture one pinned, read-only FTPS directory listing into private storage."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
ENV_FILES = (ROOT / ".env", ROOT / ".env.local")
REQUIRED = (
    "UVB_FILE_PROTOCOL",
    "UVB_FILE_HOST",
    "UVB_FILE_PORT",
    "UVB_FILE_USERNAME",
    "UVB_FILE_PASSWORD",
    "UVB_FILE_ROOT",
    "UVB_FILE_PINNED_PUBKEY",
    "UVB_PRIVATE_ARTIFACT_ROOT",
)


def parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
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


def load_config() -> dict[str, str]:
    config: dict[str, str] = {}
    for env_file in ENV_FILES:
        config.update(parse_dotenv(env_file))
    return config


def curl_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def private_directory(config: dict[str, str]) -> Path:
    path = Path(config["UVB_PRIVATE_ARTIFACT_ROOT"]).expanduser().resolve()
    if not path.is_absolute() or path == ROOT or ROOT in path.parents:
        raise ValueError("private artifact root must be outside the repository")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def main() -> int:
    config = load_config()
    missing = [name for name in REQUIRED if not config.get(name, "").strip()]
    if missing:
        print("Capture not run: incomplete configuration: " + ", ".join(missing))
        return 2
    if config["UVB_FILE_PROTOCOL"].strip().lower() not in {
        "ftpes",
        "ftps-explicit",
        "explicit-ftps",
    }:
        print("Capture not run: configured protocol is not explicit FTPS.")
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
        print("Pinned FTPS capture could not run.")
        return 2
    if result.returncode != 0:
        print("Pinned FTPS capture did not complete.")
        return 1

    entries = [line.decode("utf-8", errors="surrogateescape") for line in result.stdout.splitlines()]
    captured_at = datetime.now(UTC)
    payload = {
        "captured_at": captured_at.isoformat(),
        "root": root,
        "entry_count": len(entries),
        "entries": entries,
    }
    artifact = private_directory(config) / (
        "ftps-listing-" + captured_at.strftime("%Y%m%dT%H%M%SZ") + ".json"
    )
    artifact.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    artifact.chmod(0o600)
    content_hash = hashlib.sha256(result.stdout).hexdigest()
    print(
        "Pinned FTPS listing captured privately: "
        f"{len(entries)} entries, sha256={content_hash}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
