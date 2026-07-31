from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from inspect_visual_builder_rendered_html import (
    compare_summaries,
    main,
    render_text,
    summarize_rendered_html,
)


PRIVATE_URL = "https://private.example.test/customer/asset.png"
PRIVATE_CONTENT = "private customer offer 918273"
PRIVATE_ID = "customer-record-771"


def target_html() -> str:
    return f'''<!doctype html>
<html>
  <body>
    <section data-widget-type="container" id="{PRIVATE_ID}">
      <div class="ordinary-wrapper">
        <div data-widget-type="row">
          <div class="another-wrapper">
            <div data-widget-type="column">
              <img data-widget-type="image" src="{PRIVATE_URL}" alt="{PRIVATE_CONTENT}">
              <span data-widget-type="headline">{PRIVATE_CONTENT}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
    <footer data-widget-type="container">
      <span data-widget-type="text">{PRIVATE_CONTENT}</span>
    </footer>
  </body>
</html>
'''


class InspectVisualBuilderRenderedHtmlTests(unittest.TestCase):
    def test_counts_types_roots_and_nearest_widget_edges(self) -> None:
        summary = summarize_rendered_html(target_html())

        self.assertEqual(summary["widget_count"], 7)
        self.assertEqual(summary["root_widget_count"], 2)
        self.assertEqual(
            summary["widget_type_counts"],
            {
                "column": 1,
                "container": 2,
                "headline": 1,
                "image": 1,
                "row": 1,
                "text": 1,
            },
        )
        self.assertEqual(summary["root_widget_type_counts"], {"container": 2})
        self.assertEqual(
            summary["nearest_widget_parent_child_type_edge_counts"],
            {
                "column>headline": 1,
                "column>image": 1,
                "container>row": 1,
                "container>text": 1,
                "row>column": 1,
            },
        )

    def test_void_widget_does_not_become_parent_of_following_sibling(self) -> None:
        source = '''
        <section data-widget-type="container">
          <img data-widget-type="image" src="private-source">
          <span data-widget-type="headline">private words</span>
        </section>
        '''

        summary = summarize_rendered_html(source)

        self.assertEqual(
            summary["nearest_widget_parent_child_type_edge_counts"],
            {"container>headline": 1, "container>image": 1},
        )

    def test_invalid_and_duplicate_type_values_are_counted_but_never_returned(self) -> None:
        private_invalid = "private value /customer/918273"
        duplicate_value = "secret-token-918273"
        source = f'''
        <section data-widget-type="container">
          <div data-widget-type="{private_invalid}">
            <span data-widget-type="headline">private content</span>
          </div>
          <div data-widget-type="row" data-widget-type="{duplicate_value}"></div>
        </section>
        '''

        summary = summarize_rendered_html(source)
        rendered = json.dumps(summary, sort_keys=True)

        self.assertEqual(summary["invalid_widget_type_attribute_count"], 2)
        self.assertEqual(summary["widget_type_counts"], {"container": 1, "headline": 1})
        self.assertEqual(
            summary["nearest_widget_parent_child_type_edge_counts"],
            {"container>headline": 1},
        )
        self.assertNotIn(private_invalid, rendered)
        self.assertNotIn(duplicate_value, rendered)

    def test_comparison_reports_aggregate_missing_and_excess_counts(self) -> None:
        reference = summarize_rendered_html('''
        <main data-widget-type="container">
          <div data-widget-type="row">
            <div data-widget-type="column">
              <h1 data-widget-type="headline">reference</h1>
              <img data-widget-type="image">
            </div>
          </div>
        </main>
        ''')
        target = summarize_rendered_html('''
        <main data-widget-type="container">
          <div data-widget-type="row">
            <div data-widget-type="column">
              <p data-widget-type="text">target</p>
            </div>
          </div>
        </main>
        <aside data-widget-type="panel"></aside>
        ''')

        comparison = compare_summaries(reference, target)

        self.assertFalse(comparison["matched"])
        self.assertEqual(
            comparison["widget_types"],
            {
                "excess_counts": {"panel": 1, "text": 1},
                "excess_total": 2,
                "missing_counts": {"headline": 1, "image": 1},
                "missing_total": 2,
            },
        )
        self.assertEqual(
            comparison["root_widget_types"]["excess_counts"], {"panel": 1}
        )
        self.assertEqual(
            comparison["nearest_widget_parent_child_type_edges"]["missing_counts"],
            {"column>headline": 1, "column>image": 1},
        )
        self.assertEqual(
            comparison["nearest_widget_parent_child_type_edges"]["excess_counts"],
            {"column>text": 1},
        )

    def test_cli_json_is_source_safe_and_does_not_echo_input_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target_path = Path(directory) / "private-target-customer-918273.html"
            reference_path = Path(directory) / "private-reference-customer-918273.html"
            target_path.write_text(target_html(), encoding="utf-8")
            reference_path.write_text(target_html(), encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(
                    [
                        str(target_path),
                        "--reference",
                        str(reference_path),
                        "--json",
                    ]
                )

        output = stdout.getvalue() + stderr.getvalue()
        payload = json.loads(stdout.getvalue())
        self.assertEqual(code, 0)
        self.assertTrue(payload["comparison"]["matched"])
        self.assertNotIn(str(target_path), output)
        self.assertNotIn(str(reference_path), output)
        self.assertNotIn(PRIVATE_URL, output)
        self.assertNotIn(PRIVATE_CONTENT, output)
        self.assertNotIn(PRIVATE_ID, output)
        self.assertNotIn("<section", output)

    def test_text_output_contains_only_safe_aggregates(self) -> None:
        summary = summarize_rendered_html(target_html())

        output = render_text(summary)

        self.assertIn("widget types: column=1", output)
        self.assertIn("nearest-widget edges:", output)
        self.assertNotIn(PRIVATE_URL, output)
        self.assertNotIn(PRIVATE_CONTENT, output)
        self.assertNotIn(PRIVATE_ID, output)

    def test_missing_input_returns_generic_error_without_path_echo(self) -> None:
        missing = "/private/customer/missing-rendered-snapshot-918273.html"
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main([missing, "--json"])

        output = stdout.getvalue() + stderr.getvalue()
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(stderr.getvalue()), {"error": "input_error"})
        self.assertNotIn(missing, output)

    def test_require_match_uses_verifier_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target_path = Path(directory) / "target.html"
            reference_path = Path(directory) / "reference.html"
            target_path.write_text(
                '<main data-widget-type="container"></main>', encoding="utf-8"
            )
            reference_path.write_text(
                '<main data-widget-type="container"><h1 data-widget-type="headline">x</h1></main>',
                encoding="utf-8",
            )

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                mismatch = main(
                    [
                        str(target_path),
                        "--reference",
                        str(reference_path),
                        "--require-match",
                    ]
                )
                invalid = main([str(target_path), "--require-match", "--json"])

        self.assertEqual(mismatch, 1)
        self.assertEqual(invalid, 2)


if __name__ == "__main__":
    unittest.main()
