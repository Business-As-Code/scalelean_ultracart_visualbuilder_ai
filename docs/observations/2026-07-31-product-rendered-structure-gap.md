# Product rendered-structure gap

Date: 2026-07-31.

## Scope

This was a read-only comparison of the rendered DOM for the public Clinical
Effects Joint Support reference and the pre-refinement saved reference test product.
The comparison used only validated `data-widget-type` values and nearest-widget
parent-child relations. It retained no page copy, URLs, widget identifiers,
customer data, or source HTML.

This observation predates persistence of the preserved unsaved reference product
checkpoint. It is a baseline gap, not an acceptance result for that checkpoint.
The later saved result is recorded in
[Joint Support offer refinement](2026-07-31-joint-support-offer-refinement.md).

## Verified aggregate result

| Measure | Reference | Pre-refinement saved target |
| --- | ---: | ---: |
| Rendered widget instances | 534 | 297 |
| Root widget instances | 7 | 5 |
| Root widget type | `container` | `container` |
| Invalid widget-type attributes | 0 | 0 |

The reference has substantially more composition structure. The largest type
gaps are:

| Widget type | Reference | Pre-refinement saved target |
| --- | ---: | ---: |
| `panel` | 91 | 4 |
| `image` | 53 | 12 |
| `headline` | 40 | 19 |
| `textblock` | 37 | 8 |
| `button` | 37 | 9 |
| `slide` | 30 | 0 |
| `overlay` | 23 | 0 |
| `hover` | 21 | 0 |
| `flex` | 14 | 0 |
| `slider` | 2 | 0 |

High-count relationships that exist in the reference but not in the
pre-refinement saved target include:

- `slider -> slide`, 30 links.
- `hover -> overlay`, 21 links.
- `overlay -> image`, 21 links.
- `overlay -> button`, 23 links.
- `slide -> panel`, 21 links.
- `panel -> hover`, 21 links.

## Screenshot baseline

A same-size 1440 by 1100 desktop screenshot comparison used no masks and a
per-channel pixel delta threshold of 16. It measured:

| Metric | Baseline result |
| --- | ---: |
| Normalized mean absolute error | 0.115942818710 |
| Normalized root mean square error | 0.215323630672 |
| Maximum channel delta | 255 |
| Pixels over the delta threshold | 51.842171717172 percent |

This run used permissive limits only to measure the starting gap. It is not a
passing visual acceptance result. More than half of the pixels exceed the
declared delta threshold.

## Interpretation

The pre-refinement saved target was not a high-fidelity structural
reproduction. The gap was architectural, not only cosmetic. The reference
relied heavily on Panels, Flex, Hover, Overlay, and Slider families that the
pre-refinement saved target did not render.

Exact whole-page count equality is not a valid acceptance rule by itself. The
two sites can have different theme shells and native product controls. Use the
aggregate comparison to find missing composition families. Use region-specific
geometry, screenshots, active-control checks, and content assertions for final
acceptance.

## Reusable rule

For a public reference that exposes Visual Builder widget attributes:

1. Capture the reference and target rendered HTML privately at the same route
   state.
2. Compare widget types and nearest-widget relationships with
   `scripts/inspect_visual_builder_rendered_html.py`.
3. Treat missing high-count layout families as a hierarchy gap.
4. Use `--require-match` only for like-for-like snapshots where exact aggregate
   equality is expected, such as the same page before and after a reload.
5. Do not use aggregate equality as a substitute for visual geometry or active
   behavior verification.
