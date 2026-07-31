# Generated VM literal normalization observation

Date: 2026-07-31.

## Scope

This check used the saved item-display CJSON and its paired generated VM after
the approved reference product save. It inspected one public guarantee headline.
No source content was copied into Git.

## Verified result

- The saved CJSON contains the exact expected Headline HTML value.
- The generated VM contains the expected `headline`, `panel`, `row`,
  `itemform`, subscription-schedule, quantity, button, and bullet-list widget
  signals.
- The generated VM does not contain the headline's exact literal or its tested
  distinctive word fragments as plain source text.
- A later saved collection probe showed the compiler representation: complete
  UTF-8 strings appeared as uppercase hex in the fourth argument of a static
  `i18n.writeMlString` call.

## Interpretation

**Contradicted:** every exact CJSON text value must appear as a plain literal in
the generated VM.

The item-only check did not identify the transformation. The later collection
probe verified one mechanism for the same compiler version: a complete
multilingual value is UTF-8 encoded, converted to uppercase hex, and placed in
the fourth static `i18n.writeMlString` argument.

**Required verifier split:**

- Verify exact authored copy in saved CJSON.
- Verify encoded copy in generated VM with
  `--require-ml-literal-file <protected-file>`, then verify expected
  structural and dynamic widget signals.
- Verify exact visible copy in the public rendered DOM.

Do not treat a failed generated-VM literal search as proof that public copy is
missing. Do not treat a VM widget-type signal as proof that the exact copy
rendered.

The multilingual-literal assertion matches the complete encoded payload. It
does not prove the producing widget, active locale, public DOM, or visible
normalization.
