# Mirage 3D POV — Prep-to-Execution Handoff V2

## KNOWN GOOD

- Canonical runtime is fixed: `iy.replay/v2 -> ReplayStore -> ReplayController -> ReplayRendererSession -> existing renderer`. This package owns neither parsing, tick advancement, selection, nor replay frames.
- The 3D asset authority is only `iy.map_asset/v1`; no map asset means explicit 3D unavailable.
- The verified 2D authority is `resources/map_overviews/maps/de_mirage.json`: upper-left world origin `(-3230, 1713)`, scale `5` world units/pixel, intrinsic clockwise rotation `0`, `+X` right and `+Y` down in canvas after inversion. It has no verified vertical/layer rule. It is **not** 3D transform evidence.
- Expected installed source path: `<CS2_ROOT>/game/csgo/maps/de_mirage.vpk` (`EXPECTED_FROM_SOURCE2_CONVENTION`). Expected physics resource candidates are `maps/de_mirage/world_physics.vrman_c` and `maps/de_mirage/world_physics.vmdl_c`; neither is locally verified here. A `vphys_c` alternative is `UNKNOWN` and must not be invented.
- VRF/Source2Viewer supports VPK browsing plus Source 2 model export. An external CS2 example records the targeted form `Source2Viewer-CLI.exe -i <vpk> -d --gltf_export_format glb -o <out> -f maps/de_mirage/world_physics.vmdl_c`; verify the installed CLI's `--help` before use.
- Existing `tools/dev/Build-LocalAnubisAsset.py` is **not directly reusable**: positional GLB/output and provenance arguments are generic, but its description, `map_id`, and source description are hard-coded to Anubis. Smallest Beast change: add required `--map-id`, validate a conservative map-ID token, use it only in manifest fields/text, and rename it to a map-generic builder. Do not alter protected runtime.
- A historical Mirage local demo provenance is documented: SHA-256 `2d70058ba006fecebf804e499a13ebeab97308804b433723c0657bf7810927a2`, map `de_mirage`, 30 rounds, 97 scenes, first tick `6352`, `iy.analysis/v1` compatibility evidence. The demo and generated artifacts are ignored/local, not repository files. It is not CS2 runtime evidence (`Failed to parse message`), no committed `iy.replay/v2` regression output is found, and no active player/position/yaw/pitch visual-smoke reference is recorded. `MIRAGE_REPLAY_SOURCE: PARTIAL`.

## LOCAL ACTIONS

1. Locate `<CS2_ROOT>` and prove `<CS2_ROOT>/game/csgo/maps/de_mirage.vpk` exists.
2. Record installed CS2 build ID from the local install and calculate `Get-FileHash -Algorithm SHA256 <VPK>`.
3. Use the installed VRF tool to list the VPK and save a local text listing. Confirm the exact `world_physics.vrman_c` and `world_physics.vmdl_c` paths; only consider `vphys_c` when it appears in that listing.
4. Extract/export only the confirmed `world_physics.vmdl_c` to a local GLB; no VPK, source resource, GLB, TRI, screenshot, demo, or manifest may be committed.
5. Apply the minimal builder generalization above, then build `render_mesh.glb`, `visibility_mesh.tri`, and `manifest.json` into an ignored local directory. Record SHA-256, triangle count, bounds, identity-transform test result, and `assess_map_asset()` result.
6. Recover a Mirage replay locally: search configured/local demo roots, hash every candidate, prefer the documented hash if present, and use the existing canonical analysis conversion plus `tools/dev/Run-ReplayV2Regression.ps1`. Require a selected active player with position, yaw and pitch at the smoke tick.

## DO NOT RESEARCH AGAIN

- Do not derive a 3D transform from the overview. 3D status is `EXPECTED_IDENTITY_PENDING_LOCAL_VALIDATION`.
- Do not create a parser, store, controller, DataHub, or renderer-owned playback path.
- Do not copy the CC0 player/weapon/material/texture assets or duplicate semantic/camera/environment policies; `render_ready.json` references the shared established assets/contracts.
- Do not use historical hashes as current build proof, and do not substitute Anubis geometry/replay data.

## MUST VERIFY LOCALLY

