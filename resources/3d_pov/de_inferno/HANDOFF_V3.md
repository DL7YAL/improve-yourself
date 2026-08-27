# de_inferno — 3D POV Prep-to-Execution Handoff V3

## KNOWN GOOD
- Canonical runtime and `iy.map_asset/v1` gate are fixed; current viewer and builder are reusable AS_IS.
- 2D authority: `resources/map_overviews/maps/de_inferno.json`; origin `(-2087,3870)`, scale `4.9`, intrinsic rotation `0`, no source rotate flag, layers unresolved.
- Expected VPK: `<CS2_ROOT>\game\csgo\maps\de_inferno.vpk`.
- `maps/de_inferno/world_physics.vmdl_c` = `EXPECTED_FROM_SOURCE2_CONVENTION`; `.vrman_c`/`.vphys_c` = `UNKNOWN`.
- 3D transform: `EXPECTED_IDENTITY_PENDING_LOCAL_VALIDATION`; replay source `UNKNOWN`.

## LOCAL ACTIONS
Locate/hash/list VPK; prove exact resource; export only that GLB; build derivative using `--map-id de_inferno`; record evidence and validate transform; assess asset; recover/hash Inferno demo; generate canonical analysis/Replay V2; select active camera state through controller; run viewer; capture FP and fail-closed evidence.

## DO NOT RESEARCH AGAIN
Do not duplicate contracts/assets/runtime, infer transform from overview, guess resource extension, or fabricate replay state.

## MUST VERIFY LOCALLY
Build/VPK/resource/hash; GLB; derivative hashes/triangles/bounds; transform; manifest and assessment; demo/analysis/replay hashes; player/ticks/position/yaw/pitch; FP screenshot and 2D fallback.

## STOP CONDITIONS
Missing/unhashable VPK, no exact resource, invalid export, no normal physics nodes, missing evidence, unavailable asset, no canonical replay state, proprietary staging, or runtime bypass.

## EXACT EXECUTION ORDER
1. Main. 2. VPK/hash. 3. Listing. 4. Resource. 5. GLB. 6. Derivative. 7. Evidence. 8. Transform. 9. Asset gate. 10. Demo. 11. Analysis/Replay V2. 12. Store. 13. Controller. 14. Viewer. 15. Screenshot. 16. Fail-closed. 17. Preserve 2D.

## EXPECTED OUTPUT ARTIFACTS
`<LOCAL_ASSET_ROOT>\de_inferno\source\...`, bundle meshes/manifest/local verification; `<LOCAL_WORKFLOW_ROOT>\<DEMO_SHA>\analysis.json`, Replay V2, `smoke\viewer-2d.html`, `first-person.png`, `smoke-evidence.json`.

## FINAL VIEWER COMMAND TEMPLATE
```powershell
.\.venv\Scripts\python.exe .\tools\dev\Run-AnubisViewerDemo.py '<LOCAL_ASSET_ROOT>\de_inferno\bundle\manifest.json' '<CANONICAL_IY_REPLAY_V2_MANIFEST>' --round-number <ROUND> --tick <TICK> --player '<PLAYER_ID>' --two-d-output '<SMOKE_ROOT>\viewer-2d.html' --three-d-screenshot '<SMOKE_ROOT>\first-person.png' --seconds 12
```
