# 2026-07-31 Home imported body probe

Classification: Verified on editor hierarchy and save/reload surfaces;
public isolated effect remains Unknown.

## Scope

This was one owner-approved hierarchy probe on the MELRA Home testbed. The
probe used the existing imported `container-body` composition. It did not use
FTP, direct source editing, catalog data, checkout actions, or customer data.

## Observed sequence

1. The Home hierarchy exposed the imported roots in this order:

   ```text
   container-header
   container-body
   container-main-footer
   ```

2. The direct child palette opened from `container-body` exposed `body` as an
   allowed direct child. The palette also exposed other root-context choices;
   their presence was not treated as a placement or rendering claim.
3. Selecting `body` created one direct child under `container-body`:

   ```text
   container-body
     body
   ```

4. The editor Save control cleared its unsaved state. A reload restored the
   same direct child and its type.
5. The non-editor Home route rendered the existing storefront and did not show
   a missing-body error. Because the `body` widget has no visible content, the
   isolated visual contribution of that leaf is not observable on this route.

## Evidence classes

| Claim | Status | Evidence surface |
| --- | --- | --- |
| `body` is allowed directly under the imported body container in this editor | Verified | Current parent-aware palette |
| The inserted node is a direct child of imported `container-body` | Verified | Current hierarchy DOM |
| The relationship survives Save and editor reload | Verified | Save state and fresh hierarchy DOM |
| Home renders without a missing-body error | Verified | Non-editor Home DOM |
| The body leaf contributes visible public content | Unknown | No body content was configured |
| CJSON-to-VM causality for this exact insertion | Unknown | Source diff was not captured in this probe |
| Imported-body reuse on another route | Unknown | No second-route mutation was made |

## Reusable rule

The editor distinguishes an imported container from the leaf `body` widget.
The container is the reusable layout laboratory. The `body` widget is a
direct-child leaf and is not a parent for Sections, Rows, or Columns. Future
layout probes should open the palette from the imported container's direct
child, then use the allowed layout parent such as Section.
