#!/usr/bin/env python3
"""Validate a design brief against schema and completeness requirements."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_SCHEMA_VERSION = "1.0"


def load_json(path: Path) -> dict[str, Any]:
    """Load and parse a JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def validate_design_brief(brief: dict[str, Any], schema: dict[str, Any] | None = None) -> list[str]:
    """Validate design brief completeness and integrity.
    
    Args:
        brief: Design brief dictionary to validate
        schema: Optional JSON schema for structural validation
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []
    
    if brief.get("schema_version") != REQUIRED_SCHEMA_VERSION:
        errors.append(f"Invalid schema version: expected {REQUIRED_SCHEMA_VERSION}")
    
    if not brief.get("brief_id", "").startswith("brief-"):
        errors.append("Invalid brief_id: must start with 'brief-'")
    
    authority = brief.get("authority", {})
    if not authority.get("controlling_work_order"):
        errors.append("Missing required field: authority.controlling_work_order")
    
    test_storefront = authority.get("test_storefront", {})
    if not test_storefront.get("merchant_id"):
        errors.append("Missing required field: authority.test_storefront.merchant_id")
    if not test_storefront.get("storefront_id"):
        errors.append("Missing required field: authority.test_storefront.storefront_id")
    
    if not authority.get("rollback_owner"):
        errors.append("Missing required field: authority.rollback_owner")
    if not authority.get("acceptance_owner"):
        errors.append("Missing required field: authority.acceptance_owner")
    
    route_context = brief.get("route_context", {})
    if not route_context.get("page_class"):
        errors.append("Missing required field: route_context.page_class")
    elif route_context["page_class"] not in ["home", "content", "collection", "item", "other"]:
        errors.append(f"Invalid page_class: {route_context['page_class']}")
    
    if not route_context.get("public_route"):
        errors.append("Missing required field: route_context.public_route")
    
    acceptance_viewports = brief.get("acceptance_viewports", [])
    if not acceptance_viewports:
        errors.append("Missing required field: acceptance_viewports (must have at least one)")
    else:
        for i, viewport in enumerate(acceptance_viewports):
            if not isinstance(viewport, dict):
                errors.append(f"acceptance_viewports[{i}] is not an object")
                continue
            if "width" not in viewport:
                errors.append(f"acceptance_viewports[{i}] missing required field: width")
            if "height" not in viewport:
                errors.append(f"acceptance_viewports[{i}] missing required field: height")
            if "device_scale" not in viewport:
                errors.append(f"acceptance_viewports[{i}] missing required field: device_scale")
            if "in_scope" not in viewport:
                errors.append(f"acceptance_viewports[{i}] missing required field: in_scope")
    
    design_inventory = brief.get("design_inventory", {})
    semantic_sections = design_inventory.get("semantic_sections", [])
    if not semantic_sections:
        errors.append("design_inventory.semantic_sections must have at least one section")
    else:
        for i, section in enumerate(semantic_sections):
            if not isinstance(section, dict):
                errors.append(f"semantic_sections[{i}] is not an object")
                continue
            if not section.get("section_id", "").startswith("section-"):
                errors.append(f"semantic_sections[{i}] invalid section_id (must start with 'section-')")
            if "name" not in section:
                errors.append(f"semantic_sections[{i}] missing required field: name")
            if "order" not in section:
                errors.append(f"semantic_sections[{i}] missing required field: order")
            if section.get("ownership") not in ["shared", "page-local", "Unknown"]:
                errors.append(f"semantic_sections[{i}] invalid ownership value")
            if section.get("content_source") not in [
                "static-editorial", "dynamic-ultracart", "mixed", "Unknown"
            ]:
                errors.append(f"semantic_sections[{i}] invalid content_source value")
    
    native_behavior = brief.get("native_behavior_checklist", {})
    if "verification_status" not in native_behavior:
        errors.append("Missing required field: native_behavior_checklist.verification_status")
    elif native_behavior["verification_status"] not in ["Verified", "Contradicted", "Unknown"]:
        errors.append(f"Invalid verification_status: {native_behavior['verification_status']}")
    
    if "controls_to_preserve" not in native_behavior:
        errors.append("Missing required field: native_behavior_checklist.controls_to_preserve")
    
    acceptance_criteria = brief.get("acceptance_criteria", {})
    if not acceptance_criteria.get("zero_tolerance_checks"):
        errors.append("Missing required field: acceptance_criteria.zero_tolerance_checks")
    
    reference_evidence = brief.get("reference_evidence", {})
    if not reference_evidence.get("input_type"):
        errors.append("Missing required field: reference_evidence.input_type")
    elif reference_evidence["input_type"] not in ["url", "screenshot", "written-brief", "figma", "other"]:
        errors.append(f"Invalid input_type: {reference_evidence['input_type']}")
    
    if not reference_evidence.get("extraction_method"):
        errors.append("Missing required field: reference_evidence.extraction_method")
    elif reference_evidence["extraction_method"] not in ["automated", "manual", "hybrid", "Unknown"]:
        errors.append(f"Invalid extraction_method: {reference_evidence['extraction_method']}")
    
    return errors


def check_unknowns(brief: dict[str, Any]) -> list[str]:
    """Check for unresolved Unknown values that should be resolved.
    
    Returns:
        List of paths to Unknown values
    """
    unknowns: list[str] = []
    
    route_context = brief.get("route_context", {})
    if route_context.get("editor_route") == "Unknown":
        unknowns.append("route_context.editor_route")
    if route_context.get("public_route") == "Unknown":
        unknowns.append("route_context.public_route")
    
    design_inventory = brief.get("design_inventory", {})
    if design_inventory.get("responsive_intent") == "Unknown":
        unknowns.append("design_inventory.responsive_intent")
    
    for i, section in enumerate(design_inventory.get("semantic_sections", [])):
        if section.get("ownership") == "Unknown":
            unknowns.append(f"semantic_sections[{i}].ownership")
        if section.get("content_source") == "Unknown":
            unknowns.append(f"semantic_sections[{i}].content_source")
    
    native_behavior = brief.get("native_behavior_checklist", {})
    if native_behavior.get("verification_status") == "Unknown":
        unknowns.append("native_behavior_checklist.verification_status")
    
    reference_evidence = brief.get("reference_evidence", {})
    if reference_evidence.get("extraction_method") == "Unknown":
        unknowns.append("reference_evidence.extraction_method")
    
    return unknowns


def check_determinism(brief1_path: Path, brief2_path: Path) -> bool:
    """Check if two briefs generated from same input are identical.
    
    Args:
        brief1_path: Path to first brief
        brief2_path: Path to second brief
    
    Returns:
        True if briefs are identical (ignoring created_at timestamp)
    """
    brief1 = load_json(brief1_path)
    brief2 = load_json(brief2_path)
    
    brief1_copy = dict(brief1)
    brief2_copy = dict(brief2)
    
    brief1_copy.pop("created_at", None)
    brief2_copy.pop("created_at", None)
    
    ref1 = brief1_copy.get("reference_evidence", {})
    ref2 = brief2_copy.get("reference_evidence", {})
    ref1.pop("extraction_timestamp", None)
    ref2.pop("extraction_timestamp", None)
    
    return brief1_copy == brief2_copy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path, help="Path to design brief JSON file")
    parser.add_argument("--schema", type=Path, help="Optional path to JSON schema for validation")
    parser.add_argument("--check-unknowns", action="store_true", help="Report unresolved Unknown values")
    parser.add_argument(
        "--check-determinism",
        type=Path,
        help="Compare with another brief to verify determinism"
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    
    args = parser.parse_args()
    
    try:
        brief = load_json(args.brief)
        schema = load_json(args.schema) if args.schema else None
        
        errors = validate_design_brief(brief, schema)
        unknowns = check_unknowns(brief) if args.check_unknowns else []
        
        deterministic = None
        if args.check_determinism:
            deterministic = check_determinism(args.brief, args.check_determinism)
        
        if args.json:
            result = {
                "valid": len(errors) == 0,
                "errors": errors,
                "unknowns": unknowns,
                "deterministic": deterministic
            }
            print(json.dumps(result, indent=2))
        else:
            if errors:
                print("Validation failed:")
                for error in errors:
                    print(f"  - {error}")
            else:
                print("Design brief is valid")
            
            if unknowns:
                print("\nUnresolved Unknown values:")
                for unknown in unknowns:
                    print(f"  - {unknown}")
            
            if deterministic is not None:
                if deterministic:
                    print("\nDeterminism check: PASSED (briefs are identical)")
                else:
                    print("\nDeterminism check: FAILED (briefs differ)")
        
        if errors:
            return 2
        
    except (OSError, json.JSONDecodeError) as error:
        print(f"error: {error}")
        return 2
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
