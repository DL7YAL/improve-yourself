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

The saved prototypes are inventoried in
[`docs/PROTOTYPE_INVENTORY.md`](docs/PROTOTYPE_INVENTORY.md). The independent
[`System Check / Optimizer boundary`](docs/SYSTEM_CHECK_OPTIMIZER_BOUNDARY.md)
keeps read-only machine evidence separate from demo/replay work.
`iy-system-check` can explicitly produce the primary planning input for the
future Optimizer through `iy-optimizer-input`; `iy-workflow` remains the
separate demo analysis, bounded replay, local viewer and review path. The next
supported replay start is `tools/dev/Start-V1Review.ps1`; it also provides the
reduced review surface and source-bound local review-state persistence.
Optimizer apply/restore remains a separate later safety boundary.

## Demo Analyzer V1 foundation

Local, traceable processing of CS2 demos. Automated markers are review cues and
never proof of cheating.

### Start

```powershell
.\tools\dev\Setup-V1.ps1
.venv\Scripts\iy-analyze "D:\Path\match.dem.zst" --output results
```

The setup helper requires Python 3.13, installs the exact versions from
`requirements.lock`, installs this project in editable mode without resolving a
second dependency set, checks dependency consistency, runs the automated tests,
and smoke-tests the CLI. It reuses a valid existing `.venv` and refuses an
existing environment created with another Python version instead of deleting or
replacing it. Use `-SkipTests` only when a separate test run is intentionally
scheduled.

The importer supports `.dem`, `.dem.zst`, and `.dem.bz2`. Compressed files are
materialized only temporarily and deleted automatically after analysis.

For a repeatable real-demo regression that keeps raw matches and detailed
results local, see [`docs/DEMO_REGRESSION.md`](docs/DEMO_REGRESSION.md).

### V1 analysis rules

- A multi-kill is at least three kills by one player across the entire round.
- Missing optional event channels must not abort parsing.
- Missing footsteps are disclosed as a material data limitation.
- Results use the versioned `iy.analysis/v1` schema.
- Original demos and voice content are not stored in analysis results.
