#!/usr/bin/env python3
"""Capture a bounded pinned-FTPS tree manifest into private storage."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, deque
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from capture_ftps_listing import (
    REQUIRED,
    curl_quote,
    load_config,
    private_directory,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture a bounded private FTPS directory tree manifest."
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=4,
        help="Maximum directory depth below UVB_FILE_ROOT (default: 4).",
    )
    parser.add_argument(
        "--max-directories",
        type=int,
        default=200,
        help="Maximum directories to list (default: 200).",
    )
    parser.add_argument(
        "--relative-path",
        default="",
        help="Directory below UVB_FILE_ROOT to capture (default: configured root).",
    )
    return parser.parse_args()


def safe_relative_path(value: str) -> str:
    raw = value.strip()
    if raw.startswith("/"):
        raise ValueError("relative path must not start with a slash")
    cleaned = raw.strip("/")
    if not cleaned:
        return ""
    parts = cleaned.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("relative path must stay below the configured FTPS root")
    return cleaned


def list_directory(config: dict[str, str], remote_path: str) -> list[str] | None:
    url = (
        "ftp://"
        + config["UVB_FILE_HOST"].strip()
        + ":"
        + config["UVB_FILE_PORT"].strip()
        + quote(remote_path, safe="/")
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
            "connect-timeout = 8",
            "max-time = 10",
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
        return None
    if result.returncode != 0:
        return None
    return [
        line.decode("utf-8", errors="surrogateescape")
        for line in result.stdout.splitlines()
        if line and line not in {b".", b".."}
    ]


def main() -> int:
    args = parse_args()
    if args.max_depth < 0 or args.max_directories < 1:
        print("Capture not run: max-depth must be non-negative and max-directories positive.")
        return 2

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

    try:
        relative_path = safe_relative_path(args.relative_path)
    except ValueError as error:
        print(f"Capture not run: {error}.")
        return 2
    root = "/" + config["UVB_FILE_ROOT"].strip("/")
    if relative_path:
        root += "/" + relative_path
    queue: deque[tuple[str, int]] = deque([(root, 0)])
    directories: list[dict[str, object]] = []
    files: list[str] = []
    skipped = 0

    while queue and len(directories) < args.max_directories:
        directory, depth = queue.popleft()
        entries = list_directory(config, directory + "/")
        if entries is None:
            skipped += 1
            continue
        directories.append({"path": directory, "depth": depth, "entries": entries})
        for entry in entries:
            child = directory + "/" + entry
            # The server's list-only response does not provide entry types.
            # Treat extension-bearing names as files so this bounded discovery
            # does not attempt one network round trip per source file.
            if depth < args.max_depth and (
                depth == 0 or not Path(entry).suffix
            ):
                queue.append((child, depth + 1))
            else:
                files.append(child)

    unresolved = list(queue)
    captured_at = datetime.now(UTC)
    payload = {
        "captured_at": captured_at.isoformat(),
        "root": root,
        "max_depth": args.max_depth,
        "max_directories": args.max_directories,
        "directories": directories,
        "depth_limit_entries": files,
        "unresolved_candidates": unresolved,
        "failed_directory_attempts": skipped,
    }
    artifact = private_directory(config) / (
        "ftps-tree-" + captured_at.strftime("%Y%m%dT%H%M%SZ") + ".json"
    )
    serialized = json.dumps(payload, indent=2) + "\n"
    artifact.write_text(serialized, encoding="utf-8")
    artifact.chmod(0o600)

    extension_counts = Counter(
        Path(entry).suffix.lower()
        for directory in directories
        for entry in directory["entries"]
        if Path(entry).suffix
    )
    content_hash = hashlib.sha256(serialized.encode()).hexdigest()
    candidate_count = sum(
        extension_counts[extension] for extension in (".cjson", ".vm")
    )
    print(
        "Pinned FTPS tree captured privately: "
        f"{len(directories)} directories listed, {candidate_count} CJSON/VM name candidates, "
        f"sha256={content_hash}."
    )
    if unresolved:
        print("Capture reached its configured bound; no additional paths were listed.")
    if skipped:
        print(f"{skipped} non-directory or inaccessible path candidates were not listed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
