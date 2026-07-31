# Shared public-route composition baseline

Date: 2026-07-31.

## Scope

This was a read-only rendered-DOM comparison of the reference public Home, Shop,
and test product routes. It compared only root Visual Builder container
identity and aggregate dynamic widget presence. It made no editor change and
tested no control action.

## Verified root composition

| Route | Root Visual Builder containers |
| --- | ---: |
| Home | 7 |
| Shop collection | 6 |
| Test product | 5 |

Exactly three root containers are present on all three routes:

- `container-header`.
- `container-mailing-list-signup`.
- `container-main-footer`.

**Verified:** these three named containers participate in the current public
composition of Home, Shop collection, and the test product.

This does not prove that every descendant, state, or action is identical across
the routes. It also does not prove that an arbitrary new named container will
join those templates.

## Verified pre-probe Shop dynamic baseline

Before the later Tab probe, the public Shop route retained these data-bound
widget families:

| Dynamic family | Rendered instances |
| --- | ---: |
| Item List | 1 |
| Item List Facets | 2 |
| Item List Facets Form | 2 |
| Item List Sort Order | 1 |
| Item List Per Page | 1 |
| Item List Pagination | 2 |
| Page List | 1 |
| Page Select | 1 |
| Item Link | 9 |
| Item Image | 9 |
| Item Title | 9 |
| Item Price | 9 |

That baseline also rendered five forms, three selects, 59 links, and 16 loaded
images at the observed state.

The later saved Tab probe rechecked the main collection families after
selecting Items. See the pending-rollback collection record. It did not repeat
the full link and loaded-image count.

## Reusable rule

Before a collection mutation, capture this dynamic baseline. After save and
after rollback, require the expected editorial branch plus the continued
presence and active behavior of facets, sorting, per-page selection,
pagination, page navigation, and item links. A visually correct static grid is
not a valid replacement for the data-bound collection hierarchy.

For shared-container work, verify the same named root on at least Home, one
product route, and one collection route. Then test menu, search, cart sidepanel,
language modal, mailing-list form, and footer links separately. Root presence
alone is not behavior proof.

A later owner-approved shared-header reconstruction retained
`container-header` on all three routes and matched the Clinical Effects
desktop header geometry. See
[Clinical Effects shared-header reconstruction](2026-07-31-clinical-effects-shared-header.md).
The route readback proves shared rendering. Dynamic control actions remain
separate verifiers.
