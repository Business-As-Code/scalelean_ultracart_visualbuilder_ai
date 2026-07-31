---
name: ultracart-visual-builder-lab
description: Build, inspect, rearrange, and verify approved UltraCart StoreFront Visual Builder layouts with hierarchy-first editing, responsive configuration, session-safe saves, private CJSON and Velocity evidence, and public-route readback. Use for controlled reconstruction, element insertion, Cut and Clipboard placement, native purchase-control relocation, FTPS evidence capture, and reversible test changes.
---

# UltraCart Visual Builder Lab

Use this skill only from the `ultracart-visual-builder-lab` repository and its
governing BAC work order.

## Safety gates

1. Read `AGENTS.md` and the controlling Linear issue.
2. Treat browser state, CJSON, VM files, and rendered output as separate
   evidence surfaces.
3. Do not save, publish, import, upload, rename, delete, or write through FTP
   unless a separate work order names the test surface, mutation, rollback,
   and verifier.
4. Keep credentials, browser sessions, raw paths, listings, and source bytes
   outside Git, Linear, and chat. Use `.env` and `UVB_PRIVATE_ARTIFACT_ROOT`.
5. Use explicit FTPS with the approved pinned public key. A pin mismatch is a
   stop condition.

## Design intake gate

Read `references/design-intake-and-acceptance.md` before recreating a supplied
design. Complete its authority, route, viewport, region, hierarchy, native
control, tolerance, verification, and rollback fields before editing. Treat a
missing required field as `Unknown` and fail closed.

Read `references/core-element-settings.md` when selecting layout, content,
logic, item, or collection types. Use its settings as a planning index. Verify
the current parent-aware palette and settings panel before applying them.

Use `../../docs/reference/visual-builder-widget-types.json` for the
privacy-safe aggregate catalog of artifact-backed types, configuration keys,
and observed parent-to-child type edges.

Read `references/parent-aware-placement.md` when choosing a parent or a
specialized layout type. Follow its forced-child and constrained-parent rules.

Read `references/advanced-layout-elements.md` before using Flex, Absolute Wall,
Masonry, Table, Slider, Spotlight, Flyout, Overlay, Mega Menu, Button Group,
Sidepanel, or Modal.

Read `references/composition-and-shared-structures.md` before changing a
header, footer, collection, item page, or named container. Verify the selected
page template's explicit container composition.

Assign one browser editor writer. Other agents may inspect the reference,
public routes, shared structures, artifacts, or verification results, but they
must not edit or save the same page during the writer's save window.

## Read-only workflow

1. Validate local configuration with `python3 scripts/validate_environment.py`.
2. Confirm transport with `python3 scripts/probe_ftps.py`.
3. Capture a root listing with `python3 scripts/capture_ftps_listing.py`.
4. Capture only the approved subtree with
   `python3 scripts/capture_ftps_tree.py --relative-path <subtree> --max-depth 0 --max-directories 1`.
5. Capture only the planned CJSON and VM pair from an explicitly named tree
   manifest. Prefer repeated `--include-remote-path` flags so duplicate
   basenames cannot widen the capture.
6. Record only classifications, counts, hashes, and safe observations in Git.

## Editor capability-mapping workflow

Use only on the owner-approved test StoreFront. This workflow maps what the
editor can visibly build. It does not require a source capture for each action.

1. Open the target page in Visual Builder edit mode and record its top-level
   containers.
2. Expand one representative branch at a time. Record the parent-to-child
   hierarchy and the rendered role of dynamic elements.
3. Open the child palette from the intended parent. Record the allowed
   categories and types. Do not infer that a type is allowed elsewhere.
4. Test safe built-in controls before external data: layout nesting,
   responsive visibility, spacing, background color, and an existing image
   selected from the StoreFront picker.
5. For collection pages, inspect data-bound PageList or facet components. For
   item pages, inspect ItemForm, media, price, stock, and structured-data
   wrappers before changing product data.
6. Inspect Theme Settings, Languages, Library, and Preview as separate
   StoreFront-wide systems. Keep global defaults and language enablement
   read-only unless a work order explicitly scopes the change.
