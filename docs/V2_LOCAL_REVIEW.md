# V2 local review

`Start-V2Review.ps1` is the supported first replacement path for the isolated
legacy V1 review launcher. It runs the canonical `iy-demo-workflow`, validates
the resulting hash-bound `iy.demo_workflow/v1` manifest, lazily creates the
existing V2 Tactical HTML export, and serves only registered generated
artifacts on `127.0.0.1`.

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
