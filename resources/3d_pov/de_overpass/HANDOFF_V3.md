# de_overpass — 3D POV Prep-to-Execution Handoff V3

## KNOWN GOOD
- Canonical runtime, asset gate, viewer, and generic builder are reusable AS_IS.
- 2D authority: `resources/map_overviews/maps/de_overpass.json`; origin `(-4831,1781)`, scale `5.2`, source/intrinsic rotation `0`, layers unresolved.
- Expected VPK: `<CS2_ROOT>\game\csgo\maps\de_overpass.vpk`.
- `maps/de_overpass/world_physics.vmdl_c` = `EXPECTED_FROM_SOURCE2_CONVENTION`; `.vrman_c`/`.vphys_c` = `UNKNOWN`.
- 3D transform `EXPECTED_IDENTITY_PENDING_LOCAL_VALIDATION`; replay source `UNKNOWN`.

## LOCAL ACTIONS
Hash/list VPK; prove resource; export GLB; build using `--map-id de_overpass`; record hashes/triangles/bounds; validate transform and height/collision plausibility; assess asset; recover/hash replay; generate canonical analysis/Replay V2; select controller state; run viewer; capture FP and fallback evidence.

## DO NOT RESEARCH AGAIN
Do not duplicate shared assets/runtime, infer 3D from overview, or fabricate map/replay evidence.

## MUST VERIFY LOCALLY
Build/VPK/resource; derivative evidence; transform; map assessment; demo/replay provenance; active camera state; screenshot; fail-closed result.

## STOP CONDITIONS
Missing source/resource, failed export/build, unverifiable bounds/transform, unavailable assessment, absent canonical replay camera state, proprietary staging, or runtime bypass.

## EXACT EXECUTION ORDER
1. Main. 2. VPK/hash/list. 3. Resource/GLB. 4. Derivative/evidence. 5. Transform. 6. Asset gate. 7. Demo/analysis/Replay V2. 8. Store/controller. 9. Viewer/screenshot. 10. Fail-closed/2D preserved.

## EXPECTED OUTPUT ARTIFACTS
`<LOCAL_ASSET_ROOT>\de_overpass\source\...`, bundle meshes/manifest/local verification; canonical analysis/Replay V2; smoke HTML/PNG/evidence JSON.

## FINAL VIEWER COMMAND TEMPLATE
```powershell
.\.venv\Scripts\python.exe .\tools\dev\Run-AnubisViewerDemo.py '<LOCAL_ASSET_ROOT>\de_overpass\bundle\manifest.json' '<CANONICAL_IY_REPLAY_V2_MANIFEST>' --round-number <ROUND> --tick <TICK> --player '<PLAYER_ID>' --two-d-output '<SMOKE_ROOT>\viewer-2d.html' --three-d-screenshot '<SMOKE_ROOT>\first-person.png' --seconds 12
```
