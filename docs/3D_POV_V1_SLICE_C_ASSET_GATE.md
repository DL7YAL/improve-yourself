# 3D / POV V1 — Slice C Anubis Asset Gate

Status: `SLICE_C_COMPLETE — local-only route`

Date: 2026-08-20

Tristan authorized the recommended current-build local-only route with `next`. No map geometry is committed or distributed. No renderer work began during this gate.

## Candidate inventory

### Awpy triangle candidate

- local path class: user-local Awpy cache, not repository content;
- source: Awpy 2.0.2 downloadable `tris` artifact;
- source build: CS2 build `17595823`, dated 2025-03-04 according to Awpy's installed artifact registry;
- file: `de_anubis.tri`;
- size: 29,088,000 bytes;
- SHA-256: `3DA37BBC33A9E9B2C469E9E39F1FF0A31A6EFE4212D10026516C803B708D9787`;
- triangles: 808,000;
- bounds: X `-3202.5049..2816.5098`, Y `-3456..4736`, Z `-704..1012`;
- render materials/semantics/dynamic geometry: absent;
- distribution: unresolved; Awpy code is MIT, but that does not itself establish redistribution rights for game-derived geometry;
- gate result: `version_mismatch`, not accepted.

Technical coordinate evidence against real replay source `446eec75822c…`:

- all 2,523,998 observed player positions fall inside the triangle bounds;
- replay bounds: X `-1971.9473..1803.9713`, Y `-1759.9688..2771.7646`, Z `-191.9688..188.1563`;
- identity transform is therefore numerically plausible, but not visually/current-build verified;
- Awpy BVH controlled visible pair at round 1/tick 6401: `(-259.6265,-1595.3811,52.0313)` to `(-508.1600,-1589.8218,66.0312)` -> visible;
- controlled blocked pair at the same tick: `(-259.6265,-1595.3811,52.0313)` to `(-527.9521,2207.1423,89.0313)` -> blocked;
- these checks prove the old candidate can answer LOS in replay coordinates; they do not prove parity with current CS2 geometry.

### Installed current Valve candidate

- installed CS2 App 730 build: `24828357`;
- installed map file: `game/csgo/maps/de_anubis.vpk`;
- size: 269,890,099 bytes;
- SHA-256: `BCA91CEE11592C65C2869C599769232F29335458376ED90431A013B58C938E07`;
- companion `de_anubis_vanity.vpk`: 8,430,194 bytes;
- companion SHA-256: `2943FBDB7A7261F65CB7CA47E6C1CF4B910D1B52D281BCCEC019A49121967C39`;
- map extraction/conversion was not performed;
- no approved render/visibility derivative or transform proof exists;
- gate result: `distribution_blocked` until an explicitly approved local-only or derivative route is selected.

## Distribution finding

Awpy's package/code carries an MIT license, but the candidate triangle artifact represents Counter-Strike map geometry. The Steam Subscriber Agreement reserves Valve content rights and limits copying, derivative creation and distribution unless an applicable permission or separate term allows it. It separately permits content created with Valve Developer Tools on a non-commercial basis and directs commercial Developer Tools use to Valve. This engineering gate is not legal advice and does not infer a commercial redistribution grant.

Therefore neither candidate meets every V1 acceptance rule:

- old Awpy `.tri`: coordinate/LOS-capable but stale and distribution-unresolved;
- installed VPK: current and hashable, but not an accepted mesh and not approved for extraction/distribution.

`map_geometry` remains `unavailable`; the product must show `3D POV für diese Map nicht verfügbar: Kartenasset nicht freigegeben.`

## Machine-enforced gate

`map_assets.py` implements `iy.map_asset/v1` assessment with explicit outcomes:

- `available`;
- `missing`;
- `version_mismatch`;
- `integrity_failed`;
- `distribution_blocked`;
- `unsupported_map`.

It rejects wrong schema/map, unapproved distribution, unverified version status, incomplete transforms, missing files, path escape and SHA-256 mismatch. Synthetic tests do not include Valve data.

## Decision required

Tristan must choose one permitted route before Slice C can complete:

1. authorize a current-build, local-only extraction/derivative that is never committed or distributed, then validate transform, known points and LOS locally;
2. provide or approve a distributable controlled derivative with documented rights;
3. keep Anubis 3D unavailable until an acceptable asset exists.

No renderer, camera, player proxy or sightline implementation may begin before this decision and the resulting asset passes the complete gate.

## Local-only route result

The authorized route was executed against installed CS2 build `24828357`:

- Valve's installed `resourceinfo.exe` proved the VPK contains `world_physics.vmdl_c` with a 29,535,764-byte PHYS block;
- ValveResourceFormat CLI `19.2.6339+c72208352f5bf62f1482447ed166c548f303f8fa` was downloaded into ignored local storage and verified against its published Windows-x64 archive SHA-256 `53E7E8DAC1DDD876078346DE709C8DBE613A967E94CD0C969AA34C61EC07680D`;
- only `world_physics.vmdl_c` was decompiled locally;
- 27 normal world-physics groups were retained;
- player/nav/grenade clips, pass-bullets, window/water and sky groups were excluded;
- no Valve textures or materials were copied into the derivative;
- the replay-space render GLB has identity transform and neutral collision geometry;
- the visibility `.tri` contains 673,869 triangles.

Local ignored bundle:

- `render_mesh.glb`: 77,560,564 bytes, SHA-256 `9AD0036D7BDFB9E6A5DFD821FEFC52E6D12CB34EEEB44202F7E32FA4D5542AA6`;
- `visibility_mesh.tri`: 24,259,284 bytes, SHA-256 `D667D72898680B5C5E559C8BF39535D4C1F0E72EBA4224FEC55608BDD606639F`;
- manifest SHA-256 after verification: `D39B9BE7A86EC85599F9B1658995A7F2BF87C8EE622412B3F3E8A4F88FA56013`;
- distribution: `local_only`;
- transform: scale 1, rotation `[0,0,0]`, translation `[0,0,0]`;
- machine assessment: `available` in 0.141 seconds.

Validation against real replay `446eec75822c…`:

- geometry bounds match the established Anubis candidate bounds;
- all 2,523,998 observed positions remain inside bounds;
- 25,439 sampled replay positions visually follow the top-down corridors and playable areas without mirror, quarter-turn or translation mismatch;
- 10,289 sampled positions pass the perspective height/floor plausibility check;
- the known visible pair remains visible;
- the known blocked pair remains blocked;
- normal load, hash validation and missing-file behavior are tested.

For this exact local machine/build, `map_geometry=verified`. For any packaged or other-machine run without this matching local bundle, it remains unavailable. A CS2 build/hash change invalidates the bundle and requires regeneration/revalidation.

## Next

Slice D may now begin as a minimal renderer protocol/native-embed spike using only this ignored local bundle. It must not package the asset or silently turn the local-only result into a distribution decision.
