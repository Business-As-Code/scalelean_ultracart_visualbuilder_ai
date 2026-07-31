# Visual Builder capability map

Scope: owner-approved exploration of the reference development StoreFront in the
Visual Builder. This is the historical starting map. Later dated deltas link
source-proven results. Use the consolidated system model and observation
register for current state.

## Verified Home-page patterns

| Capability | Observed behavior | Evidence class |
| --- | --- | --- |
| Structure | The Home canvas is composed of named containers such as header, slider, featured content, mailing list, and footer. | Verified in editor hierarchy |
| Nested layout | A Mailing List container accepted a `section`; that section accepted a nested `section`. | Verified in editor hierarchy and canvas |
| Parent-aware palette | The element picker changes with the selected parent. Under a Section, only a nested Section and Checkout Condition appeared in the Grid category. | Verified in editor palette |
| Item component | A blank Item child rendered an explicit `No item ID configured` state. It requires configuration before it can render a product. | Verified in canvas |
| Background image | A Section can select an existing StoreFront image from the built-in picker. The selected image rendered as the Section background. | Verified in editor and canvas |
| Section controls | Section settings include responsive visibility, width, background color and image, lazy loading, background position, spacing, borders, corners, fonts, sticky behavior, effects, animation, CSS, and search. | Verified in settings panel |
| Save | Saving the edited Home containers produced the editor confirmation `Containers saved.` | Verified in editor |

The controlled Mailing List experiment also verified that adding and saving a
Section changes the selected logical CJSON and VM pair together. See
`2026-07-30-controlled-save.md` for its limited proof boundary.

## Verified hierarchy grammar

The element palette is parent-aware. The observed parent-to-child rules differ
materially:

| Selected parent | Observed allowed children or categories | Evidence class |
| --- | --- | --- |
| Section | Nested Section and Checkout Condition in its Grid palette. | Verified in palette |
| Generic Item | Advanced, Blog, Checkout, Content, Grid, Input, Item, Item List, Layout, Logic, My Account, Navigation, Off Page, Other, Page, Store Locator, and Testing. | Verified in palette |
| HideIf | The same broad category palette opened when the context menu requested a child. | Verified in palette |

The Generic Item palette contained these observed core types:

| Category | Types |
| --- | --- |
| Content | Divider, Site Attribute, Webchat |
| Grid | Absolute Wall, Checkout Condition, Flex, Masonry Wall, Page Container, Panel, Row, Section, Table |
| Item List | Item List, Item List Form |
| Layout | Accordion, Slider |
| Logic | Hide If, If, Show If |
| Navigation | Mega Menu, Skiplink |

### Conditional-wrapper experiment

On the approved Home test branch, the saved Section tree showed `Divider`,
`HideIf`, and `Item` at the same visible indentation. The canvas presented the
HideIf layer over the item region. In contrast, the existing Footer hierarchy
has a `HideIf` node with `Headline` and `Menu` as its direct children.
Therefore a logic node can be an ordinary containing branch or an adjacent
control, depending on the existing hierarchy and insertion behavior. The
editor menu's `Add Child` wording is not sufficient proof of a resulting tree
relationship. Inspect the hierarchy after every insertion.

The HideIf settings exposed conditions for checkout mode, affiliate pages,
single- and multi-page checkout, upsell, receipt, My Account, wholesale and
non-wholesale status, logged-in status, coupon state, and item stock state.
No condition value was set in this experiment.

### Shared Header and slider patterns

The shared Home Header hierarchy contained these verified paths:

```text
Header
  Mobile/Tablet Menu
  Desktop Menu
    Logo Column
      HomeLink
        Image
    Menu Column
      HideIf
      CartItemCount
```

`Mobile Side Menu`, `Cart Snapshot Sidepanel`, and `Language Picker Modal`
appear as separate siblings of Header inside the shared Header container, not
as children of its desktop-menu branch.

The Mobile Side Menu has its own component tree:

