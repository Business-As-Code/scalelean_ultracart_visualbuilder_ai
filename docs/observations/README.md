# Visual Builder observation register

## Current boundary

Only the owner-authorized Header Section probe is active. All other StoreFront
work remains paused. The temporary collection Tab probe remains in the last
source-proven persisted state. A delete was initiated but was not confirmed or
saved. Its editor dirty state is Unknown. Inspect it before any Shop action.

## Current state

| Surface | State | Source and public proof | Rollback | Authority | Authoritative record |
| --- | --- | --- | --- | --- | --- |
| Header container Section probe | Saved structural branch | Editor hierarchy, parent-aware palettes, save confirmation, and editor reload | Pending owner decision | User instruction; work order not recorded | [Header Section probe](2026-07-31-header-container-section-probe.md) |
| Shared header | Accepted saved test state | Yes | No causal rollback sequence | Work order not recorded in this repository | [Shared header](2026-07-31-clinical-effects-shared-header.md) |
| Joint Support product | Accepted saved test state | Yes | No causal rollback sequence | Work order not recorded in this repository | [Joint Support offer](2026-07-31-joint-support-offer-refinement.md) |
| Shop collection probe | Temporary saved state | Yes | Required and incomplete | Work order not recorded in this repository | [Collection Tab probe](2026-07-31-collection-tab-probe-pending-rollback.md) |
| Mailing List experiment | Historical mutation | Yes at experiment time | Not performed | SL-52 | [Controlled save](2026-07-30-controlled-save.md) |
| Early Home additions | Historical mutation | Editor evidence; current presence Unknown | Not recorded | Work order not recorded in this repository | [Homepage layout build](2026-07-30-reference-homepage-layout-build.md) |

Owner approval in the browser session does not supply a missing Linear work
order identifier. The register therefore marks that governance metadata as not
recorded instead of inferring it.

## Evidence register

| Record | Classification |
| --- | --- |
| [Home read-only baseline](2026-07-30-reference-home-readonly-baseline.md) | Historical baseline |
| [Homepage hierarchy baseline](../reference-homepage-hierarchy-baseline.md) | Historical baseline |
| [Visual Builder capability map](2026-07-30-visual-builder-capability-map.md) | Historical starting map with later deltas |
| [Controlled save](2026-07-30-controlled-save.md) | Historical controlled mutation |
| [Homepage layout build](2026-07-30-reference-homepage-layout-build.md) | Superseded build state |
| [Clinical Effects Home reconstruction](2026-07-30-clinical-effects-home-reconstruction.md) | Superseded build state |
| [Item-page build](2026-07-30-reference-item-page-build.md) | Historical build state with later accepted result |
| [Shared route composition](2026-07-31-shared-route-composition.md) | Pre-probe public baseline |
| [External image rendering](2026-07-31-external-image-rendering.md) | Method and limitation note |
| [Product rendered-structure gap](2026-07-31-product-rendered-structure-gap.md) | Superseded baseline |
| [Generated VM literal normalization](2026-07-31-generated-vm-literal-normalization.md) | Current compiler method note |
| [Shared header](2026-07-31-clinical-effects-shared-header.md) | Current accepted saved state |
| [Joint Support offer](2026-07-31-joint-support-offer-refinement.md) | Current accepted saved state |
| [Header Section probe](2026-07-31-header-container-section-probe.md) | Current bounded hierarchy experiment |
| [Collection Tab probe](2026-07-31-collection-tab-probe-pending-rollback.md) | Temporary state pending rollback |

## Open gates

- Inspect the current collection editor hierarchy and dirty state before any
  reload.
- Decide whether to retain or roll back the Header Section structural probe.
- Map another Section palette category, then record only the confirmed direct-child choices. Use hierarchy `add > Add Child` when canvas controls are unavailable.
- Complete the collection-probe rollback.
- Capture and verify rollback CJSON and VM.
- Verify the exact two-Tab order and probe marker absence.
- Recheck collection data-bound controls after rollback.
- Test dynamic header actions.
- Test product purchase, Notify Me, and out-of-stock states.
- Complete mobile and tablet acceptance.
- Reconstruct and verify the footer.
