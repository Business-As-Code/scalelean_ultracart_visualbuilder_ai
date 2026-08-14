from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_design_brief import build_design_brief, generate_brief_id
from validate_design_brief import validate_design_brief, check_unknowns, check_determinism


FIXTURES_DIR = ROOT / "tests" / "fixtures" / "design-briefs"


class DesignBriefSchemaTests(unittest.TestCase):
    """Test design brief schema validation and structure."""
    
    def test_generate_brief_id_is_deterministic(self) -> None:
        """Brief ID generation is deterministic from work order and page class."""
        brief_id1 = generate_brief_id("SL-148", "home")
        brief_id2 = generate_brief_id("SL-148", "home")
        self.assertEqual(brief_id1, brief_id2)
        self.assertEqual(brief_id1, "brief-sl-148-home")
    
    def test_brief_id_normalization(self) -> None:
        """Brief IDs are normalized to lowercase with hyphens."""
        self.assertEqual(generate_brief_id("SL-148", "home"), "brief-sl-148-home")
        self.assertEqual(generate_brief_id("TEST_123", "item"), "brief-test-123-item")
    
    def test_minimal_valid_brief(self) -> None:
        """A minimal but valid brief passes validation."""
        brief = build_design_brief(
            work_order="TEST-001",
            reference_type="url",
            reference_path="https://example.test/",
            merchant_id="test-merchant",
            storefront_id="test-storefront",
            allowed_writes=["hierarchy-edit"],
            rollback_owner="test-operator",
            acceptance_owner="test-verifier"
        )
        errors = validate_design_brief(brief)
        self.assertEqual(errors, [])
    
    def test_validates_required_authority_fields(self) -> None:
        """Validation catches missing authority fields."""
        brief = build_design_brief(
            work_order="TEST-001",
            reference_type="url",
            reference_path="https://example.test/",
            merchant_id="test-merchant",
            storefront_id="test-storefront",
            allowed_writes=["hierarchy-edit"],
            rollback_owner="test-operator",
            acceptance_owner="test-verifier"
        )
        
        del brief["authority"]["rollback_owner"]
        errors = validate_design_brief(brief)
        self.assertIn("Missing required field: authority.rollback_owner", errors)
    
    def test_validates_route_context(self) -> None:
        """Validation checks route context completeness."""
        brief = build_design_brief(
            work_order="TEST-001",
            reference_type="url",
            reference_path="https://example.test/",
            merchant_id="test-merchant",
            storefront_id="test-storefront",
            allowed_writes=["hierarchy-edit"],
            rollback_owner="test-operator",
            acceptance_owner="test-verifier"
        )
        
        brief["route_context"]["page_class"] = "invalid-class"
        errors = validate_design_brief(brief)
        self.assertTrue(any("Invalid page_class" in e for e in errors))
    
    def test_validates_acceptance_viewports_present(self) -> None:
        """At least one acceptance viewport is required."""
        brief = build_design_brief(
            work_order="TEST-001",
            reference_type="url",
            reference_path="https://example.test/",
            merchant_id="test-merchant",
            storefront_id="test-storefront",
            allowed_writes=["hierarchy-edit"],
            rollback_owner="test-operator",
            acceptance_owner="test-verifier"
        )
        
        brief["acceptance_viewports"] = []
        errors = validate_design_brief(brief)
        self.assertIn("Missing required field: acceptance_viewports (must have at least one)", errors)
    
    def test_validates_semantic_sections_structure(self) -> None:
        """Semantic sections must have proper structure."""
        brief = build_design_brief(
            work_order="TEST-001",
            reference_type="url",
            reference_path="https://example.test/",
            merchant_id="test-merchant",
            storefront_id="test-storefront",
            allowed_writes=["hierarchy-edit"],
            rollback_owner="test-operator",
            acceptance_owner="test-verifier"
        )
        
        brief["design_inventory"]["semantic_sections"][0]["section_id"] = "invalid-id"
        errors = validate_design_brief(brief)
        self.assertTrue(any("invalid section_id" in e for e in errors))
    
    def test_validates_native_behavior_status(self) -> None:
        """Native behavior verification status must be valid."""
        brief = build_design_brief(
            work_order="TEST-001",
            reference_type="url",
            reference_path="https://example.test/",
            merchant_id="test-merchant",
            storefront_id="test-storefront",
            allowed_writes=["hierarchy-edit"],
            rollback_owner="test-operator",
            acceptance_owner="test-verifier"
        )
        
        brief["native_behavior_checklist"]["verification_status"] = "Invalid"
        errors = validate_design_brief(brief)
        self.assertTrue(any("Invalid verification_status" in e for e in errors))
    
    def test_validates_reference_evidence_fields(self) -> None:
        """Reference evidence must have valid input type and extraction method."""
        brief = build_design_brief(
            work_order="TEST-001",
            reference_type="url",
            reference_path="https://example.test/",
            merchant_id="test-merchant",
            storefront_id="test-storefront",
            allowed_writes=["hierarchy-edit"],
            rollback_owner="test-operator",
            acceptance_owner="test-verifier"
        )
        
        brief["reference_evidence"]["input_type"] = "invalid-type"
        errors = validate_design_brief(brief)
        self.assertTrue(any("Invalid input_type" in e for e in errors))


