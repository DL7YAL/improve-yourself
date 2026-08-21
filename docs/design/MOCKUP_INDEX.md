# Improve Yourself — Mockup Index

## Source status

The approved visual concept set exists as the **Improve Yourself Concept Preview** (10-page English preview, created 2026-08-17). The concept screens use example data. This index translates those approved screens into an implementation reference so agents do not need chat history to understand the target.

The original raster mockup exports are not yet stored as standalone files in this repository. Until they are added, this document plus `UI_SPEC.md` is the canonical implementation reference. Do **not** invent missing visual details.

## Approved screens

### 01 — Concept cover
Purpose: product presentation only. Not an application-screen contract.

### 03 — Home / Overview
Binding visual ideas:
- persistent dark left sidebar;
- compact header/brand area;
- module cards across the main content;
- progress/recent/quick-access panels below;
- dark navy surfaces with restrained blue accents.

Illustrative only:
- exact user profile, counters, scores and module metrics.

### 04 — Improve Analyzer
Binding visual ideas:
- analyzer as dense but ordered workspace;
- filters/profile/rules at top;
- overview/analysis results and comparison visible without becoming a raw spreadsheet;
- findings/scenes/patterns arranged in panels;
- lower supporting areas for strengths/weaknesses/next steps/rules where functionality exists.

Superseded by current product decisions:
- current neutral scene/review language;
- current profile/player-selection/rule-engine workflow;
- no fabricated scoring just to resemble the concept.

### 05 — Demo Analyzer
Binding visual ideas:
- demo library/list on left side of content;
- selected demo receives a clear summary and visual/context area;
- import/parser/analyze readiness visible;
- match overview and quick actions grouped below.

Current implementation should evolve this into the agreed Demo Preflight: map, rounds, teams, players, parser/data-quality status before analysis.

### 06 — 2D Tactical / Viewer
Binding visual ideas:
- map dominates the center;
- situation/round filters to the left;
- event timeline/details to the right;
- playback/timeline controls below map;
- direct action back to CS2 demo/tick;
- same global sidebar and application shell.

Existing tested Tactical Replay behavior is authoritative for zoom/pan/reset and functional details.

### 07 — My Improvement
Binding visual ideas for the later persistent-development view:
- category trend cards across top;
- strengths, weaknesses and next focus areas in a second row;
- concrete scenes connected to scores/trends below.

Do not implement fake longitudinal metrics in V1 if persistence/data is not ready.

### 08 — Improve Optimizer
Binding visual ideas:
- safety/transparency statement prominent;
- system overview cards near top;
- optimization/recommendation cards below;
- evidence/details accessible;
- rollback/safety concept visible only where functionally supported;
- same dark shell.

Current read-only System Check/Optimizer boundaries override old illustrative apply actions.

### 09 — Improve Benchmark
Binding visual ideas:
- start/control area;
- current result and frametime/performance visualization;
- benchmark/map context;
- scene/test sequence;
- prior benchmark history where backed by data.

Benchmark runtime itself is a separate workstream.

## Missing standalone references

The following current tabs may not have a dedicated original concept-preview image:
- Rules
- Reports
- Settings
- dedicated System Check
- 3D/POV

For these, derive layout from the global shell and closest approved module as specified in `UI_SPEC.md`. Do not create a competing visual language.

## Future asset drop

When standalone approved images are available, store them under:

`docs/design/mockups/`

Recommended names:
- `home-overview.png`
- `improve-analyzer.png`
- `demo-analyzer.png`
- `2d-tactical-viewer.png`
- `my-improvement.png`
- `improve-optimizer.png`
- `improve-benchmark.png`

Adding those images should not alter the design decisions documented here; they are visual evidence for the same approved direction.
