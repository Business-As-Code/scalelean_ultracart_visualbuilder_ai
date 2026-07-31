# Desktop design intake and acceptance contract

Use this contract before recreating an approved desktop design in UltraCart
Visual Builder. Treat every blank or unverified field as `Unknown`. Do not
accept the result while a required field is `Unknown`.

## 1. Lock the authority and route

Record these values before opening the editor:

| Required field | Record |
| --- | --- |
| Controlling work order | Issue ID and approved mutation |
| Test StoreFront | Merchant and StoreFront identity |
| Page class | Home, content, collection, item, or other |
| Editor route | Exact URL and `editMode` state |
| Public route | Exact non-editor URL |
| Reference design | Exact URL, image, or design artifact |
| Allowed writes | Named Visual Builder changes only |
| Forbidden writes | Catalog, price, inventory, checkout, customer data, and direct FTP writes unless separately approved |
| Rollback owner | Named operator |
| Acceptance owner | Named verifier |

Confirm that the editor URL, visible canvas, top-level hierarchy, and public
route identify the same page. Stop if they disagree.

## 2. Freeze the comparison viewport

Record the desktop viewport width, height, device scale, browser, zoom, and
scroll position. Capture the reference and result with the same values. Record
whether lazy-loaded content requires scrolling before measurement.

Before the first screenshot comparison, record all four maximum thresholds,
the pixel-delta threshold, and every zero-based mask rectangle. Record `none`
when no mask is approved. Do not add or tune a mask or threshold after viewing
comparison metrics. Masks may exclude declared dynamic regions only; they must
not conceal a layout defect.

List every responsive viewport in scope with its width and acceptance checks.
If the task is desktop-only, state that mobile and tablet are out of scope and
`Unknown`.

Do not infer mobile, tablet, cross-browser, or production behavior from one
desktop check. Mark each untested viewport or environment `Unknown`.

## 3. Inventory the design

Divide the page into ordered regions. At minimum, classify the header, main
body, and footer. Divide the body into named sections in top-to-bottom order.
Treat shared header and footer branches as separate mutation surfaces. Do not
edit them unless the work order names them.
For each region, record:

| Property | Required decision |
| --- | --- |
| Ownership | Shared StoreFront structure or page-local structure |
| Content source | Static editorial content or UltraCart dynamic content |
| Required copy | Exact text, punctuation, capitalization, and line-break intent |
| Required assets | Source URL or approved asset, alt text, crop, and intended dimensions |
| Typography | Font family, weight, size, line height, letter spacing, color, and alignment |
| Surface | Background color or image, border, radius, and shadow |
| Geometry | Container width, column ratio, element width and height, gap, padding, and margin |
| Behavior | Link, form action, selection state, conditional state, or no interaction |

Do not replace a dynamic component with static content unless the work order
explicitly permits that loss of behavior. Do not claim that repeated rendered
cards, slides, products, or records require one authorable node per instance.

## 4. Protect native behavior

List every native control that must remain active. For an item page, inspect
the complete `ItemForm` branch before editing. Include the applicable product
media, title, reviews, price, stock state, subscription schedule, quantity,
Add to Cart, structured-data wrapper, and conditional purchase branches.

Move the smallest containing Row that preserves its Columns, Labels, and
conditional descendants. Do not move only the visible control leaf. Treat an
unexercised alternate state, including out-of-stock or Notify Me behavior, as
`Unknown` even when its branch remains present.

Do not execute a native control action unless the work order authorizes that
interaction.

## 5. Approve the hierarchy plan

Write the intended tree before editing. Use exact parent, child order, and
responsive width values. Prefer the observed page grammar and the existing
rendered branch. Do not assume that a new top-level container will compose
into the public route.

For each planned node, record:

```text
region | parent | type | purpose | sibling position | responsive values
```

Open the selected parent's palette and confirm that it offers the planned
child type. Mark unsupported placement `Unknown`; do not infer support from a
different parent. Reopen the hierarchy after each insertion or move and
verify indentation and sibling order.