7. Use Preview at mobile, tablet, and desktop before making responsive claims.
   It is a rendering check, not a cross-browser or production acceptance test.
8. Save a coherent, owner-approved test batch. Treat the editor confirmation
   and canvas render as proof of editor behavior only.
9. Capture CJSON/VM deltas only for a named source claim, not as a prerequisite
   for every visual observation.

Use `docs/observations/2026-07-30-visual-builder-capability-map.md` as the
historical verified starting map. Extend it with evidence classes: Verified,
Contradicted, or Unknown.

Read [the system model](../../docs/visual-builder-system-model.md) for the
consolidated architecture and [the observation register](../../docs/observations/README.md)
for current state and open rollback gates.

## Hierarchy-first rules

1. Start with the page container, then expand one branch at a time. Record
   exact visible parent-to-child order.
2. Open the selected parent's palette before choosing an element. The palette
   is parent-aware; a type that appears under Item may be unavailable under
   Section.
3. Treat `Add Child` as an editor request, not proof of a resulting nested
   relationship. Re-open the hierarchy after insertion and inspect indentation
   and sibling order.
4. Treat `HideIf`, `If`, and `ShowIf` as context-dependent. They can be normal
   containing branches or adjacent controls. Verify their actual tree shape
   and rendered scope before using them to control content.
   When relocating native controls, move the smallest containing Row that
   preserves its Columns, Labels, and conditional wrappers. Do not move only
   the visible Button or Quantity leaf if an inactive-state branch is its
   sibling. Responsive Hide is styling, not runtime `HideIf` logic.
   The hierarchy Hidden control is a third mechanism. It retains the widget
   in the hierarchy but suppressed the observed public widget with
   `display: none` after a clean save and reload. Do not classify it as
   responsive `showOn` or runtime `HideIf` logic.
5. For a content page, identify the existing layout grammar first. Many
   templates use Container, Section, Row, Column, then a dynamic or leaf
   element. This is not a universal creation chain. The selected parent alone
   determines which child types are allowed. For collection pages, trace
   PageList and PageLink separately from Group Facets, PageTitle, and Tabs.
   For item pages, trace ItemForm, media, stock, and
   structured-data wrappers. On the observed item template, keep media in the
   first item-form column and title, reviews, pricing, description, and buying
   controls in the second column. Inspect named Rows before moving or changing
   them.
6. Distinguish authorable descendants from rendered instances. A Slider can
   render many slides while appearing as one named node, and a PageList can
   render many records from a small component branch. Do not invent one child
   node per visible card, slide, or record.
7. For shared header work, keep desktop menu branches separate from Mobile Side
   Menu, Cart Snapshot Sidepanel, and Language Picker Modal. They are siblings
   in the shared Header container.
8. Confirm that the current URL, visible canvas, and top-level hierarchy names
   describe the same page before recording a result. A direct route can render
   one page while the hierarchy panel retains earlier state. Start collection
   mapping at the parent collection route before testing a subgroup route.
9. Save only after a coherent hierarchy batch and record the resulting tree.

## Static editorial reconstruction pattern

Use this pattern when the approved task is a visual recreation, rather than a
request to bind an external CMS or product feed.

1. Recreate the composition from `Section > Row > Column` branches. For a
   primary story plus sidebar, an 8/4 Row is an observed usable starting
   layout. Add visual leaves to the Columns only after the Row exists.
2. Use `Image`, `Headline`, and `Text` as static leaves. A visual card made
   from these leaves does not become a live Blog, PageList, or product card.
   State that limitation in the observation record.
3. Treat an external image URL as unverified until it renders after a save in
   the non-editor page. The image field accepts text, but acceptance in the
   settings panel is not rendering proof.
4. Inspect an existing Slider before treating it as a runtime-only display.
   On the observed reference Home page, `Main Slider > Slider` exposes named
   `Slide 1` through `Slide 3`, each with editable `Title` and `Subtitle`
   leaves.
5. Save after a cohesive set of visual edits. Reopen the public test page to
   verify the active slide or other rendered instance. A different active
   slide can make a valid edit appear absent.

## Item-page composition rule

