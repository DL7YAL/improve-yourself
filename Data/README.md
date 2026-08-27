# Data Authority

`Data/` is the central authority and reference point for project assets, blueprints, specifications, UI masters, test/reference data, and other maintained non-code project data.

## Rules

- `app/` remains the location for executable module code and program logic.
- Existing production/runtime paths remain unchanged until a deliberate, tested migration is approved.
- Existing files are copied into `Data/` when consolidating; source locations are not deleted or moved during the soft-reset phase.
- New or updated maintained reference data should be created or promoted through `Data/`.
- Replaced confirmed MASTER files are preserved in the relevant `Archive/` before a new MASTER becomes authoritative.
- Git/GitHub is the rollback mechanism for code. `Data/.../Archive` is the rollback/history mechanism for maintained MASTER/reference assets.
- Unknown or ambiguous files must be marked `UNRESOLVED`; do not promote them by filename or modification date alone.
- Demos are stored once in the neutral shared pool `Data/Demos/`; modules reference them from there instead of keeping duplicate module-specific demo copies.

See `DATA_MASTER_INDEX.md` for the current authority map.
