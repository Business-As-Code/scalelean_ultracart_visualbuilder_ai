from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from inspect_visual_builder_vm import Expectations, evaluate_assertions, main, summarize_vm


SECRET_LITERAL = "private-offer-copy-9f41"
SECRET_CLONE_ROOT = "customer/private/root-77"
REQUIRED_PATTERN = r"data-control-id=\"purchase-[0-9]+\""
ML_LITERAL = "Café 🚀"
ML_LITERAL_HEX = ML_LITERAL.encode("utf-8").hex().upper()


def synthetic_vm() -> str:
    return f'''#set($privateValue = "{SECRET_LITERAL}")
<section data-widget-type="row" data-clone-root="{SECRET_CLONE_ROOT}"
  data-class="hide-for-large" class="show-for-medium widget-hidden">
  <div data-widget-type='headline' class='d-lg-none hide-for-small-only'>Safe heading</div>
</section>
#parse("/themes/Elements/theme/containers/header.vm")
#parse('/alternate/path/header.vm')
#parse($dynamicTemplate)
#foreach($item in $items)
  $menuManager.render($item)
#end
$group.code
#if($checkout)
  <button data-control-id="purchase-42">Buy</button>
#end
hideAncestorIfEmpty
${{i18n.writeMlString("probe-widget", "richText", true, "{ML_LITERAL_HEX}")}}
'''


