# de_ancient — 3D POV Prep-to-Execution Handoff V3

## KNOWN GOOD
- Runtime: `iy.replay/v2 → ReplayStore → ReplayController → ReplayRendererSession → PandaReplayRenderer`.
- Map gate: `iy.map_asset/v1`; 2D must remain available when 3D fails closed.
- Viewer and map-generic local builder are reusable AS_IS.
- 2D authority: `resources/map_overviews/maps/de_ancient.json`; origin `(-2953,2164)`, scale `5`, intrinsic rotation `0`, layers `UNRESOLVED`.
- Expected VPK: `<CS2_ROOT>\game\csgo\maps\de_ancient.vpk`.
- Resource candidates: `maps/de_ancient/world_physics.vmdl_c` = `EXPECTED_FROM_SOURCE2_CONVENTION`; `.vrman_c` and `.vphys_c` = `UNKNOWN`.
- 3D transform: `EXPECTED_IDENTITY_PENDING_LOCAL_VALIDATION`.
- Replay source: `PARTIAL`; historical source SHA-256 `c183dd61fc6a619f7af435d45eab374cd6f0097a7bd0da779971b15ef6746f7f`, canonical workflow and tick 3654 documented, local artifacts not committed.

## LOCAL ACTIONS
Locate/hash the VPK; list it with the installed VRF CLI; extract only the exact listed world-physics resource; export GLB; build the local derivative with `--map-id de_ancient`; measure bounds/hashes/triangles; verify transform; mark the manifest verified only after evidence; run `assess_map_asset()`; regenerate/revalidate the Ancient demo into canonical analysis and Replay V2; select an active player with position/yaw/pitch; run the existing viewer and capture evidence.

## DO NOT RESEARCH AGAIN
Do not redesign runtime, duplicate shared assets, infer 3D from 2D, create a map-specific parser/viewer/controller, or treat the historical hash as current local proof.

## MUST VERIFY LOCALLY
CS2 build; VPK path/hash/listing; extracted GLB; mesh hashes, triangle count and XYZ bounds; exact transform; manifest and `available` assessment; demo hash; analysis/Replay V2 paths; player ID; requested/resolved tick; position/yaw/pitch; FP screenshot; fail-closed 2D-only result.

## STOP CONDITIONS
Stop for missing/unhashable VPK, absent listed resource, failed GLB/derivative, missing bounds, non-available map assessment, no canonical replay camera state, proprietary artifact staging, or any runtime bypass.

## EXACT EXECUTION ORDER
1. Current main. 2. Build ID/VPK/hash. 3. VPK listing. 4. Exact resource. 5. GLB. 6. Local derivative. 7. Hashes/triangles/bounds. 8. Transform validation. 9. `iy.map_asset/v1`. 10. Demo recovery. 11. Analysis/Replay V2. 12. ReplayStore. 13. ReplayController. 14. Viewer. 15. FP screenshot. 16. Fail-closed test. 17. Confirm 2D remains usable.

## EXPECTED OUTPUT ARTIFACTS
`<LOCAL_ASSET_ROOT>\de_ancient\source\...`, `bundle\render_mesh.glb`, `bundle\visibility_mesh.tri`, `bundle\manifest.json`, `bundle\local-verification.json`, `<LOCAL_WORKFLOW_ROOT>\<DEMO_SHA>\analysis.json`, Replay V2 manifest/chunks, `smoke\viewer-2d.html`, `smoke\first-person.png`, `smoke\smoke-evidence.json`.

## FINAL VIEWER COMMAND TEMPLATE
```powershell
.\.venv\Scripts\python.exe .\tools\dev\Run-AnubisViewerDemo.py '<LOCAL_ASSET_ROOT>\de_ancient\bundle\manifest.json' '<CANONICAL_IY_REPLAY_V2_MANIFEST>' --round-number <ROUND> --tick <TICK> --player '<PLAYER_ID>' --two-d-output '<SMOKE_ROOT>\viewer-2d.html' --three-d-screenshot '<SMOKE_ROOT>\first-person.png' --seconds 12
```
