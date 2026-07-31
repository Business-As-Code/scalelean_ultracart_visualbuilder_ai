# Advanced layout elements

Use this reference only when normal `Section > Row > Column` and Panel layout
cannot represent the approved design cleanly. These settings come from the
loaded reference editor runtime catalog. Unless stated otherwise, persistence,
generated VM, responsive behavior, and public rendering remain `Unknown`.

## Evidence rule

For each advanced element, prove these states in order:

1. The selected parent's visible palette offers the type.
2. The editor creates the expected forced or constrained child hierarchy.
3. A save produces valid CJSON parentage and settings.
4. The matching VM contains the expected structure and responsive rules.
5. The public route matches the intended geometry and interaction.
6. Rollback restores the baseline.

Do not select an advanced element only because its runtime schema exists.

## Flex

Flex is a general child-bearing Grid element. Its settings are breakpoint-aware:

```text
flexDirection flexJustifyContent flexAlignItems flexWrap flexGap flexGapUnit
flexUseBlockerDuringCartUpdates flexSemanticElement flexAriaLabel
flexOrder flexWidth flexWidthSize flexWidthSizeUnit flexGrow flexShrink
flexAlignSelf
```

It also supports background, spacing, borders, corners, sticky behavior,
animation, gradient, display, classes, and scoped CSS.

Use Flex for a composition that requires content order, grow, shrink, wrap, or
alignment that is awkward in the Foundation Row and Column grid. Verify all
in-scope breakpoints.

## Absolute Wall and Absolute Block

Absolute Wall forces Absolute Block children. The Wall provides overall width,
background, height, and snap-grid pixels. Each Block provides width, height,
top, left, right, bottom, and z-index plus its own surface and spacing.

Use this only for an intentionally fixed artboard-style composition. It has a
high responsive-overlap risk. Require viewport-specific geometry checks and do
not use it for ordinary flowing product content.

## Masonry Wall and Masonry Block

Masonry Wall forces Masonry Block children and provides a gutter. Each Block
uses small, medium, and large width-column counts plus corresponding height
column counts and alignment.

Use this for an approved masonry card design. Verify order, gaps, block height,
lazy-loaded media, and reflow at every in-scope viewport.

## Table hierarchy

Use this constrained grammar:

```text
Table
  Table Head
    Table Row
      Table Column
  Table Body
    Table Row
      Table Column
```

The Table can also receive a direct Table Row or Page Attribute. Table parts
support normal background, spacing, borders, corners, animation, gradient,
display, and scoped CSS.

Use a Table for tabular relationships, not general page alignment. Verify
semantic output and small-screen overflow before acceptance.

## Slider and Slide

Slider accepts only Slide children. Configure:

- fixed, viewport, or aspect-ratio height;
- direction;
- slides shown and scrolled at small, medium, and large breakpoints;
- autoplay and speed;
- arrows, offsets, colors, and borders;
- dots, dimensions, position, offset, and colors;
- slide text and background color.

A Slide provides image URL, cover behavior, opacity, overlay color, link,
target, alt text, vertical alignment, and local CSS. It accepts normal content
children in the observed runtime.

The existing Home Slider hierarchy proves editable Slide children. Its exact
CJSON and VM schema is not in the current complete artifact set. Test one
duplicate or temporary Slide, active-slide behavior, keyboard navigation,
autoplay, image loading, and rollback before using it in a final design.

## Spotlight and Spotlight Item

Spotlight configures orientation, center mode, chip size, loop, arrows, dots,
autoplay, speed, and spacing. Spotlight Item configures an item key and detail
widget targets.

Treat Spotlight as a specialized interactive selector. Its artifact and public
behavior are `Unknown` on reference. Do not substitute it for Slider without a
controlled test.

## Flyout and Overlay

Flyout targets an overlayed element and configures background, direction,
arrow, padding, display, and local CSS. Overlay targets an element and provides
normal and hover colors, phone and tablet behavior, surface styling, spacing,
borders, corners, animation, and local CSS.

These elements depend on target IDs. Verify the target remains stable after
duplication or moves. Test keyboard, pointer, and touch behavior separately.

## Page Container and Item Container

Page Container and Item Container select a named reusable container through
`pageContainerName` or `itemContainerName`. They expose surface, typography,
spacing, borders, animation, and gradient settings, but the observed runtime
does not expose normal child insertion.

Treat them as references to existing dynamic container definitions. Do not
assume that they create or compose a new top-level template container.

## Button Group

Button Group accepts children and configures a default Button and remembered
state. Each Button still owns its native action, targets, styling,
accessibility, and analytics.

Use Button Group for visual or state selection only after confirming that its
state behavior matches the required product or form behavior. Do not replace
native product option, quantity, subscription, or purchase controls with a
static Button Group.

## Mega Menu and Mega Menu Item

Mega Menu forces Mega Menu Item children. Configure toggle-only behavior,
normal and active colors, active borders, typography, padding, content width,
and content position. Each Mega Menu Item provides a label, link, spacing,
borders, and normal child content.

Preserve the existing menu widget and mobile navigation unless the work order
explicitly requires a Mega Menu. Verify desktop focus, keyboard navigation,
touch behavior, link targets, and small-screen fallback.

## Sidepanel and Modal

Both are normal child-bearing off-page elements.

Sidepanel settings include side, type, responsive width, height, speed,
underlay, lazy rendering, automatic triggers, padding, borders, corners,
fonts, gradient, scrollbars, and scoped CSS.

Modal settings include width, lazy rendering, underlay and close behavior,
timeout, exit-intent, scroll, URL parameter, subtotal, item-count and
specific-item triggers, elements to hide before open, spacing, borders,
corners, fonts, shadow, animations, gradient, and scoped CSS.

Preserve existing show, hide, and toggle target IDs when moving Buttons or
off-page elements. Do not enable an automatic trigger during a layout test
unless the work order requires it.

## Controlled experiment order

Test advanced elements in this order because each step increases interaction
and responsive risk:

1. Flex.
2. Accordion and Tabs.
3. Slider.
4. Table.
5. Masonry Wall.
6. Absolute Wall.
7. Flyout and Overlay.
8. Mega Menu.
9. Sidepanel and Modal triggers.
10. Spotlight.

Use one disposable branch or reversible duplicate at a time. Capture the exact
CJSON and VM pair and verify public behavior before the next experiment.
