# reference StoreFront home page. Read-only baseline

Observed 2026-07-30 in the owner-provided development StoreFront.

## Boundary

- Entered Visual Builder edit mode.
- Opened Hierarchy, Theme Settings, and Developer Tools. Server Log.
- Did not save, publish, import, upload, delete, rename, or download.
- No screenshots, source files, logs, or credentials are retained in this
  repository.

## Confirmed observations

- The Visual Builder exposes a page-level hierarchy of named containers and
  typed elements.
- The Home page hierarchy includes header, home-slider, banner, featured-page,
  featured-item, mailing-list, and footer containers.
- The hierarchy includes sections, sidepanels, and modals. Observed examples
  include a mobile side menu, cart snapshot sidepanel, and language picker
  modal.
- Theme Settings provide defaults for body, containers, sidepanels, buttons,
  headings, inputs, labels, tabs, accordions, colors, and fonts.
- Developer Tools exposes Server Log and Client Log. Cloud and Minify controls
  were visible but not changed.
- The Server Log showed the Home page passing through the StoreFront render
  flow and a Velocity template named `template_home.vm`. It also showed theme
  CSS and JavaScript asset processing.

## Warnings observed in edit mode

- The page reported a legacy PayPal messaging element that will not display to
  customers.
- Edit-mode diagnostics also reported missing alt text and an unknown item ID.

These are observations, not a remediation request.

## Still unproven

- The exact reference `.cjson` source location for each container.
- The precise generated `.vm` output and its source-to-output mapping.
- Whether a given Visual Builder interaction produces one file change, several
  file changes, or an internal record update before compilation.

## Next evidence step

Create a private manifest of the approved StoreFront subtree through the
pinned FTPS path. Correlate only names, timestamps, sizes, and hashes with a
separately approved controlled change.
