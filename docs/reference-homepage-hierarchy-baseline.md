# reference homepage hierarchy baseline

Observed: 2026-07-30.

Status: read-only browser observation. This is not an export or proof of the
underlying file layout.

This is a historical baseline. For the current saved shared header, see
[Clinical Effects shared-header reconstruction](observations/2026-07-31-clinical-effects-shared-header.md).

## Scope

- Surface: reference development StoreFront home page in Visual Builder edit mode.
- Theme observed: Elements.
- Observation method: visible Visual Builder hierarchy only.
- No Save, Publish, Import, upload, download, or other write action occurred.

## Observed root containers

| Container | Observed top-level structure | Classification |
| --- | --- | --- |
| `container-header` | Subheader, Header, Mobile Side Menu, cart Snapshot sidepanel, Language Picker Modal | Reusable header and navigation boundary |
| `container-home-slider` | Main-Slider section | Homepage content boundary |
| `container-paypal-banner` | PayPal Messaging section | Homepage content boundary |
| `container-home-subgroup-list` | Featured Pages section | Homepage content boundary |
| `container-featured-items` | Featured Items section | Homepage content boundary |
| `container-mailing-list-signup` | Mailing List section | Homepage content boundary |
| `container-main-footer` | Footer section | Reusable footer boundary |

## Editor controls observed

The editor exposed Hierarchy, Items, Theme Settings, Languages, Library,
Preview, Save, Help, and Exit. The hierarchy exposed a name/type filter and an
add-element control at each observed container. Save was visible but was not
used.

## Not yet proven

- Exact child-element tree and settings schema for each container.
- Exact FTP path for each named container.
- CJSON source file to compiled Velocity file mapping.
- Whether the visible PayPal Messaging warning changes the generated output.

## Next evidence

Create a private FTPS manifest that captures only the approved StoreFront
subtree. Match candidate CJSON and VM file names to these observed container
names. Treat each match as a hypothesis until a controlled before-and-after
test is approved and verified.
