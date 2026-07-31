# Joint Support offer hierarchy refinement

Date: 2026-07-31.

## Scope

This was an owner-approved reconstruction on the reference development
StoreFront item route. The reference was the owner-controlled Clinical
Effects Joint Support page. Acceptance used a 1440 by 1100 desktop viewport.
The logged-in public route added a 36-pixel UltraCart admin bar, which was
excluded from storefront vertical comparisons. No purchase action, product
data change, direct FTP write, or customer-data action occurred.

## Saved hierarchy

The saved ItemForm retained UltraCart's native product and purchase branches.
The reference-matching branch was:

```text
row-4806392: 5/7 hero
  column-4806393
    image-4808923
    textblock-4806395: retained and hidden
    bulletlist-4806396: four public benefit items
  column-4806432
    headline-4806394
    headline-4806433
    textblock-4806434
    panel-1000 > image-1000, headline-1001, textblock-1000
    panel-1001 > headline-1004, image-1002, headline-1002, textblock-1001
    panel-1002 > image-1003, headline-1003, textblock-1002
    panel-1003 > bulletlist-4806435, row-387942, image-4810903
    image-4808924
    image-1001
    row-4717
    headline-1000
```

The three one-time offer Panels are static presentation components.
`panel-1003` is mixed: it owns static presentation leaves and native
subscription `row-387942`. Native purchase `row-4717` is a later sibling in
the offer Column. Static content does not replace subscription schedule,
quantity, Add to Cart, or Notify Me behavior.

## Verified desktop geometry

| Region | Public result |
| --- | --- |
| Hero Row | x 120, width 1200 |
| Hero Columns | 500 and 700 pixels |
| Main product image | 500 by 500 pixels |
| One-time Panels | 195.328125 by 295.4375 pixels |
| Subscription Panel | width 599.992 pixels, height 237 pixels |
| Benefits list | width 500 pixels, height 461 pixels |

The recorded one-time card box residuals against the reference were no more
than 0.6 pixels. The benefits list rendered with Roboto at 20 pixels and a
32-pixel line height. Its native 20-pixel `circle-check` marker used the
configured blue icon color. The retained duplicate Text Block computed to
`display: none`.

## Scoped-style behavior

The observed `scopedStyles` setting accepted breakpoint-keyed CSS strings.
Bare declaration blocks targeted the owning widget. Descendant selectors were
automatically prefixed by the compiler. Parent Panel styles positioned known
descendants without global CSS. Repeating the owner's generated ID in its own
style would produce a double-prefixed selector and must be avoided.

## Save and source evidence

The editor reported `Containers saved.`, cleared the unsaved-change state,
and retained the hierarchy after reload. The public item route retained the
layout, images, four benefits, icon styling, hidden Text Block, and native
purchase-control structure after reload.

A fresh bounded FTPS capture completed at 2026-07-31 15:29 UTC with no
candidate failures. The source hashes were:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `item-display.cjson` | 301948 | `13ee5f1a07fda1c66bdde3c485d16023145d015ebb012c14b131b25bd6a6aa30` |
| `item-display.vm` | 188462 | `b53718ff0f1019ea298d8a2a696182ef80e7a3b4c77c8e01b5f7f501c99c1042` |

CJSON confirmed the 5/7 Row settings, direct Panel children, hidden widget,
four-item Bullet List, image width, and native Row parentage. Generated
Velocity contained the expected scoped selectors, Image, native controls,
and `circle-check` list rendering.

## Evidence matrix

| Claim | Editor | Public | CJSON | VM | Status |
| --- | --- | --- | --- | --- | --- |
| `Panel > Image` direct child | Yes | Yes | Yes | Yes | Verified |
| Hidden Text Block retained and rendered hidden | Yes | Yes | Yes | Yes | Verified |
| Three one-time offer Panels | Yes | Yes | Yes | Yes | Verified |
| Mixed subscription Panel with native subscription Row | Yes | Yes | Yes | Yes | Structurally verified |
| Four-item benefits list | Yes | Yes | Yes | Yes | Verified |
| Native purchase Rows retained | Yes | Present | Yes | Yes | Structurally verified |

## Limits

- The purchase, Notify Me, and out-of-stock actions were not exercised.
- Mobile and tablet visual acceptance were outside this pass.
- Static offer content does not prove catalog or pricing data binding.
- This pass proves the saved state, not baseline-to-save-to-rollback causality.
- Re-enabling or rolling back the hidden Text Block remains untested.