Required evidence contract before `LOCAL_VERIFIED`: installed CS2 build ID; VPK path; VPK SHA-256; saved VPK listing; exact physics resource path; extracted source GLB path and SHA-256; render mesh SHA-256; visibility mesh SHA-256; triangle count; geometry bounds; transform; ignored local manifest path; `assess_map_asset()` result; demo SHA-256; analysis path; replay-v2 manifest/summary; active player ID; tick; position; yaw; pitch; renderer screenshot(s).

## STOP CONDITIONS

BLOCKED if the VPK is absent; build ID/hash cannot be recorded; required `world_physics.vmdl_c` is absent; only an unproven alternate resource exists; VRF cannot export the confirmed resource; builder cannot produce a fail-closed local manifest; `assess_map_asset()` is not `available`; no matching/usable Mirage demo can provide active position+yaw+pitch; replay-v2 validation fails; or visual smoke has no renderer evidence. Do not claim `LOCAL_VERIFIED` or `VISIBLE_PASS` in any of those cases.

## EXACT EXECUTION ORDER

1. `CS2 root -> build ID -> de_mirage.vpk SHA-256`.
2. `VPK listing -> confirm world_physics.vrman_c + world_physics.vmdl_c`.
3. `Extract only world_physics.vmdl_c -> GLB -> record source GLB hash`.
4. `Minimal map-ID builder generalization -> render_mesh.glb + visibility_mesh.tri + manifest.json`.
5. `Hash/count/bounds/transform -> assess_map_asset() == available`.
6. `Demo-root search -> hash/provenance -> canonical analysis -> replay-v2 regression`.
7. `Choose active player/tick with position+yaw+pitch -> existing ReplayController/ReplayRendererSession smoke -> screenshots`.

## EXPECTED OUTPUT ARTIFACTS

All local-only/ignored:

```text
results/local-map-assets/de_mirage/<build-id>-<vpk-sha12>/manifest.json
results/local-map-assets/de_mirage/<build-id>-<vpk-sha12>/render_mesh.glb
results/local-map-assets/de_mirage/<build-id>-<vpk-sha12>/visibility_mesh.tri
results/local-map-assets/de_mirage/<build-id>-<vpk-sha12>/evidence.json
results/replay-v2/<demo-sha12>/replay-v2.json
results/replay-v2/<demo-sha12>/regression-summary.json
results/3d-pov-smoke/de_mirage/<demo-sha12>/tick-<tick>-fp.png
results/3d-pov-smoke/de_mirage/<demo-sha12>/tick-<tick>-tp.png
```

## FINAL SMOKE COMMAND TEMPLATE

```powershell
# Existing canonical replay-v2 conversion/validation.
.\tools\dev\Run-ReplayV2Regression.ps1 -Demo '<LOCAL_MIRAGE_DEMO>' -Analysis '<LOCAL_IY_ANALYSIS_V1_JSON>' -OutputRoot 'results\replay-v2'

# After Beast's minimal --map-id generalization (placeholder paths are genuinely local).
.\.venv\Scripts\python.exe .\tools\dev\Build-LocalMapAsset.py '<EXTRACTED_WORLD_PHYSICS_GLB>' '<LOCAL_MAP_ASSET_OUTPUT_DIR>' --map-id de_mirage --source-build-id '<CS2_BUILD_ID>' --source-vpk-sha256 '<DE_MIRAGE_VPK_SHA256>' --reference-demo-sha256 '<MIRAGE_DEMO_SHA256>'

# Existing renderer/session smoke must consume the generated iy.map_asset/v1 manifest and canonical replay-v2 manifest; use the project’s current Beast-owned smoke entry point, not a second replay path.
<EXISTING_RENDERER_SMOKE_ENTRYPOINT> --map-manifest '<LOCAL_MAP_ASSET_MANIFEST>' --replay-manifest '<LOCAL_REPLAY_V2_MANIFEST>' --player-id '<ACTIVE_PLAYER_ID>' --tick <RESOLVED_TICK> --view first_person --screenshot '<FP_PNG>'
```

State labels: `PREP_READY` is this repository metadata; `LOCAL_VERIFIED` requires the complete local evidence contract; `VISIBLE_PASS` additionally requires reviewed renderer screenshots.