On the reference test item page, the rendered product branch is:

```text
container-item-display
  Error Message Modal
  Section
    ItemForm
      Row-2
        Column 1 > product media
        Column 2 > title, price, description, and purchase controls
```

Keep the ItemForm branch intact. Add editorial content only as a verified
descendant or sibling of the rendered `Section`, then reopen the public item
route after saving. A newly named container can display in edit mode but not
render publicly even when its VM is parsed. Verify the template parse, compiled
condition, and public marker separately.

### Proven item-page insertion pattern

The reference public item route rendered new editorial content when it was added
as direct Rows under the existing `ItemForm`.

```text
ItemForm
  Existing product Rows
  Row
    Column
      Headline
      Text Block
      Bullet List
    Column
      Headline
      Text Block
      Bullet List
  Row
    Column
      Headline
      Text Block
      Bullet List
      Headline
      Text Block
```

Use this sequence:

1. Expand `container-item-display > Section > ItemForm`.
2. Add a `Row` from the Grid palette under `ItemForm`.
3. Select the Row width before expecting the Row to appear. `12` creates one
   full-width Column. Add another Column as a Row child for a two-column
   composition.
4. Add `Headline`, `Text Block`, and `Bullet List` leaves as Column children.
5. Reopen the hierarchy after each insertion and verify the new parent.
6. Save the page and wait until the Save control no longer reports unsaved
   changes.
7. Reload the non-editor item URL and verify every required heading and list
   item.

Do not use a new top-level container for this pattern. The observed reference
item template did not compose that container into the public route.

### Verified row-move workflow

The observed hierarchy did not reorder a Row through pointer dragging. The
editor exposed a different move workflow:

1. Open the source Row flyout and select `Cut`.
2. Verify that the Row disappears from its current parent.
3. Open the target Row placement control and choose `Add Above` or
   `Add Below`.
4. In the element palette, open `Clipboard`.
5. Select the cut Row from the Clipboard card.
6. Reopen the hierarchy and verify the new direct-child order before saving.

Treat the cut as unsaved editor state until the Clipboard insertion and page
save both complete. If the session expires after the cut, reload the editor
and confirm that the last saved hierarchy is intact before repeating the
move. Do not use browser drag behavior as evidence of a supported reorder.
Do not navigate or reload while a widget exists only in Clipboard state.
Verify both the target parent's direct-child order and the source parent's
absence before saving.

On the observed reference item page, this workflow moved the native subscription
Row `row-387942` and purchase Row `row-4717` into an editorial offer Column.
Moving the containing Rows preserved the subscription schedule, quantity,
Add to Cart Button, and the contained Notify Me conditional branch. The
alternate out-of-stock state remains untested.

### Image and responsive-layout rules

Add `Image` as a Column or compatible container child. Configure `imageUrl`,
`imageAltText`, and `imageWidth`. Use `display: inline-block` for intrinsic
badge or package-image width. Reload the public route, scroll lazy-loaded
images into view, and verify non-zero bounds. Confirm the URL and alt text in
CJSON and the generated asset reference in VM.

For the observed equal desktop split, each hero Column used small `12`,
medium `6`, and large `6`. The later Clinical Effects recreation used `5/7`.
Verify responsive values in CJSON and compare public bounding boxes. Do not
claim mobile behavior without testing it.

### Rich-text persistence rule

On the observed editor, changing visible rich text was not sufficient proof
that the widget model changed. The public route retained placeholder text
until the same content was written through the widget's HTML source editor.

For repeatable rich-text changes:

1. Open the target widget settings from the hierarchy.
2. Open its rich-text editor.
3. Switch to HTML source mode.
4. Replace the source through the available source surface and apply the
   editor save action.
5. Return to visual mode and save the widget.
6. Save the page.
7. Reload the public route and check for the exact text.

The same source-editor method is verified for `Headline`, `Text Block`, and
`Bullet List`. Treat a visual-editor-only change as unverified until public
readback succeeds. The observed modal selectors and save event are
version-specific implementation details, not stable API.

### Save, timeout, and session rules

