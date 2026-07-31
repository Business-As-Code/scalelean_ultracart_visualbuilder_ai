# reference homepage layout build

Scope: owner-authorized implementation test in the reference development
StoreFront Visual Builder. This is an editor-side layout record. It does not
assert source-file equivalence or production readiness.

This is a superseded historical build record. Its custom header Section is now
the hidden legacy section-4806347. See the
[current shared-header record](2026-07-31-clinical-effects-shared-header.md).

## Saved result

The Home containers were saved after these structural additions:

```text
container-header
  Header
  Section
    Row-3
      Column 1
        Image
      Column 2
        Text
      Column 3
        Headline

Home body
  Section
    Row-2
      Headline
      Text

container-main-footer
  Section
    Row-2
      Headline
  Footer
    existing footer navigation and legal content
```

The new header band uses an image selected from the existing StoreFront image
library, a paragraph, and a headline. The new body block adds an editorial
headline and supporting paragraph after the existing newsletter module. The
new footer section appears before the existing footer navigation and contains
the custom headline `Keep in touch`.

## Verification

| Check | Result | Evidence |
| --- | --- | --- |
| Header tree persisted after save | Verified | Reopened hierarchy showed `Section > Row-3 > Image, Text, Headline`. |
| Editorial body block rendered | Verified | Canvas showed the two-column section with its new headline and paragraph. |
| Footer addition persisted after save | Verified | Reopened hierarchy showed a Section in `container-main-footer` before the existing Footer branch. |
| Existing hero, featured content, newsletter, and footer links remained present | Verified in editor | Canvas retained the existing components. |
| Mobile and external non-editor rendering | Not verified | Preview confirmation did not produce an inspectable non-editor viewport in this pass. |

## Boundaries

- No CJSON upload or import was used.
- No product, checkout, customer, or form-submission configuration changed.
- No StoreFront file was uploaded, downloaded, or modified through FTPS.
- Existing images were selected through the Visual Builder image library.

## Follow-up

Before treating this as a launch-ready design, verify desktop and mobile
non-editor rendering, add the required final brand copy and accessibility
review, and take a before/after source capture only if source-output evidence
is needed.
