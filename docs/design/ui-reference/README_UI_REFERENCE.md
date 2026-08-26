# Improve Yourself — UI Reference Pack v1.0.0

This folder is the **visual source of truth** for Improve Yourself UI work.

## Authority

- `*_MASTER.png` files are implementation and visual-acceptance references.
- `*_SUPERSEDED.png` files are historical only and **must not** be used as implementation targets.
- Do **not** reconstruct a screen from the Concept Preview PDF when a matching MASTER PNG exists.
- Example/mockup values in the images are not product rules. Runtime data, evidence, safety boundaries, and implemented feature truth override example content.

## Optimizer — special rule

The old Optimizer visual from the Concept Preview PDF is superseded. The current authoritative Optimizer references are:

1. `optimizer_overview_MASTER.png`
2. `system_optimizer_detail_MASTER.png`

`optimizer_legacy_from_concept_pdf_SUPERSEDED.png` is included only to prevent accidental reuse.

## Recommended repository location

Place this complete folder unchanged at:

`docs/design/ui-reference/`

Agents should read `UI_REFERENCE_MANIFEST.json` before UI implementation.

## Visual acceptance rule

For a screen to pass, the runtime view should be immediately recognizable as an implementation of the corresponding MASTER image at a comparable viewport. Compare at minimum:

- layout and region placement
- proportions and spacing
- navigation and active states
- cards/panels and border treatment
- typography hierarchy
- colors and contrast
- status semantics
- right-side detail panels where present

Do not accept a screen merely because the same information exists somewhere in the UI.

## Included screens

- Dashboard / Home
- Improve Analyzer
- Demo Analyzer
- 2D Tactical / Viewer
- My Improvement
- Improve Benchmark
- Optimizer overview (new master)
- System Optimizer detail (new master)
- Legacy Optimizer from PDF (superseded, archival only)

See `UI_REFERENCE_MANIFEST.json` for hashes, dimensions, and exact authority status.
