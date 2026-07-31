# UltraCart-supplied source registry

Date: 2026-07-31.

## Purpose

The private registry converts the UltraCart-supplied Visual Builder packet into
a queryable authoring contract. It lets an agent inspect the closed element
catalog, setting schemas, placement signals, forced children, references,
responsive wrappers, and known source conflicts before using the editor.

The raw packet and normalized registry remain outside Git. The repository
contains only the parser, validator, query tool, synthetic tests, and this
aggregate receipt.

## Verified source receipt

The current private audit passed with these aggregate results:

| Check | Result |
| --- | ---: |
| Packet files matched to the private intake manifest | 1,703 |
| Packet bytes matched | 13,758,675 |
| Element types | 563 |
| Distinct friendly names | 548 |
| Setting instances | 22,616 |
| Unique setting keys | 1,937 |
| Element schemas hashed | 563 |
| Element documents hashed | 563 |
| Description sidecars hashed | 560 |
| Supplied examples accepted in existing-content mode | 4 of 4 |

The normalized private registry SHA-256 is
`938f9db64c277c1552e54a89de360081f75215cb931107ee9e1144990056a9b6`.
The path-free machine-readable receipt is
[`reference/supplied-source-registry-receipt.json`](reference/supplied-source-registry-receipt.json).

## Hierarchy model

The packet yields these child-model counts:

| Child model | Element types |
| --- | ---: |
| Forced child | 7 |
| Constrained or general | 137 |
| Contextual or runtime | 13 |
| Leaf | 378 |
| Undocumented | 28 |

Thirty-two placement tokens describe runtime or context constraints that are
not closed element type names. The query tool preserves them as unresolved.
It does not guess a parent or child.

The source can disagree with itself. Placement queries therefore return
`bilateral`, `unilateral`, `contradicted`, `unknown`, or `denied`. New authoring
accepts only bilateral edges. Other results require a current editor test.

## Source anomalies

The registry preserves 630 supplier-source anomalies:

| Anomaly | Count |
| --- | ---: |
| Conditional reference cannot be resolved locally | 375 |
| Default value has a different declared type | 25 |
| Default is absent from its enum | 37 |
| Setting uses an unmapped editor type | 189 |
| Description has no active setting | 4 |

These findings are not proof of editor defects. They are fail-closed authoring
signals. Existing supplied examples can retain historical value shapes as
warnings, but newly generated content must satisfy current source constraints.

## Workflow

Set `UVB_PRIVATE_ARTIFACT_ROOT`, then build and audit a registry:

```text
python3 scripts/build_supplied_source_registry.py \
  <private-bundle-root> \
  --intake-manifest <private-intake-manifest.json> \
  --output <private-registry.json>

python3 scripts/audit_supplied_source_registry.py \
  <private-bundle-root> \
  <private-intake-manifest.json> \
  <private-registry.json> \
  --output <private-audit-receipt.json> \
  --public-receipt <reviewable-aggregate-receipt.json>
```

The public-receipt option emits a fixed aggregate subset. It omits source
prose, file names, paths, example labels, widget IDs, and configuration values.

Query the private registry without printing the complete corpus:

```text
python3 scripts/query_supplied_source_registry.py \
  <private-registry.json> element row
python3 scripts/query_supplied_source_registry.py \
  <private-registry.json> setting row <setting-key>
python3 scripts/query_supplied_source_registry.py \
  <private-registry.json> children row
```

Use the `prose` query only when source narrative is necessary. Its output is
private source material and must not be copied to Git, Linear, or public chat.

Validate a proposed tree before using the editor:

```text
python3 scripts/validate_cjson_against_registry.py \
  <private-registry.json> <proposed.cjson> --mode authoring --json
```

The validator checks static source shape, types, settings, references, forced
children, and documented placement. It cannot prove save and reload behavior,
generated Velocity, public rendering, responsive geometry, or native commerce
behavior. Those remain separate live acceptance gates.

## Ten authoring gates

The capability fails closed at these gates:

1. Packet and registry hashes match the approved private intake manifest.
2. Every node satisfies the recursive node contract and uses only allowed node
   keys.
3. Every `type` exists in the closed source catalog.
4. Every config key belongs to the selected element or to the explicit
   bookkeeping contract.
5. Values satisfy declared types, enums, and current shared enums.
6. Multilingual, responsive, and scoped-style wrappers use their distinct
   documented shapes.
7. Conditions resolve and dynamic options come from current merchant data.
8. Parent-child edges have bilateral placement support and obey forced-child
   rules.
9. IDs are unique; parent, container, and widget references resolve in the
   proposed tree or declared external context.
10. Legacy and transient keys are not authored, and live acceptance remains
    incomplete until save/reload, VM, public render, responsive render, and
    native behavior evidence all pass.

`existing` mode converts historical value-shape, legacy, transient, dynamic,
condition, and placement conflicts to warnings when structural safety permits.
It is for audit and migration. It is not an authoring bypass.
