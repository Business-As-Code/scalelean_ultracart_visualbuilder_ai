# Source-first Visual Builder learning plan

Date: 2026-07-31.

## Decision

Storefront work is paused while the UltraCart-supplied agent bundle is
ingested and the learning program is rebuilt around it.

The private bundle is the authoritative source for the legal element catalog,
generated configuration schemas, documented placement rules, examples, and
authoring conventions for its stated build. Browser and saved-artifact tests
remain authoritative for the behavior of the currently loaded MELRA editor.
Neither source can silently override the other.

The program's product outcome is now an efficient example-to-UltraCart agent
system, not an encyclopedic set of manual browser observations. See
[Example-to-UltraCart agent system](example-to-site-agent-system.md).

The bundle contains 563 element types. The earlier public registry contains 93
types observed in one MELRA theme snapshot. These numbers describe different
populations and must not be treated as a coverage discrepancy.

## Corrected concepts

- An imported container is a named reusable CJSON and generated VM document
  that a template can compose into one or more routes.
- `container` is the root structural widget inside such a document.
- `body` is a leaf page-level settings widget. It is allowed directly under a
  `container` and has no normal layout children.
- `pagecontainer` establishes server-rendered page context inside supported
  page or group-list structures. Its displayed name is not a reusable
  imported-container selector.
- `itemcontainer` establishes server-rendered item context inside supported
  item-list structures. Its displayed name is not a reusable
  imported-container selector.
- Header, body, and footer are container names or composition roles. They are
  not special hierarchy types.

## Evidence model

Each claim has one status: `Verified`, `Contradicted`, or `Unknown`. Each claim
also names one or more evidence surfaces:

1. UltraCart-supplied source.
2. Current editor DOM and parent-aware palette.
3. Persisted CJSON.
4. Generated Velocity.
5. Template composition.
6. Non-editor rendered route.

`Verified` is always scoped to its evidence surface and source version. A
source placement rule does not prove that the current editor exposes it. A
palette choice does not prove save, compilation, or rendering.

## Work program

### 0. Freeze and intake

- Keep all StoreFront, browser, and FTP actions paused.
- Preserve the supplied bundle unchanged in the private shelf.
- Record its manifest hash, generator metadata, counts, and privacy scan.
- Keep raw source private. No license or publication notice was present in the
  delivered package, so public copying requires an UltraCart decision.

### 1. Build the normalized private source registry

- Parse all 563 legal types and their schemas. Use stable type keys; the 548
  friendly names are not unique.
- Record configuration keys, defaults, enums, control hints, breakpoint
  shapes, conditional visibility, inheritance groups, warnings, and examples.
- Parse documented parents, children, all seven forced-child pairs, context requirements,
  sibling interactions, runtime-managed children, and reference fields.
- Keep authoring-tree edges separate from runtime-projected descendants. Do not
  merge non-reciprocal parent and child lists into one allow-list.
- Preserve source anomalies, including default/type mismatches, unresolved
  condition references, unrecognized setting types, and internal placement
  conflicts. Do not normalize them silently.
- Validate uniqueness, referential integrity, and source hashes.
- Generate only privacy-safe aggregate or independently authored public
  documentation.

### 2. Reconcile the current public model

- Correct Body, Page Container, and Item Container semantics.
- Separate the 563-type supplied catalog from the 93-type MELRA observation
  catalog.
- Compare supplied placement rules with current editor palettes and saved
  examples.
- Create a discrepancy queue. Known initial discrepancies include root
  `container` choices and Modal or Sidepanel child choices.
- Leave every unresolved difference as `Unknown`; do not choose a source by
  preference.

### 3. Rebuild the MELRA Home testbed

Resume this phase only after the source registry and discrepancy queue pass
validation.

- Repair the currently missing imported `body.vm` reference first.
- Compose Home from minimal imported header, one imported layout-lab
  container, and minimal imported footer. Include the leaf Body widget only
  where the source and current editor require it.
- Use the imported layout-lab container for hierarchy experiments. Do not use
  the Body widget as a parent.
- Verify composition through editor hierarchy, persisted CJSON, generated VM,
  template order, and non-editor rendering.

### 4. Verify layout topology in dependency order

- Test structural roots and forced-child pairs first: Container, Section,
  Row/Column, Absolute Wall/Block, Masonry Wall/Block, Accordion/Item,
  Tabs/Tab, Slider/Slide, Table/Head/Body/Row/Column, Panel, Flex, Aligner,
  Modal, and Sidepanel.
- For each type, record allowed parents, allowed children, forced insertion,
  sibling placement, defaults, persistence, responsive behavior, and render
  effect.
- Test only rules that conflict with source, depend on runtime context, or are
  material to skill safety. Use source-backed records for the remaining closed
  catalog.

### 5. Verify settings and special contexts

- Extract every discoverable setting into the registry before manual tests.
- Distinguish sparse `small`/`medium`/`large` responsive values from the seven
  responsive scoped-CSS names.
- Prioritize hierarchy, references, actions, data binding, visibility,
  breakpoints, and compiler-affecting settings.
- Test Page Container and Item Container only in their documented runtime
  contexts. Do not infer record scope from palette presence.
- Treat checkout, account, dynamic-list, payment, and integration elements as
  separate context families.

### 6. Improve the skill and work rate

- Prefer normalized source queries over repeated visual inspection.
- Use targeted widget patches rather than whole-container replacement.
- Record task duration, repeated browser actions, failures, and the smallest
  reliable procedure for each experiment family.
- Add automated checks for unknown types, undocumented setting keys, invalid
  parent-child edges, broken widget references, stale hashes, unsafe public
  artifacts, and evidence without a status or source version.

## Work-order design

The 563 source types must each have a registry record. They do not each need a
manual browser mutation or a separate Linear issue. Linear work orders are
created for bounded verification units:

- source ingestion and validation;
- hierarchy and forced-child clusters;
- settings and breakpoint clusters;
- runtime-context families;
- source/editor discrepancies;
- persistence and public-render experiments;
- skill evaluation and speed improvements.

Existing per-widget issues remain historical planning records. Reconcile them
against the 563-type source registry before creating, closing, or expanding
the issue set.

The primary implementation work orders now align to the source registry,
reference analyzer, hierarchy planner, patch compiler, editor executor,
verifier, benchmark suite, and learning loop.

## Acceptance tests

- The private source registry accounts for all 563 manifest element types and
  validates every parsed schema and reference.
- Public validation distinguishes supplied-source coverage from MELRA
  observation coverage and contains no supplied source bytes.
- Body, Page Container, and Item Container have corrected semantics and
  versioned evidence.
- Every layout primitive has a source record. Every material source/editor
  conflict has a bounded live test or remains explicitly `Unknown`.
- The repaired Home testbed persists and renders without a missing-template
  error before layout experiments resume.
- High-risk settings pass save/reload and rendered-behavior tests in their
  valid contexts.
- Repository validation fails on stale hashes, unsafe artifacts, incomplete
  registries, invalid hierarchy references, or missing evidence status.
- The skill demonstrates a measured reduction in repeated browser work while
  preserving evidence quality.

## Resume gate

Do not resume StoreFront changes until phases 0 through 2 pass, the controlling
work order reflects this plan, and the next mutation has one named writer and
one bounded verifier.
