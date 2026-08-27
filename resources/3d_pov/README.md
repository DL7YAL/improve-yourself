# Anubis 3D / POV data-preparation pilot

This area is research, evidence and static contract metadata only. It does not
implement a renderer, camera playback, parsing, timing, interpolation, tactical
state or another map-asset authority.

The existing runtime boundaries remain authoritative:

```text
AnalyzerCore -> AnalyzerDataHub -> iy.replay/v2 -> ReplayStore -> ReplayController
                                                    |
                                                    v
                                      ReplayRenderer / renderer session
```

`iy.map_asset/v1` remains the runtime asset gate. The prep document here does
not replace that manifest; it inventories candidate inputs, records validated
reference facts and tells a future consumer which canonical data it must use.

## Files

- `schema/iy.3d_pov_prep.v1.schema.json` — isolated preparation contract.
- `de_anubis/prep.json` — Anubis research and reference package.
- `../../tools/pov_prep_data/validate.py` — deterministic offline validator.
- `../../tests/pov_prep_data/test_anubis_pov_prep.py` — metadata tests.

No geometry, texture, material, demo, replay frame or executable is bundled.

## Asset and geometry inventory

### Current-build local derivative

The strongest accepted reference is the existing ignored local-only derivative
recorded by `docs/3D_POV_V1_SLICE_C_ASSET_GATE.md`:

- installed CS2 build: `24828357`;
- installed `de_anubis.vpk` SHA-256:
  `BCA91CEE11592C65C2869C599769232F29335458376ED90431A013B58C938E07`;
- 27 retained normal world-physics groups;
- neutral render GLB, 77,560,564 bytes, SHA-256
  `9AD0036D7BDFB9E6A5DFD821FEFC52E6D12CB34EEEB44202F7E32FA4D5542AA6`;
- visibility triangle file, 24,259,284 bytes, 673,869 triangles, SHA-256
  `D667D72898680B5C5E559C8BF39535D4C1F0E72EBA4224FEC55608BDD606639F`;
- identity transform into replay coordinates;
- no Valve texture/material redistribution;
- availability is machine/build/hash specific and `local_only`.

The files remain ignored local artifacts and are not reproduced here.

### Historical Awpy triangle candidate

Awpy 2.0.2 previously supplied a `de_anubis.tri` artifact:

- artifact build: `17595823` from March 2025;
- SHA-256:
  `3DA37BBC33A9E9B2C469E9E39F1FF0A31A6EFE4212D10026516C803B708D9787`;
- 808,000 little-endian float32 triangles;
- bounds X `-3202.5049..2816.5098`, Y `-3456..4736`, Z `-704..1012`;
- collision/visibility geometry only;
- no materials, semantic surfaces or dynamic props;
- status `VERSION_MISMATCH` for the accepted current-build route;
- redistribution rights for game-derived geometry remain unresolved.

Awpy's code is MIT-licensed, but its documentation states that downloadable map
images, navigation meshes and triangles are separate artifacts that can change
with game updates. The code license does not by itself grant redistribution
rights to Valve-derived geometry.

### Installed Valve VPK

The installed VPK is a current, hashable source reference but cannot be bundled:

- `de_anubis.vpk`: 269,890,099 bytes;
- companion vanity VPK: 8,430,194 bytes;
- current-build extraction is permitted only through the already approved
  local-only process;
- package redistribution remains blocked absent separate rights.

ValveResourceFormat is an MIT-licensed parser/decompiler tool. That license
covers the tool, not the Valve assets it reads.

## Coordinate contract

The accepted local derivative and canonical Replay V2 positions share
`cs2_world` coordinates with an identity scene transform:

```text
scene_x = world_x
scene_y = world_y
scene_z = world_z
```

- scale: `1.0` source unit per scene unit;
- rotation: `[0, 0, 0]` degrees;
- translation: `[0, 0, 0]`;
- axis swap: none;
- axis inversion: none;
- Z axis: up;
- physical conversion to metres: `UNRESOLVED` and unnecessary for identity
  replay/geometry alignment;
