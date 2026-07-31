# Contributing

This repository is a public collaboration surface for understanding the
UltraCart Visual Builder and improving the accompanying agent skill.

## Suitable public contributions

- Corrected architecture or hierarchy documentation.
- Sanitized widget metadata and configuration schemas.
- Parent-child and forced-child rules.
- Synthetic CJSON, Velocity, HTML, or screenshot fixtures.
- Offline parsers, validators, and tests.
- Version-specific behavior with a reproducible verifier.

## Do not publish

- Credentials, access tokens, cookies, session data, or server key material.
- Raw customer StoreFront files, private URLs, directory listings, or paths.
- Customer data, order data, personal data, or browser recordings.
- UltraCart source or internal files that are not approved for public release.

Deliver restricted source packets through an agreed private channel. Record
their provenance, applicability, byte count, and SHA-256 privately. Contribute
only the authorized, sanitized facts, schemas, catalogs, and synthetic tests
derived from them.

## Evidence labels

Label behavioral claims as one of:

- `Verified`: repeatable evidence supports the claim.
- `Hypothesis`: plausible, but not yet proven.
- `Contradicted`: later evidence disproved the earlier claim.
- `Unknown`: current evidence is insufficient.

Keep editor state, persisted CJSON, generated Velocity, template composition,
and public rendering as separate evidence surfaces.

## Validation

Run these checks before submitting a pull request:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover tests
python3 /path/to/skill-creator/scripts/quick_validate.py \
  skills/ultracart-visual-builder-lab
git diff --check
```

Describe the affected Visual Builder version, evidence surface, proof boundary,
and any remaining unknowns in the pull request.
