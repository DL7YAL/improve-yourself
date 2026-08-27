# Mirage 3D POV — Prep-to-Execution Handoff V2

**Static status:** `PREP_READY` after repository validation only. This is not `LOCAL_VERIFIED` and not `VISIBLE_PASS`.

## KNOWN GOOD

- Map ID: `de_mirage`.
- Canonical runtime is fixed: `iy.replay/v2 → ReplayStore → ReplayController → ReplayRendererSession → PandaReplayRenderer / existing renderer`.
- `iy.map_asset/v1` is the sole map-asset gate. A missing, mismatched, unverified, non-local-only, or hash-invalid asset must fail closed; 2D remains usable when 3D is unavailable.
- The current `tools/dev/Run-AnubisViewerDemo.py` is functionally map-generic despite its Anubis-only filename/title/help. It consumes local manifest/replay CLI arguments, obtains map ID from the canonical replay manifest for `assess_map_asset()`, and uses only `ReplayStore`, `ReplayController`, `ReplayRendererSession`, and `PandaReplayRenderer`. **Viewer reuse: `AS_IS`.** Do not create a second launcher, replay path, renderer, camera authority, or controller.
- `tools/dev/Build-LocalAnubisAsset.py` now requires `--map-id` and is reusable for Mirage. It preserves `build_local_derivative`, output names (`render_mesh.glb`, `visibility_mesh.tri`, `manifest.json`), `iy.map_asset/v1`, `local_only`, and unverified-by-default fail-closed behavior. **Local asset builder reuse: `MINIMAL_GENERALIZATION_REQUIRED`, completed by this prep.**
- Expected installed VPK path: `<CS2_ROOT>\game\csgo\maps\de_mirage.vpk` (`EXPECTED_FROM_SOURCE2_CONVENTION`; local installation remains authoritative).
- Resource classification:

  | Resource | Classification | Rule |
  | --- | --- | --- |
  | `maps/de_mirage/world_physics.vmdl_c` | `EXPECTED_FROM_SOURCE2_CONVENTION` | Primary candidate; list the local VPK before extraction. |
  | `maps/de_mirage/world_physics.vrman_c` | `UNKNOWN` | Do not assume or extract unless the local VPK lists it. |
  | `maps/de_mirage/world_physics.vphys_c` | `UNKNOWN` | Do not assume or extract unless the local VPK lists it. |

- Exact 2D authority is `resources/map_overviews/maps/de_mirage.json`: origin `(-3230, 1713)`, scale `5`, intrinsic clockwise rotation `0`, canvas top-left with positive world X right and positive world Y down. Layer/Z thresholds remain `UNRESOLVED`. This is not 3D transform evidence.
- 3D world→scene status is `EXPECTED_IDENTITY_PENDING_LOCAL_VALIDATION`: candidate scale `1.0`, rotation `[0,0,0]`, translation `[0,0,0]`; it is not verified for Mirage.
- Historical Mirage source SHA-256 is `2d70058ba006fecebf804e499a13ebeab97308804b433723c0657bf7810927a2`. It is Awpy/analysis provenance only, not current CS2 runtime acceptance: normal playback previously failed with `Failed to parse message`. `MIRAGE_REPLAY_SOURCE` is `PARTIAL`.

## LOCAL ACTIONS

1. Use the current `main` checkout and the static prep at `resources/3d_pov/de_mirage/prep.json`.
2. Locate CS2 and read the installed build ID. Keep machine-specific roots local.
3. Hash the exact VPK:

   ```powershell
   $vpk = '<CS2_ROOT>\game\csgo\maps\de_mirage.vpk'
   Get-FileHash -Algorithm SHA256 -LiteralPath $vpk
   ```

4. Inspect the locally installed VRF CLI help, then list the VPK. Command shape:

   ```powershell
   & '<SOURCE2VIEWER_CLI>' -i $vpk --vpk_list |
     Select-String -Pattern 'maps/de_mirage/world_physics\.(vmdl_c|vrman_c|vphys_c)'
   ```

