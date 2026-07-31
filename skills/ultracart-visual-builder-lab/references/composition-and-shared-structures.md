# Composition and shared structures

Use this reference Elements reference when rebuilding shared navigation, footers,
collection pages, or item pages. Treat it as StoreFront-specific evidence, not
as a universal UltraCart schema.

## Contents

- [Compose pages through explicit parses](#compose-pages-through-explicit-parses)
- [Preserve the shared header](#preserve-the-shared-header)
- [Preserve the shared footer](#preserve-the-shared-footer)
- [Build standard and simple collections](#build-standard-and-simple-collections-in-their-existing-containers)
- [Place item-page content](#place-item-page-content-inside-the-rendered-item-branch)
- [Avoid the named-container condition trap](#avoid-the-named-container-condition-trap)
- [Keep these questions open](#keep-these-questions-open)
- [Run experiments in this order](#run-experiments-in-this-order)

## Compose pages through explicit parses

Treat each page template as an explicit ordered composition of container VM
files. Do not assume that creating or saving a named container makes it global.

Edit the Visual Builder hierarchy that owns the CJSON. Do not edit generated VM
files. Each observed generated VM warns against direct edits, checks its CJSON
source hash, and recompiles the matching CJSON when required.

Use this verified template matrix. Read each arrow chain as parse order:

```text
site_404.vm
  header -> mailing-list-signup -> main-footer
template_blog.vm
  header -> theme/containers/blogpost-list
  -> mailing-list-signup -> main-footer
template_blog_post.vm
  header -> blogpost -> mailing-list-signup -> main-footer
template_catalog.vm
  header -> paypal-banner -> subgroup-list -> group_facets
  -> mailing-list-signup -> main-footer
template_catalog_simple.vm
  header -> paypal-banner -> conditional group_item_list
  -> mailing-list-signup -> main-footer
template_catalog_wholesale.vm
  header -> paypal-banner -> wholesale-item-list
  -> mailing-list-signup -> main-footer
template_contact.vm
  header -> contact-form -> mailing-list-signup -> main-footer
template_home.vm
  header -> home-slider -> paypal-banner -> home-subgroup-list
  -> featured-items -> mailing-list-signup -> main-footer
template_item.vm
  header -> clinical_product_editorial -> item-display
  -> mailing-list-signup -> main-footer
template_order_tracking_info.vm
  header -> order-tracking -> main-footer
template_page.vm
  header -> content-page -> mailing-list-signup -> main-footer
template_store_locator.vm
  header -> store-locator -> mailing-list-signup -> main-footer
template_email.vm
  email-header -> compiled email content -> email-footer
template_email_simple.vm
  compiled email content -> email-footer
postcard templates
  no observed container parses
```

Treat `container-header` and `container-main-footer` as shared web structures
because the customer-facing web templates parse them explicitly. Do not treat
them as email or postcard structures.

## Preserve the shared header

Rebuild visible header Sections inside `container-header`. Preserve or
deliberately replace these separate top-level operational branches:

```text
container-header
  Subheader
  Header
    Mobile/Tablet Menu
    Desktop Menu
  custom content Section
  Mobile Side Menu
  Cart Snapshot Sidepanel
  Language Picker Modal
```

Keep the Mobile Side Menu, Cart Snapshot Sidepanel, and Language Picker Modal
as siblings of the visible Header Section. Do not nest them under the desktop
menu.

Move existing dynamic widgets instead of recreating them when possible.
Preserve these observed bindings:

- Keep each dynamic Menu widget on menu name header. The current static
  desktop navigation Text Block has no menu binding and is a visual workaround.
- Keep the hamburger button's toggle target on the Mobile Side Menu.
- Keep both language buttons' show target on the Language Picker Modal.
- Keep the cart-sidepanel close button's hide target on the Cart Snapshot
  Sidepanel.
- Keep the cart-sidepanel checkout button on the native `Checkout` action.
- Preserve Search Input, My Account Link, Cart Item Count, Cart View, Cart
  Snapshot, and Language List as dynamic widgets.

Verify the cart-sidepanel open trigger at runtime. The hierarchy proves the
panel, its contents, close action, and checkout action, but it does not expose
an explicit header-button target for opening that panel.

### Observed reference header branch identifiers

These identifiers record the current saved Elements-theme header branch.
Locate widgets by role and ancestor path before using an identifier in a later
session.

```text
container-header
  section-1573 > row-1603: desktop utility Row
    column-1604 > sociallinks-3660 hidden, textblock-4810908 phone
    column-1605 > wishlistsummary-8732, panel-478893
      wishlistsummary-8732 hidden
      panel-478893 > searchinput-1606, myaccountlink-1607
        hideif-488082 desktop language branch hidden
  section-1574: visible Header
    row-1575: mobile and tablet header
    row-1608: desktop header
      column-1611 > homelink-9864 > image-1612
      column-1613
        hideif-9914 > menu-1614 hidden on desktop
        cartitemcount-1615
        textblock-4810909 static desktop navigation
  section-4806347: hidden legacy custom strip
  sidepanel-1583: Mobile Side Menu
  sidepanel-6460: Cart Snapshot
  modal-478833: Language Picker
```

Preserve row-1575 and the three operational siblings while changing the
desktop Rows. Retain Search Input, My Account Link, dynamic Menu bindings, and
Cart Item Count. The current static desktop navigation matches copy and
geometry, but it does not replace or verify dynamic menu behavior.

## Preserve the shared footer

Build the replacement design inside `container-main-footer`. Keep or
deliberately replace this observed grammar:

```text
container-main-footer
  optional custom Section
  Footer Section
    Webchat
    four-column Row
      Column 1 > HideIf > Headline, Footer Menu
      Column 2 > HideIf > Headline, Help Menu
      Column 3 > HideIf > Headline, Account Menu
      Column 4 > Headline, Panel > Site Attributes
    three-column Row
      legal and policy links
      Image
      Social Links
    two-column Row
      Copyright
      Payment Methods, Purchase Bubble
```

Preserve the observed menu bindings `Footer`, `help`, and `account`. Preserve
Webchat, Site Attribute, Social Links, Copyright, Payment Methods, and Purchase
Bubble as dynamic widgets when the replacement requires their behavior.

Add the replacement Section before hiding or removing the existing Footer
Section. Verify every required route and dynamic action first.

## Build standard and simple collections in their existing containers

Use the standard catalog grammar for pages rendered by
`template_catalog.vm`:

```text
container-subgroup-list
  Section
    Row
      Column
        PageList
          PageLink
            PageTitle
              PageImage
        PageSelect

container-group_facets
  Section
    Row
      Column
        PageTitle
        Tabs
          Items Tab
            Row
              facets Column > ItemListFacetsForm
              results Column
                sort Row > Sort Order, Per Page, Pagination
                item Row > ItemList > ItemLink > product leaves
                bottom Pagination Row
                PayPal Pay Later Row
          Filters Tab
            ItemListFacetsForm
```

Keep the responsive Filters tab separate from the Items tab. Preserve ItemList,
ItemLink, Item Wishlist, Item Sale, Item Out Of Stock, Item Image, Item Title,
Item Review Summary, and Item Price as dynamic components.

The later saved collection probe verified this parent-aware insertion:

~~~text
Tabs tabs-3327
  existing Items Tab tab-3328
  existing Filters Tab tab-3332
  temporary editorial Tab tab-4810913
    Text Block textblock-4810914
~~~

Tabs forced a Tab child, and the new Tab accepted a direct Text Block. Append
editorial Tabs without moving the existing data-bound descendants. This probe
is still present in the last source-proven saved state. Its delete, save, and
rollback were not confirmed. Treat editor dirty state as Unknown and inspect
the existing editor before resuming.

Use the simple catalog grammar only for pages rendered by
`template_catalog_simple.vm`:

```text
container-group_item_list
  Section
    title Row > PageTitle
    items Row
      ItemList
        ItemLink
          Item Wishlist > Headline > Item Sale > Item Out Of Stock > Item Image
          Item Title
          Item Review Summary
          Item Price
    PayPal Pay Later Row
```

Do not assume which catalog template a group uses. Identify the public
container root or server-log template before editing.

## Place item-page content inside the rendered item branch

Preserve `container-item-display > Section > ItemForm`. Keep the error modal as
a separate container child.

Use direct ItemForm Rows for publicly rendered editorial and offer content:

```text
ItemForm
  custom hero Row
    media and editorial Column
    offer Column
      three one-time offer Panels
      subscription Panel
        static presentation leaves
        native subscription Row
      native purchase Row
  native product Row
    product-media Column
    title, review, price, description, option, and stock Column
  description and review Tabs Row
  related-items Row
  Item Structured Data
  trust and editorial Row
```

Move the complete native subscription and purchase Rows. Preserve their
Columns, Labels, Item Auto Order Schedule, Item Quantity, native Add to Cart
Button, Notify Me HideIf, and modal descendants. Do not move only the visible
leaf control.

Treat Notify Me and out-of-stock runtime behavior as `Unknown` until exercised
in the corresponding item state.

The later desktop reference-matching pass used a 5/7 hero Row. Its first
Column retained product media and a four-item benefits Bullet List. Its second
Column used three sibling one-time offer Panels and a mixed subscription
Panel. That Panel owns static presentation leaves and native subscription Row
row-387942. Native purchase Row row-4717 is a later sibling in the offer
Column. Preserve both native control branches; static presentation does not
implement their behavior.

## Avoid the named-container condition trap

Inspect every new named container's compiled condition before relying on its
editor canvas.

The observed `clinical_product_editorial` container is explicitly parsed by
the item template, but its current compiled content is wrapped in an empty
Checkout Condition equivalent to `isCondition("null", "")`. This is the most
likely reason the container appeared in edit mode but did not render publicly.
Confirm the condition at the public route before calling the cause verified.

Treat automatic insertion of that container parse as a strong inference, not
controlled proof. The current item template is 52 bytes larger than the
earlier File Manager observation, and the added parse line is exactly 52
bytes. No artifact-level template before-and-after capture proved the action.

Prefer the existing rendered container. If a new named container is required,
verify all three conditions:

1. The intended page template explicitly parses its VM.
2. Its root hierarchy is not suppressed by an invalid or false condition.
3. The public route contains the expected container and marker after save.

## Keep these questions open

- Determine which StoreFront setting selects standard, simple, or wholesale
  catalog templates.
- Verify shared header and footer rendering on every required public route.
- Confirm the exact public effect of the empty named-container Checkout
  Condition.
- Identify the runtime trigger that opens the Cart Snapshot Sidepanel.
- Test checkout-only header behavior after a full replacement.
- Test wholesale rendering for anonymous and wholesale-authenticated states.
- Test moved Notify Me and out-of-stock branches in their real runtime states.

## Run experiments in this order

1. Add unique markers inside the existing header and footer containers. Save,
   capture both pairs, verify all required public routes, then roll back.
2. Rebuild desktop and mobile header Rows while preserving sidepanels, modal,
   dynamic widgets, and target bindings. Test every action.
3. Build the replacement footer above the existing Footer Section. Move dynamic
   widgets, test links and actions, then hide the old Section.
4. Identify standard, simple, and wholesale catalog routes from public
   container roots and server logs before modifying collection layouts.
5. Test PageList navigation, facets, sorting, per-page selection, pagination,
   responsive Filters, and product-card bindings.
6. Move one marker outside the empty custom-container Checkout Condition. Save,
   capture the custom pair and item template, and verify the public DOM.
7. Rehearse a complete reference reconstruction. Require matching editor
   hierarchy, CJSON parentage, compiled VM, template parse, public DOM,
   functional controls, and viewport-matched screenshots.

Classify each result as `Verified`, `Contradicted`, or `Unknown`. Do not treat
editor visibility, a completed save callback, a VM parse, or a screenshot alone
as public-render proof.
