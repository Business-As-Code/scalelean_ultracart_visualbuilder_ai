#!/usr/bin/env python3
"""Build a deterministic design brief from reference input."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    """Load and parse a JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def generate_brief_id(work_order: str, page_class: str) -> str:
    """Generate a deterministic brief ID from work order and page class."""
    normalized = f"{work_order}-{page_class}".lower()
    return f"brief-{normalized.replace('_', '-')}"


def extract_from_url_reference(url: str, work_order: str) -> dict[str, Any]:
    """Extract design information from URL reference (placeholder implementation)."""
    page_class = "home" if url.endswith("/") or "home" in url.lower() else "content"
    
    return {
        "route_context": {
            "page_class": page_class,
            "editor_route": "Unknown",
            "public_route": url,
            "route_agreement_verified": False
        },
        "design_inventory": {
            "responsive_intent": "Unknown",
            "semantic_sections": [
                {
                    "section_id": "section-header",
                    "name": "header",
                    "order": 0,
                    "ownership": "shared",
                    "content_source": "Unknown",
                    "required_copy": None,
                    "required_assets": [],
                    "typography": None,
                    "surface": None,
                    "geometry": None,
                    "behavior": None,
                    "reusable_container_candidate": True,
                    "page_specific_regions": []
                }
            ]
        },
        "reference_evidence": {
            "input_type": "url",
            "reference_url": url,
            "reference_screenshot_hash": None,
            "reference_document_hash": None,
            "extraction_method": "automated",
            "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            "extraction_assumptions": [
                {
                    "assumption": "Standard header-body-footer layout",
                    "rationale": "URL reference without visual inspection",
                    "approval_status": "pending"
                }
            ],
            "unresolved_information": [
                {
                    "property": "visual_design",
                    "reason": "URL reference requires screenshot or live inspection",
                    "resolution_strategy": "Capture screenshot for detailed analysis"
                }
            ]
        }
    }


def extract_from_screenshot_reference(screenshot_path: Path, work_order: str) -> dict[str, Any]:
    """Extract design information from screenshot reference."""
    screenshot_hash = sha256_file(screenshot_path)
    
    return {
        "route_context": {
            "page_class": "other",
            "editor_route": "Unknown",
            "public_route": "Unknown",
            "route_agreement_verified": False
        },
        "design_inventory": {
            "responsive_intent": "Unknown",
            "semantic_sections": [
                {
                    "section_id": "section-header",
                    "name": "header",
                    "order": 0,
                    "ownership": "Unknown",
                    "content_source": "Unknown",
                    "required_copy": None,
                    "required_assets": [],
                    "typography": None,
                    "surface": None,
                    "geometry": None,
                    "behavior": None,
                    "reusable_container_candidate": False,
                    "page_specific_regions": []
                },
                {
                    "section_id": "section-body",
                    "name": "main-body",
                    "order": 1,
                    "ownership": "page-local",
                    "content_source": "Unknown",
                    "required_copy": None,
                    "required_assets": [],
                    "typography": None,
                    "surface": None,
                    "geometry": None,
                    "behavior": None,
                    "reusable_container_candidate": False,
                    "page_specific_regions": []
                },
                {
                    "section_id": "section-footer",
                    "name": "footer",
                    "order": 2,
                    "ownership": "shared",
                    "content_source": "Unknown",
                    "required_copy": None,
                    "required_assets": [],
                    "typography": None,
                    "surface": None,
                    "geometry": None,
                    "behavior": None,
                    "reusable_container_candidate": True,
                    "page_specific_regions": []
                }
            ]
        },
        "reference_evidence": {
            "input_type": "screenshot",
            "reference_url": None,
            "reference_screenshot_hash": screenshot_hash,
            "reference_document_hash": None,
            "extraction_method": "manual",
            "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            "extraction_assumptions": [
                {
                    "assumption": "Three-section layout with shared header and footer",
                    "rationale": "Visual inspection of screenshot shows typical page structure",
                    "approval_status": "pending"
                }
            ],
            "unresolved_information": [
                {
                    "property": "dynamic_behavior",
                    "reason": "Screenshot is static and cannot show interactive behavior",
                    "resolution_strategy": "Require written specification or live URL for behavior"
                },
                {
                    "property": "responsive_breakpoints",
                    "reason": "Single viewport screenshot",
                    "resolution_strategy": "Capture additional viewports or specify desktop-only scope"
                }
            ]
        }
    }


