# Header container Section probe

Date: 2026-07-31.

## Scope

One owner-authorized hierarchy experiment in the reference test StoreFront
Home page Visual Builder. The scope was limited to one new direct Section
inside `container-header`, then one conventional structural branch inside that
Section. No file-transfer or source-artifact action occurred.

## Verified editor behavior

1. `container-header` rendered its direct hierarchy as a nested
   `ul.child-widgets` list. Each direct child exposed a StoreFront-local
   `data-widget-id`.
2. The Header container's selected Grid palette exposed three direct choices:
   Checkout Condition, Page Container, and Section.
3. Selecting Section appended one new Section after the existing Section,
   Sidepanel, and Modal direct children.
4. The new node was a direct child of `container-header`, not a descendant of
   an existing Section, Header, Mobile Side Menu, Cart Snapshot Sidepanel, or
   Language Picker Modal.
5. The Section's parent-aware palette exposed 17 visible categories. Its Grid
   category exposed: Absolute Wall, Checkout Condition, Flex, Masonry Wall,
   Page Container, Panel, Row, Section, and Table.
6. Selecting Row opened a width picker. Selecting the full-width layout
   created a Row and its required one full-width Column in one action.
7. The Row's Column then exposed a broader parent-aware palette. Its Content
   category exposed 21 choices, including Headline, Image, Text, and Text
   Block.
8. The probe added a Headline, Text Block, and Image beneath that Column. The
   saved parent chain is `Header container > Section > Row > Column > leaves`.
   The Image was added with its default editor state only. No asset was
   selected or uploaded.
9. The Section also accepted Panel as a direct sibling of the Row. The Panel
   exposed a broader palette with 32 visible categories and accepted Headline
   as a direct child.
10. The hierarchy-panel node action menu provided the reliable placement flow:
    select `add`, choose `Add Child`, then use the resulting parent-aware
    palette. Canvas hover controls did not reliably open the palette after a
    saved reload.
11. Visible save showed both the saving state and `Containers saved.`. A reload
    retained the complete branch and every verified parent relationship.

## DOM and console observations

- The editor uses a direct-child list for this container. The hierarchy DOM is
  useful evidence for parentage and order, but is not a supported API.
- The inspected page console had no application warnings or errors during the
  add, save, or reload sequence. Browser-extension warnings were excluded.
- The Section's precise generated identifier, raw page source, browser state,
  and account information remain private.

## Proof boundary

This proves editor hierarchy persistence for two normal structural branches on
the observed Visual Builder version. It demonstrates the mapping method: the
selected parent determines its visible direct-child palette. It does not prove
a universal container-child schema, CJSON-to-VM causality, non-editor public
rendering, responsive layout, or behavior of the other types exposed in either
palette.

## Current decision

The saved Section now contains a default Row, Column, Headline, Text Block,
Image, Panel, and Panel Headline. It visibly adds an editor-region band.
Retain or roll it back only under the next explicit owner instruction.
