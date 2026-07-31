# Parent-aware placement reference

Use this reference to choose the correct parent before opening the element
palette. It records the reference editor catalog loaded with compiler `0.1.0`.
Treat it as versioned evidence. The current visible palette is authoritative.

## Contents

- [Placement algorithm](#placement-algorithm)
- [Forced child pairs](#forced-child-pairs)
- [Constrained parents](#constrained-parents)
- [Container palette](#container-palette)
- [Section palette](#section-palette)
- [Broad content parents](#broad-content-parents)
- [Context-dependent containers](#context-dependent-containers)
- [Button child palette](#button-child-palette)

## Placement algorithm

1. Find the intended existing parent by route, container, ancestor path, type,
   and visible title. Do not start from a remembered widget ID.
2. Inspect the parent's implementation only as a prediction.
3. Open that parent's visible Add Child palette.
4. Confirm the exact child type in the palette or forced-child flow.
5. Insert the child.
6. Reopen hierarchy and verify parentage, indentation, and sibling order.
7. Verify saved CJSON before treating the relationship as persistent.

## Forced child pairs

The observed editor bypassed a general palette for these parents:

| Parent | Forced child |
| --- | --- |
| Row | Column |
| Accordion | Accordion Item |
| Tabs | Tab |
| Absolute Wall | Absolute Block |
| Masonry Wall | Masonry Block |
| Mega Menu | Mega Menu Item |

For a Row, select the Column width requested by the editor. Do not interpret an
empty general child palette as proof that the Row cannot receive a Column.

## Constrained parents

| Parent | Observed child constraint |
| --- | --- |
| Button | Page Attribute, Page Title, Item Attribute, credit-card logos, Text, Cart Item Count, Icon, Text Block, Row, Item Price, or pending subtotal |
| Checkout Accordion | Checkout Condition or Checkout Accordion Item |
| Experiment | Experiment Variation |
| Item Offer | Offer axis, offer labels, common layout/content leaves, or Item Offer Conditional |
| Item Variations | Text Block, Text, HTML, CSS, or Velocity |
| Slider | Slide |
| Spotlight | Spotlight Item |
| Table | Table Head, Table Body, Table Row, or Page Attribute |
| Table Head or Body | Table Row |
| Table Row | Table Column |
| Upsell Modal | Row or Panel |

Do not add advanced CSS, Script, or Velocity merely because a palette exposes
them. Use normal Visual Builder hierarchy and settings unless the approved
design cannot be represented safely and the work order authorizes custom code.

## Container palette

The observed top-level Container palette exposed 23 types:

```text
Body
Script
Velocity
Checkout Location
Purchase Bubble
Checkout Condition
Item Container
Page Container
Section
Hide If
If
Show If
My Account Address Book Entry Modal
My Account Credit Card Entry Modal
Skiplink
Alert Modal
Confirm Modal
Item Modal
Modal
Order Modal
Sidepanel
Upsell Modal
Experiment
```

Use Section for normal visible page content. Keep modals and sidepanels as
top-level siblings. A top-level container still requires explicit page-template
composition before it can render publicly.

## Section palette

The observed Section palette exposed 48 structural or page-level types:

```text
Script, Velocity
Blog Post List, Blog Post List Filter
Checkout Form, Checkout Location
Divider, Site Attribute, Webchat
Absolute Wall, Checkout Condition, Flex, Item Container, Masonry Wall,
Page Container, Panel, Row, Section, Table
Button
Item, Item Form
Item List, Item List Form
Item Review Input Form
Accordion, Slider
Hide If, If, Show If
My Account Condition, My Account Loyalty Condition, My Account Order List
Mega Menu, Skiplink
Alert Modal, Confirm Modal, Item Modal, Modal, Order Modal, Sidepanel,
Upsell Modal
HTML
Page, Page Attribute, Page List
Store Locator Form
Experiment
```

Use `Section > Row > Column` as the normal editorial grammar. Add a specialized
form, list, page, item, slider, accordion, menu, or off-page element only when
the design and route require that dynamic behavior.

## Broad content parents

The observed Column and Panel palettes each exposed 231 types. The Aligner
palette exposed 338. ItemForm, HideIf, CheckoutCondition, Tab, ItemLink,
Modal, and Sidepanel also exposed broad context-sensitive palettes.

Do not treat a high palette count as permission to mix unrelated checkout,
email, account, item, and collection contexts. Use the route's existing dynamic
grammar. Prefer these common children for ordinary reconstruction:

- Row or Panel for local structure;
- Headline, Text Block, Bullet List, Image, Divider, Button, Link, or Video for
  editorial content;
- Accordion, Tabs, Slider, or Table for a matching interaction pattern;
- HideIf or ShowIf only for a required runtime condition;
- existing Item, Page, List, Menu, Cart, Account, Language, or Form widgets for
  dynamic behavior.

## Context-dependent containers

The observed implementation decided child support dynamically for Affiliate
Attribute, Headline, Item Attribute, Item Out Of Stock, Item Sale, Item
Wishlist, OpenAI Headline, Page Attribute, Page Title, Site Attribute, and
Theme Attribute.

These types can contain a wrapper or overlay in one context and behave as a
leaf in another. Verify their visible Add Child control and saved CJSON. Do not
generalize from one saved product-card overlay.

## Button child palette

The observed Button palette exposed only ten child types:

```text
Cart Item Count
Checkout Credit Card Logos
Icon
Text
Text Block
Row
Item Attribute
Item Price
Page Attribute
Page Title
```

Use Button configuration for its action, show/hide targets, URL, accessibility,
and style. Preserve existing native Button actions instead of recreating them
from visible text.
