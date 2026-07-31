# Clinical Effects homepage reconstruction test

Scope: owner-authorized visual reconstruction on the reference development
StoreFront. The source reference was the owner-controlled public Clinical
Effects homepage. This is a test-site editor change only.

This is a superseded historical build record. Its custom header Section is now
the hidden legacy section-4806347. See the
[current shared-header record](2026-07-31-clinical-effects-shared-header.md).

## Reference composition

The reference page combines a compact utility and navigation header with an
editorial article grid. Its leading composition has a wide primary feature,
two stacked secondary stories, and an additional split story row before the
product-action content.

## Saved reference changes

```text
container-header
  Header
  Section
    Row-3
      Column 1 > Image
      Column 2 > Text
      Column 3 > Headline: Clinical Effects

Home Slider container
  Main Slider
    Slider
      Slide 3
        Title: Supporting your brain in a distracted world

Home body
  Section
    existing Row-2 > Headline, Text
    added Row-2 (8/4 split)
      Column 1 > Image
      Column 2 > empty at save
```

The image leaf was configured with an owner-authorized public Clinical Effects
feature image and descriptive alternative text. In the saved non-editor page,
the image did not render. The editor accepted the URL, but that is not proof
that cross-site image URLs are supported by this StoreFront renderer.

## Verified findings

| Finding | Evidence class |
| --- | --- |
| A Section accepted a new Row with an 8/4 column split. | Verified in the editor canvas and Row settings. |
| An Image can be added as a direct leaf of the new left Column. | Verified in the hierarchy and canvas. |
| Existing Slider leaves can be edited inline and accepted by Save. | Verified in the inline editor with the `Containers saved.` confirmation. Artifact persistence and the public active slide were not matched in this pass. |
| The visible slide can differ while the carousel advances. | Verified by editor and public-page renders showing different slide instances. |
| External image URL acceptance results in a rendered image. | Unknown. The configured Image leaf remained missing after save. This can reflect a renderer restriction or an incomplete configuration event. |

## Limits

- This pass reproduces selected visual hierarchy and copy patterns. It does
  not reproduce the Clinical Effects dynamic blog-card feed, header behavior,
  typography, or data bindings.
- No product, checkout, customer, mailing-list, CJSON import, FTPS, or source
  file action was performed.
- A second pass should upload owner-authorized assets to the approved
  StoreFront image library, then use those local paths. It should build the
  primary and secondary cards as separate approved rows and verify the desktop
  page after each saved batch.