class DesignBriefAnalyzerTests(unittest.TestCase):
    """Test design brief analyzer/builder functionality."""
    
    def test_url_reference_brief_generation(self) -> None:
        """URL reference generates valid brief with expected unknowns."""
        brief = build_design_brief(
            work_order="SL-148",
            reference_type="url",
            reference_path="https://example-store.test/",
            merchant_id="merchant-redacted",
            storefront_id="storefront-redacted",
            allowed_writes=["visual-builder-hierarchy-edit"],
            rollback_owner="test-operator",
            acceptance_owner="test-verifier"
        )
        
        self.assertEqual(brief["schema_version"], "1.0")
        self.assertEqual(brief["authority"]["controlling_work_order"], "SL-148")
        self.assertEqual(brief["reference_evidence"]["input_type"], "url")
        self.assertEqual(
            brief["reference_evidence"]["reference_url"],
            "https://example-store.test/"
        )
        
        errors = validate_design_brief(brief)
        self.assertEqual(errors, [])
        
        unknowns = check_unknowns(brief)
        self.assertIn("route_context.editor_route", unknowns)
    
    def test_screenshot_reference_brief_generation(self) -> None:
        """Screenshot reference generates three-section layout."""
        screenshot_path = FIXTURES_DIR / "screenshot-reference-synthetic.png"
        self.assertTrue(screenshot_path.exists(), "Synthetic screenshot fixture not found")
        
        brief = build_design_brief(
            work_order="SL-148",
            reference_type="screenshot",
            reference_path=str(screenshot_path),
            merchant_id="merchant-redacted",
            storefront_id="storefront-redacted",
            allowed_writes=["visual-builder-hierarchy-edit"],
            rollback_owner="test-operator",
            acceptance_owner="test-verifier"
        )
        
        self.assertEqual(brief["reference_evidence"]["input_type"], "screenshot")
        self.assertIsNotNone(brief["reference_evidence"]["reference_screenshot_hash"])
        
        sections = brief["design_inventory"]["semantic_sections"]
        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0]["name"], "header")
        self.assertEqual(sections[1]["name"], "main-body")
        self.assertEqual(sections[2]["name"], "footer")
        
        errors = validate_design_brief(brief)
        self.assertEqual(errors, [])
    
    def test_written_brief_reference_generation(self) -> None:
        """Written brief input preserves detailed design specifications."""
        written_brief_path = FIXTURES_DIR / "written-brief-input.json"
        self.assertTrue(written_brief_path.exists(), "Written brief fixture not found")
        
        brief = build_design_brief(
            work_order="SL-148",
            reference_type="written-brief",
            reference_path=str(written_brief_path),
            merchant_id="merchant-redacted",
            storefront_id="storefront-redacted",
            allowed_writes=["visual-builder-hierarchy-edit"],
            rollback_owner="test-operator",
            acceptance_owner="test-verifier"
        )
        
        self.assertEqual(brief["reference_evidence"]["input_type"], "written-brief")
        self.assertEqual(brief["route_context"]["page_class"], "item")
        
        sections = brief["design_inventory"]["semantic_sections"]
        self.assertEqual(len(sections), 3)
        
        product_section = sections[1]
        self.assertEqual(product_section["name"], "product-detail")
        self.assertEqual(product_section["content_source"], "dynamic-ultracart")
        
        errors = validate_design_brief(brief)
        self.assertEqual(errors, [])
    
    def test_deterministic_generation_from_same_input(self) -> None:
        """Same input produces identical briefs (excluding timestamps)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brief1_path = Path(tmpdir) / "brief1.json"
            brief2_path = Path(tmpdir) / "brief2.json"
            
            brief1 = build_design_brief(
                work_order="SL-148",
                reference_type="url",
                reference_path="https://example.test/",
                merchant_id="test-merchant",
                storefront_id="test-storefront",
                allowed_writes=["edit"],
                rollback_owner="operator",
                acceptance_owner="verifier"
            )
            
            brief2 = build_design_brief(
                work_order="SL-148",
                reference_type="url",
                reference_path="https://example.test/",
                merchant_id="test-merchant",
                storefront_id="test-storefront",
                allowed_writes=["edit"],
                rollback_owner="operator",
                acceptance_owner="verifier"
            )
            
            brief1_path.write_text(json.dumps(brief1, indent=2, sort_keys=True))
            brief2_path.write_text(json.dumps(brief2, indent=2, sort_keys=True))
            
            self.assertTrue(check_determinism(brief1_path, brief2_path))
    
    def test_extraction_assumptions_recorded(self) -> None:
        """URL extraction records explicit assumptions."""
        brief = build_design_brief(
            work_order="SL-148",
            reference_type="url",
            reference_path="https://example.test/",
            merchant_id="test-merchant",
            storefront_id="test-storefront",
            allowed_writes=["edit"],
            rollback_owner="operator",
            acceptance_owner="verifier"
        )
        
        assumptions = brief["reference_evidence"]["extraction_assumptions"]
        self.assertGreater(len(assumptions), 0)
        self.assertIn("assumption", assumptions[0])
        self.assertIn("rationale", assumptions[0])
    
    def test_unresolved_information_tracked(self) -> None:
        """Unknowns are explicitly recorded in unresolved_information."""
        brief = build_design_brief(
            work_order="SL-148",
            reference_type="url",
            reference_path="https://example.test/",
            merchant_id="test-merchant",
            storefront_id="test-storefront",
            allowed_writes=["edit"],
            rollback_owner="operator",
            acceptance_owner="verifier"
        )
        
        unresolved = brief["reference_evidence"]["unresolved_information"]
        self.assertGreater(len(unresolved), 0)
        self.assertIn("property", unresolved[0])
        self.assertIn("reason", unresolved[0])


class DesignBriefFixturesTests(unittest.TestCase):
    """Test synthetic fixtures are valid and safe."""
    
    def test_url_fixture_exists(self) -> None:
        """URL reference fixture exists."""
        fixture_path = FIXTURES_DIR / "url-reference-input.json"
        self.assertTrue(fixture_path.exists())
    
    def test_screenshot_fixture_exists(self) -> None:
        """Screenshot fixture exists and is a valid PNG."""
        fixture_path = FIXTURES_DIR / "screenshot-reference-synthetic.png"
        self.assertTrue(fixture_path.exists())
        
        with open(fixture_path, "rb") as f:
            header = f.read(8)
            self.assertEqual(header, b'\x89PNG\r\n\x1a\n')
    
    def test_written_brief_fixture_exists(self) -> None:
        """Written brief fixture exists and is valid JSON."""
        fixture_path = FIXTURES_DIR / "written-brief-input.json"
        self.assertTrue(fixture_path.exists())
        
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIn("route_context", data)
            self.assertIn("design_inventory", data)
    
    def test_fixtures_are_merchant_neutral(self) -> None:
        """Fixtures contain no real merchant or client data."""
        written_brief = FIXTURES_DIR / "written-brief-input.json"
        with open(written_brief, "r", encoding="utf-8") as f:
            content = f.read()
            
            self.assertIn("example-store.test", content)
            self.assertIn("Example Store", content)
            self.assertNotIn("ultracart.com", content.lower())
            
            with open(written_brief, "r", encoding="utf-8") as brief_file:
                data = json.load(brief_file)
            for section in data["design_inventory"]["semantic_sections"]:
                for asset in section.get("required_assets", []):
                    self.assertEqual(asset["provenance"], "synthetic")


if __name__ == "__main__":
    unittest.main()
