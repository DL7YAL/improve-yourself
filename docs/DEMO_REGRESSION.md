# Demo Analyzer regression strategy

Real CS2 demos remain local test inputs. Raw demos, player identities, voice
content, and full analysis results are not committed to this repository.

## Local run

Prepare the locked Python 3.13 baseline, then provide one explicit demo path:

```powershell
.\tools\dev\Setup-V1.ps1
.\tools\dev\Run-DemoRegression.ps1 -Demo 'D:\private\match.dem.zst'
```

The regression output is written below the ignored `results/regression/`
directory, namespaced by the first 12 characters of the source SHA-256. The
harness runs `iy-analyze`, validates the complete `iy.analysis/v1` contract and
domain invariants, and writes a compact `regression-summary.json` without
player names or kill details.

## Required evidence

Record only non-sensitive aggregate evidence in the Codex handoff:

- source SHA-256, not the original filename;
- map and tickrate;
- aggregate kill and round-wide multi-kill counts;
- data-quality status;
- available and missing event channels;
- warning count and whether the material footstep limitation is disclosed;
- command outcome and validator outcome.

Missing `footsteps`/`player_sound` is a source-capability limitation, not proof
that a demo is damaged. A valid limited result must list `footsteps` as missing,
set quality to `limited` or `not_assessable`, and include the material German
footstep warning. Automated markers remain review cues and never cheat proof.

## Source-controlled fixtures

Do not add a real match merely to make regression convenient. A future binary
fixture may be committed only when it is deliberately generated or licensed,
contains no private voice or player data, is small enough for normal Git use,
and has an explicit provenance note. Until then, unit tests use synthetic
`iy.analysis/v1` payloads while end-to-end parsing uses an explicitly supplied
local demo.
