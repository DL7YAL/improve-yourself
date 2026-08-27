# de_train — 3D POV Prep-to-Execution Handoff V3

## KNOWN GOOD
- Canonical runtime, asset gate, viewer, and builder are reusable AS_IS.
- 2D authority: `resources/map_overviews/maps/de_train.json`; origin `(-2308,2078)`, scale `4.082077`, intrinsic rotation `0`.
- `VERTICAL_STRUCTURE: KNOWN_PRESENT`; source 2D split exists, while `3D_LAYER_THRESHOLDS: UNRESOLVED_PENDING_LOCAL_GEOMETRY`.
- Expected VPK: `<CS2_ROOT>\game\csgo\maps\de_train.vpk`.
- `maps/de_train/world_physics.vmdl_c` = `EXPECTED_FROM_SOURCE2_CONVENTION`; `.vrman_c`/`.vphys_c` = `UNKNOWN`.
- 3D transform `EXPECTED_IDENTITY_PENDING_LOCAL_VALIDATION`; replay source `UNKNOWN`.

## LOCAL ACTIONS
Hash/list VPK; extract one proven resource; export GLB; build with `--map-id de_train`; capture hashes/triangles/bounds; validate identity and representative upper/lower positions; assess asset; recover canonical replay; select controller state; run viewer and fallback checks.

## DO NOT RESEARCH AGAIN
Do not convert the 2D altitude split into asserted 3D floors, duplicate runtime/assets, or invent demo evidence.

## MUST VERIFY LOCALLY
Generic asset/replay evidence plus multi-height geometry coverage, Z preservation, and representative collision/visibility plausibility.

## STOP CONDITIONS
Generic stop conditions plus absent vertical geometry, flattened/misaligned Z, inferred layer thresholds, or unavailable lower/upper replay samples.

## EXACT EXECUTION ORDER
1. Main. 2. VPK/hash/list. 3. Resource/GLB. 4. Derivative/evidence. 5. Vertical transform validation. 6. Asset gate. 7. Demo/analysis/Replay V2. 8. Store/controller. 9. Viewer/screenshot. 10. Fail-closed/2D preserved.

## EXPECTED OUTPUT ARTIFACTS
`<LOCAL_ASSET_ROOT>\de_train\source\...`, bundle meshes/manifest/local verification; canonical replay artifacts; `smoke\viewer-2d.html`, `first-person.png`, `vertical-level-evidence.json`, `smoke-evidence.json`.

## FINAL VIEWER COMMAND TEMPLATE
```powershell
.\.venv\Scripts\python.exe .\tools\dev\Run-AnubisViewerDemo.py '<LOCAL_ASSET_ROOT>\de_train\bundle\manifest.json' '<CANONICAL_IY_REPLAY_V2_MANIFEST>' --round-number <ROUND> --tick <TICK> --player '<PLAYER_ID>' --two-d-output '<SMOKE_ROOT>\viewer-2d.html' --three-d-screenshot '<SMOKE_ROOT>\first-person.png' --seconds 12
```
