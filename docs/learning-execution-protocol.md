# Learning execution protocol

This protocol makes the Visual Builder investigation faster without weakening
evidence quality or creating competing browser writers.

## Efficiency objective

Improve the execution loop after each tested primitive. A faster loop must
still preserve parent, placement, save, reload, and rendering evidence.

## Operating rules

1. Use one browser writer for one StoreFront. Parallel work is limited to
   source analysis, documentation, registry generation, and test execution.
2. Reuse a confirmed UI procedure only after it has a saved and reloaded
   result. Record its inputs, expected UI state, and failure signal.
3. Batch independent read-only checks. Do not batch writes that affect the
   same container or route.
4. Treat editor latency, browser bridge failures, and prompt behavior as
   measured constraints. Record them as `Unknown` or `Contradicted` workflow
   claims until a repeatable workaround is verified.
5. Prefer hierarchy DOM for child rules, canvas for layout, the console for
   errors, CJSON and VM for serialization, and non-editor routes for rendered
   proof. Do not repeat a weaker check after a stronger one answers the same
   question.
6. After every layout primitive, update the registry and the reusable
   procedure before starting the next primitive.

## Per-primitive completion record

- Parent and insertion action.
- Direct-child and forced-child result.
- Settings opened and keys discovered.
- Save and reload result.
- Desktop and responsive result when the primitive affects layout.
- Observed delay, failure mode, and the next loop improvement.

## Stop conditions

Stop a browser mutation when the current editor state is ambiguous, a native
dialog cannot be read back, or a save result is not confirmed. Continue with
read-only source analysis and documentation until the UI state is restored.
