# External image rendering observation

Date: 2026-07-31.

## Scope

This was a read-only public-route check of rendered image widgets on the saved
reference test product. The check retained only source host, load state, and
non-zero rendered-bound counts. It retained no full image URLs, page copy,
widget identifiers, or image bytes.

## Verified result

The page rendered 12 Visual Builder image widgets.

| Source host | Image widgets | Loaded with natural dimensions | Non-zero rendered bounds |
| --- | ---: | ---: | ---: |
| Clinical Effects public CDN | 11 | 11 | 9 |
| Placeholder host | 1 | 0 | 0 |

The two loaded CDN images without current rendered bounds can be explained by
off-screen, hidden, or lazy-rendered state. They are not failed network loads.

## Interpretation

**Verified:** an absolute image URL from the observed Clinical Effects public
CDN can render in a reference Visual Builder image widget.

**Contradicted:** one failed placeholder URL proves that all external image
URLs fail in reference.

**Unknown:** whether UltraCart imports or copies the remote bytes into its file
manager. Public rendering from an absolute URL does not prove asset ingestion,
ownership, durability, cache behavior, or future availability.

## Reusable rule

Test image sources individually. Verify all of the following on the exact
public route:

1. The image request completes with non-zero natural dimensions.
2. The widget obtains non-zero rendered bounds after any required scroll.
3. The saved CJSON retains the expected source setting.
4. The generated VM contains the image widget signal.
5. The source URL meets the design's ownership and durability requirements.

Use StoreFront-owned uploads when the source must remain stable independently
of an external host. Do not infer a global external-image policy from one
failed host.
