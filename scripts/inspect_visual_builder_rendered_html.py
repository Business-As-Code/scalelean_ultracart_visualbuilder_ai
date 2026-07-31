#!/usr/bin/env python3
"""Inspect rendered Visual Builder HTML without exposing page content."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from typing import Sequence


MAX_HTML_BYTES = 64 * 1024 * 1024
MAX_WIDGET_TYPE_LENGTH = 128
SAFE_WIDGET_TYPE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")

# HTMLParser does not implicitly close void elements. Keeping them off the
# element stack prevents a widget-bearing image or input from becoming the
# apparent parent of later siblings.
VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "command",
    "embed",
    "hr",
    "img",
    "input",
    "keygen",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class InputError(ValueError):
    """Report an input problem without retaining or displaying private data."""


def validated_widget_type(value: str | None) -> str | None:
    """Return a safe widget type token, or None for an unsafe value."""

    if value is None or len(value) > MAX_WIDGET_TYPE_LENGTH:
        return None
    if not SAFE_WIDGET_TYPE.fullmatch(value):
        return None
    return value


class RenderedWidgetParser(HTMLParser):
    """Collect type-level hierarchy evidence from one rendered HTML document."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.widget_type_counts: Counter[str] = Counter()
        self.root_widget_type_counts: Counter[str] = Counter()
        self.nearest_widget_parent_child_type_edge_counts: Counter[str] = Counter()
        self.invalid_widget_type_attribute_count = 0
        self._element_stack: list[tuple[str, str | None]] = []

    def _widget_type(self, attrs: list[tuple[str, str | None]]) -> str | None:
        values = [
            value
            for name, value in attrs
            if name.lower() == "data-widget-type"
        ]
        if not values:
            return None
        if len(values) != 1:
            self.invalid_widget_type_attribute_count += 1
            return None
        value = validated_widget_type(values[0])
        if value is None:
            self.invalid_widget_type_attribute_count += 1
        return value

    def _record_widget(self, attrs: list[tuple[str, str | None]]) -> str | None:
        widget_type = self._widget_type(attrs)
        if widget_type is None:
            return None

        self.widget_type_counts[widget_type] += 1
        parent_type = next(
            (
                candidate
                for _tag, candidate in reversed(self._element_stack)
                if candidate is not None
            ),
            None,
        )
        if parent_type is None:
            self.root_widget_type_counts[widget_type] += 1
        else:
            edge = f"{parent_type}>{widget_type}"
            self.nearest_widget_parent_child_type_edge_counts[edge] += 1
        return widget_type

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        normalized_tag = tag.lower()
        widget_type = self._record_widget(attrs)
        if normalized_tag not in VOID_ELEMENTS:
            self._element_stack.append((normalized_tag, widget_type))

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self._record_widget(attrs)

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        for index in range(len(self._element_stack) - 1, -1, -1):
            if self._element_stack[index][0] == normalized_tag:
                del self._element_stack[index:]
                return

    def summary(self) -> dict[str, object]:
        widget_count = sum(self.widget_type_counts.values())
        root_widget_count = sum(self.root_widget_type_counts.values())
        return {
            "invalid_widget_type_attribute_count": (
                self.invalid_widget_type_attribute_count
            ),
            "nearest_widget_parent_child_type_edge_counts": dict(
                sorted(self.nearest_widget_parent_child_type_edge_counts.items())
            ),
            "root_widget_count": root_widget_count,
            "root_widget_type_counts": dict(
                sorted(self.root_widget_type_counts.items())
            ),
            "widget_count": widget_count,
            "widget_type_counts": dict(sorted(self.widget_type_counts.items())),
        }


def summarize_rendered_html(source: str) -> dict[str, object]:
    """Return a deterministic aggregate hierarchy summary."""

    parser = RenderedWidgetParser()
    try:
        parser.feed(source)
        parser.close()
    except (AssertionError, ValueError) as error:
        raise InputError("rendered HTML could not be parsed") from error
    return parser.summary()


def _count_delta(
    reference: dict[str, int], target: dict[str, int]
) -> dict[str, object]:
    reference_counts = Counter(reference)
    target_counts = Counter(target)
    missing = reference_counts - target_counts
    excess = target_counts - reference_counts
    return {
        "excess_counts": dict(sorted(excess.items())),
        "excess_total": sum(excess.values()),
        "missing_counts": dict(sorted(missing.items())),
        "missing_total": sum(missing.values()),
    }