```text
Mobile Side Menu
  Hide Search If Checkout Only
  Hide Menu If Checkout Only
  Row-3
    Column 1
      HTML
    Column 2
      MyAccountLink
    Column 3
      CartView
```

This confirms that shared side panels use the same Row and Column layout
grammar as page content, but remain separate branches from the desktop header.
The two HideIf entries appear as direct siblings of that layout Row.

The Cart Snapshot Sidepanel is also a composite sibling branch, rather than a
leaf widget:

```text
Cart Snapshot Sidepanel
  Count Title Close
    Column 1
      CartItemCount
    Column 2
    Column 3
  Divider
  Contents
  Divider
  Buttons
```

The editor labels the Count Title Close, Divider, Contents, and Buttons
entries as Rows. The currently visible tree verifies only CartItemCount inside
Count Title Close's first column. The exact descendants of its other columns,
Contents, and Buttons are still unknown.

The shared Footer is likewise a composite branch:

```text
Footer
  Webchat
  Row-4
    Column 1
      HideIf
        Headline
        Menu
    Column 2
      HideIf
    Column 3
      HideIf
    Column 4
      Headline
      Panel
        SiteAttribute
  Row-3
  Row-2
```

`Menu` had no visible authorable descendants in this expansion. It is a
dynamic leaf in this observed template, even though it renders several links.
Columns 2 and 3 had unexpanded HideIf branches. The other footer Rows require
later expansion.

The Home carousel began with:

```text
Home Slider container
  Main Slider
    Slider
```

The canvas rendered a carousel. A later hierarchy expansion exposed authorable
slide branches:

```text
Home Slider container
  Main Slider
    Slider
      Slide 1
        Title
        Subtitle
      Slide 2
      Slide 3
        Title
        Subtitle
```

`Slide 1` and `Slide 3` both exposed `Title` and `Subtitle` leaves in the
current Home configuration. The active rendered slide can differ from the
expanded branch, so a public render is needed to confirm which visible slide
received a change.

### Mailing-list component pattern

The Mailing List container starts with a normal layout branch, then a
data-aware signup component:

```text
Mailing List
  Row-1
    Column 1
      Mailing List Signup
        Headline Row
          Column 1
            Headline
        Form Field Row
          Column 1
            Label
          Column 2
            Label
          Column 3
            Label
          Column 4
            Button
        Mailing List Signup Error
        Mailing List Signup Success
```

The error and success entries are editor-labelled modal branches. The three
Labels render the visible email, first-name, and last-name fields in this
template, but their exact binding configuration is not yet inspected. The
Button renders the visible signup action.

### Working model for hierarchy decisions

| Kind of element | What to expect in the hierarchy | Example evidence |
| --- | --- | --- |
| Structural layout | An explicit authorable branch. | Section, Row, and Column. |
| Conditional or presentation control | It can be a normal containing branch or a sibling control. Verify its actual indentation after insertion. | HideIf. |
| Data-driven display | A small named tree can render many records or instances. Do not look for one editable child per rendered card or slide. | Slider and PageList. |
| Shared UI surface | A separate sibling branch can use normal structural children while remaining outside the page's desktop layout. | Mobile Side Menu. |

`Section → Row → Column` is a repeated pattern in existing templates. It is
not a universal construction rule. On the approved test Section, the child
picker offered only a nested Section and Checkout Condition. Inspect the
palette of the selected parent before planning a new layout branch.

## Verified collection-page patterns

The Shop collection page loaded in the same edit mode but exposed a different
content model:

```text
Collection page containers
  Header
  PayPal Messaging
  Subgroup List
  Group Facets
  Mailing List
  Footer

Subgroup List
  Row-1
    Column 1
      PageList (editor badge: 1/3)
        PageLink
          PageTitle
      PageSelect
```

`PageList` settings exposed display mode, optional page path, maximum pages,
background color and image, hide-ancestor-if-empty behavior, row and column
padding, and responsive column counts. The page also has a Group Facets
container, represented by its own top-level Section, separate from the
subgroup-list container:

