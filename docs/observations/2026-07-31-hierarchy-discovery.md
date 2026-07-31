# 2026-07-31 hierarchy and settings discovery

Classification: Verified browser-editor palette and DOM metadata evidence.

Scope: MELRA demo StoreFront. Read-only probes. No save or source capture was
performed for this observation.

## Hierarchy

- A Container root offered Section, Page Container, and special-purpose
  widgets. It did not offer generic Row, Panel, Flex, or Table.
- Section offered Row, Section, Panel, Flex, Absolute Wall, Masonry Wall,
  Table, Accordion, Slider, Page Container, and Checkout Condition.
- A full-width Row created a Column child. Existing hierarchy gave direct
  examples of `Section > Row > Column`, `Column > Panel`, and
  `Panel > Headline`.
- Modal and Sidepanel offered the same observed layout choices: Absolute Wall,
  Aligner, Flex, Masonry Wall, Panel, Row, Table, Accordion, Slider, Tabs,
  Modal, and Sidepanel.
- An item route offered Item Container and Page Container. A catalog group and
  ordinary page offered Page Container only. This is palette evidence, not yet
  persistence or record-scope proof.

## Settings discovery

The settings sidebar uses `data-setting-key` for discoverable serializable
controls. A setting can expose default, breakpoint, refresh, render-parent,
and reset-runtime metadata. Responsive fields used small, medium, and large
breakpoints. Conditional field visibility is declarative in DOM attributes.

## Limits

No statement here proves CJSON or VM serialization, save/reload persistence,
public rendering, or route-record attachment. Those tests remain required by
the relevant widget work orders.
