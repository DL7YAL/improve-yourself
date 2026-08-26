# V2 local review

`Start-V2Review.ps1` is the supported first replacement path for the isolated
legacy V1 review launcher. It runs the canonical `iy-demo-workflow`, validates
the resulting hash-bound `iy.demo_workflow/v1` manifest, lazily creates the
existing V2 Tactical HTML export, and serves only registered generated
artifacts on `127.0.0.1`.

The launcher reports its four user-visible phases: local demo selected,
canonical V2 analysis/replay build, hash-bound workflow validation, and the
local review URL. Results are predictably placed below the chosen output root
in a folder named by the source-demo SHA-256 prefix.

```powershell
.\tools\dev\Start-V2Review.ps1 -Demo '<match.dem.zst>'
```

For a reproducible no-server smoke after workflow generation:

```powershell
.\tools\dev\Start-V2Review.ps1 -Demo '<match.dem.zst>' -NoServe
```

The launcher and `iy-v2-local-review` reject a workflow unless its schema,
status, source hash, parser contract, analysis, V2 ReplayStore/chunk hashes,
match data, validation report, flow and timeline all validate through the
existing V2 workflow gate. They do not parse a demo, create another store or
controller, accept V1 replay input, upload data, bind to LAN, or change system
settings. `iy-workflow` and `Start-V1Review.ps1` remain supported legacy paths
and are untouched by this replacement.

## Manual review checklist for Brix

1. Run the one-command launch with a local `.dem` or `.dem.zst` file.
2. Confirm the terminal reports the four phases and the local `127.0.0.1` URL.
3. Open `/review.html`; verify map, roster, selected analysis context and scene
   list are shown without any uploaded-data claim.
4. Open Tactical Replay from the review page; use scene, frame, speed and
   player navigation. The page must show the V2 shared-replay marker.
5. Re-run with `-NoServe`; confirm the printed `review.html` path is inside the
   SHA-256-named output folder and no server remains running.
6. Deliberately select an incomplete or modified V2 workflow with
   `iy-v2-local-review`; confirm it refuses to serve and reports whether the
   workflow status, source hash, or artifact/Replay V2 integrity check failed.
