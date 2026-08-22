# Optimizer Visual Fidelity Pass

Status: **final Portable runtime reviewed — `WAITING_FOR_TRISTAN`**

## Scope lock

This pass changes only the visible treatment of the approved Optimizer pilot:
the overview and the System Optimizer detail screen.  Existing navigation,
System Check adapters, Matrix Pack, evidence, recommendation contracts,
read-only policy and other application pages are unchanged.

The visual source of truth is the approved Optimizer reference set, including
the checked-in concept master page 07 and the supplied System Optimizer detail
reference.  Real locally loaded values replace illustrative mockup values.

## Central Optimizer visual system

`analyzer_shell.py` now has one optimizer-only metallic token family for the
two screens:

- near-black midnight page ground and deep blue-black raised/card surfaces;
- restrained cyan edge-light and focus/selected treatment;
- cool primary/secondary/muted text contrast;
- semantic accent colours for checked, already-matched and conditional states;
- low-fill, rounded actions instead of filled platform-style rectangles; and
- matching rounded hardware chips, detail surfaces, table shell and controls.

The custom chrome wraps the pre-existing Tk content widgets. It does not
change callbacks, result models or the read-only data path.

## Final runtime comparison — 2026-08-22

The fresh Portable build was opened at the normal Experimental window size
(`1360x860`).  Both required runtime screens were captured directly after the
last package was created.

| Screen | Required visual qualities | Final runtime finding | Result |
| --- | --- | --- | --- |
| Optimizer overview | Midnight/metallic ground, dark rounded hero and cards, subtle blue contours, compact chips, 2x2 cards, fixed detail column, readable active state, no bright/native surfaces | All four cards are simultaneously complete at the target size; cards, status surface, chips, right explanation panel and actions use the same low-fill rounded surface language. The active System card is cyan-led without making blue the card ground. | **PASS** |
| System Optimizer detail | Back action, dark metric cards, compact search/filter, dark table with selected state, restrained semantic colour, fixed rounded explanation panel and secondary technical disclosure | The final runtime has the required hierarchy. Search/filter/table remain dark and compact; the selected row is readable, and the primary explanation uses user-readable labels. Raw contract values are only exposed through the deliberate technical disclosure. | **PASS** |

### Explicit comparison dimensions

- **Colour and contrast:** midnight black remains dominant; cyan is an edge,
  active or meaning accent rather than a surface fill.
- **Surface allocation:** hero, metrics, four area cards, detail column and
  table are clearly separated by tonal depth and thin contours.
- **Typography:** Orbitron stays restricted to titles/technical headings;
  Inter remains the reading/table/control face.
- **Form language:** cards, hardware chips and actions use the same rounded,
  dark low-fill treatment; no white or bright native-looking control is shown.
- **Information hierarchy:** read-only status and real counts lead; area
  summaries follow; technical details remain secondary.

## Validation and final portable

- full build gate: **187 passed**;
- `python -m compileall -q src`: PASS;
- `git diff --check`: PASS before checkpoint;
- final Portable manifest: `dist/experimental/experimental-build.json`;
- final EXE SHA-256:
  `A721203F811CA56736132716F242552DF3B1D7B195B6903D17E3860B6FEF4D80`;
- final ZIP SHA-256:
  `78661DB219DEDE2B6EC08CC6899F32AF2D8C942B2FDCC50387337F52BB2B3D62`.

## Boundary

Stop after the two final Optimizer runtime captures.  No other page receives
these styles until an explicit follow-up request.  The only next action is a
human visual decision against the supplied references.
