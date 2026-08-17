# Integrated local V1 workflow

## Supported Windows start

From the repository root, the supported local entry point is:

```powershell
.\tools\dev\Start-V1Review.ps1 -Demo '<match.dem.zst>'
```

For Mirage with the local Awpy radar:

```powershell
.\tools\dev\Start-V1Review.ps1 -Demo '<match.dem.zst>' `
  -Radar "$env:USERPROFILE\.awpy\maps\de_mirage.png" `
  -PosX -3230 -PosY 1713 -Scale 5
```

The launcher validates input paths and numeric limits, prepares the idempotent
locked Python 3.13 baseline and starts a loopback-only Analyzer V1 session.
It first shows the active profile and a read-only Demo-Preflight. Only the
explicit **Analyse starten** action runs the existing analysis/replay workflow.
`Ctrl+C` stops the local service. It does not silently open a browser, hide logs,
upload data, elevate privileges or apply system/Optimizer changes.

`-SkipSetup` is intended only when the baseline was already prepared and
verified. For non-interactive artifact generation, invoke `iy-workflow`
directly; the supported product launcher intentionally keeps the explicit
Preflight-before-Analyse step interactive.

`iy-workflow` executes the post-Preflight local demo/replay path without applying
any system optimization or running a System Check:

1. analyze one explicit local demo into `iy.analysis/v1`;
2. export bounded Multi-Kill scenes into `iy.replay/v1`;
3. create a self-contained local 2D viewer;
4. create a local review page with grouped review hints, Tactical-Replay links
   and a manual CS2 original-demo command for each relevant tick;
5. write an `iy.workflow/v1` manifest linking those artifacts.

```powershell
.venv\Scripts\iy-workflow '<match.dem.zst>' --output results\workflow
```

For a local Mirage radar resource:

```powershell
.venv\Scripts\iy-workflow '<match.dem.zst>' --output results\workflow `
  --radar "$env:USERPROFILE\.awpy\maps\de_mirage.png" `
  --pos-x -3230 --pos-y 1713 --scale 5
```

The run directory is keyed by the demo SHA-256 prefix. Its manifest records
only relative artifact paths, the source hash, local/no-change policy and the
mandatory human-review boundary. It does not contain the original demo path.

Open `review.html` as the human entry point. It summarizes findings without
copying raw JSON into the interface and links to the generated `viewer.html`.

For persistent user-authored review states and notes, start the loopback-only
local service and open the printed address:

```powershell
.venv\Scripts\iy-review-server '<run-directory>\workflow.json'
```

The UI supports `unreviewed`, `reviewed`, `discarded` and `clip-worthy`, plus a
note of at most 2,000 characters per known scene. It writes only
`review-state.json` (`iy.review_state/v1`) beside the generated artifacts.
Analysis and replay JSON remain unchanged. Requests are size-limited, scene- and
source-bound, same-origin checked, atomically written and accepted only through
`127.0.0.1`; the service never binds to the LAN.

`READY_FOR_REVIEW` means processing succeeded; it does not mean that a marker
is suspicious or that any player conclusion has been reached. The workflow
does not change Windows, apply an Optimizer profile, elevate privileges, upload
data or make an automated cheat verdict.

System diagnostics are deliberately a separate explicit path. For the
read-only System Check to Optimizer planning boundary, see
[`SYSTEM_CHECK_OPTIMIZER_BOUNDARY.md`](SYSTEM_CHECK_OPTIMIZER_BOUNDARY.md).
