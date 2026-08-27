# de_dust2 — 3D POV Prep-to-Execution Handoff V3

## KNOWN GOOD
- Runtime: `iy.replay/v2 → ReplayStore → ReplayController → ReplayRendererSession → PandaReplayRenderer`; gate: `iy.map_asset/v1`; viewer/builder reuse AS_IS.
- 2D authority: `resources/map_overviews/maps/de_dust2.json`; origin `(-2476,3239)`, scale `4.4`, intrinsic rotation `0`. Source `rotate=1` is presentation provenance only. Layers unresolved.
- Expected VPK: `<CS2_ROOT>\game\csgo\maps\de_dust2.vpk`.
- `maps/de_dust2/world_physics.vmdl_c` is `EXPECTED_FROM_SOURCE2_CONVENTION`; `.vrman_c` and `.vphys_c` are `UNKNOWN` pending local listing.
- 3D transform: `EXPECTED_IDENTITY_PENDING_LOCAL_VALIDATION`. Replay source: `UNKNOWN`.

## LOCAL ACTIONS
Hash/list the VPK; prove and extract one exact physics resource; export GLB; run the generic builder with `--map-id de_dust2`; record mesh evidence and validate transform; assess the manifest; discover/hash a Dust2 demo; run existing canonical analysis/Replay V2; select canonical active position/yaw/pitch; run viewer; capture FP and fail-closed evidence.

## DO NOT RESEARCH AGAIN
Do not reinterpret source rotate=1 as 3D rotation, duplicate shared assets/runtime, invent replay provenance, or create map-specific implementations.

## MUST VERIFY LOCALLY
Build/VPK/hash/resource; GLB and derivative hashes; triangles/bounds; transform; manifest assessment; demo/analysis/Replay V2 provenance; player/tick/camera state; screenshot; 2D-only fallback.

## STOP CONDITIONS
Stop on missing source, unknown resource, export/build failure, unavailable assessment, absent canonical replay state, staged proprietary data, or runtime bypass.

## EXACT EXECUTION ORDER
1. Main. 2. VPK/hash. 3. Listing. 4. Resource. 5. GLB. 6. Derivative. 7. Evidence. 8. Transform. 9. Asset gate. 10. Demo. 11. Analysis/Replay V2. 12. Store. 13. Controller. 14. Viewer. 15. Screenshot. 16. Fail-closed. 17. Preserve 2D.

## EXPECTED OUTPUT ARTIFACTS
`<LOCAL_ASSET_ROOT>\de_dust2\source\...`, `bundle\render_mesh.glb`, `visibility_mesh.tri`, `manifest.json`, `local-verification.json`; `<LOCAL_WORKFLOW_ROOT>\<DEMO_SHA>\analysis.json`, Replay V2, `smoke\viewer-2d.html`, `first-person.png`, `smoke-evidence.json`.

## FINAL VIEWER COMMAND TEMPLATE
```powershell
.\.venv\Scripts\python.exe .\tools\dev\Run-AnubisViewerDemo.py '<LOCAL_ASSET_ROOT>\de_dust2\bundle\manifest.json' '<CANONICAL_IY_REPLAY_V2_MANIFEST>' --round-number <ROUND> --tick <TICK> --player '<PLAYER_ID>' --two-d-output '<SMOKE_ROOT>\viewer-2d.html' --three-d-screenshot '<SMOKE_ROOT>\first-person.png' --seconds 12
```
