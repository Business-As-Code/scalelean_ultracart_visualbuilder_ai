# UltraCart Visual Builder system model

Date: 2026-07-31.

## Scope and confidence

This is the current system model for the reference Elements-theme Visual Builder.
It combines editor observations, saved CJSON, generated Velocity, page-template
composition, and public-route readback. It is not a universal UltraCart
specification.

The observed editor loaded Visual Builder compiler 0.1.0 with 532 widget
implementations. Treat widget types, settings, compiler output, runtime names,
and internal editor objects as version-specific until the incoming UltraCart
files establish a wider contract.

Classify each claim as Verified, Hypothesis, Contradicted, or Unknown. An
editor canvas, CJSON file, generated VM, template parse, and public render are
independent evidence. Agreement on one surface does not prove another.

## End-to-end model

~~~text
Visual Builder editor
  loaded hierarchy: containers
  dirty container keys: changedContainers
  dirty-state function: unsavedWidgets()
        |
        | coherent edit and visible Save
        v
CJSON for one named container
  id, type, parentWidgetId, ordered childWidgets, configuration
        |
        | Elements Visual Builder compiler
        v
Generated container VM
  widget markup, Velocity logic, data bindings,
  responsive classes, scoped CSS, multilingual strings
        |
        | explicit ordered #parse from a page template
        v
Runtime context and compiled conditions
        |
        v
Public DOM, geometry, assets, and interactions
~~~

The names containers, changedContainers, unsavedWidgets(), and
saveContainers(callback) are observed front-end names. They are not supported
APIs.

Generated VM files warn against direct edits, refer to their CJSON source
hash, and can be regenerated from the matching CJSON. A controlled save proved
that one named container's CJSON and VM can change together. A specific
CJSON-to-VM causal claim still requires agreement across baseline, saved, and
rollback states. The current header and item results prove saved state. They do
not prove complete rollback causality.

A compiled VM does not render automatically. The selected page template must
parse it, and its runtime conditions must permit output.

## Hierarchy model

The selected parent controls the available child palette. Section, Row, and
Column are a common editorial grammar, not a universal creation chain.

Use these rules:

1. Reopen the hierarchy after every insertion. Add Child is a request, not
   proof of parentage.
2. Treat child order as semantic. Verify the complete direct-child order in
   saved CJSON when order matters.
3. Locate a node by route, container, ancestor path, role, and type. Treat
   widget IDs as StoreFront-state identifiers, not portable schema IDs.
4. Dynamic widgets can render many instances from one authorable branch.
   ItemList, PageList, Menu, and similar widgets are not one node per rendered
   record.
5. Preserve native dynamic branches. Static Text Blocks, Panels, and Images
   can reproduce presentation. They do not recreate menu, catalog, pricing,
   subscription, cart, or form behavior.

Observed forced-child pairs include:

| Parent | Forced child |
| --- | --- |
| Row | Column |
| Accordion | Accordion Item |
| Tabs | Tab |
| Absolute Wall | Absolute Block |
| Masonry Wall | Masonry Block |
| Mega Menu | Mega Menu Item |

Keep three visibility mechanisms separate:

1. Responsive showOn.
2. Runtime HideIf, ShowIf, or If.
3. The hierarchy Hidden control. It retained a widget but rendered it with
   display: none in the observed saved state.

## Compiler behavior

Observed content keys are:

- Headline: html.
- Text Block: richText.
- Bullet List: html.

Multilingual copy does not need to appear as plaintext in generated VM. The
observed compiler emitted complete UTF-8 values as uppercase hex in the fourth
argument of this static call:

~~~text
$i18n.writeMlString("widget", "key", true|false, "UPPERCASE_HEX")
~~~

Use three separate checks:

1. Verify exact authored copy in CJSON.
2. Verify the complete encoded VM value with the multilingual-literal
   assertion. Do not search for a plaintext fragment.
3. Verify exact visible copy in the public DOM.

Generated VM also provides structural evidence through widget types,
responsive classes, parse targets, dynamic loops and contexts, native control
signals, and compiled styles.

The observed scopedStyles setting is a breakpoint-keyed object. Verified keys
include all and medium-up. Bare declarations target the owning widget.
Descendant selectors are prefixed with the widget scope. Repeating the owning
generated ID can produce a double-prefixed selector. Treat this as
compiler-version-specific behavior.

## Template composition

