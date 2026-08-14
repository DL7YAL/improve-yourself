# Improve Yourself

Private development repository for a CS2-focused system analysis, optimization, demo analysis and tactical replay platform.

## Status

**V1 foundation — in development**

The current priority is to consolidate the existing prototypes into one clean, reliable V1 codebase. Older local builds remain reference material and are not treated as active branches.

## V1 modules

- `system_check` — hardware, drivers, Windows and anti-cheat readiness checks
- `optimizer` — curated, reversible performance-oriented configuration
- `demo_analyzer` — CS2 demo parsing and scene analysis
- `tactical_replay` — visual reconstruction of relevant scenes

## Project principles

- Reliability before feature count
- Clear recommendations instead of data overload
- Few deliberate user choices
- No unnecessary overclocking or risky tweaks
- Changes should be reversible whenever possible
- Analysis before raw statistics
- Tactical Replay uses its own analysis-oriented sound language
- V2/V3 ideas are documented, not silently pulled into V1

## Repository structure

```text
improve-yourself/
├── app/
│   ├── system_check/
│   ├── optimizer/
│   ├── demo_analyzer/
│   └── tactical_replay/
├── assets/
├── config/
├── docs/
├── tests/
├── tools/
├── .gitignore
├── CHANGELOG.md
└── README.md
```

## Development workflow

- `main` = stable, reviewable project state
- `dev/v1-foundation` = active V1 consolidation branch
- New work is developed on short-lived `feature/...`, `fix/...` or `docs/...` branches when useful
- Changes reach `main` through a pull request once the branch is in a coherent state
- Do not commit generated reports, demos, caches, virtual environments, secrets or machine-specific files

See [`docs/BRANCHING.md`](docs/BRANCHING.md) for the branch policy and [`docs/ROADMAP.md`](docs/ROADMAP.md) for the product roadmap.

## Current next step

Inventory the saved prototypes, classify each component as **keep / revise / discard / defer**, and move only the approved parts into the new V1 development branch.

## Demo Analyzer V1 foundation

Local, traceable processing of CS2 demos. Automated markers are review cues and
never proof of cheating.

### Start

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\iy-analyze "D:\Path\match.dem.zst" --output results
```

The importer supports `.dem`, `.dem.zst`, and `.dem.bz2`. Compressed files are
materialized only temporarily and deleted automatically after analysis.

### V1 analysis rules

- A multi-kill is at least three kills by one player across the entire round.
- Missing optional event channels must not abort parsing.
- Missing footsteps are disclosed as a material data limitation.
- Results use the versioned `iy.analysis/v1` schema.
- Original demos and voice content are not stored in analysis results.