def compare_summaries(
    reference: dict[str, object], target: dict[str, object]
) -> dict[str, object]:
    """Compare aggregate hierarchy counts without exposing document details."""

    categories = {
        "nearest_widget_parent_child_type_edges": (
            "nearest_widget_parent_child_type_edge_counts"
        ),
        "root_widget_types": "root_widget_type_counts",
        "widget_types": "widget_type_counts",
    }
    comparison: dict[str, object] = {}
    matched = True
    for output_name, summary_name in categories.items():
        delta = _count_delta(reference[summary_name], target[summary_name])
        comparison[output_name] = delta
        if delta["missing_total"] or delta["excess_total"]:
            matched = False
    comparison["matched"] = matched
    return comparison


def _format_counts(values: dict[str, int]) -> str:
    if not values:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in values.items())


def _render_summary(label: str, summary: dict[str, object]) -> list[str]:
    return [
        f"{label}:",
        f"  widgets: {summary['widget_count']}",
        f"  root widgets: {summary['root_widget_count']}",
        "  widget types: " + _format_counts(summary["widget_type_counts"]),
        "  root widget types: "
        + _format_counts(summary["root_widget_type_counts"]),
        "  nearest-widget edges: "
        + _format_counts(
            summary["nearest_widget_parent_child_type_edge_counts"]
        ),
        "  invalid widget type attributes: "
        + str(summary["invalid_widget_type_attribute_count"]),
    ]


def render_text(
    target: dict[str, object],
    reference: dict[str, object] | None = None,
    comparison: dict[str, object] | None = None,
) -> str:
    lines = ["Rendered Visual Builder HTML summary"]
    lines.extend(_render_summary("target", target))
    if reference is None or comparison is None:
        return "\n".join(lines)

    lines.extend(_render_summary("reference", reference))
    lines.append("comparison:")
    for name in (
        "widget_types",
        "root_widget_types",
        "nearest_widget_parent_child_type_edges",
    ):
        delta = comparison[name]
        label = name.replace("_", " ")
        lines.append(
            f"  {label} missing: " + _format_counts(delta["missing_counts"])
        )
        lines.append(
            f"  {label} excess: " + _format_counts(delta["excess_counts"])
        )
    lines.append("  matched: " + ("yes" if comparison["matched"] else "no"))
    return "\n".join(lines)


def _read_html(path_value: str) -> str:
    path = Path(path_value)
    try:
        with path.open("rb") as handle:
            source = handle.read(MAX_HTML_BYTES + 1)
    except OSError as error:
        raise InputError("rendered HTML input is unavailable") from error
    if len(source) > MAX_HTML_BYTES:
        raise InputError("rendered HTML input is too large")
    try:
        return source.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise InputError("rendered HTML input is not valid UTF-8") from error


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize rendered Visual Builder hierarchy attributes without "
            "printing HTML, paths, URLs, IDs, or page content."
        )
    )
    parser.add_argument("target_html", metavar="TARGET_HTML")
    parser.add_argument(
        "--reference",
        metavar="REFERENCE_HTML",
        help="compare one explicit reference snapshot with the target",
    )
    parser.add_argument(
        "--require-match",
        action="store_true",
        help="return a mismatch exit code unless all compared aggregate counts match",
    )
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.require_match and args.reference is None:
        if args.json:
            print(json.dumps({"error": "input_error"}, sort_keys=True), file=sys.stderr)
        else:
            print("error: --require-match needs an explicit reference", file=sys.stderr)
        return 2
    try:
        target = summarize_rendered_html(_read_html(args.target_html))
        reference = None
        comparison = None
        if args.reference is not None:
            reference = summarize_rendered_html(_read_html(args.reference))
            comparison = compare_summaries(reference, target)
    except InputError as error:
        if args.json:
            print(json.dumps({"error": "input_error"}, sort_keys=True), file=sys.stderr)
        else:
            print(f"error: {error}", file=sys.stderr)
        return 2

    if args.json:
        payload: dict[str, object] = {"target": target}
        if reference is not None and comparison is not None:
            payload["comparison"] = comparison
            payload["reference"] = reference
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(target, reference, comparison))
    if args.require_match and comparison is not None and not comparison["matched"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