The complete parse matrix is in the shared-composition reference. The main
observed routes are:

~~~text
Home
  header -> home-slider -> paypal-banner -> home-subgroup-list
  -> featured-items -> mailing-list-signup -> main-footer

Standard catalog
  header -> paypal-banner -> subgroup-list -> group_facets
  -> mailing-list-signup -> main-footer

Simple catalog
  header -> paypal-banner -> conditional group_item_list
  -> mailing-list-signup -> main-footer

Item
  header -> clinical_product_editorial -> item-display
  -> mailing-list-signup -> main-footer
~~~

Creating and saving a named container does not automatically compose it into a
route. The template must parse its VM, its compiled conditions must permit
output, and the public route must contain the expected marker. The
clinical_product_editorial experiment showed that editor visibility alone is
insufficient.

## Shared and route-specific composition

The observed Home route had seven root Visual Builder containers. Shop had
six. The test product had five. container-header,
container-mailing-list-signup, and container-main-footer rendered on all three.

### Shared header

~~~text
container-header
  visible utility and header Sections
  preserved mobile and tablet Row
  preserved Mobile Side Menu
  preserved Cart Snapshot Sidepanel
  preserved Language Picker Modal
~~~

The current desktop header retains Search Input, My Account Link, and Cart
Item Count. Desktop navigation is a static Text Block workaround. The
original bound Menu remains hidden in its desktop branch, while the separate
mobile branch retains its own bound menu. Search, account, cart, language, and
checkout actions remain untested.

### Item page

~~~text
container-item-display
  Error Message Modal
  Section
    ItemForm
      editorial and offer Rows
      native product branches
      native subscription and purchase controls
      structured data and other dynamic branches
~~~

The saved item uses a 5/7 hero, three static one-time offer Panels, one mixed
subscription Panel, a four-item benefits list, and preserved native controls.
The mixed Panel owns the native subscription Row. The native purchase Row is a
later sibling in the offer Column. Purchase, Notify Me, and out-of-stock
behavior remain untested.

### Standard collection

~~~text
container-group_facets
  Section
    Row
      Column
        PageTitle
        Tabs
          Items Tab
            dynamic facets, sort, pagination, and ItemList
          Filters Tab
            dynamic facet form
          optional editorial Tab
            editorial descendants
~~~

Tabs forces a Tab. The saved probe proves that a Tab can accept a direct Text
Block. Append editorial tabs without moving the Items or Filters dynamic
descendants.

## Save and session model

Use this sequence:

1. Assign one browser writer.
2. Capture the saved baseline and exact browser checkpoint.
3. Make one coherent hierarchy batch.
4. Reopen the hierarchy and verify parentage and order.
5. Store the unsaved checkpoint before save, navigation, or authentication
   recovery.
6. Use the visible Save control.
7. Require Containers saved. and a Save control with no unsaved state.
8. Reload the editor hierarchy.
9. Capture fresh CJSON and VM.
10. Reload and verify the public route.
11. Roll back the exact test and repeat the evidence cycle.

A completed saveContainers(callback) proves only request completion. If
authentication expires, keep the mutable editor tab open and authenticate in a
separate tab. Do not reload an editor that contains unprotected unsaved work.
After an ambiguous save, inspect fresh CJSON and VM before another retry.

If a rollback action times out before confirmation and save, the last
source-proven saved state remains authoritative. Treat editor dirty state as
Unknown. Stop. On resumption, inspect the existing editor before reloading.

Rollback should restore semantic hierarchy, settings, generated behavior, and
public output. Byte equality is stronger evidence, but UltraCart can normalize
an otherwise equivalent CJSON document during save.

## Evidence and acceptance

| Surface | What it proves |
| --- | --- |
| Editor | Available controls, current hierarchy, settings, and dirty state |
| CJSON | Persisted types, parentage, order, content, assets, responsive values, and visibility |
| VM and template | Generated structure, conditions, bindings, styles, encoded copy, and route composition |
| Public route | Actual DOM, visible copy, loaded assets, geometry, and authorized interactions |

The following proof boundaries apply:

- Editor canvas visibility is not public-render proof.
- A VM widget signal is not exact-copy proof.
- A screenshot is not hierarchy or interaction proof.
- Root-container presence is not dynamic-action proof.
- A path-free run manifest binds roles, sizes, hashes, and viewport. It does
  not validate artifact meaning.
