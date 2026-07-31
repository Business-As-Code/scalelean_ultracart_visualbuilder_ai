# Scale Lean UltraCart Visual Builder AI

This public repository contains the UltraCart Visual Builder learning skill,
safe evidence tools, and a sanitized reference StoreFront evidence model. It
supports governed inspection and separately approved, reversible
reconstruction work.

UltraCart collaborators should read [CONTRIBUTING.md](CONTRIBUTING.md) before
sharing files or technical findings. Restricted vendor or customer source
files must stay outside this public repository.

The repository does not authorize a StoreFront edit. A controlled mutation
requires a work order that names the StoreFront, route, allowed changes,
rollback, and verifier.

## Start here

1. Read [AGENTS.md](AGENTS.md).
2. Read [the skill](skills/ultracart-visual-builder-lab/SKILL.md).
3. Read [the consolidated system model](docs/visual-builder-system-model.md)
   and [the current observation register](docs/observations/README.md). For authoring,
   also read [the supplied-source registry workflow](docs/supplied-source-registry.md).
4. Read [the read-only runbook](runbooks/read-only-discovery.md) for discovery
   or the skill's design-intake contract for an approved reconstruction.
5. Copy `.env.example` to `.env` locally and fill only the approved
   connection values. The `.env` file is ignored by Git.
6. Do not connect a file-transfer client until the work order records the verified
   protocol, host, permitted root, and server-side read-only access.

## Source-first authoring

The UltraCart-supplied packet stays outside Git. Normalize it into a private
registry before planning a hierarchy. The current verified registry covers 563
element types and 22,616 setting instances. It also preserves source conflicts
instead of silently resolving them.

Use `scripts/query_supplied_source_registry.py` to select types, inspect
settings, and check candidate parent-child relationships. Use
`scripts/validate_cjson_against_registry.py` before any editor write. A static
pass does not prove an editor save, generated VM, public render, responsive
result, or native commerce behavior.

Once the owner has approved and set a verified server public-key pin, run one
minimal listing with `python3 scripts/probe_ftps.py`. It does not download,
display, or modify remote files. The lab treats the UltraCart certificate chain
as a fixed vendor constraint. A public-key mismatch is a stop condition, not an
automatic pin update.

For a private root-listing manifest, use
`python3 scripts/capture_ftps_listing.py`. It stores raw directory names only
under `UVB_PRIVATE_ARTIFACT_ROOT`, outside Git, and prints only a count and
SHA-256 digest.

For a bounded private tree manifest, use
`python3 scripts/capture_ftps_tree.py`. It stops at the configured directory
and depth bounds. It does not download remote files.

Pass `--relative-path` when the approved StoreFront subtree is known. For
example, Visual Builder container work can be bounded to
`<storefront-host>/themes/Elements/theme/containers` below the configured FTPS
root.

After a tree manifest identifies CJSON or VM candidates, use an explicit
manifest and exact remote paths:

```text
python3 scripts/capture_ftps_candidates.py \
  --tree-manifest <exact-tree-manifest> \
  --include-remote-path <exact-cjson-path> \
  --include-remote-path <exact-vm-path>
```

The capture is read-only and stores bytes and its private hash manifest outside
Git. The latest-tree fallback exists only for compatibility and emits a warning.

Inspect one private CJSON or editor checkpoint without printing content values:

```text
python3 scripts/inspect_visual_builder_artifact.py <private-json> --json
```

Immediately after each coherent unsaved editor batch, validate and store its
exact browser checkpoint in configured private storage:

```text
python3 scripts/store_browser_checkpoint.py \
  <exact-browser-checkpoint.json> \
  --label <safe-run-label>
```

This validates hierarchy integrity and preserves exact bytes. It does not prove
the editor URL, StoreFront identity, dirty state, or a successful save.

Create a safe aggregate type catalog from explicit artifacts:

```text
python3 scripts/catalog_visual_builder_artifacts.py <cjson> [<cjson> ...]
```

After the rollback capture, compare explicit private capture directories:

