# Read-only discovery runbook

Controlling work order: SL-51.

## Preconditions

- The work order names the test storefront and allows browser observation.
- The owner is available to authenticate the browser session if UltraCart
  expires it.
- No save, publish, import, upload, delete, rename, or file transfer write is
  authorized.
- The private evidence destination is available before collecting any raw
  artifact.

## Browser pass

1. Open the named test storefront in edit mode.
2. Inventory menus, element types, imported-component controls, and warnings.
3. Capture only redacted notes in Linear or BAC.
4. Do not press Save, Publish, Import, Delete, or any control whose effect is
   unknown.

## File-transfer pass

Do not connect until the owner confirms the exact protocol, host, permitted
root, and server public-key pin. The UltraCart certificate chain is a known
vendor constraint for this lab. Do not replace a changed pin automatically.
Stop and obtain owner approval to verify and update it. On connection:

1. Record protocol and TLS or SSH negotiation outcome.
2. List only the approved root and create a private manifest.
3. Do not mount the remote drive, synchronize folders, or open files in an
   editor that might write metadata.
4. Do not infer an editor-to-file relationship from one listing.

## Exit criteria

Post a redacted control inventory and a classified evidence map to SL-51. The
next result is a controlled-change proposal, not an edit.
