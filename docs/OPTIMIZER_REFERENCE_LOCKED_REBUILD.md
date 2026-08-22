# Optimizer Reference-Locked Rebuild

Status: **implemented and visually verified in the final Portable build** on
`dev/v1-foundation`.

## Reference lock

The two approved Optimizer references define the visible structure for this
slice.  The earlier linear native Optimizer page was not retained as a layout
constraint.  The existing `analyzer_shell.py` is the only desktop surface in
this checkout; no PyWebView or WebView2 host exists to reuse, so no framework
was added or replaced.

Existing System Check, Matrix Pack, Rule Pack, Evidence and read-only security
contracts remain the only data source.  The visible rework does not add a
recommendation, a hardware assertion, an Apply/Restore action or a second
engine.

## Implemented composition

### Optimizer overview

- persistent existing global sidebar;
- page title and four hardware chips in the header, projected only from the
  loaded local System Check;
- large `EMPFEHLUNGEN & STATUS` surface with real checked/already/conditional
  counts and the existing read-only System Check action;
- four actual Optimizer cards in a 2×2 raster: System, Graphics, Network and
  BIOS;
- a fixed right `DETAILS & ERKLÄRUNG` column; and
- no Evidence Matrix, Rule ID, Pack, Source-Type or Provenance wall in the
  default overview.

### System Optimizer detail

- explicit `← Zurück zur Übersicht` navigation;
- `System Optimizer` title and the same hardware chips;
- three status metrics;
- search field and status filter;
- a structured setting table with `Einstellung`, `Aktueller Zustand`,
  `Improve Empfehlung` and `Status` columns;
- selected row drives the persistent right detail column; and
- technical provenance/evidence is only reachable via the right-column
  `Technische Details` disclosure.

Table cells use a compact display label only where the real immutable contract
value is too long for the approved column width.  The complete original value
remains in the selected-row detail, so no fact is changed or hidden.

## Final runtime comparison — 2026-08-22

The final Portable build was opened at the normal Experimental resolution
(`1360×860` shell).  Runtime screenshots were captured directly from the
desktop application after the final package was created.

| Screen | Reference-locked required structure | Runtime finding | Result |
| --- | --- | --- | --- |
| Optimizer overview | Sidebar; title/header chips; large recommendation/status area; 2×2 domain card raster; fixed details column; no open evidence wall | All required structural areas are visible in the final Portable. The four areas are real cards with their own open action. Hardware values are actual loaded System Check values, and missing Network quality remains a `PREVIEW`, not a fabricated result. | **PASS** |
| System Optimizer | Back navigation; title; metrics; search/filter; structured setting list with four status columns; row-controlled fixed details column; technical data only in detail | All required areas are visible in the final Portable. Selecting the first actual row populates `DETAILS & ERKLÄRUNG`; `Technische Details` is a deliberate secondary action. No Apply/Restore path is rendered. | **PASS** |

The visible shell remains native Tk because that is the existing desktop
architecture.  It is not a pixel-for-pixel image clone; the acceptance result
is based on the binding page composition, hierarchy, active states, readable
data path and absence of the retired developer-style linear layout.

## Validation

- `python -m compileall -q src`: PASS
- `python -m pytest -q`: **187 passed**
- `git diff --check`: PASS
- final Portable build including manifest: PASS
- final EXE SHA-256:
  `E48214C3F41D61A64E52EC1030733C9FEF4AC5532F3958FBF0AF272B14E7F7F4`
- final ZIP SHA-256:
  `CFEF0F406CDCF768A17ABCFCCBFEB88495937A7781CE3B5E0C341C805786A1BB`

## Boundary after this slice

Stop after the two reference-locked Optimizer screenshots.  The next state is
`WAITING_FOR_TRISTAN`; no other page, UI, Optimizer capability, rule, evidence
contract, benchmark or infrastructure work follows from this document.