Prefer the visible Save control. The observed editor also exposed its normal
front-end save path as `saveContainers(callback)`. A completed callback proves
only that the request returned. It does not prove artifact persistence, and
it might not clear the client dirty indicator.

For an ordinary successful save in the observed editor, require the visible
`Containers saved.` confirmation and a Save control without an unsaved-change
state. Then reload the editor hierarchy and the public route.

If a save times out or UltraCart reports an expired session, do not reload the
editor while it contains unsaved work. Restore the admin session in a separate
tab, then retry once. After any ambiguous save, inspect fresh CJSON and VM
before another retry. Confirm persistence with artifact capture, editor
reload, hierarchy readback, and public-route readback.

If a rollback action times out before confirmation and save, treat the last
source-proven saved state as authoritative and editor dirty state as Unknown.
Stop. On resumption, inspect the existing editor before reloading.

Before the first mutation and after every coherent unsaved batch, capture the
loaded hierarchy outside Git. On the observed editor version, the serializable
model is the `containers` object, the dirty container IDs are the keys of
`changedContainers`, and `unsavedWidgets()` reports the client dirty state.
Store a private checkpoint with its timestamp and editor URL. Treat these
names as version-specific observations. Rediscover them if they are absent.

As soon as the exact checkpoint bytes exist in a private temporary file, store
them before saving, navigating, or attempting session recovery:

```text
python3 scripts/store_browser_checkpoint.py \
  <exact-browser-checkpoint.json> \
  --label <safe-run-label>
```

Require a successful exit and retain the printed SHA-256 for the run record.
The tool validates and privately stores the hierarchy bytes. Record the editor
URL, StoreFront identity, and dirty state separately; the tool does not prove
them.

Validate a private checkpoint or CJSON without printing content values:

```text
python3 scripts/inspect_visual_builder_artifact.py <private-json> \
  --expect-type <widget>=<type> \
  --expect-parent <child>=<parent> \
  --expect-absent-child <source-parent>=<moved-child> \
  --expect-config '<widget>.<key>=<json-value>'
```

Use `--expect-order <parent>=<child1>,<child2>` when the complete direct-child
order is part of the verifier. The command must report zero hierarchy and
expectation failures before relying on the checkpoint.

When authentication expires, keep the mutable editor tab open. Authenticate
in the separate admin tab. Before saving, verify the StoreFront identity,
editor URL, expected dirty container IDs, and the checkpointed widget
parentage. Do not retry a save while the admin tab still shows the login form.

## Shared-structure rules

Use `references/composition-and-shared-structures.md` as the current reference
template and hierarchy map. Apply these high-level rules:

1. Treat page templates as explicit ordered `#parse` compositions. A saved
   named container does not render unless the selected template parses it and
   its compiled conditions allow it.
2. Rebuild the shared header inside `container-header`. Preserve the Mobile
   Side Menu, Cart Snapshot Sidepanel, and Language Picker Modal as separate
   top-level operational siblings.
3. Rebuild the shared footer inside `container-main-footer`. Preserve menus,
   site attributes, social links, copyright, payment methods, purchase bubble,
   and webchat as dynamic widgets when required.
4. Keep item-page editorial and offer Rows inside the rendered ItemForm branch.
   Preserve the native media, price, stock, subscription, quantity, purchase,
   Notify Me, and structured-data branches.
5. Rebuild collection layouts inside the existing PageList, facet, ItemList,
   and simple-list containers selected by the active catalog template. Tabs
   forces a Tab; the observed Tab accepted a direct Text Block.
6. Verify shared changes on every in-scope route. One editor canvas or public
   page does not prove global coverage.

## Controlled-change workflow

Use only after the work order approves a named change.

1. Capture the exact private baseline before changing the editor.
2. Make one reversible editor change. Do not combine experiments.
3. Save once, then capture the same candidate pair privately.
4. Confirm the editor hierarchy and rendered test page independently.
5. Remove only the test change, save, and recapture the same pair.
6. Compare the explicitly selected baseline, saved, and rollback captures:

```text
python3 scripts/compare_ftps_captures.py \
  --before <baseline-capture-dir> \
  --after <saved-capture-dir> \
  --rollback <rollback-capture-dir> \
  --expect-stem <logical-cjson-vm-stem>
```

