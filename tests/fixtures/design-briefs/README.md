# Design Brief Synthetic Fixtures

This directory contains merchant-neutral synthetic fixtures for testing design
brief generation and validation. These fixtures are safe for the public
repository and do not contain any client brand names, private site content, or
real merchant assets.

## Fixtures

### 1. URL Reference Input (`url-reference-input.json`)

Represents a design brief generated from a URL reference. Uses `example-store.test`
as a synthetic merchant-neutral domain. The analyzer extracts minimal information
from URL-only input and marks most design details as `Unknown`.

**Usage:**
```bash
python3 scripts/build_design_brief.py \
  --work-order SL-148 \
  --reference-type url \
  --reference-path https://example-store.test/ \
  --output output-url-brief.json
```

### 2. Screenshot Reference Input (`screenshot-reference-synthetic.png`)

A minimal 1x1 PNG file serving as a synthetic screenshot reference. In production
use, this would be a full-resolution screenshot of a reference design. The
analyzer extracts layout structure (header-body-footer) from visual inspection.

**Usage:**
```bash
python3 scripts/build_design_brief.py \
  --work-order SL-148 \
  --reference-type screenshot \
  --reference-path tests/fixtures/design-briefs/screenshot-reference-synthetic.png \
  --output output-screenshot-brief.json
```

### 3. Written Brief Input (`written-brief-input.json`)

Represents a detailed written design specification for an item/product page.
This fixture includes complete route context, semantic sections with typography
and geometry, native UltraCart behavior (ItemForm), and explicit asset
provenance. The analyzer reads this structured input and produces a complete
design brief.

**Usage:**
```bash
python3 scripts/build_design_brief.py \
  --work-order SL-148 \
  --reference-type written-brief \
  --reference-path tests/fixtures/design-briefs/written-brief-input.json \
  --output output-written-brief.json
```

## Determinism Testing

The analyzer must produce identical briefs (excluding timestamps) when given
the same input:

```bash
# Generate brief twice
python3 scripts/build_design_brief.py \
  --work-order SL-148 \
  --reference-type url \
  --reference-path https://example-store.test/ \
  --output brief1.json

python3 scripts/build_design_brief.py \
  --work-order SL-148 \
  --reference-type url \
  --reference-path https://example-store.test/ \
  --output brief2.json

# Verify determinism
python3 scripts/validate_design_brief.py brief1.json \
  --check-determinism brief2.json
```

## Safety Rules

1. **No Real Merchant Data**: All fixtures use synthetic identifiers like
   `merchant-redacted`, `storefront-redacted`, and `example-store.test`.

2. **No Client Brand Names**: Fixtures avoid any real company names, logos, or
   brand-specific content.

3. **No Private Assets**: The synthetic PNG is generated programmatically and
   contains no real design content.

4. **Explicit Provenance**: All assets in fixtures are marked with provenance
   `synthetic` to indicate they are test data.

5. **No Credentials**: Fixtures contain no API keys, passwords, session tokens,
   or authentication data.
