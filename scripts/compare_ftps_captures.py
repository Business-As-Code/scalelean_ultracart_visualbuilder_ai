#!/usr/bin/env python3
"""Compare pinned private CJSON and Velocity capture manifests."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from capture_ftps_listing import load_config, private_directory


def capture_directories(private_root: Path) -> list[Path]:
    """Return valid candidate capture directories in deterministic order."""
    return sorted(
        path.resolve()
        for path in private_root.glob("ftps-candidates-*")
        if path.is_dir() and (path / "manifest.json").is_file()
    )


def resolve_capture_directory(private_root: Path, selector: str) -> Path:
    """Resolve one bare directory name or an absolute path inside private_root."""
    resolved_root = private_root.resolve()
    requested = Path(selector).expanduser()
    if requested.is_absolute():
        selected = requested.resolve()
    else:
        if requested.name != selector or requested.name in {"", ".", ".."}:
            raise ValueError(
                "capture selector must be a directory name or an absolute path "
                "within UVB_PRIVATE_ARTIFACT_ROOT"
            )
        selected = (resolved_root / requested.name).resolve()

    try:
        selected.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(
            "capture selector must stay within UVB_PRIVATE_ARTIFACT_ROOT"
        ) from error
    if not selected.is_dir() or not (selected / "manifest.json").is_file():
        raise FileNotFoundError("selected private candidate capture does not exist")
    return selected


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare pinned private CJSON and VM captures."
    )
    parser.add_argument(
        "--before",
        help=(
            "Select the baseline capture by directory name under "
            "UVB_PRIVATE_ARTIFACT_ROOT or by an absolute path within that root."
        ),
    )
    parser.add_argument(
        "--after",
        help=(
            "Select the saved-state capture by directory name under "
            "UVB_PRIVATE_ARTIFACT_ROOT or by an absolute path within that root."
        ),
    )
    parser.add_argument(
        "--rollback",
        help=(
            "Optionally select a rollback capture by directory name under "
            "UVB_PRIVATE_ARTIFACT_ROOT or by an absolute path within that root."
        ),
    )
    parser.add_argument(
        "--expect-stem",
        help="Verify that this logical CJSON/VM stem changed without printing paths.",
    )
    return parser.parse_args(argv)


def manifest_items(capture_directory: Path) -> dict[str, dict[str, object]]:
    """Index captured metadata by remote candidate path without exposing content."""
    manifest = json.loads(
        (capture_directory / "manifest.json").read_text(encoding="utf-8")
    )
    return {str(item["path"]): item for item in manifest["captured"]}


def capture_root(capture_directory: Path, private_root: Path) -> str:
    """Read the recorded FTPS root through a root-contained tree manifest."""
    manifest = json.loads(
        (capture_directory / "manifest.json").read_text(encoding="utf-8")
    )
    resolved_root = private_root.resolve()
    tree_path = (resolved_root / str(manifest["tree_manifest"])).resolve()
    try:
        tree_path.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(
            "capture tree manifest must stay within UVB_PRIVATE_ARTIFACT_ROOT"
        ) from error
    if not tree_path.is_file():
        raise FileNotFoundError("capture tree manifest does not exist")
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    return str(tree["root"])


def changed_pair_stems(
    changed_paths: set[str],
    items: dict[str, dict[str, object]],
) -> set[str]:
    """Return logical stems whose CJSON and VM candidates both changed."""
    changed_stems = {
        str(Path(path).with_suffix(""))
        for path in changed_paths
        if path in items and str(items[path]["extension"]) in {".cjson", ".vm"}
    }
    return {
        stem
        for stem in changed_stems
        if stem + ".cjson" in changed_paths and stem + ".vm" in changed_paths
    }


def saved_change_summary(
    before_items: dict[str, dict[str, object]],
    after_items: dict[str, dict[str, object]],
) -> tuple[set[str], set[str]]:
    """Print aggregate saved-state changes and return changed paths and pair stems."""
    common_paths = set(before_items) & set(after_items)
    changed_paths = {
        path
        for path in common_paths
        if before_items[path]["sha256"] != after_items[path]["sha256"]
    }
    changes_by_extension = Counter(
        str(after_items[path]["extension"]) for path in changed_paths
    )
    added_paths = set(after_items) - set(before_items)
    removed_paths = set(before_items) - set(after_items)
    paired_changes = changed_pair_stems(changed_paths, after_items)
    print(
        "Private capture comparison: "
        f"{changes_by_extension['.cjson']} CJSON changed, "
        f"{changes_by_extension['.vm']} VM changed, "
        f"{len(paired_changes)} matched CJSON/VM pairs changed, "
        f"{len(added_paths)} added, {len(removed_paths)} removed."
    )
    return changed_paths, paired_changes


def rollback_matches_baseline(
    before_items: dict[str, dict[str, object]],
    rollback_items: dict[str, dict[str, object]],
) -> bool:
    """Report and verify candidate-path and content equality after rollback."""
    before_paths = set(before_items)
    rollback_paths = set(rollback_items)
    matching_paths = before_paths & rollback_paths
    content_mismatches = {
        path
        for path in matching_paths
        if before_items[path]["sha256"] != rollback_items[path]["sha256"]
    }
    baseline_only = before_paths - rollback_paths
    rollback_only = rollback_paths - before_paths
    matches = not content_mismatches and not baseline_only and not rollback_only
    print(
        "Private rollback comparison: "
        f"{len(matching_paths)} matching candidates, "
        f"{len(content_mismatches)} content mismatches, "
        f"{len(baseline_only)} baseline-only, "
        f"{len(rollback_only)} rollback-only."
    )
    print("Expected rollback matches baseline: " + ("yes." if matches else "no."))
    return matches


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if bool(args.before) != bool(args.after):
        print("Comparison not run: --before and --after must be supplied together.")
        return 2

    config = load_config()
    if not config.get("UVB_PRIVATE_ARTIFACT_ROOT", "").strip():
        print("Comparison not run: UVB_PRIVATE_ARTIFACT_ROOT is not configured.")
        return 2
    private_root = private_directory(config)

    try:
        if args.before and args.after:
            before = resolve_capture_directory(private_root, args.before)
            after = resolve_capture_directory(private_root, args.after)
        else:
            captures = capture_directories(private_root)
            if len(captures) < 2:
                print("Comparison not run: two private candidate captures are required.")
                return 2
            before, after = captures[-2:]
            print(
                "Warning: --before and --after were not supplied; using the two "
                "newest private candidate captures for compatibility.",
                file=sys.stderr,
            )
        rollback = (
            resolve_capture_directory(private_root, args.rollback)
            if args.rollback
            else None
        )

        selected_roots = {
            capture_root(capture, private_root)
            for capture in (before, after, rollback)
            if capture is not None
        }
        if len(selected_roots) != 1:
            print("Comparison not run: selected captures have different FTPS roots.")
            return 2

        before_items = manifest_items(before)
        after_items = manifest_items(after)
        _, paired_changes = saved_change_summary(before_items, after_items)

        status = 0
        if args.expect_stem:
            expected_changed = any(
                Path(stem).name == args.expect_stem for stem in paired_changes
            )
            print(
                "Expected logical CJSON/VM pair changed: "
                + ("yes." if expected_changed else "no.")
            )
            if not expected_changed:
                status = 1

        if rollback is not None:
            rollback_items = manifest_items(rollback)
            if not rollback_matches_baseline(before_items, rollback_items):
                status = 1
        return status
    except (
        FileNotFoundError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        print(f"Comparison not run: {error}.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