```text
Group Facets
  Section
    Row-1
      Column 1
        PageTitle
        Tabs
          Tab
            Row-2
          Tab
```

The canvas maps `PageTitle` to the `SHOP` heading and `Tabs` to the Items and
Filters interface. The editor also renders an `Add Tab` authoring affordance;
it was not a third saved Tab node in this 2026-07-30 baseline. A later saved
probe created a third Tab with a direct Text Block child. See
[Collection Tab probe pending rollback](2026-07-31-collection-tab-probe-pending-rollback.md).
The deeper pre-existing Items and Filters descendants remain a separate
dynamic hierarchy.

## Verified item-page patterns

The item page loaded in edit mode with an Item Display container. Its core
visible hierarchy was:

```text
Item Display
  Section
    ItemForm
      Row
        Column
          ItemOutOfStock
            ItemImageGallery (hidden)
            ItemImageGalleryV2
      Row
      Row
      ItemStructuredData
```

The media row is a two-column Row. Its first Column contains `ItemOutOfStock`,
then `ItemImageGallery` (marked hidden) and `ItemImageGalleryV2`. The second
Column contains the normal item-detail sequence:

```text
Column 2
  ItemTitle
  ItemReviewSummary
  Row-Price-Review
    Column 1
      ItemPrice
    Column 2
  Row-Sezzle
  Row-Affirm
  Row-Description
  Row-1
  Subscription Row
  Row-3
  HideIf - Out of Stock
  Row-2
```

The names after `Row-Description` are existing component names, not claims
about their rendered purpose. Their internal children still require a focused
inspection before modification.

The active item view showed an image gallery, item title and price, description,
subscription selector, quantity control, add-to-cart action, and stock-state
presentation. The `ItemOutOfStock` wrapper is a conditional presentation
layer. It is not evidence that the tested item is out of stock.

At the container level, `container-item-display` has two first-level branches:
an `error message modal` and a main Section. This separates error handling
from the item-layout tree.

## Verified shared editor systems

| System | Observed behavior | Evidence class |
| --- | --- | --- |
| Theme Settings | Global element-default groups include body, containers, side panels, buttons, headings, inputs, labels, tabs, and accordions. | Verified in editor panel |
| Languages | The StoreFront presents a language enablement list and per-language edit controls. Only English was enabled in the observed demo state. | Verified in editor panel |
| Library | The library is organized into My Elements, Bookmarked Elements, Shared With Me, Featured Elements, and Search. | Verified in editor panel |
| Preview | Preview opens separately with Mobile, Tablet, Desktop, and All modes, device presets, custom width/height inputs, and an apply action. | Verified in preview surface |

The responsive preview rendered the same item template at mobile, tablet, and
desktop breakpoints. This verifies the preview workflow, not visual quality or
cross-browser compatibility.

## 2026-07-31 capability delta

A later owner-approved desktop pass added source-proven hierarchy evidence.

| Capability | Verified result | Remaining limit |
| --- | --- | --- |
| Reversible hierarchy visibility | A retained Text Block compiled and rendered as `display: none` after save and reload. | This is not responsive `showOn` or runtime `HideIf`. |
| Panel composition | A Panel accepted an Image as a direct child; three offer Panels and one mixed subscription Panel persisted in CJSON and generated VM. | Static presentation does not replace native subscription or purchase behavior. |
| Item layout | A 5/7 hero, four-item benefits list, offer cards, and preserved native subscription and purchase Rows passed editor, source, and public readback. | Purchase, Notify Me, and out-of-stock actions were not exercised. |
| Shared desktop header | Utility and navigation Rows, logo, phone content, Search Input, My Account Link, and Cart Item Count persisted and rendered on Home, Shop, and product routes. | Search, account-state, cart-sidepanel, language, and mobile behavior need separate action tests. |
| Scoped styles | Breakpoint-keyed CSS strings compiled with root and descendant scoping and matched public computed styles. | Treat this as compiler-version specific. |
| Collection Tab insertion | Tabs forced a Tab child; the saved Tab accepted a direct Text Block and rendered publicly without replacing the observed collection families. | Delete, rollback capture, and current editor dirty state remain unconfirmed. |

