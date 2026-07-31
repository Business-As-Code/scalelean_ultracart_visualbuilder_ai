# Widget evidence registry

`widget-evidence-registry.json` is the public, privacy-safe contract for the
learning program.

It lists every widget type and serialized setting key in the current aggregate
catalog. Each record has an explicit evidence status:

- `Verified`: a controlled test supports the claim.
- `Contradicted`: a controlled test disproves the claim.
- `Unknown`: evidence is not sufficient.

The registry does not store source values, widget IDs, route names, customer
data, browser state, or raw CJSON and Velocity files.

## Update procedure

1. Build the aggregate catalog from approved private artifacts.
2. Generate or refresh the registry:

   ```sh
   python3 scripts/build_widget_evidence_registry.py \
     docs/reference/visual-builder-widget-types.json \
     --output docs/reference/widget-evidence-registry.json
   ```

3. Replace only directly tested `Unknown` fields with `Verified` or
   `Contradicted`. Record the corresponding evidence in `docs/observations/`.
4. Validate before commit:

   ```sh
   python3 scripts/validate_widget_evidence_registry.py \
     docs/reference/visual-builder-widget-types.json \
     docs/reference/widget-evidence-registry.json \
     --repository-root .
   ```

The validation fails if the catalog hash is stale, a widget or setting is
undocumented, an evidence status is missing, or a raw CJSON, VM, HAR, or
environment file appears in the public repository.
