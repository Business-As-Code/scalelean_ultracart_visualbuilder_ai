# Clinical Effects shared-header reconstruction

Date: 2026-07-31.

## Scope

This was an owner-approved desktop reconstruction inside the reference shared
`container-header`. The reference was the owner-controlled Clinical Effects
site. Acceptance used a 1440 by 1100 viewport. The logged-in public route's
36-pixel UltraCart admin bar was excluded from storefront vertical
comparisons. The mobile header was preserved but was not a visual acceptance
target.

## Saved hierarchy

```text
container-header
  section-1573
    row-1603: 1200-pixel 3/9 utility Row
      column-1604
        sociallinks-3660: hidden
        textblock-4810908: phone presentation
      column-1605
        wishlistsummary-8732: hidden
        panel-478893
          searchinput-1606: native
          myaccountlink-1607: native
          hideif-488082: desktop language branch hidden
  section-1574
    row-1575: mobile and tablet branch preserved
    row-1608: 1200-pixel 3/9 desktop Row
      column-1611 > homelink-9864 > image-1612
      column-1613
        hideif-9914 > menu-1614: hidden on desktop
        cartitemcount-1615: native
        textblock-4810909: desktop navigation presentation
  section-4806347: hidden legacy custom strip
  sidepanel-1583: Mobile Side Menu preserved
  sidepanel-6460: Cart Snapshot preserved
  modal-478833: Language Picker preserved
```

The desktop navigation is a static Text Block because the Visual Builder Menu
widget did not expose menu-record authoring. The original bound Menu remains
hidden in its desktop branch. The separate mobile and sidepanel branches were
preserved. This is a deliberate visual workaround, not proof that desktop
navigation remains data-bound or that mobile behavior passed.

## Verified desktop geometry

| Region | Public result | Reference residual |
| --- | --- | --- |
| Utility Section | 56 pixels high | exact after admin-bar adjustment |
| Utility Row | x 120, width 1200, height 36 | exact |
| Search Input | x 435, width 580, height 36 | exact |
| Main Section | 84.296875 pixels high | exact |
| Main Row | x 120, width 1200 | exact |
| Logo image | x 155, width 168.21875, height 32 | exact |
| Desktop navigation | Roboto 18, weight 400, 1-pixel letter spacing | measured match |

The utility and main Sections also matched the two recorded reference
box-shadows. The phone, account, cart icon, cart count, logo, and navigation
positions were within approximately 0.04 pixels of the reference after the
admin-bar adjustment.

## Dynamic preservation

| Control | Result |
| --- | --- |
| Search Input | Existing native widget retained and rendered |
| My Account Link | Existing native widget retained and rendered |
| Cart Item Count | Existing native widget retained and rendered |
| Mobile Menu | Existing bound widget and Sidepanel branch retained |
| Cart Snapshot | Existing Sidepanel, close action, contents, and Checkout action retained structurally |
| Language Picker | Existing Modal and mobile trigger retained structurally |

Changing `image-1612` also updated the existing StoreFront logo attribute
through its current binding. Any inherited mobile-logo effect remains
untested. No account, cart, language, search-result, or checkout action was
executed in this visual pass.

## Shared-route and source evidence

The saved header rendered with the same measured structure on Home, Shop, and
the test product route. This proves shared route composition for those three
routes. It does not prove every control state.

A fresh bounded FTPS capture completed at 2026-07-31 15:29 UTC with no
candidate failures. The source hashes were:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `header.cjson` | 80024 | `136633c30d3a0637354e49c95132517a6e43970bfa8240be90b902f8a89b3a5d` |
| `header.vm` | 74700 | `55090a031a40e6245fcddf12d03325e20aa9dfaddd55689cc6cecef4857e3ea0` |

CJSON confirmed the two new Text Blocks, hidden legacy widgets, desktop Row
settings, logo configuration, and scoped styles. Generated Velocity contained
the compiled utility and navigation styles, account presentation, logo
rendering, and static desktop links.

## Limits

- Mobile and tablet visual acceptance remain `Unknown`.
- Search, account-state, cart-sidepanel, language-modal, and checkout actions
  require separate tests.
- Static desktop navigation must be maintained separately from UltraCart menu
  records.
- This pass proves the saved state, not baseline-to-save-to-rollback causality.