Use capture directory names under `UVB_PRIVATE_ARTIFACT_ROOT`, or absolute
paths that stay within that root. The no-selector newest-two behavior is
compatibility-only. Do not use it for controlled-change evidence.

Do not claim CJSON-to-VM causality until the before, saved, and rollback states
all agree. A timestamp, a version increment, or a visible editor change alone
is not sufficient.

Use `scripts/inspect_visual_builder_artifact.py` against the explicit baseline,
saved, and rollback CJSON files. Assert required widget types, parentage, exact
child order, source-parent absence, and configuration values. Do not select an
artifact only because it is the newest private capture.

Verify the explicit generated VM without printing its source or matched private
values:

```text
python3 scripts/inspect_visual_builder_vm.py <saved-vm-path> \
  --require-widget-type <expected-type> \
  --require-literal-file <protected-file-containing-private-literal> \
  --require-ml-literal-file <protected-file-containing-encoded-copy> \
  --require-parse-basename <expected-container.vm> \
  --require-regex '<expected-generated-pattern>' \
  --prohibit-regex '<forbidden-generated-pattern>'
```

Repeat assertion flags as needed. Use only the assertions that apply to the
approved change. A passing VM check proves the named generated-source signals,
not browser rendering or active-control behavior.

Use `--require-literal <non-secret-marker>` only for values that are safe in a
local process list. Use the protected-file form for private values.
Use the multilingual protected-file form for complete UTF-8 values compiled as
uppercase hex in a static i18n.writeMlString call.

Use an exact rendered-hierarchy match only for like-for-like snapshots, such as
baseline and rollback from the same route, state, viewport, and capture method:

```text
python3 scripts/inspect_visual_builder_rendered_html.py \
  <rollback-rendered.html> \
  --reference <baseline-rendered.html> \
  --require-match \
  --json
```

This exact match covers aggregate widget types, root types, and nearest-widget
edges only. It does not prove source equality, copy, assets, geometry,
visibility, or behavior. Omit `--require-match` for intentionally different
design states.

Read `references/design-intake-and-acceptance.md` and record every screenshot
mask and threshold before comparison. Do not tune them after seeing results.
Compare same-size screenshots with all accepted thresholds explicit:

```text
python3 scripts/compare_visual_screenshots.py \
  <reference.png> <target.png> \
  --mask <x,y,width,height> \
  --pixel-delta-threshold <0..255> \
  --max-normalized-mae <0..1> \
  --max-normalized-rmse <0..1> \
  --max-channel-delta <0..255> \
  --max-percent-pixels-over-threshold <0..100> \
  --json
```

Repeat `--mask` only for predeclared dynamic regions. Omit it when the recorded
mask set is `none`. A passing comparison is visual evidence only.

Create one private, path-free manifest that binds the explicit artifacts used
for the run:

```text
python3 scripts/build_visual_builder_run_manifest.py \
  --run-label <safe-run-label> \
  --logical-stem <safe-logical-stem> \
  --viewport-width <css-px> --viewport-height <css-px> \
  --viewport-dpr <device-pixel-ratio> \
  --checkpoint unsaved=<checkpoint.json> \
  --cjson baseline=<baseline.cjson> --cjson saved=<saved.cjson> \
  --cjson rollback=<rollback.cjson> \
  --vm baseline=<baseline.vm> --vm saved=<saved.vm> \
  --vm rollback=<rollback.vm> \
  --rendered-html baseline=<baseline.html> \
  --rendered-html saved=<saved.html> \
  --screenshot reference=<reference.png> \
  --screenshot saved=<saved.png> \
  --output <new-private-run-manifest.json>
```

Repeat artifact flags for other safe roles. The manifest stores roles, sizes,
hashes, run metadata, and viewport without source paths or bytes. It binds the
selected files but does not validate their semantics or comparison policy.

Assert all four surfaces:

1. CJSON target parent contains the moved IDs in the intended order.
2. CJSON source parent no longer contains those IDs.
3. VM contains the expected text, assets, styles, and native controls.
4. The public route renders the intended hierarchy and active controls.