- Keep raw files, screenshots, sessions, private URLs, and source bytes
  outside Git.

## Exact paused reference state

Storefront work paused on 2026-07-31 at the owner's request. No later browser,
FTP, or UltraCart action is part of this consolidation.

The last source-proven Shop collection state contains the temporary probe:

| Field | Proven saved value |
| --- | --- |
| Container | container-group_facets |
| Tabs parent | tabs-3327 |
| Baseline order | tab-3328, tab-3332 |
| Last saved order | tab-3328, tab-3332, tab-4810913 |
| Added Tab | tab-4810913 |
| Tab title | UVB Probe |
| Tab visibility | desktop |
| Direct child | textblock-4810914 |
| Marker | UVB-COLLECTION-TAB-PROBE-001 |

The saved CJSON semantic delta contained one child-order change, two excess
nodes, and one editModeSelectedTab configuration change. It contained no
missing nodes, parent changes, or type changes. The saved VM retained the
existing collection widget families and added one Tab and one Text Block. The
public Tab label and marker rendered. Returning to Items retained nine visible
item links, two facet widgets, sort, per-page selection, two paginations,
PageList, five forms, and three selects.

| Artifact | Baseline SHA-256 | Saved SHA-256 |
| --- | --- | --- |
| group_facets.cjson | ec0ff94108af91ed5b20279ba3139b68d333ae7033be5dc04d05a88542954869 | 23be065bdd3262d5e3a1d44b761988893fe032aa02742abe8bb628c43cacd625 |
| group_facets.vm | 4b490221d745975c99a7d32ae7dab4e3ce351b0b5c3926d88414a407a0f07cac | 3b64fdfb93104a7f151b57ce942252c7353155fd2628f0b0ce0fc87a3c5e89fb |

The path-free run-manifest SHA-256 is
9864a8fef8a2ae78fcf60fee4edd9323c207dcf99f2056fdfcc5a700f83eff69.

A delete action was initiated for tab-4810913, but the browser operation timed
out before readback. There was no confirmed deletion, no save, and no rollback
capture. The last source-proven persisted state still contains the probe Tab.
The current editor dirty state is Unknown. Rollback is incomplete.

## Known unknowns

- Exact unsaved editor state after the timed-out delete.
- Collection rollback equivalence.
- The StoreFront setting that selects standard, simple, or wholesale catalog
  templates.
- Mobile and tablet acceptance for the rebuilt header and product.
- Search, account, cart-sidepanel, language-modal, checkout, mailing-list, and
  footer actions.
- Product purchase, Notify Me, and out-of-stock behavior.
- Complete footer reconstruction.
- Whether external asset URLs are copied into UltraCart or only referenced.
- Public behavior and compiler output for most advanced elements.
- The exact cause of the condition that suppressed clinical_product_editorial.
- Whether reference compiler 0.1.0 behavior applies to other themes or versions.

## Incoming UltraCart file intake

Do not resume StoreFront editing only because files arrive.

1. Record provenance, delivery date, version applicability, confidentiality,
   filename, byte count, and SHA-256 before analysis.
2. Keep originals in private storage. Commit only redacted facts, aggregate
   catalogs, schemas, and synthetic fixtures.
3. Classify files as widget metadata, hierarchy and serialization, placement
   rules, save and session protocol, compiler transformations, templates,
   runtime bindings, responsive styling, or examples and tests.
4. Compare authoritative definitions with the reference evidence. Mark each result
   confirmed, contradicted, version-dependent, or still unknown.
5. Extract a versioned widget catalog, parent-child constraints, forced-child
   pairs, configuration schema, compiler rules, and template graph.
6. Add synthetic offline tests for every parser or compiler rule.
7. Update the operating skill only with repeatable facts.
8. Before later site work, inspect the existing Shop editor state and complete
   or deliberately supersede the pending collection rollback under explicit
   authorization.

## Canonical supporting records

- Current and historical state: observations/README.md.
- Evidence definitions: evidence-model.md.
- Parent-aware placement: the skill reference.
- Core settings and compiler-version observations: the skill reference.
- Shared composition and reference hierarchy: the skill reference.
- Exact dated IDs, hashes, geometry, and limits: the observation records.
- Aggregate widget catalog scope: reference/README.md. The current JSON catalog
  is a pre-probe snapshot, not the latest persisted collection state.
