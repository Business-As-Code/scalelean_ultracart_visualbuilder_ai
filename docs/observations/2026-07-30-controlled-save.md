# reference controlled Visual Builder save

Controlling work order: SL-52.

## Scope

- Surface: owner-approved reference development StoreFront home page.
- Editor action: add one temporary `section` child beneath the Mailing List
  container and save it. An earlier `body` child remains in the test surface.
- File access: pinned, read-only FTPS. Raw directory names and file bytes stay
  in the local private artifact store.
- This pass did not perform rollback. Future mutations must use a fresh
  before/save/rollback sequence.

## Observations

- The Visual Builder accepts a `body` element as a child of the Mailing List
  container. It is structural. It provides no editable body text field.
- The Visual Builder picker groups `section` with grid-oriented elements. The
  inserted empty section remained visible in the saved Mailing List hierarchy.
- A private pre-save and post-save capture of the Mailing List and footer pairs
  found exactly one CJSON change and one VM change. The verifier confirmed that
  the changed CJSON/VM stem was the Mailing List pair.
- The selected footer CJSON/VM pair did not change in this section experiment.
- A private capture was limited to the owner-confirmed reference Elements
  containers subtree. It found 94 CJSON or VM candidates. Only the Mailing
  List and footer pairs were downloaded into the private artifact store.

## Classification

| Claim | Classification | Reason |
| --- | --- | --- |
| Adding and saving an empty Mailing List `section` changes its CJSON and VM pair together. | Verified | The saved editor hierarchy and private same-root before/after capture agree. |
| The selected footer pair changes when the Mailing List section changes. | Contradicted in this experiment | The selected footer CJSON/VM pair did not change. |
| A title marker persists to source or compiled output. | Unknown | The earlier `body` title marker did not appear in the hierarchy. |

## Remaining verifier

1. Use a distinct marker whose expected rendered output is explicit.
2. Capture the same CJSON and VM pairs before save, after save, and after
   rollback.
3. Compare private hashes and structured JSON content against each state.
