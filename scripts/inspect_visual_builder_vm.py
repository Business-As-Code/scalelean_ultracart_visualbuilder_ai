#!/usr/bin/env python3
"""Inspect generated Visual Builder Velocity without exposing source content."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import hmac
import json
from pathlib import Path
import re
import sys
from typing import Iterable, Sequence


MAX_VM_BYTES = 64 * 1024 * 1024
MAX_LITERAL_BYTES = 1024 * 1024
MAX_PATTERN_LENGTH = 4096
SAFE_WIDGET_TYPE = re.compile(r"^[A-Za-z0-9_.:-]+$")
SAFE_BASENAME = re.compile(r"^[A-Za-z0-9_.@${}:-]+$")
SAFE_CLASS = re.compile(r"^[A-Za-z0-9_.:-]+$")

WIDGET_TYPE_ATTRIBUTE = re.compile(
    r"""(?<![A-Za-z0-9_:-])data-widget-type\s*=\s*(?:
        "(?P<double>[A-Za-z0-9_.:-]+)"
        |'(?P<single>[A-Za-z0-9_.:-]+)'
        |(?P<bare>[A-Za-z0-9_.:-]+)
    )""",
    re.IGNORECASE | re.VERBOSE,
)
CLASS_ATTRIBUTE = re.compile(
    r"""(?<![A-Za-z0-9_:-])class\s*=\s*(?:
        "(?P<double>[^"\r\n]*)"
        |'(?P<single>[^'\r\n]*)'
        |(?P<bare>[^\s>'"]+)
    )""",
    re.IGNORECASE | re.VERBOSE,
)
CLONE_ATTRIBUTE = re.compile(
    r"""(?<![A-Za-z0-9_:-])(?P<name>data-[A-Za-z0-9_:-]*clone[A-Za-z0-9_:-]*)\s*=\s*(?:
        "(?P<double>[^"\r\n]*)"
        |'(?P<single>[^'\r\n]*)'
        |(?P<bare>[^\s>'"]+)
    )""",
    re.IGNORECASE | re.VERBOSE,
)
STATIC_PARSE = re.compile(
    r"""\#\s*parse\s*\(\s*(?:
        "(?P<double>[^"\r\n]+)"
        |'(?P<single>[^'\r\n]+)'
    )\s*\)""",
    re.IGNORECASE | re.VERBOSE,
)
ANY_PARSE = re.compile(r"\#\s*parse\b", re.IGNORECASE)
VELOCITY_BLOCK_COMMENT = re.compile(r"#\*.*?\*#", re.DOTALL)
VELOCITY_LINE_COMMENT = re.compile(r"##[^\r\n]*")
ANY_ML_STRING_CALL = re.compile(
    r"\$(?:\{\s*)?i18n\.writeMlString\s*\("
)
STATIC_ML_STRING_CALL = re.compile(
    r'''\$(?:\{\s*)?i18n\.writeMlString\s*\(\s*
        "[^"\r\n]*"\s*,\s*
        "[^"\r\n]*"\s*,\s*
        (?:true|false)\s*,\s*
        "(?P<payload>(?:[0-9A-F]{2})*)"\s*
    \)''',
    re.VERBOSE,
)

RESPONSIVE_VISIBILITY_PATTERNS = (
    re.compile(
        r"^(?:show|hide|visible|hidden)(?:-for)?-"
        r"(?:small|medium|large|xlarge|xxlarge|sm|md|lg|xl|xxl|mobile|tablet|desktop)"
        r"(?:-(?:only|up|down))?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^d-(?:sm|md|lg|xl|xxl)-"
        r"(?:none|block|inline|inline-block|flex|inline-flex|grid|table|table-cell)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:sm|md|lg|xl|xxl):"
        r"(?:hidden|block|inline|inline-block|flex|inline-flex|grid|table)$",
        re.IGNORECASE,
    ),
)


class InputError(ValueError):
    """Raised for invalid verifier input without retaining sensitive details."""


@dataclass(frozen=True)
class AssertionResult:
    kind: str
    index: int
    passed: bool
    subject: str | None = None


@dataclass(frozen=True)
class Expectations:
    required_widget_types: tuple[str, ...] = ()
    prohibited_widget_types: tuple[str, ...] = ()
    required_literals: tuple[str, ...] = ()
    required_ml_literals: tuple[str, ...] = ()
    required_parse_basenames: tuple[str, ...] = ()
    required_regexes: tuple[str, ...] = ()
    prohibited_regexes: tuple[str, ...] = ()


def _matched_value(match: re.Match[str]) -> str:
    for name in ("double", "single", "bare"):
        value = match.groupdict().get(name)
        if value is not None:
            return value
    raise AssertionError("attribute regular expression returned no value")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _count(source: str, pattern: str, flags: int = 0) -> int:
    return sum(1 for _ in re.finditer(pattern, source, flags))


def _is_responsive_visibility_class(value: str) -> bool:
    if not SAFE_CLASS.fullmatch(value):
        return False
    return any(pattern.fullmatch(value) for pattern in RESPONSIVE_VISIBILITY_PATTERNS)


def _basename(target: str) -> str:
    return target.replace("\\", "/").rsplit("/", 1)[-1]


def _summarize_parse_targets(source: str) -> tuple[list[dict[str, object]], set[str], int]:
    target_counts: Counter[str] = Counter()
    for match in STATIC_PARSE.finditer(source):
        target_counts[_matched_value(match)] += 1

    records: list[dict[str, object]] = []
    basenames: set[str] = set()
    for target, count in target_counts.items():
        basename = _basename(target)
        basenames.add(basename)
        record: dict[str, object] = {
            "count": count,
            "target_sha256": _sha256(target),
        }
        if SAFE_BASENAME.fullmatch(basename):
            record["basename"] = basename
        else:
            record["basename_sha256"] = _sha256(basename)
        records.append(record)

    records.sort(
        key=lambda item: (
            str(item.get("basename", "")),
            str(item.get("basename_sha256", "")),
            str(item["target_sha256"]),
        )
    )
    static_count = sum(target_counts.values())
    dynamic_count = max(0, len(ANY_PARSE.findall(source)) - static_count)
    return records, basenames, dynamic_count


def _without_velocity_comments(source: str) -> str:
    return VELOCITY_LINE_COMMENT.sub("", VELOCITY_BLOCK_COMMENT.sub("", source))


def summarize_vm(source: str) -> dict[str, object]:
    """Return a deterministic summary containing no source or matched values."""

    widget_types: Counter[str] = Counter(
        _matched_value(match) for match in WIDGET_TYPE_ATTRIBUTE.finditer(source)
    )

    responsive_classes: Counter[str] = Counter()
    for match in CLASS_ATTRIBUTE.finditer(source):
        for token in _matched_value(match).split():
            if _is_responsive_visibility_class(token):
                responsive_classes[token] += 1

    clone_attributes: Counter[str] = Counter()
    clone_root_count = 0
    clone_root_hashes: set[str] = set()
    for match in CLONE_ATTRIBUTE.finditer(source):
        name = match.group("name").lower()
        clone_attributes[name] += 1
        compact_name = re.sub(r"[^a-z0-9]", "", name)
        if "cloneroot" in compact_name:
            clone_root_count += 1
            clone_root_hashes.add(_sha256(_matched_value(match)))

    parse_targets, parse_basenames, dynamic_parse_count = _summarize_parse_targets(source)

    executable_source = _without_velocity_comments(source)
    ml_payload_digests: set[bytes] = set()
    nonempty_ml_payload_count = 0
    invalid_utf8_ml_payload_count = 0
    static_ml_call_count = 0
    for match in STATIC_ML_STRING_CALL.finditer(executable_source):
        static_ml_call_count += 1
        payload_hex = match.group("payload")
        if payload_hex:
            nonempty_ml_payload_count += 1
        payload_bytes = bytes.fromhex(payload_hex)
        try:
            payload_bytes.decode("utf-8")
        except UnicodeDecodeError:
            invalid_utf8_ml_payload_count += 1
        ml_payload_digests.add(hashlib.sha256(payload_bytes).digest())

    return {
        "byte_count": len(source.encode("utf-8")),
        "line_count": len(source.splitlines()),
        "widget_type_counts": dict(sorted(widget_types.items())),
        "clone": {
            "attribute_counts": dict(sorted(clone_attributes.items())),
            "root_attribute_count": clone_root_count,
            "root_value_sha256": sorted(clone_root_hashes),
            "signal_counts": {
                "clone_foreach": _count(
                    source,
                    r"\#\s*foreach\s*\([^)]*\bclone\b",
                    re.IGNORECASE | re.DOTALL,
                ),
                "clone_identifier": _count(
                    source,
                    r"\b(?:cloneRoot|cloneId|cloneIndex|isClone|clonedFrom)\b",
                    re.IGNORECASE,
                ),
                "clone_velocity_reference": _count(
                    source,
                    r"\$(?:!)?(?:\{)?[A-Za-z_][A-Za-z0-9_.]*clone[A-Za-z0-9_.}]*",
                    re.IGNORECASE,
                ),
            },
        },
        "responsive_visibility_class_counts": dict(sorted(responsive_classes.items())),
        "visibility_signal_counts": {
            "hide_ancestor": _count(
                source,
                r"\bhide[-_:]*ancestor(?:\b|(?=if))",
                re.IGNORECASE,
            ),
            "hide_ancestor_if_empty": _count(
                source,
                r"\bhide[-_:]*ancestor[-_:]*if[-_:]*empty\b",
                re.IGNORECASE,
            ),
            "widget_hidden": _count(source, r"\bwidget-hidden\b", re.IGNORECASE),
        },
        "parse_targets": parse_targets,
        "dynamic_parse_count": dynamic_parse_count,
        "dynamic_signal_counts": {
            "checkout_condition": _count(
                source,
                r"\#\s*(?:if|elseif)\s*\([^)]*\bcheckout\b[^)]*\)",
                re.IGNORECASE | re.DOTALL,
            ),
            "foreach": _count(source, r"\#\s*foreach\b", re.IGNORECASE),
            "group_context": _count(
                source,
                r"\$(?:!)?(?:\{)?group(?:\b|[.}\[])",
                re.IGNORECASE,
            ),
            "item_context": _count(
                source,
                r"\$(?:!)?(?:\{)?item(?:\b|[.}\[])",
                re.IGNORECASE,
            ),
            "menu_manager": _count(
                source,
                r"\$(?:!)?(?:\{)?menuManager\b",
                re.IGNORECASE,
            ),
        },
        "i18n_ml_string_counts": {
            "write_call_count": len(ANY_ML_STRING_CALL.findall(executable_source)),
            "static_hex_call_count": static_ml_call_count,
            "nonempty_static_hex_call_count": nonempty_ml_payload_count,
            "invalid_utf8_payload_count": invalid_utf8_ml_payload_count,
        },
        "_parse_basenames": parse_basenames,
        "_ml_payload_digests": ml_payload_digests,
    }


def _validate_expectations(expectations: Expectations) -> None:
    for value in expectations.required_widget_types + expectations.prohibited_widget_types:
        if not SAFE_WIDGET_TYPE.fullmatch(value):
            raise InputError("invalid widget type assertion")
    for value in expectations.required_parse_basenames:
        if (
            not value
            or _basename(value) != value
            or not SAFE_BASENAME.fullmatch(value)
        ):
            raise InputError("invalid parse basename assertion")
    for value in expectations.required_literals + expectations.required_ml_literals:
        if not value:
            raise InputError("empty literal assertion")
        if len(value.encode("utf-8")) > MAX_LITERAL_BYTES:
            raise InputError("literal assertion is too large")
    for values, kind in (
        (expectations.required_regexes, "required"),
        (expectations.prohibited_regexes, "prohibited"),
    ):
        for index, value in enumerate(values, start=1):
            if not value or len(value) > MAX_PATTERN_LENGTH:
                raise InputError(f"invalid {kind} regex at index {index}")
            try:
                re.compile(value, re.MULTILINE)
            except re.error as error:
                raise InputError(f"invalid {kind} regex at index {index}") from error


def _literal_present(source: str, expected: str) -> bool:
    start = source.find(expected)
    if start < 0:
        return False
    actual = source[start : start + len(expected)]
    return hmac.compare_digest(_sha256(actual), _sha256(expected))


def evaluate_assertions(
    source: str,
    summary: dict[str, object],
    expectations: Expectations,
) -> list[AssertionResult]:
    """Evaluate repeatable assertions without retaining private match values."""

    _validate_expectations(expectations)
    widget_types = set(summary["widget_type_counts"])
    parse_basenames = set(summary["_parse_basenames"])
    ml_payload_digests = set(summary["_ml_payload_digests"])
    results: list[AssertionResult] = []

    for index, value in enumerate(expectations.required_widget_types, start=1):
        results.append(AssertionResult("required_widget_type", index, value in widget_types, value))
    for index, value in enumerate(expectations.prohibited_widget_types, start=1):
        results.append(AssertionResult("prohibited_widget_type", index, value not in widget_types, value))
    for index, value in enumerate(expectations.required_literals, start=1):
        results.append(
            AssertionResult(
                "required_literal_sha256",
                index,
                _literal_present(source, value),
            )
        )
    for index, value in enumerate(expectations.required_ml_literals, start=1):
        expected_digest = hashlib.sha256(value.encode("utf-8")).digest()
        results.append(
            AssertionResult(
                "required_ml_literal_sha256",
                index,
                any(
                    hmac.compare_digest(expected_digest, actual_digest)
                    for actual_digest in ml_payload_digests
                ),
            )
        )
    for index, value in enumerate(expectations.required_parse_basenames, start=1):
        results.append(
            AssertionResult("required_parse_basename", index, value in parse_basenames, value)
        )
    for index, value in enumerate(expectations.required_regexes, start=1):
        pattern = re.compile(value, re.MULTILINE)
        results.append(
            AssertionResult("required_regex", index, pattern.search(source) is not None)
        )
    for index, value in enumerate(expectations.prohibited_regexes, start=1):
        pattern = re.compile(value, re.MULTILINE)
        results.append(
            AssertionResult("prohibited_regex", index, pattern.search(source) is None)
        )
    return results


def _public_summary(summary: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in summary.items() if not key.startswith("_")}


def _format_counts(values: dict[str, int]) -> str:
    if not values:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in values.items())


def render_text(summary: dict[str, object], assertions: Sequence[AssertionResult]) -> str:
    public = _public_summary(summary)
    clone = public["clone"]
    lines = [
        "Visual Builder VM summary",
        f"bytes: {public['byte_count']}",
        f"lines: {public['line_count']}",
        "widget types: " + _format_counts(public["widget_type_counts"]),
        "clone attributes: " + _format_counts(clone["attribute_counts"]),
        f"clone root attributes: {clone['root_attribute_count']}",
        f"clone root value hashes: {len(clone['root_value_sha256'])}",
        "clone signals: " + _format_counts(clone["signal_counts"]),
        "responsive visibility classes: "
        + _format_counts(public["responsive_visibility_class_counts"]),
        "visibility signals: " + _format_counts(public["visibility_signal_counts"]),
        "dynamic signals: " + _format_counts(public["dynamic_signal_counts"]),
        "i18n multilingual strings: "
        + _format_counts(public["i18n_ml_string_counts"]),
        f"dynamic parse directives: {public['dynamic_parse_count']}",
        "parse targets:",
    ]
    parse_targets = public["parse_targets"]
    if not parse_targets:
        lines.append("  none")
    else:
        for record in parse_targets:
            label = record.get("basename")
            if label is None:
                label = "basename-sha256=" + str(record["basename_sha256"])
            lines.append(
                f"  {label} count={record['count']} target-sha256={record['target_sha256']}"
            )

    lines.append("assertions:")
    if not assertions:
        lines.append("  none")
    else:
        for result in assertions:
            status = "PASS" if result.passed else "FAIL"
            subject = f" {result.subject}" if result.subject is not None else ""
            lines.append(f"  {status} {result.kind}[{result.index}]{subject}")
    lines.append("result: " + ("pass" if all(item.passed for item in assertions) else "fail"))
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize one generated Visual Builder VM without printing its source.",
    )
    parser.add_argument("vm_path", help="explicit private generated VM path")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    parser.add_argument("--require-widget-type", action="append", default=[], metavar="TYPE")
    parser.add_argument("--prohibit-widget-type", action="append", default=[], metavar="TYPE")
    parser.add_argument(
        "--require-literal-sha256",
        "--require-literal",
        dest="required_literals",
        action="append",
        default=[],
        metavar="TEXT",
        help=(
            "require exact non-secret text; output contains only pass or fail, "
            "but the argument remains visible to the local process list"
        ),
    )
    parser.add_argument(
        "--require-literal-file",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "read one exact private literal from a local UTF-8 file; output "
            "contains only pass or fail"
        ),
    )
    parser.add_argument(
        "--require-ml-literal",
        dest="required_ml_literals",
        action="append",
        default=[],
        metavar="TEXT",
        help=(
            "require one complete UTF-8 literal encoded as the fourth argument "
            "of a static i18n.writeMlString call; the argument remains visible "
            "to the local process list"
        ),
    )
    parser.add_argument(
        "--require-ml-literal-file",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "read one private UTF-8 literal and require its complete encoded "
            "i18n.writeMlString payload; output contains only pass or fail"
        ),
    )
    parser.add_argument(
        "--require-parse-basename",
        action="append",
        default=[],
        metavar="BASENAME",
    )
    parser.add_argument("--require-regex", action="append", default=[], metavar="PATTERN")
    parser.add_argument("--prohibit-regex", action="append", default=[], metavar="PATTERN")
    return parser


def _read_vm(path_value: str) -> str:
    path = Path(path_value)
    try:
        if not path.is_file() or path.stat().st_size > MAX_VM_BYTES:
            raise InputError("input VM is unavailable or too large")
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise InputError("input VM could not be read as UTF-8") from error


def _read_literal_file(path_value: str) -> str:
    path = Path(path_value)
    try:
        if not path.is_file() or path.stat().st_size > MAX_LITERAL_BYTES:
            raise InputError("literal assertion file is unavailable or too large")
        value = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise InputError("literal assertion file could not be read as UTF-8") from error
    if not value:
        raise InputError("literal assertion file is empty")
    return value


def _expectations_from_args(args: argparse.Namespace) -> Expectations:
    file_literals = tuple(_read_literal_file(path) for path in args.require_literal_file)
    ml_file_literals = tuple(
        _read_literal_file(path) for path in args.require_ml_literal_file
    )
    return Expectations(
        required_widget_types=tuple(args.require_widget_type),
        prohibited_widget_types=tuple(args.prohibit_widget_type),
        required_literals=tuple(args.required_literals) + file_literals,
        required_ml_literals=tuple(args.required_ml_literals) + ml_file_literals,
        required_parse_basenames=tuple(args.require_parse_basename),
        required_regexes=tuple(args.require_regex),
        prohibited_regexes=tuple(args.prohibit_regex),
    )


def _json_output(
    summary: dict[str, object], assertions: Iterable[AssertionResult]
) -> str:
    assertions_list = list(assertions)
    payload = {
        "assertions": [asdict(item) for item in assertions_list],
        "passed": all(item.passed for item in assertions_list),
        "summary": _public_summary(summary),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        source = _read_vm(args.vm_path)
        summary = summarize_vm(source)
        assertions = evaluate_assertions(source, summary, _expectations_from_args(args))
    except InputError as error:
        if args.json:
            print(json.dumps({"error": "input_error"}, sort_keys=True), file=sys.stderr)
        else:
            print(f"error: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(_json_output(summary, assertions))
    else:
        print(render_text(summary, assertions))
    return 0 if all(item.passed for item in assertions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
