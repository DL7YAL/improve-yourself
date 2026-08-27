# de_nuke — 3D POV Prep-to-Execution Handoff V3

## KNOWN GOOD
- Canonical runtime and `iy.map_asset/v1` gate are fixed; viewer/builder reuse AS_IS.
- 2D authority: `resources/map_overviews/maps/de_nuke.json`; origin `(-3453,2887)`, scale `7`, intrinsic rotation `0`.
- `VERTICAL_STRUCTURE: KNOWN_PRESENT`; 2D threshold split is documented, but `3D_LAYER_THRESHOLDS: UNRESOLVED_PENDING_LOCAL_GEOMETRY`.
- Expected VPK: `<CS2_ROOT>\game\csgo\maps\de_nuke.vpk`.
- `maps/de_nuke/world_physics.vmdl_c` = `EXPECTED_FROM_SOURCE2_CONVENTION`; `.vrman_c`/`.vphys_c` = `UNKNOWN`.
- 3D transform `EXPECTED_IDENTITY_PENDING_LOCAL_VALIDATION`; replay source `UNKNOWN`. Benchmark references are not canonical replay provenance.

## LOCAL ACTIONS
Hash/list VPK; prove/extract exact physics resource; export GLB; build with `--map-id de_nuke`; record hashes/triangles/full XYZ bounds; explicitly sample replay positions on both vertical levels; validate transform and visibility; assess asset; recover canonical Nuke replay; run viewer and fail-closed checks.

## DO NOT RESEARCH AGAIN
Do not treat 2D altitude thresholds as 3D floors, reuse benchmark camera/map data as Replay V2, duplicate runtime, or invent level selection.

## MUST VERIFY LOCALLY
All generic evidence plus upper/lower replay samples, vertical geometry coverage, no Z flattening, and collision/visibility plausibility across levels.

## STOP CONDITIONS
Generic stop conditions plus any missing lower/upper geometry, incorrect Z placement, inferred floor thresholds, or benchmark/runtime crossover.

## EXACT EXECUTION ORDER
1. Main. 2. VPK/hash/list. 3. Resource/GLB. 4. Derivative/evidence. 5. Identity/Z validation across levels. 6. Asset gate. 7. Demo/analysis/Replay V2. 8. Store/controller. 9. Viewer/FP screenshot. 10. Fail-closed/2D preserved.

## EXPECTED OUTPUT ARTIFACTS
`<LOCAL_ASSET_ROOT>\de_nuke\source\...`, bundle meshes/manifest/local verification; replay artifacts; `smoke\viewer-2d.html`, `first-person.png`, `vertical-level-evidence.json`, `smoke-evidence.json`.

## FINAL VIEWER COMMAND TEMPLATE
```powershell
.\.venv\Scripts\python.exe .\tools\dev\Run-AnubisViewerDemo.py '<LOCAL_ASSET_ROOT>\de_nuke\bundle\manifest.json' '<CANONICAL_IY_REPLAY_V2_MANIFEST>' --round-number <ROUND> --tick <TICK> --player '<PLAYER_ID>' --two-d-output '<SMOKE_ROOT>\viewer-2d.html' --three-d-screenshot '<SMOKE_ROOT>\first-person.png' --seconds 12
```
