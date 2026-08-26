# Integrated local V1 workflow

> **Legacy-compatible local workflow.** `iy-workflow` produces the separate
> `iy.replay/v1` artifact contract described below. It remains supported for
> its own local viewer/review artifacts, but is not the canonical V2 replay
> path and must not be used as a fallback for V2 consumers. The canonical
> `iy.replay/v2` path is `iy-demo-workflow`; see
> [`PRODUCT_ROADMAP_ALIGNMENT.md`](PRODUCT_ROADMAP_ALIGNMENT.md).

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

The launcher validates input paths and numeric limits, runs the idempotent
locked Python 3.13 setup without deleting an existing environment, executes the
workflow, validates the returned manifest, prints the exact local review URL
and then runs the loopback service in the foreground. `Ctrl+C` stops it. It does
not silently open a browser, hide logs, upload data, elevate privileges or apply
system/Optimizer changes.

`-SkipSetup` is intended only when the baseline was already prepared and
verified. `-NoServe` performs and validates the workflow but intentionally does
not start the HTTP service; it exists for reproducible smoke tests and artifact
generation.

`iy-workflow` connects the first usable local demo/replay path without applying
any system optimization or running a System Check:

1. analyze one explicit local demo into `iy.analysis/v1`;
2. export bounded Multi-Kill scenes into `iy.replay/v1`;
3. create a self-contained local 2D viewer;
4. create a reduced local review start page with data quality, scene list and
   viewer link;
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

The UI supports `unreviewed`, `reviewed`, `discarded` and `follow-up`, plus a
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
