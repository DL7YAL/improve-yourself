# de_vertigo — 3D POV Prep-to-Execution Handoff V3

## KNOWN GOOD
- Canonical runtime, asset gate, viewer, and generic builder are reusable AS_IS.
- 2D authority: `resources/map_overviews/maps/de_vertigo.json`; origin `(-3168,1762)`, scale `4`, intrinsic rotation `0`.
- `VERTICAL_STRUCTURE: KNOWN_PRESENT`; source 2D vertical sections exist, while `3D_LAYER_THRESHOLDS: UNRESOLVED_PENDING_LOCAL_GEOMETRY`.
- Expected VPK: `<CS2_ROOT>\game\csgo\maps\de_vertigo.vpk`.
- `maps/de_vertigo/world_physics.vmdl_c` = `EXPECTED_FROM_SOURCE2_CONVENTION`; `.vrman_c`/`.vphys_c` = `UNKNOWN`.
- 3D transform `EXPECTED_IDENTITY_PENDING_LOCAL_VALIDATION`; replay source `UNKNOWN`.

## LOCAL ACTIONS
Hash/list VPK; prove/extract exact resource; export GLB; build with `--map-id de_vertigo`; record derivative evidence; validate identity, large Z range, upper/lower coverage and collision; assess asset; recover canonical replay; drive Store/Controller/viewer; capture FP and fallback evidence.

## DO NOT RESEARCH AGAIN
Do not treat overview sections as 3D floor proof, flatten Z, duplicate runtime/assets, or invent replay provenance.

## MUST VERIFY LOCALLY
Generic evidence plus upper/lower geometry coverage, correct absolute Z placement, replay samples across levels, and no false inter-floor visibility.

## STOP CONDITIONS
Generic stops plus missing level geometry, Z collapse/offset, unsupported inferred thresholds, or inability to prove collision/visibility across vertical separation.

## EXACT EXECUTION ORDER
1. Main. 2. VPK/hash/list. 3. Resource/GLB. 4. Derivative/evidence. 5. Vertical identity/collision validation. 6. Asset gate. 7. Demo/analysis/Replay V2. 8. Store/controller. 9. Viewer/screenshot. 10. Fail-closed/2D preserved.

## EXPECTED OUTPUT ARTIFACTS
`<LOCAL_ASSET_ROOT>\de_vertigo\source\...`, bundle meshes/manifest/local verification; canonical replay artifacts; `smoke\viewer-2d.html`, `first-person.png`, `vertical-level-evidence.json`, `smoke-evidence.json`.

## FINAL VIEWER COMMAND TEMPLATE
```powershell
.\.venv\Scripts\python.exe .\tools\dev\Run-AnubisViewerDemo.py '<LOCAL_ASSET_ROOT>\de_vertigo\bundle\manifest.json' '<CANONICAL_IY_REPLAY_V2_MANIFEST>' --round-number <ROUND> --tick <TICK> --player '<PLAYER_ID>' --two-d-output '<SMOKE_ROOT>\viewer-2d.html' --three-d-screenshot '<SMOKE_ROOT>\first-person.png' --seconds 12
```
