# Core element and setting reference

Use this reference to plan a Visual Builder hierarchy before opening element
settings. Verify every planned type in the selected parent's palette. Runtime
metadata predicts capability; it does not prove that a type is available under
the current parent, persists in CJSON, compiles to Velocity, or renders on the
public route.

## Contents

- [Catalog boundary](#catalog-boundary)
- [Layout primitives](#layout-primitives)
- [Static content](#static-content)
- [Local scoped styles](#local-scoped-styles)
- [Visibility and conditional logic](#visibility-and-conditional-logic)
- [Item and collection elements](#item-and-collection-elements)
- [Responsive serialization rule](#responsive-serialization-rule)

## Catalog boundary

The observed reference editor loaded Visual Builder compiler `0.1.0` with 532
widget implementations. The runtime grouped them into content, grid, layout,
logic, input, navigation, item, item list, page, blog, cart, checkout, order,
my-account, review, email, search, and other specialized groups.

The implementation metadata exposed four different child signals:

- `allowAddChildren: true` for a normal containing type;
- a function-valued `allowAddChildren` for a context-dependent container;
- `addChildForceType` for a forced child type;
- `allowedUnder` and `allowedChild` predicates for placement constraints.

The observed catalog contained 154 normal containers, 11 context-dependent
containers, 6 forced-child containers, and 361 types without a general child
capability. Treat these as a versioned catalog observation. Confirm actual
placement through the visible parent-aware palette.

## Layout primitives

### Section

Use a Section for a full page region. Its observed settings include:

- width and custom width;
- background color, image, responsive image, lazy loading, and position;
- responsive margin, padding, and borders;
- corner radius, font defaults, sticky behavior, shadow, animation, and
  gradient;
- `scopedStyles`, display, CSS classes, clear, print, and search-index rules.

### Row

A Row forces Column children. Configure:

- `width`, `widthCustom`, `rowDisplay`, and `height`;
- background color or image;
- breakpoint-aware `gridRowGap` and `gridColumnGap`;
- responsive Row padding and Column padding;
- equalized Columns and minimum equalizer breakpoint;
- `rowAlternateSmall`, `rowAlternateMedium`, and `rowAlternateLarge`;
- responsive margin and borders;
- corners, sticky behavior, shadow, animation, gradient, and scoped CSS.

Use `rowDisplay: grid` only after verifying its generated layout. The normal
Elements grammar uses a Row with Column children.

### Column

A Column is allowed under a Row. Configure:

- `gridColumnCountSmall`, `gridColumnCountMedium`, and
  `gridColumnCountLarge`;
- per-breakpoint horizontal alignment;
- per-breakpoint push, pull, and offset;
- background color or image;
- responsive margin, padding, and borders;
- corners, shadow, animation, gradient, display, and scoped CSS.

Use a `12` small width as the safe stacked default. Set medium and large widths
from the approved design. Do not assume that a large value is serialized when
it is redundant with medium.

### Panel

Use a Panel as a card, badge group, or local visual container. Configure:

- `panelSmallWidth`, `panelMediumWidth`, and `panelLargeWidth`;
- optional height and aspect ratio at each breakpoint;
- background color, static image, or context-bound page, item, or blog image;
- responsive margin, padding, borders, and flex order/grow/shrink/alignment;
- corners, sticky behavior, animation, gradient, display, and scoped CSS.

Panels accept normal child content. The observed offer cards used intrinsic
inline-block widths, backgrounds, padding, radius, and a selected-card border.

### Aligner, Accordion, and Tabs

- Aligner accepts content and provides responsive vertical and horizontal
  alignment.
- Accordion forces Accordion Item children. Configure multi-expand and
  all-closed behavior on the parent. Configure title colors, content
  background, open-on-load state, spacing, and fonts on each item.
- Tabs accept Tab children. Configure tab alignment, small-screen accordion
  behavior, default tab, remembered selection, colors, spacing, borders, and
  fonts. A Tab provides desktop and small-screen titles plus local surface
  settings.

## Static content

### Image

Use these observed keys:

```text
imageUrl imageWidth imageHeight imageFullWidth imageDecorative imageAltText
imageSiteAttributeName imageLightboxFullSize imageLazyLoad imageAspectRatio
imageResponsivePictureTag alignSmall alignMedium alignLarge imageVerticalAlign
imageRadius imageOpacity imageColor
```

Images also support responsive borders and margins, local padding, animation,
gradient, display, CSS classes, and scoped CSS. Verify the saved URL and alt
text, then scroll the public image into view and require non-zero bounds.

### Headline

Use `html` for content and select `headlineTag`. Configure display, width,
vertical position, responsive alignment, text and background colors, overlay,
line height, transform, letter spacing, columns, responsive spacing and
borders, corners, and fonts.

The font group includes Typekit, Google, native, and generic font choices plus
base, medium, large, fluid size, and weight. The observed font picker saved a
Google family through `googleFont`.

### Text Block and Bullet List

Text Block uses `richText`. Bullet List uses `html` and supports icon, icon
color, alignment, special list type, and new-item display settings. Both
support color, typography, spacing, animation, gradient, display, and scoped
CSS. Use the HTML source editor and public readback for persistence proof.

### Button, Link, Divider, Video, and HTML

- Button supports text, subtext, icon or image, action, URL target, Add to Cart
  behavior, post-action behavior, coupon, item and quantity changes, mailto,
  show/hide/toggle targets, scroll target, confirmation, colors, responsive
  width and alignment, typography, spacing, analytics, accessibility, and SEO.
- Link accepts children and supports URL, target, alt text, nofollow, stretched
  ancestor behavior, spacing, analytics, and scoped CSS.
- Divider supports line style, width, alignment, optional text, spacing, and
  fonts.
- Video supports URL, autoplay, controls, loop, maximum width, poster,
  captions, transcript, playback-triggered element display, and local CSS.
- HTML uses `htmlBlock`. Treat it as an escape hatch, not a substitute for a
  hierarchy that must remain editable and dynamic.

Do not execute purchase, form, coupon, or other state-changing Button actions
during a visual verification unless the work order authorizes that action.

## Local scoped styles

The observed `scopedStyles` setting used a breakpoint-keyed object whose
values were CSS strings. Verified keys included `all` and `medium-up`. `all`
applied without a media wrapper. `medium-up` applied at the observed 40em
minimum-width breakpoint.

A bare declaration block targets the owning widget. Descendant selectors are
automatically prefixed with that widget's scope. Do not repeat the owning
widget's generated ID inside its own scoped styles because that can produce a
double-prefixed selector. Parent Panel styles can target their descendants.

This behavior is compiler-version specific. Verify public computed styles and
fresh source artifacts before making a CJSON or Velocity persistence claim.

## Visibility and conditional logic

Use responsive `showOn` for device visibility. Do not confuse it with runtime
business conditions.

`HideIf` and `ShowIf` can test checkout mode, affiliate, checkout type, upsell,
receipt, my-account, wholesale status, login, coupon, item stock, country,
state, URL path, translation availability, customer tag, and related context.
The generic `If` supports a type, Velocity statement, URL parameter, cart or
order item, subtotal, item tag, and show/hide target IDs.

Verify the resulting tree scope and compiled wrapper. An empty or invalid
condition can hide an entire otherwise valid container.

## Item and collection elements

Preserve the existing dynamic branch whenever possible.

- ItemForm owns post-action show, hide, toggle, and scroll behavior plus Open
  Graph output.
- ItemTitle supports tag, display, width, content, colors, typography, and
  spacing.
- ItemPrice supports original, sale, from, case-unit, and total display.
- ItemQuantity supports plus/minus controls, zero initialization, checkbox
  mode, responsive flex alignment, colors, spacing, and fonts.
- ItemAutoOrderSchedule supports `hideAncestorIfEmpty` and hiding the None
  option. Move its containing Label and Row when preserving subscription UI.
- ItemImageGalleryV2 supports image bounds, variant-media behavior, theme,
  context, orientation, thumbnail layout, media display, and modal behavior.
- ItemList and PageList are authorable list containers, not one node per
  rendered record. Both support layout, maximum count, gap, Column counts,
  alignment, equalization, spacing, borders, animation, and local CSS.

For ItemList, preserve the nested ItemLink, ItemTitle, ItemPrice, media,
wishlist, sale, stock, review, and other dynamic leaves. For PageList, preserve
PageLink and its title and image descendants.

## Responsive serialization rule

The editor uses two responsive patterns:

1. Explicit keys such as `gridColumnCountSmall`, `Medium`, and `Large`.
2. One setting key whose saved CJSON value is a breakpoint map, such as a
   border color or padding object keyed by `small`, `medium`, or `large`.

Inspect the saved CJSON instead of assuming one representation. Verify each
in-scope viewport on the public route.

On the observed Elements compiler, `showOn` produced these visibility classes:

| `showOn` value | Compiled visibility |
| --- | --- |
| `mobile` | Hide medium-only and large |
| `mobile,tablet` | Hide large |
| `tablet,desktop` | Hide small-only |
| `desktop` | Hide small-only and medium-only |

This mapping is verified for the captured compiler version only. Recheck the
generated VM when the theme or compiler changes.
