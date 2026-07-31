# UltraCart Visual Builder learning lab

## Governing context

- BAC goal: [G21](https://github.com/Business-As-Code/bac/blob/main/goals/g21-ultracart-visual-builder-capability.md)
- BAC project: [UltraCart Visual Builder skill and learning lab](https://github.com/Business-As-Code/bac/blob/main/projects/ultracart-visual-builder-skill-lab.md)
- Controlling work order: [SL-51](https://linear.app/scale-lean/issue/SL-51/read-only-discovery-map-an-approved-ultracart-visual-builder-test)

The governance links can require Scale Lean access. The safety, privacy, and
evidence rules below are complete for public contributors.

Linear is the live work tracker. BAC is the durable coordination record. This
repository owns only implementation code, safe runbooks, and synthetic tests.

## Boundary

This repository is a forensic learning lab. It is not a storefront editor,
deployment mechanism, or authority to change UltraCart.

Default to read-only work. Do not save, publish, import, upload, delete,
rename, or edit through a file-transfer client. Do not call undocumented APIs.
Any controlled change needs a separate approved Linear work order with a
named test surface, baseline, expected effect, rollback, and verifier.

## Privacy and secrets

Never commit credentials, raw storefront files, screenshots, browser
recordings, customer data, session data, or a `.env` file. Put approved raw
captures in the governed private shelf, not GitHub. Commit only source code,
synthetic fixtures, redacted manifests, hashes, and aggregate evidence.

## Working method

1. Confirm the named test storefront and allowed access path from the work
   order.
2. Record observations as verified, hypothesis, or unknown.
3. Capture a private baseline before proposing a controlled change.
4. Compare editor state, file artifacts, and rendered output only after an
   approved experiment.
5. Update the skill only from repeatable evidence.
