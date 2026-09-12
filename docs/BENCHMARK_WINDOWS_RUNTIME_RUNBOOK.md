# Windows runbook — benchmark world runtime acceptance

This runbook closes only the normal-viewer runtime and visual-evidence gates
for `iy-benchmark/v1.2-candidate.2`. Windows is the runtime authority. Linux/WSL
is only the SSH/Git connection and must not be reported as CS2 runtime proof.

## 1. Prepare the Windows checkout

From a Windows terminal in the repository checkout:

```powershell
git fetch --prune origin
git switch codex/benchmark-v1.2-runtime-evidence
git pull --ff-only
git status --short --branch
```

The worktree must be clean and the branch must match
`origin/codex/benchmark-v1.2-runtime-evidence`.

Verify the installed source without deploying:

```powershell
.\tools\benchmark\Sync-BenchmarkAddon.ps1
```

Expected result: both manifest sources match and the command exits `0`. Do not
use `-Deploy` when the read-only comparison already passes.

## 2. Run once without interruption

Launch `improve_yourself_benchmark` through the CS2 Workshop Tools project
selector and the normal CS2 viewer. Start the map exactly once. Do not press
Hammer Run again, reload the script, restart the map or change level until the
measured end marker appears.

Nominal timeline from the first `READY` line:

| Elapsed | Phase |
| ---: | --- |
| 0–3 s | cinema boot delay |
| 3–67 s | complete 64-second warmup |
| 67–70 s | fixed cooldown |
| 70–134 s | complete 64-second measured pass |

Allow at least 140 seconds after `READY`. The required terminal line is:

```text
[IYBENCH] PASS_END type=measured runtime_status=complete measurement_status=unverified
```

The final `measurement_status=unverified` is correct without a separately
proven frame collector.

## 3. Capture the world evidence

Keep raw screenshots or a local lossless recording outside Git. Required
views:

1. cinema boot-delay view from behind the audience;
2. `ancient_b/water_reflection` at 27 seconds;
3. `ancient_b/red_room` at 38 seconds;
4. `inferno_apps_a/stairs` at 48 seconds;
5. `inferno_apps_a/apps_details` at 53 seconds.

The marker times are relative to the start of each 64-second pass, not to the
initial `READY`. A local recording may be used to select the exact marked
frames afterward. Do not add screenshot commands to the measured controller;
disk I/O would alter the workload.

For the audience reproducibility gate, repeat a clean map start and capture the
same cinema view a second time. Compare bot count, order, transforms, facing
and animation state. The current static placement can be reviewed, but the
assignment remains `PARTIAL` until the separate one-bot cheer gate succeeds.

## 4. Validate and hash on Windows

Save or paste the full VConsole output or only its newest uninterrupted
segment, beginning at `READY`, into a local UTF-8 text file. The validator
accepts the authoritative `cs_script` channel and ignores quoted `Console`
duplicates. Then run:

```powershell
py -3.13 .\tools\benchmark\validate_benchmark_runtime.py '<LOG_PATH>' --json
```

Expected exit code and result: `0`, `status=PASS`, 39 canonical contract
events, `runtime_status=complete`, `measurement_status=unverified`, and no
errors.

After all five capture files exist:

```powershell
py -3.13 .\tools\benchmark\collect_benchmark_evidence.py `
  --log '<LOG_PATH>' `
  --intro '<CAPTURE_DIR>\intro.png' `
  --ancient-water '<CAPTURE_DIR>\ancient-water-27.png' `
  --ancient-red-room '<CAPTURE_DIR>\ancient-red-room-38.png' `
  --inferno-stairs '<CAPTURE_DIR>\inferno-stairs-48.png' `
  --inferno-apps '<CAPTURE_DIR>\inferno-apps-53.png' `
  --output '<EVIDENCE_DIR>\benchmark-world-evidence.json'
```

The output manifest intentionally leaves every capture `UNREVIEWED`. Inspect
the images before assigning `WORLD PASS`, `WORLD NEEDS WORK` or `BLOCKED`.

## 5. Repository handoff

Commit only safe textual evidence: source hashes, log/capture SHA-256 values,
marker correlation, visual findings and the final status. Never commit raw
logs, screenshots, videos, compiled VPKs, Valve payloads, credentials or
private absolute paths. Push the working branch before starting another large
slice when the remaining Codex usage capacity is low.