class InspectVisualBuilderVmTests(unittest.TestCase):
    def test_summary_reports_required_generated_vm_signals(self) -> None:
        report = summarize_vm(synthetic_vm())

        self.assertEqual(report["widget_type_counts"], {"headline": 1, "row": 1})
        self.assertEqual(report["clone"]["root_attribute_count"], 1)
        self.assertEqual(len(report["clone"]["root_value_sha256"]), 1)
        self.assertEqual(
            report["responsive_visibility_class_counts"],
            {"d-lg-none": 1, "hide-for-small-only": 1, "show-for-medium": 1},
        )
        self.assertEqual(report["visibility_signal_counts"]["widget_hidden"], 1)
        self.assertEqual(report["visibility_signal_counts"]["hide_ancestor"], 1)
        self.assertEqual(report["visibility_signal_counts"]["hide_ancestor_if_empty"], 1)
        self.assertEqual(report["dynamic_signal_counts"]["foreach"], 1)
        self.assertGreaterEqual(report["dynamic_signal_counts"]["item_context"], 2)
        self.assertEqual(report["dynamic_signal_counts"]["group_context"], 1)
        self.assertEqual(report["dynamic_signal_counts"]["menu_manager"], 1)
        self.assertEqual(report["dynamic_signal_counts"]["checkout_condition"], 1)
        self.assertEqual(
            report["i18n_ml_string_counts"],
            {
                "write_call_count": 1,
                "static_hex_call_count": 1,
                "nonempty_static_hex_call_count": 1,
                "invalid_utf8_payload_count": 0,
            },
        )

    def test_parse_detection_reports_only_basename_and_hash(self) -> None:
        report = summarize_vm(synthetic_vm())

        self.assertEqual(report["dynamic_parse_count"], 1)
        self.assertEqual(len(report["parse_targets"]), 2)
        self.assertEqual(
            {record["basename"] for record in report["parse_targets"]},
            {"header.vm"},
        )
        self.assertEqual(
            len({record["target_sha256"] for record in report["parse_targets"]}),
            2,
        )
        serialized = json.dumps(report["parse_targets"], sort_keys=True)
        self.assertNotIn("/themes/", serialized)
        self.assertNotIn("/alternate/", serialized)

    def test_repeatable_assertions_pass_and_fail(self) -> None:
        source = synthetic_vm()
        report = summarize_vm(source)
        passing = Expectations(
            required_widget_types=("row", "headline"),
            prohibited_widget_types=("image",),
            required_literals=(SECRET_LITERAL,),
            required_ml_literals=(ML_LITERAL,),
            required_parse_basenames=("header.vm",),
            required_regexes=(REQUIRED_PATTERN,),
            prohibited_regexes=(r"data-widget-type=\"image\"",),
        )
        failing = Expectations(
            required_widget_types=("image",),
            prohibited_widget_types=("row",),
            required_literals=("missing-private-value",),
            required_ml_literals=("missing multilingual value",),
            required_parse_basenames=("footer.vm",),
            required_regexes=(r"never-matches-[0-9]+",),
            prohibited_regexes=(REQUIRED_PATTERN,),
        )

        self.assertTrue(all(item.passed for item in evaluate_assertions(source, report, passing)))
        self.assertTrue(
            all(not item.passed for item in evaluate_assertions(source, report, failing))
        )

    def test_cli_exit_codes_and_source_safe_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vm_path = Path(directory) / "private.vm"
            vm_path.write_text(synthetic_vm(), encoding="utf-8")
            literal_path = Path(directory) / "expected-literal.txt"
            literal_path.write_text(SECRET_LITERAL, encoding="utf-8")
            ml_literal_path = Path(directory) / "expected-ml-literal.txt"
            ml_literal_path.write_text(ML_LITERAL, encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                passing_code = main(
                    [
                        str(vm_path),
                        "--json",
                        "--require-widget-type",
                        "row",
                        "--prohibit-widget-type",
                        "image",
                        "--require-literal-file",
                        str(literal_path),
                        "--require-ml-literal-file",
                        str(ml_literal_path),
                        "--require-parse-basename",
                        "header.vm",
                        "--require-regex",
                        REQUIRED_PATTERN,
                        "--prohibit-regex",
                        r"secret-regex-never-matches",
                    ]
                )

            output = stdout.getvalue() + stderr.getvalue()
            self.assertEqual(passing_code, 0)
            self.assertNotIn(SECRET_LITERAL, output)
            self.assertNotIn(SECRET_CLONE_ROOT, output)
            self.assertNotIn(ML_LITERAL, output)
            self.assertNotIn(ML_LITERAL_HEX, output)
            self.assertNotIn(hashlib.sha256(ML_LITERAL.encode("utf-8")).hexdigest(), output)
            self.assertNotIn(REQUIRED_PATTERN, output)
            self.assertNotIn(str(vm_path), output)
            self.assertNotIn(str(literal_path), output)
            self.assertNotIn(str(ml_literal_path), output)
            self.assertNotIn("/themes/Elements", output)

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                failing_code = main(
                    [str(vm_path), "--require-widget-type", "image"]
                )
            self.assertEqual(failing_code, 1)

    def test_invalid_regex_is_input_error_and_pattern_is_not_echoed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vm_path = Path(directory) / "private.vm"
            vm_path.write_text(synthetic_vm(), encoding="utf-8")
            invalid_pattern = "private-pattern-("
            stdout = io.StringIO()
            stderr = io.StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main([str(vm_path), "--require-regex", invalid_pattern])

            self.assertEqual(code, 2)
            self.assertNotIn(invalid_pattern, stdout.getvalue() + stderr.getvalue())

    def test_missing_input_returns_input_error_without_path_echo(self) -> None:
        missing = "/private/nonexistent/customer-artifact.vm"
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main([missing])

        self.assertEqual(code, 2)
        self.assertNotIn(missing, stdout.getvalue() + stderr.getvalue())

    def test_missing_literal_file_is_input_error_without_path_echo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vm_path = Path(directory) / "private.vm"
            vm_path.write_text(synthetic_vm(), encoding="utf-8")
            missing = str(Path(directory) / "private-missing-literal.txt")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main([str(vm_path), "--require-literal-file", missing])

            self.assertEqual(code, 2)
            self.assertNotIn(missing, stdout.getvalue() + stderr.getvalue())

    def test_ml_literal_match_is_complete_and_static_uppercase_only(self) -> None:
        source = synthetic_vm()
        report = summarize_vm(source)

        exact = evaluate_assertions(
            source, report, Expectations(required_ml_literals=(ML_LITERAL,))
        )
        prefix = evaluate_assertions(
            source, report, Expectations(required_ml_literals=("Café",))
        )
        plain = evaluate_assertions(
            source, report, Expectations(required_literals=(ML_LITERAL,))
        )

        self.assertTrue(exact[0].passed)
        self.assertFalse(prefix[0].passed)
        self.assertFalse(plain[0].passed)

        invalid_source = '\n'.join(
            [
                '$i18n.writeMlString("a", "b", true, "636166c3a9")',
                '$i18n.writeMlString("a", "b", true, "ABC")',
                '$i18n.writeMlString("a", "b", true, "GG")',
                '$i18n.writeMlString("a", "b", true, $dynamic)',
            ]
        )
        invalid_report = summarize_vm(invalid_source)
        self.assertEqual(invalid_report["i18n_ml_string_counts"]["write_call_count"], 4)
        self.assertEqual(invalid_report["i18n_ml_string_counts"]["static_hex_call_count"], 0)

    def test_ml_literal_ignores_comments_and_non_invocation_lookalikes(self) -> None:
        lookalikes = '\n'.join(
            [
                f'## $i18n.writeMlString("a", "b", true, "{ML_LITERAL_HEX}")',
                f'#* $i18n.writeMlString("a", "b", true, "{ML_LITERAL_HEX}") *#',
                f'i18n.writeMlString("a", "b", true, "{ML_LITERAL_HEX}")',
                f'$foo.i18n.writeMlString("a", "b", true, "{ML_LITERAL_HEX}")',
            ]
        )
        report = summarize_vm(lookalikes)
        result = evaluate_assertions(
            lookalikes, report, Expectations(required_ml_literals=(ML_LITERAL,))
        )

        self.assertEqual(report["i18n_ml_string_counts"]["write_call_count"], 0)
        self.assertEqual(report["i18n_ml_string_counts"]["static_hex_call_count"], 0)
        self.assertFalse(result[0].passed)

    def test_invalid_utf8_ml_payload_is_counted_but_not_matched(self) -> None:
        source = '$i18n.writeMlString("a", "b", true, "FF")'
        report = summarize_vm(source)
        result = evaluate_assertions(
            source, report, Expectations(required_ml_literals=("ÿ",))
        )

        self.assertEqual(report["i18n_ml_string_counts"]["write_call_count"], 1)
        self.assertEqual(report["i18n_ml_string_counts"]["static_hex_call_count"], 1)
        self.assertEqual(report["i18n_ml_string_counts"]["invalid_utf8_payload_count"], 1)
        self.assertFalse(result[0].passed)

    def test_missing_ml_literal_file_is_redacted_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vm_path = Path(directory) / "private.vm"
            vm_path.write_text(synthetic_vm(), encoding="utf-8")
            missing = str(Path(directory) / "private-missing-ml-literal.txt")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main([str(vm_path), "--require-ml-literal-file", missing])

            self.assertEqual(code, 2)
            self.assertNotIn(missing, stdout.getvalue() + stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