This delta raises confidence for item, collection, and desktop shared-header
work. It does not raise the overall hierarchy score because collection
rollback and editor-state resolution, footer reconstruction, rollback
equivalence, and dynamic-control action proofs remain.

## Operating implications

1. Start from the intended container and inspect its allowed child palette.
   Do not assume every element type can be added at every level.
2. After an insertion, re-open the hierarchy and verify indentation and sibling
   order. Do not rely on `Add Child` as a proof of parentage.
3. Use Sections, Rows, and Columns for layout. Use dynamic components such as
   PageList and ItemForm when the page must bind StoreFront data. Treat the
   Section-to-Row-to-Column sequence as a template-reading pattern, not a
   guarantee that any selected Section can accept a Row or Column.
4. Configure backgrounds through the editor's existing-image picker when an
   asset is already in the StoreFront. Do not upload a file for a capability
   test.
5. Save after a coherent test batch and capture source deltas only when a
   specific CJSON/VM claim needs proof.
6. Use Preview to inspect responsive behavior before claiming that a layout is
   ready for mobile, tablet, or desktop.
7. Keep global theme and language settings read-only during discovery. They
   apply beyond the current page.
8. Keep item configuration and customer-facing flows out of exploratory tests
   unless the required product data and verifier are known.

## Hierarchy readiness assessment

This assessment applies only to the observed reference Elements-theme development
StoreFront. It is not a claim that every UltraCart theme or custom element uses
the same tree.

| Common task | Current hierarchy guidance | Confidence |
| --- | --- | --- |
| Read and change a normal page layout | Begin at the named container, expand the existing Section, Row, and Column branch, then inspect that parent’s palette before adding. | 8/10 |
| Place or inspect image content | Treat an image as a leaf in a known content or media branch. Use existing asset selection only; do not assume an image is a generic child of every Section. | 8/10 |
| Add or inspect content | Use the selected parent’s palette. Verified editorial leaves include Image, Headline, Text Block, Bullet List, and Divider. Specialized dynamic leaves remain parent-dependent. | 8/10 |
| Change shared navigation | Keep Desktop Menu, Mobile Side Menu, Cart Snapshot Sidepanel, and Language Picker Modal as separate Header-container siblings. | 8/10 |
| Change collection navigation | Work in Subgroup List, then follow Row, Column, PageList, PageLink, and PageSelect. | 8/10 |
| Change collection filtering | Work in Group Facets, not PageList. Trace its Section, Row, Column, PageTitle, and Tabs branch. | 8/10 |
| Change an item template | Work in Item Display, then ItemForm. Keep media and details in their observed separate columns; retain Error Message Modal as a sibling. | 8/10 |
| Use conditions | Re-open the resulting tree after insertion. HideIf can be a conventional parent or an adjacent control. | 7/10 |

The evidence supports an **8/10 operating understanding for hierarchy-first
work on this StoreFront**. The score is for locating the correct branch,
understanding the major structural and data-bound components, and avoiding the
most likely invalid-parent mistakes. It does not cover arbitrary custom
components, complete conditional semantics, product data changes, uploads, or
source-code equivalence.

## Open questions

- The unexpanded descendants and settings of Home Slider Slide 2.
- The descendants of Cart Snapshot Contents and Buttons, and the Footer's
  lower Rows.
- The deeper pre-existing dynamic contents of Group Facets Items and Filters,
  and uninspected ItemForm branches.
- Which layouts each non-Section parent permits.

## Session-specific route caution

The parent route `shop/?editMode=true` loaded a matching collection canvas and
the collection containers listed above. A direct subgroup route earlier
rendered a collection while retaining a Home-shaped hierarchy, and refresh
then returned the editor to Home. Before recording a collection tree, verify
that the page URL, visible canvas, and top-level container names all agree.
Prefer the parent collection route for first-pass hierarchy work.