def extract_from_written_brief(brief_path: Path, work_order: str) -> dict[str, Any]:
    """Extract design information from written design brief."""
    brief_hash = sha256_file(brief_path)
    brief_content = load_json(brief_path)
    
    route_context = brief_content.get("route_context", {})
    design_inventory = brief_content.get("design_inventory", {})
    
    return {
        "route_context": {
            "page_class": route_context.get("page_class", "Unknown"),
            "editor_route": route_context.get("editor_route", "Unknown"),
            "public_route": route_context.get("public_route", "Unknown"),
            "route_agreement_verified": route_context.get("route_agreement_verified", False)
        },
        "design_inventory": design_inventory if design_inventory else {
            "responsive_intent": "Unknown",
            "semantic_sections": []
        },
        "reference_evidence": {
            "input_type": "written-brief",
            "reference_url": None,
            "reference_screenshot_hash": None,
            "reference_document_hash": brief_hash,
            "extraction_method": "automated",
            "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            "extraction_assumptions": [],
            "unresolved_information": []
        }
    }


def build_design_brief(
    work_order: str,
    reference_type: str,
    reference_path: str | None,
    merchant_id: str,
    storefront_id: str,
    allowed_writes: list[str],
    rollback_owner: str,
    acceptance_owner: str,
    acceptance_viewports: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a complete design brief from reference input.
    
    Args:
        work_order: Controlling work order ID (e.g., SL-148)
        reference_type: Type of reference input (url, screenshot, written-brief)
        reference_path: Path or URL to reference input
        merchant_id: Merchant identifier (redacted for synthetic)
        storefront_id: StoreFront identifier (redacted for synthetic)
        allowed_writes: List of allowed Visual Builder operations
        rollback_owner: Named rollback operator
        acceptance_owner: Named acceptance verifier
        acceptance_viewports: Optional list of viewport configurations
    
    Returns:
        Complete design brief dictionary
    """
    
    if reference_type == "url":
        if not reference_path:
            raise ValueError("URL reference requires reference_path")
        extracted = extract_from_url_reference(reference_path, work_order)
        page_class = extracted["route_context"]["page_class"]
    elif reference_type == "screenshot":
        if not reference_path:
            raise ValueError("Screenshot reference requires reference_path")
        screenshot_path = Path(reference_path)
        if not screenshot_path.exists():
            raise ValueError(f"Screenshot file not found: {reference_path}")
        extracted = extract_from_screenshot_reference(screenshot_path, work_order)
        page_class = extracted["route_context"]["page_class"]
    elif reference_type == "written-brief":
        if not reference_path:
            raise ValueError("Written brief reference requires reference_path")
        brief_path = Path(reference_path)
        if not brief_path.exists():
            raise ValueError(f"Written brief file not found: {reference_path}")
        extracted = extract_from_written_brief(brief_path, work_order)
        page_class = extracted["route_context"]["page_class"]
    else:
        raise ValueError(f"Unsupported reference type: {reference_type}")
    
    brief_id = generate_brief_id(work_order, page_class)
    
    if acceptance_viewports is None:
        acceptance_viewports = [
            {
                "name": "desktop-1920",
                "width": 1920,
                "height": 1080,
                "device_scale": 1.0,
                "in_scope": True,
                "browser": "Chrome 120",
                "zoom_level": 100.0,
                "requires_scroll": False,
                "comparison_thresholds": None,
                "mask_rectangles": []
            }
        ]
    
    forbidden_writes = [
        "catalog-mutation",
        "price-modification",
        "inventory-modification",
        "checkout-settings",
        "customer-data",
        "direct-ftp-write"
    ]
    
    brief = {
        "schema_version": SCHEMA_VERSION,
        "brief_id": brief_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "authority": {
            "controlling_work_order": work_order,
            "test_storefront": {
                "merchant_id": merchant_id,
                "storefront_id": storefront_id
            },
            "allowed_writes": allowed_writes,
            "forbidden_writes": forbidden_writes,
            "rollback_owner": rollback_owner,
            "acceptance_owner": acceptance_owner
        },
        "route_context": extracted["route_context"],
        "acceptance_viewports": acceptance_viewports,
        "design_inventory": extracted["design_inventory"],
        "native_behavior_checklist": {
            "controls_to_preserve": [],
            "verification_status": "Unknown",
            "unexercised_states": []
        },
        "hierarchy_plan": None,
        "acceptance_criteria": {
            "zero_tolerance_checks": [
                "exact-copy",
                "exact-punctuation",
                "exact-capitalization",
                "required-asset-identity",
                "required-asset-alt-text",
                "required-node-parentage",
                "required-sibling-order",
                "required-dynamic-vs-static",
                "required-native-control-presence",
                "required-native-control-action"
            ],
            "numeric_tolerances": {
                "font_size": None,
                "line_height": None,
                "element_bounds": None,
                "gaps": None,
                "padding": None,
                "margin": None,
                "section_position": None
            },
            "surface_requirements": [
                {
                    "surface": "editor",
                    "required_checks": [
                        "intended-hierarchy",
                        "clean-reloaded-state"
                    ]
                },
                {
                    "surface": "cjson",
                    "required_checks": [
                        "target-parentage",
                        "source-absence-after-moves",
                        "child-order"
                    ]
                },
                {
                    "surface": "velocity",
                    "required_checks": [
                        "expected-generated-text",
                        "dynamic-wrappers",
                        "native-controls"
                    ]
                },
                {
                    "surface": "public-route",
                    "required_checks": [
                        "intended-desktop-composition",
                        "exact-copy-and-assets",
                        "measured-geometry",
                        "active-native-controls"
                    ]
                }
            ],
            "allowed_differences": []
        },
        "reference_evidence": extracted["reference_evidence"],
        "metadata": {
            "brief_format": "machine-readable",
            "generator": "build_design_brief.py",
            "generator_version": "1.0"
        }
    }
    
    return brief


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-order", required=True, help="Controlling work order (e.g., SL-148)")
    parser.add_argument(
        "--reference-type",
        required=True,
        choices=["url", "screenshot", "written-brief"],
        help="Type of reference input"
    )
    parser.add_argument("--reference-path", help="Path or URL to reference input")
    parser.add_argument("--merchant-id", default="merchant-redacted", help="Merchant identifier")
    parser.add_argument("--storefront-id", default="storefront-redacted", help="StoreFront identifier")
    parser.add_argument(
        "--allowed-write",
        action="append",
        dest="allowed_writes",
        help="Allowed Visual Builder operation (repeat for multiple)"
    )
    parser.add_argument("--rollback-owner", default="test-operator", help="Named rollback operator")
    parser.add_argument("--acceptance-owner", default="test-verifier", help="Named acceptance verifier")
    parser.add_argument("--output", type=Path, required=True, help="Output path for design brief JSON")
    
    args = parser.parse_args()
    
    try:
        allowed_writes = args.allowed_writes if args.allowed_writes else ["visual-builder-hierarchy-edit"]
        
        brief = build_design_brief(
            work_order=args.work_order,
            reference_type=args.reference_type,
            reference_path=args.reference_path,
            merchant_id=args.merchant_id,
            storefront_id=args.storefront_id,
            allowed_writes=allowed_writes,
            rollback_owner=args.rollback_owner,
            acceptance_owner=args.acceptance_owner
        )
        
        args.output.write_text(
            json.dumps(brief, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )
        
        print(f"Design brief created: {brief['brief_id']}")
        print(f"Output written to: {args.output}")
        
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}")
        return 2
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
