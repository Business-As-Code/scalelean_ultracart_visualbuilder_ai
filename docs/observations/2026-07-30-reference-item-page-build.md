# reference item-page hierarchy and composition observation

## Scope

Owner-approved test work on the reference StoreFront item route. No catalog,
price, inventory, checkout, or customer data was changed. All layout
mutations were made through Visual Builder. No direct FTP write occurred.
Visual Builder saves generated new CJSON and Velocity versions.

This record includes intermediate build states. The current accepted saved
product hierarchy is recorded in
[Joint Support offer refinement](2026-07-31-joint-support-offer-refinement.md).

## Verified hierarchy

The inspected item route used this rendered product branch:

```text
container-item-display
  Error Message Modal
  Section
    ItemForm
      Row-2
        Column 1: product media
        Column 2: title, price, description, and purchase controls
```

The live item also retained its quantity and add-to-cart controls in the
ItemForm branch.

## Editor experiment

A new named container, `clinical_product_editorial`, was created above the
item-display container. The editor allowed nested Rows, Headline, and Text
leaves in that container. The editor canvas displayed the editorial content:

- Thoughtful care, made practical
- Transparent by design
- Made for real life

The public item route did not render that named container after a confirmed
save and reload.

## Result

**Contradicted:** a new named container is automatically part of the public
item-page composition.

**Verified:** a named container can be created, edited, saved, and displayed
in Visual Builder edit mode.

**Required next test:** add one static leaf under the existing rendered
`container-item-display > Section` branch, save it, then verify the public
item route before using that branch for a full product-page editorial layout.

## Reusable rule

For item pages, preserve `ItemForm` and build editorial content only from a
verified rendered Section relationship. Do not treat canvas visibility as
public rendering proof.

## Follow-up controlled build

The required next test passed on the same reference item route.

Two new Rows were added as direct children of the existing `ItemForm`.
The first Row used two Columns. The second Row used one full-width Column.
The new hierarchy was:

```text
ItemForm
  Row
    Column
      Headline: Why customers choose Clinical Effects
      Text Block
      Bullet List
    Column
      Headline: 7 Powerful Benefits
      Text Block
      Bullet List
  Row
    Column
      Headline: Clean, Safe Standards
      Text Block
      Bullet List
      Headline: More About the Product
      Text Block
```

The page was saved. The Save control returned to its no-unsaved-changes
state. The non-editor item route was reloaded and contained all of these
signals:

- `Why customers choose Clinical Effects`
- `7 Powerful Benefits`
- `Made in the USA and third-party tested`
- `Clean, Safe Standards`
- `180-day money-back confidence`
- `More About the Product`
- the Directions and Shipping copy

## Rich-text persistence observation

Bullet List source changes persisted on the first public readback. Visible
rich-text edits to the new Headline and Text Block widgets did not. The
public route still showed the default placeholder text.

The same widgets were then edited through the Visual Builder HTML source
mode. Their CodeMirror source was replaced, each widget was saved, and the
page was saved again. The next public reload contained the exact expected
headings and copy.

**Verified:** Rows added directly under the rendered `ItemForm` compose into
the public reference item route.

**Verified:** a Row width selection is a required completion step when adding
a Row from the Grid palette.

**Verified:** source-editor readback is the reliable persistence path for the
observed Headline, Text Block, and Bullet List widgets.

**Contradicted:** a successful visible rich-text edit is sufficient evidence
that the public widget content changed.

## Row placement and move observation

The item-page test also inspected how a direct `ItemForm` Row can move ahead
of the native product Row.

Pointer dragging did not change sibling order. The source Row flyout exposed
`Cut`. After Cut, the Row disappeared from the hierarchy. Opening
`Add Above` on the native product Row opened the parent-aware element palette.
That palette contained a `Clipboard` section with the cut Row as a selectable
card.

**Verified:** the editor represents a cut Row in the placement palette's
Clipboard section.

**Verified:** `Add Above` is a target-relative placement action, separate from
creating a new Row.

**Contradicted:** pointer dragging alone is the observed Row reorder method.

The first move attempt expired before Clipboard insertion and was safely
discarded by reload. A later attempt completed Cut, target-relative placement,
Clipboard insertion, save, artifact capture, editor reload, and public
readback.

**Verified:** the custom editorial Row renders before the native product Row.

## Native purchase-control relocation

The native subscription Row `row-387942` and purchase Row `row-4717` were cut
from `column-4700` and inserted into the custom offer Column
`column-4806432`. The saved target order placed the subscription Row before
the purchase Row. Fresh CJSON showed both new `parentWidgetId` values and
showed that the source Column no longer owned either Row. Generated VM kept
the subscription schedule, quantity field, native Add to Cart action, and the
contained Notify Me conditional branch inside the ItemForm.

**Verified:** moving the containing Rows preserved their descendant hierarchy
and native control structure in CJSON, VM, editor, and public DOM. Active
purchase behavior was not exercised.

**Unknown:** the out-of-stock and Notify Me alternate runtime state was not
exercised. Structural presence of `hideif-358784` is not behavioral proof.

## Image, responsive, and save evidence

The reconstruction used product, package, guarantee, USA, and FDA images.
Observed image setting keys were `imageUrl`, `imageAltText`, and
`imageWidth`. `display: inline-block` preserved intrinsic package and badge
width. Below-fold lazy images required scroll before rendered bounds became
non-zero.

The initial hero used small `12`, medium `6`, and large `6` for both Columns.
CJSON and public desktop bounding boxes confirmed that saved split. A later
reference-matching pass changed the desktop geometry to `5/7`. A clean save,
editor reload, public bounding-box readback, and fresh CJSON and VM capture
verified the desktop result.

The direct front-end save callback completed during the verified move, but the
editor dirty indicator remained set. Fresh CJSON and VM captures contained the
expected parentage, native controls, text, assets, and background style.
Reloading the editor provided the clean-state confirmation. The dirty
indicator alone is not a persistence verifier.

| Claim | Editor | CJSON | VM | Public | Status |
| --- | --- | --- | --- | --- | --- |
| Editorial Row before native Row | Yes | Yes | Yes | Yes | Verified |
| Intermediate hero Columns at `12/6/6` | Yes | Yes | Yes | Yes | Superseded verified state |
| Current desktop hero Columns at `5/7` | Yes | Yes | Yes | Yes | Verified |
| Product and trust images | Yes | Yes | Yes | Yes | Verified |
| Subscription Row moved into offer branch | Yes | Yes | Yes | Yes | Verified intermediate state; later nested in the mixed subscription Panel |
| Quantity and Add to Cart Row under offer Column | Yes | Yes | Yes | Yes | Verified |
| Notify Me alternate condition | Present | Present | Present | Not tested | Unknown |
| Save callback equals clean state | No | N/A | N/A | N/A | Contradicted |
