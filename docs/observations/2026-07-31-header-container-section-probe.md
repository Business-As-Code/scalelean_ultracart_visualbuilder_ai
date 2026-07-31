# Header container Section probe

Date: 2026-07-31.

## Scope

One owner-authorized hierarchy experiment in the reference test StoreFront
Home page Visual Builder. The scope was limited to one new direct Section
inside `container-header`. No child was added to that Section. No file-transfer
or source-artifact action occurred.

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
5. The editor showed an empty Section with an `ADD NEW ELEMENT` affordance.
   That control was not used. Its allowed child palette is still `Unknown`.
6. Visible save showed both the saving state and `Containers saved.`. A reload
   of the editor retained the Section as the seventh direct Header child.

## DOM and console observations

- The editor uses a direct-child list for this container. The hierarchy DOM is
  useful evidence for parentage and order, but is not a supported API.
- The inspected page console had no application warnings or errors during the
  add, save, or reload sequence. Browser-extension warnings were excluded.
- The Section's precise generated identifier, raw page source, browser state,
  and account information remain private.

## Proof boundary

This proves editor hierarchy persistence for one Section insertion on the
observed Visual Builder version. It does not prove a universal container-child
schema, CJSON-to-VM causality, non-editor public rendering, responsive layout,
or any allowed Section child type.

## Current decision

The saved empty Section remains on the reference Header. It visibly adds a
blank editor-region band. Retain or roll it back only under the next explicit
owner instruction.
