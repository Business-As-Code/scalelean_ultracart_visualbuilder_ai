#!/usr/bin/env python3
"""Privately capture CJSON and Velocity candidates from an FTPS tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from capture_ftps_listing import (
    REQUIRED,
    curl_quote,
    load_config,
    private_directory,
)


def latest_tree(private_root: Path) -> Path | None:
    trees = sorted(private_root.glob("ftps-tree-*.json"))
    return trees[-1] if trees else None


def resolve_tree_manifest(
    private_root: Path,
    requested_manifest: str | None,
) -> tuple[Path, bool]:
    """Resolve a tree manifest and report whether latest-tree fallback was used."""
    resolved_root = private_root.resolve()
    if requested_manifest is None:
        selected = latest_tree(resolved_root)
        if selected is None:
            raise FileNotFoundError("no private FTPS tree manifest is available")
        return selected.resolve(), True

    requested = Path(requested_manifest).expanduser()
    if requested.is_absolute():
        selected = requested.resolve()
    else:
        if requested.name != str(requested) or requested.name in {"", ".", ".."}:
            raise ValueError(
                "tree manifest must be a filename or an absolute path within "
                "UVB_PRIVATE_ARTIFACT_ROOT"
            )
        selected = (resolved_root / requested.name).resolve()

    try:
        selected.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(
            "tree manifest must stay within UVB_PRIVATE_ARTIFACT_ROOT"
        ) from error
    if not selected.is_file():
        raise FileNotFoundError("selected private FTPS tree manifest does not exist")
    return selected, False


def candidate_remote_paths(tree: dict[str, Any]) -> list[str]:
    """Return sorted unique CJSON and VM paths recorded in a tree manifest."""
    return sorted(
        {
            str(directory["path"]).rstrip("/") + "/" + str(entry)
            for directory in tree["directories"]
            for entry in directory["entries"]
            if Path(str(entry)).suffix.lower() in {".cjson", ".vm"}
        }
    )


def select_candidates(
    candidates: list[str],
    include_basenames: list[str],
    include_remote_paths: list[str],
) -> list[str]:
    """Apply one deterministic candidate-selection mode."""
    if include_basenames and include_remote_paths:
        raise ValueError(
            "include-basename and include-remote-path cannot be used together"
        )
    if include_remote_paths:
        available = set(candidates)
        missing = sorted(set(include_remote_paths) - available)
        if missing:
            raise ValueError(
                "exact remote path is not a CJSON or VM candidate in the selected "
                "tree: " + ", ".join(missing)
            )
        requested = set(include_remote_paths)
        return [path for path in candidates if path in requested]
    if include_basenames:
        requested = set(include_basenames)
        return [path for path in candidates if Path(path).name in requested]
    return candidates


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Privately capture selected CJSON and VM candidates."
    )
    parser.add_argument(
        "--tree-manifest",
        help=(
            "Select a manifest filename under UVB_PRIVATE_ARTIFACT_ROOT or an "
            "absolute path within that root."
        ),
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--include-basename",
        action="append",
        default=[],
        help="Capture only this exact file base name. Repeat to include a pair.",
    )
    selection.add_argument(
        "--include-remote-path",
        action="append",
        default=[],
        help="Capture only this exact remote path. Repeat to include a pair.",
    )
    return parser.parse_args(argv)


def fetch_file(config: dict[str, str], remote_path: str) -> bytes | None:
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
            "disable-epsv",
            "connect-timeout = 8",
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
        return None
    return result.stdout if result.returncode == 0 else None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
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

    private_root = private_directory(config)
    try:
        tree_path, used_fallback = resolve_tree_manifest(
            private_root,
            args.tree_manifest,
        )
    except (FileNotFoundError, ValueError) as error:
        print(f"Capture not run: {error}.")
        return 2
    if used_fallback:
        print(
            "Warning: --tree-manifest was not supplied; using the latest private "
            f"tree manifest: {tree_path.name}.",
            file=sys.stderr,
        )
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    candidates = candidate_remote_paths(tree)
    try:
        candidates = select_candidates(
            candidates,
            args.include_basename,
            args.include_remote_path,
        )
    except ValueError as error:
        print(f"Capture not run: {error}.")
        return 2
    if not candidates:
        print("No selected CJSON or VM candidates were present in the private tree.")
        return 0

    captured_at = datetime.now(UTC)
    capture_directory = private_root / (
        "ftps-candidates-" + captured_at.strftime("%Y%m%dT%H%M%S%fZ")
    )
    capture_directory.mkdir(mode=0o700)
    capture_directory.chmod(0o700)
    captured: list[dict[str, object]] = []
    failures = 0
    for remote_path in candidates:
        content = fetch_file(config, remote_path)
        if content is None:
            failures += 1
            continue
        remote_hash = hashlib.sha256(remote_path.encode()).hexdigest()
        local_path = capture_directory / (remote_hash + Path(remote_path).suffix.lower())
        local_path.write_bytes(content)
        local_path.chmod(0o600)
        captured.append(
            {
                "path": remote_path,
                "extension": Path(remote_path).suffix.lower(),
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "local_name": local_path.name,
            }
        )
    manifest = {
        "captured_at": captured_at.isoformat(),
        "tree_manifest": str(tree_path.relative_to(private_root)),
        "captured": captured,
        "failed_candidate_count": failures,
    }
    manifest_path = capture_directory / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest_path.chmod(0o600)
    extensions = {".cjson": 0, ".vm": 0}
    for item in captured:
        extensions[str(item["extension"])] += 1
    print(
        "Pinned FTPS candidates captured privately: "
        f"{extensions['.cjson']} CJSON and {extensions['.vm']} VM files, "
        f"{failures} failures."
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