- handedness label: `UNRESOLVED`; consumers must not infer one from this prep
  document.

Known geometry bounds:

```text
X -3202.5049 .. 2816.5098
Y -3456.0000 .. 4736.0000
Z  -704.0000 .. 1012.0000
```

Observed real replay bounds:

```text
X -1971.9473 .. 1803.9713
Y -1759.9688 .. 2771.7646
Z  -191.9688 .. 188.1563
```

All 2,523,998 observed positions in the recorded validation were inside the
geometry bounds. These ranges do not define floors. No floor names, Z bands or
layer-selection policy are asserted.

### Relation to the 2D overview

The existing `resources/map_overviews/maps/de_anubis.json` remains the 2D
projection authority:

```text
overview_x = (world_x + 2796) / 5.22
overview_y = (3328 - world_y) / 5.22
```

The 3D prep package references that file and records expected 2D values for its
three world anchors. It does not copy or replace the 2D transform contract.

## Camera / POV canonical input contract

A future viewer must consume a committed ReplayController snapshot and the
resolved canonical ReplayFrame. Required First Person inputs are:

- `current_tick` / resolved tick from ReplayController;
- selected stable `player_id`;
- `PlayerState.active`;
- `PlayerState.alive` when available;
- `PlayerState.position.x/y/z`;
- `PlayerState.view_yaw_deg`;
- `PlayerState.view_pitch_deg`.

Optional evidence:

- velocity;
- health, armor and weapon;
- FOV only if a future canonical source supplies it.

No canonical per-player FOV or eye height is asserted by this package. Eye
height remains a renderer calibration/configuration value, not replay truth.
Roll remains zero only under the existing camera contract when no roll evidence
exists.

The existing camera convention is:

```text
forward.x = cos(pitch) * cos(yaw)
forward.y = cos(pitch) * sin(yaw)
forward.z = -sin(pitch)
```

Thus yaw zero points along positive world X, positive yaw turns toward positive
world Y, positive Source pitch looks downward, and positive world Z is up.

**Current tick and entity/POV state MUST come from canonical Replay/Analyzer
data through ReplayStore and ReplayController.** This package contains no
runtime frame and owns no clock.

## Reference anchors

Three neutral world-coordinate references come from the existing local Anubis
round-1/tick-6401 validation. Their scene coordinates are identical because the
accepted transform is identity:

1. observer: `(-259.6265, -1595.3811, 52.0313)`;
2. visible target: `(-508.1600, -1589.8218, 66.0312)`;
3. blocked target: `(-527.9521, 2207.1423, 89.0313)`.

The visible/blocked labels are local geometry-validation outcomes, not gameplay,
awareness or cheat conclusions. The anchors do not name landmarks.

## Redistribution boundary

- No Valve VPK, mesh, texture, material, radar or model is committed.
- No Awpy map artifact is committed.
- Local-only hashes and measurements are evidence references, not downloadable
  repository assets.
- A matching `iy.map_asset/v1` local bundle remains mandatory before 3D use.
- A build/hash mismatch must produce unavailable/version-mismatch, never a
  fallback geometry.

## Beast consumer handoff

1. Read `de_anubis/prep.json` as evidence only.
2. Continue to use `iy.map_asset/v1` and `assess_map_asset()` for runtime asset
   authority.
3. Require the exact local build/hash bundle before loading geometry.
4. Apply the identity world-to-scene transform only for the accepted bundle.
5. Resolve current tick/frame/player exclusively through ReplayController and
   ReplayStore.
6. Reuse the existing First Person and fixed Third Person camera contracts.
7. Do not infer eye height, FOV, floors, dynamic geometry or materials.
8. Do not package any referenced geometry or Valve-derived asset.
9. If the bundle is absent, mismatched or distribution-blocked, keep 3D
   unavailable while 2D remains usable.
10. This package is data/research metadata only and must never become a second
    runtime path.
