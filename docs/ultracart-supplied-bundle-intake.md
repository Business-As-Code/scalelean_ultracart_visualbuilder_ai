# UltraCart-supplied bundle intake

Date: 2026-07-31.

## Provenance and boundary

UltraCart supplied an agent authoring bundle directly to the project owner.
Its internal manifest identifies the bundle as `sfvb-cjson-authoring`, generated
on 2026-07-31 by `tools/build-agent-bundle.js`.

The packet is stored unchanged in the private project shelf. A separate
private intake manifest records a SHA-256 digest for every file. The internal
manifest has SHA-256 digest
`923cb7f19536ac732aba65723e4e2b1921f93273cfd11abc046949e4006113c6`.

The packet contains no license, notice, redistribution grant, source commit,
or product release identifier. Public reuse rights are `Unknown`. This public
record therefore contains independently written aggregate findings only. It
does not contain supplied schemas, examples, source paths, warning text, or
documentation excerpts.

## Integrity result

- 1,703 listed files and 13,758,675 listed bytes.
- No missing, unlisted, duplicated, or size-mismatched files.
- All 1,127 JSON documents parse.
- 563 unique catalog keys, 563 schemas, and 563 paired element documents.
- Four structurally validated examples, two recipes, one node schema, and one
  authoring guide.

## Catalog and settings profile

- 563 stable element keys and 548 friendly names. Friendly names are not
  unique identifiers.
- Five elements have no widget group.
- 22,616 setting instances across 1,937 unique keys.
- Two elements have no settings. The median is 44 settings and the maximum is
  114.
- 11,091 settings declare a default and 11,525 do not.
- Mechanical checks found 25 declared-type/default mismatches and 37
  enum/default mismatches. These remain supplier-source anomalies. The model
  must not silently repair them.
- 5,254 setting instances are marked breakpoint-enabled.
- 4,414 setting instances have conditional metadata. There are 375 condition
  references that do not resolve inside the same schema, across 175 schemas.
- Supplier metadata contains 53 warning occurrences in 22 schemas. Separate
  mechanical checks found 189 unrecognized-type setting instances across 60
  schemas. Supplier warnings and derived findings must remain separate.
- 4,267 active settings have supplier-sidecar descriptions. The remaining
  18,349 use generated fallback descriptions and still need semantic review.

Responsive configuration has two different vocabularies. Ordinary responsive
setting values use sparse `small`, `medium`, and `large` keys. Responsive
scoped CSS uses seven named scopes: `all`, `small-only`, `medium-only`,
`medium-up`, `large-only`, `xlarge-up`, and `xxlarge-up`.

## Hierarchy profile

- 172 types allow general child insertion. 391 do not.
- Seven types force a child: Row to Column, Accordion to Accordion Item, Tabs
  to Tab, Absolute Wall to Absolute Block, Masonry Wall to Masonry Block, Mega
  Menu to Mega Menu Item, and Email Row to Email Column.
- Several other types constrain children without forcing automatic insertion,
  including Slider, Spotlight, Experiment, Button Group, and the Table family.
- The documentation contains 571 distinct concrete directional placement
  claims, but only 83 exact reciprocal claims.
- Twenty-eight child-enabled types have an empty documented child list.
- Thirteen types disable general child insertion while documenting
  context-dependent or runtime-managed descendants.
- Absolute Wall has an internal documentation conflict between its declared
  children and prose placement rule.

The normalized model must therefore keep these fields separate:

- allowed-under predicate;
- allowed-child predicate;
- general child-insertion flag;
- forced-child type;
- contextual placement rule;
- authoring-tree descendants;
- runtime-projected descendants;
- source anomaly status.

It is unsafe to create one allow-list by taking the union or intersection of
the supplied parent and child lists.

## CJSON authoring contract

- One CJSON document is one root widget and its ordered descendant tree. It is
  not a page.
- Each node requires `id`, `type`, `config`, and `childWidgets`.
- Node-level unknown properties fail the supplied node schema. `config`
  permits additional keys, so config-schema validation is a separate gate.
- Legal types are closed. An unknown type can pass structural validation and
  render nothing.
- Node schemas do not enforce placement, references, template composition,
  save behavior, VM generation, or public rendering.
- A supplied subtree can retain parent, container, or widget references to
  targets outside that subtree. Full target-page context is required before a
  safe insert, duplicate, move, or replacement.
- IDs and all internal references must be rewritten together. Runtime state,
  offsets, context, and editor-computed measurements must not be authored.
- Targeted widget updates are preferred over subtree replacement. Whole
  container replacement is the last resort.

## Runtime flags

- 462 elements are server-rendered.
- 34 consume item context.
- 27 cause clones.
- Inherited ancestor setting groups can change a descendant's effective
  configuration even when the child has no local value.

These flags do not prove selected-template composition, save persistence, VM
generation, or public behavior. Those remain separate live evidence surfaces.

## Immediate decisions

1. Keep the packet and normalized source model private.
2. Ask UltraCart for written publication and redistribution terms.
3. Use a closed 563-type private registry as the coverage ledger.
4. Use Linear for bounded discrepancy, context, persistence, render, and skill
   evaluation work. Do not create 563 manual browser experiments.
5. Keep StoreFront work paused until the source registry and discrepancy queue
   validate and the Home repair has a bounded work order.