```text
python3 scripts/compare_ftps_captures.py \
  --before <baseline-capture-dir> \
  --after <saved-capture-dir> \
  --rollback <rollback-capture-dir> \
  --expect-stem <logical-cjson-vm-stem>
```

The selectors can be directory names under `UVB_PRIVATE_ARTIFACT_ROOT`, or
absolute paths that stay within that root. The command prints aggregate
CJSON/VM hash changes and verifies byte-level rollback equality. Calling it
without `--before` and `--after` uses the newest two captures for
compatibility only.
Do not use that fallback for controlled-change evidence.

UltraCart can normalize CJSON during save. If bytes differ, require structured
hierarchy and configuration equality plus equivalent generated and rendered
behavior before deciding whether rollback succeeded.

Verify one explicit generated VM without printing its source or matched private
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

Repeat assertion flags as needed and omit assertions that do not apply. A
passing generated-VM check does not replace editor hierarchy or public-route
verification.

Use `--require-literal <non-secret-marker>` only for values that are safe in a
local process list. Use the protected-file form for private values.
Use the multilingual protected-file form when the compiler stores a complete
UTF-8 value as uppercase hex in an i18n.writeMlString call.

Compare rendered hierarchy aggregates only for like-for-like HTML snapshots:

```text
python3 scripts/inspect_visual_builder_rendered_html.py \
  <rollback-rendered.html> \
  --reference <baseline-rendered.html> \
  --require-match \
  --json
```

`--require-match` requires exact equality of widget-type, root-type, and
nearest-widget edge counts. It does not compare HTML bytes, copy, assets,
geometry, visibility, or behavior. Omit it for an intentional design change or
snapshots from different routes, states, viewports, or capture procedures.

Declare every mask and threshold in the design acceptance contract before the
first screenshot comparison. Then compare same-size captures:

```text
python3 scripts/compare_visual_screenshots.py \
  <reference.png> \
  <target.png> \
  --mask <x,y,width,height> \
  --pixel-delta-threshold <0..255> \
  --max-normalized-mae <0..1> \
  --max-normalized-rmse <0..1> \
  --max-channel-delta <0..255> \
  --max-percent-pixels-over-threshold <0..100> \
  --json
```

Repeat `--mask` for predeclared dynamic regions. If no mask is approved, omit
the flag and record `none`. Do not tune masks or thresholds after seeing a
result. A passing image comparison does not prove hierarchy or interaction.

Tie the explicit private artifacts for one run together with one path-free
manifest:

```text
python3 scripts/build_visual_builder_run_manifest.py \
  --run-label <safe-run-label> \
  --logical-stem <safe-logical-stem> \
  --viewport-width <css-px> \
  --viewport-height <css-px> \
  --viewport-dpr <device-pixel-ratio> \
  --checkpoint unsaved=<checkpoint.json> \
  --cjson baseline=<baseline.cjson> \
  --cjson saved=<saved.cjson> \
  --cjson rollback=<rollback.cjson> \
  --vm baseline=<baseline.vm> \
  --vm saved=<saved.vm> \
  --vm rollback=<rollback.vm> \
  --rendered-html baseline=<baseline.html> \
  --rendered-html saved=<saved.html> \
  --screenshot reference=<reference.png> \
  --screenshot saved=<saved.png> \
  --output <new-private-run-manifest.json>
```

Repeat artifact flags for additional safe role names. The new mode-0600
manifest records roles, byte counts, hashes, timestamp, logical stem, and
viewport, but no artifact paths or source bytes. It binds selected evidence;
it does not validate routes, comparison policy, or artifact meaning.

## Repository contents

| Path | Purpose |
| --- | --- |
| `runbooks/` | Safe observation and controlled-test procedures. |
| `docs/` | Evidence model and data-handling rules. |
| `skills/` | Reusable hierarchy-first operating skill and references. |
| `scripts/` | Non-mutating probe, capture, inspection, catalog, and diff tools. |
| `tests/` | Synthetic fixtures and local tests only. |

## Evidence rule

An editor observation, an FTP-visible file, and a rendered page are separate
facts. A relationship between them remains Unknown until a separately approved
controlled test captures a before-and-after comparison.