5. Extract only the exact listed primary resource. Expected VRF export shape, subject to the installed CLI help:

   ```powershell
   & '<SOURCE2VIEWER_CLI>' `
     -i $vpk `
     -d `
     --gltf_export_format glb `
     -o '<LOCAL_ASSET_ROOT>\de_mirage\source' `
     -f 'maps/de_mirage/world_physics.vmdl_c'
   ```

6. Build only a local derivative; do not commit the GLB, mesh, VPK, or demo:

   ```powershell
   .\.venv\Scripts\python.exe .\tools\dev\Build-LocalAnubisAsset.py `
     '<EXTRACTED_WORLD_PHYSICS_GLB>' `
     '<LOCAL_ASSET_ROOT>\de_mirage\bundle' `
     --map-id de_mirage `
     --source-build-id '<INSTALLED_CS2_BUILD_ID>' `
     --source-vpk-sha256 '<DE_MIRAGE_VPK_SHA256>' `
     --reference-demo-sha256 '<MIRAGE_DEMO_SHA256>'
   ```

7. Measure and write a local-only `local-verification.json` next to `manifest.json`; record bounds, triangle count, hashes, transform evidence, and `assess_map_asset()` output. The builder records triangle count and an explicit `PENDING_LOCAL_MEASUREMENT` bounds status; it does not invent bounds.
8. Search configured/local demo roots for `.dem` and `.dem.zst`; SHA-256 each candidate. Use a candidate only after the existing canonical analysis/replay conversion identifies `de_mirage` and produces hash-bound `iy.analysis/v1` and `iy.replay/v2` artifacts.
9. Choose a smoke state only when the canonical resolved frame contains one active/alive selected player with position, yaw, and pitch.
10. Launch the existing viewer demo and retain local-only screenshots/evidence.

## DO NOT RESEARCH AGAIN

- Do not rediscover the replay authority, map gate, 2D metadata, local-only licensing boundary, or generic fallback assets/contracts in `resources/3d_pov/**`.
- Do not duplicate player/weapon proxies, semantic weapon mapping, camera fallback policy, environment fallback policy, render-ready schema, or licensing text for Mirage.
- Do not infer a 3D transform from the 2D overview.
- Do not use the old Mirage demo hash as a runtime acceptance source without reproducing its current local behavior.
- Do not try `vrman_c` or `vphys_c` unless the local VPK listing proves they exist.
- Do not create a map-specific viewer, parser, ReplayStore, ReplayController, camera, renderer, or V1 path.

## MUST VERIFY LOCALLY

`LOCAL_VERIFIED` requires all of the following local-only evidence:

- installed CS2 build ID;
- exact VPK path and SHA-256;
- exact VPK-listed resource path;
- extracted source GLB path;
- render mesh and visibility mesh SHA-256;
- visibility triangle count;
- geometry bounds min/max X/Y/Z;
- exact world→scene transform plus replay-to-mesh validation evidence;
- `iy.map_asset/v1` manifest path and `assess_map_asset()` result `available`;
- demo SHA-256;
- hash-bound `iy.analysis/v1` and `iy.replay/v2` provenance;
- player ID, requested/resolved tick, position, yaw, and pitch;
- first-person screenshot and third-person screenshot if the current viewer path supports it.

## STOP CONDITIONS

Return `BLOCKED` if the VPK is missing/unhashable; none of the listed world-physics resources exists; VRF cannot produce a valid GLB; the derivative contains no normal world-physics nodes; mesh hashes/triangle count/bounds cannot be recorded; `assess_map_asset()` is not `available`; a proprietary artifact would be committed/distributed; no runnable canonical Mirage replay with active position/yaw/pitch exists; or any solution would bypass the canonical runtime or introduce a parallel authority.

## EXACT EXECUTION ORDER

1. Current `main` checkout and this prep.
2. Installed CS2 build ID.
3. `de_mirage.vpk` path and SHA-256.
4. VPK listing.
5. Exact `world_physics` resource decision.
6. Single-resource extraction.
7. Source GLB export.
8. Local derivative (`render_mesh.glb`, `visibility_mesh.tri`, manifest).
9. Local bounds/hash/triangle evidence.
10. `iy.map_asset/v1` manifest assessment.
11. Mirage demo discovery and SHA-256.
12. Existing canonical analysis conversion to `iy.analysis/v1`.
13. Existing canonical replay conversion to `iy.replay/v2`.
14. `ReplayStore` load.
15. `ReplayController` seek/select/first-person state.
16. Existing viewer demo.
17. Local screenshots and smoke evidence.

## EXPECTED OUTPUT ARTIFACTS

```text
<LOCAL_ASSET_ROOT>\de_mirage\source\...
<LOCAL_ASSET_ROOT>\de_mirage\bundle\render_mesh.glb
<LOCAL_ASSET_ROOT>\de_mirage\bundle\visibility_mesh.tri
<LOCAL_ASSET_ROOT>\de_mirage\bundle\manifest.json
<LOCAL_ASSET_ROOT>\de_mirage\bundle\local-verification.json

<LOCAL_WORKFLOW_ROOT>\<MIRAGE_DEMO_SHA256>\analysis.json
<LOCAL_WORKFLOW_ROOT>\<MIRAGE_DEMO_SHA256>\<CANONICAL_REPLAY_V2_MANIFEST>
<LOCAL_WORKFLOW_ROOT>\<MIRAGE_DEMO_SHA256>\smoke\viewer-2d.html
<LOCAL_WORKFLOW_ROOT>\<MIRAGE_DEMO_SHA256>\smoke\first-person.png
<LOCAL_WORKFLOW_ROOT>\<MIRAGE_DEMO_SHA256>\smoke\third-person.png
<LOCAL_WORKFLOW_ROOT>\<MIRAGE_DEMO_SHA256>\smoke\smoke-evidence.json
```

## FINAL VIEWER COMMAND TEMPLATE

The existing launcher is functionally map-generic and is the required path:

```powershell
.\.venv\Scripts\python.exe .\tools\dev\Run-AnubisViewerDemo.py `
  '<LOCAL_ASSET_ROOT>\de_mirage\bundle\manifest.json' `
  '<CANONICAL_িয_REPLAY_V2_MANIFEST>' `
  --round-number <ROUND_NUMBER> `
  --tick <REQUESTED_TICK> `
  --player '<ACTIVE_PLAYER_ID>' `
  --two-d-output '<LOCAL_WORKFLOW_ROOT>\<MIRAGE_DEMO_SHA256>\smoke\viewer-2d.html' `
  --three-d-screenshot '<LOCAL_WORKFLOW_ROOT>\<MIRAGE_DEMO_SHA256>\smoke\first-person.png' `
  --seconds 12
```

This launcher currently captures the first-person 3D screenshot. Do not claim a third-person screenshot unless a separately selected canonical `analysis_third_person` run is supported and evidenced through the same `ReplayController`/`ReplayRendererSession` path.
