# Collection Tab probe pending rollback

Date: 2026-07-31.

Safe run label: group-facets-tab-probe-paused.

Test StoreFront: reference development StoreFront.

Authority: the owner authorized test changes in the active session. A
controlling Linear work order identifier is not recorded in this repository.

## Scope

This experiment tested hierarchy insertion inside the standard Shop collection
Group Facets container. It added one temporary desktop Tab and one direct Text
Block child. It did not move or rebuild the existing Items or Filters
descendants.

Site work paused before rollback could be confirmed. This record therefore
describes the last source-proven saved state and a fail-closed recovery gate.

## Baseline and saved hierarchy

The baseline direct children of tabs-3327 were:

~~~text
tabs-3327
  tab-3328
  tab-3332
~~~

The clean saved and reloaded hierarchy was:

~~~text
tabs-3327
  tab-3328
  tab-3332
  tab-4810913
    textblock-4810914
~~~

The added Tab configuration was:

- tabTitle: ENG equals UVB Probe.
- showOn: desktop.
- direct child: textblock-4810914.
- richText marker: ENG equals UVB-COLLECTION-TAB-PROBE-001.

The editor reported Containers saved., cleared its unsaved state, and retained
the exact three-Tab order after reload.

## CJSON and VM evidence

The saved CJSON inspector verified the added types, direct parentage, complete
Tabs order, title, visibility, and marker configuration.

The semantic CJSON comparison reported:

| Difference | Count |
| --- | ---: |
| Child-order changes | 1 |
| Excess nodes | 2 |
| Configuration changes | 1 |
| Missing nodes | 0 |
| Parent changes | 0 |
| Type changes | 0 |

The configuration change was editModeSelectedTab. The saved CJSON was smaller
than baseline because UltraCart normalized the document during save. The
structured comparison did not show unrelated hierarchy loss.

| Artifact | Baseline bytes | Baseline SHA-256 | Saved bytes | Saved SHA-256 |
| --- | ---: | --- | ---: | --- |
| group_facets.cjson | 76077 | ec0ff94108af91ed5b20279ba3139b68d333ae7033be5dc04d05a88542954869 | 59146 | 23be065bdd3262d5e3a1d44b761988893fe032aa02742abe8bb628c43cacd625 |
| group_facets.vm | 73348 | 4b490221d745975c99a7d32ae7dab4e3ce351b0b5c3926d88414a407a0f07cac | 73978 | 3b64fdfb93104a7f151b57ce942252c7353155fd2628f0b0ce0fc87a3c5e89fb |

Generated VM changed from two to three Tab widgets and from zero to one Text
Block. The pre-existing collection widget signals remained present.

The compiler did not emit the title or marker as plaintext. It encoded each
complete UTF-8 value as uppercase hex in the fourth argument of a static
i18n.writeMlString call:

- Tab title hex: 5556422050726F6265.
- Marker hex:
  5556422D434F4C4C454354494F4E2D5441422D50524F42452D303031.

This proves the compiler representation for these values. CJSON remains the
exact authored-copy source, and the public DOM remains the visible-copy proof.

The private path-free run manifest contains ten artifact roles and has
SHA-256
9864a8fef8a2ae78fcf60fee4edd9323c207dcf99f2056fdfcc5a700f83eff69.
It binds baseline and unsaved checkpoints, baseline and saved CJSON and VM, and
baseline and saved public HTML and screenshots at 1440 by 1100 with DPR 1.

## Public readback

The public desktop Shop route displayed the UVB Probe Tab. Selecting it
displayed the marker with non-zero bounds:

| Axis | Value |
| --- | ---: |
| x | 265 |
| y | 839.984375 |
| width | 910 |
| height | 25.59375 |

Selecting Items restored the observed data-bound collection surface:

- nine visible Item Links;
- two Item List Facets;
- one sort control;
- one per-page control;
- two pagination controls;
- one PageList;
- five forms;
- three selects.

This proves the temporary editorial Tab did not replace those visible dynamic
families in the saved state. It does not prove every interaction state.

## Rollback status

Rollback is Pending and Unknown.

A delete action was initiated for tab-4810913. The browser operation timed out
before readback. There was:

- no confirmed deletion;
- no post-delete hierarchy readback;
- no save confirmation;
- no editor reload;
- no rollback CJSON or VM capture;
- no public rollback verification.

The current editor dirty state is Unknown. The last source-proven persisted
state still contains tab-4810913 and textblock-4810914. Do not describe the
probe as reverted, reversible, baseline-restored, or complete.

## Required resumption verifier

1. Restore authentication separately if needed.
2. Inspect the existing editor hierarchy and dirty state before any reload.
3. Determine whether the timed-out delete changed only unsaved local state.
4. Remove the probe if it remains present.
5. Save once and require a clean confirmation.
6. Reload the editor hierarchy and public route.
7. Require exact Tabs order tab-3328, tab-3332.
8. Require the probe title, marker, Tab, and Text Block to be absent.
9. Recheck all preserved dynamic collection counts and permitted actions.
10. Capture rollback CJSON and VM.
11. Require semantic hierarchy and configuration equality with no excess
    nodes, missing nodes, parent changes, type changes, or child-order changes.
12. Record any byte-hash difference separately. Do not fail or pass semantic
    rollback on byte difference alone when UltraCart normalization is proven.

Mark rollback complete only after all applicable checks pass.