## 6. Set acceptance rules before editing

Use zero tolerance for these checks:

- exact copy, punctuation, and capitalization;
- required asset identity and alt text;
- required node parentage and sibling order;
- required dynamic versus static classification;
- required native-control presence and action;
- exact colors when the reference supplies color values;
- required link targets and form ownership.

Record numeric tolerances for font size, line height, element bounds, gaps,
padding, margin, and section position before editing. Record a tolerance per
property and viewport. Do not invent a default. If the reference does not
provide a measurable value or the owner does not approve a tolerance, mark
that property `Unknown` and exclude it from a pass claim.

Define acceptance as all required checks passing within their recorded
tolerances. Do not substitute visual similarity, an editor preview, or a save
confirmation for the recorded checks.

## 7. Control the editing session

Assign one writer to the mutable editor tab. Keep all other agents and browser
tabs read-only. Do not let two writers modify the same page or shared
structure in one save window.

Use these checkpoints:

1. Capture the private baseline CJSON and VM pair.
2. Record the saved hierarchy and editor dirty state.
3. Make one coherent hierarchy batch.
4. Reopen the hierarchy, compare it with the approved plan, and immediately
   store an exact private browser checkpoint before any save or navigation.
5. Save once through the visible editor path.
6. Wait for a completed save response, then verify persistence separately.
7. Capture fresh CJSON and VM.
8. Reload the editor only after protecting or resolving all unsaved work.
9. Reload the public route and perform acceptance measurements.

If UltraCart expires the session, do not reload the unsaved editor. Restore
the admin session in a separate tab, then retry once. After an ambiguous save,
inspect fresh CJSON and VM before another retry.

## 8. Verify all four surfaces

Require agreement across these independent surfaces:

| Surface | Required proof |
| --- | --- |
| Editor | Intended hierarchy, names, settings, and clean reloaded state |
| CJSON | Target parentage, source absence after moves, child order, text, assets, responsive settings, and visibility settings |
| Velocity | Expected generated text, assets, styles, dynamic wrappers, and native controls |
| Public route | Intended desktop composition, exact copy and assets, measured geometry, active native controls, and owner-approved interaction checks |

Treat a save callback, version increment, canvas render, or dirty indicator as
one signal only. Do not accept CJSON-to-VM causality without a before, saved,
and rollback sequence that agrees across the relevant surfaces.

Use rendered-HTML `--require-match` only for like-for-like snapshots from the
same route, state, viewport, and capture method. Its exact match covers
aggregate Visual Builder type and hierarchy-edge counts, not content or visual
identity. Use screenshot comparison only with the thresholds and masks recorded
before editing. A passing screenshot does not prove native-control behavior.

## 9. Roll back and close the test

Capture the accepted saved state before rollback. Remove only the approved
test change through Visual Builder, save once, and recapture the same CJSON
and VM pair. Reload the editor and public route. Confirm that the baseline
hierarchy and rendered behavior return.

Record any semantic hierarchy, configuration, generated-behavior, or rendered
mismatch as a failed rollback. A byte-only difference is unresolved until a
structured comparison determines whether UltraCart normalized an equivalent
document. Stop further editing until the rollback owner resolves any semantic
or behavioral mismatch. Keep credentials, raw captures, screenshots, session
data, and source bytes out of Git and chat.

## 10. Report the result

Report each claim as `Verified`, `Contradicted`, or `Unknown`. Include the
route, viewport, hierarchy branch, tolerance, and four-surface evidence for
every accepted claim. State unsupported capabilities as `Unknown`; do not
generalize reference observations into universal UltraCart behavior.

Create one run manifest from the explicit checkpoint, CJSON, VM, rendered-HTML,
and screenshot artifacts used for the claim. The manifest binds roles to hashes
and byte counts without retaining source paths or bytes. It does not replace the
claim-level verifier or record screenshot masks and thresholds.
