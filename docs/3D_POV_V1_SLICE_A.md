# 3D / POV V1 — Slice A canonical replay truth

Status: `SLICE_A_COMPLETE`

Date: 2026-08-20

Slice A implements the renderer-independent `iy.replay/v2` full-match truth defined by `3D_POV_V1_IMPLEMENTATION_SPEC.md`. It does not add a controller, renderer, camera, sightline calculation, map asset or UI.

## Implemented modules

- `replay_contract.py` — frozen contract values for player identity/state, frame, event, utility and capabilities;
- `replay_builder.py` — Awpy 2.0.2 normalization and round-chunk export;
- `replay_validation.py` — manifest, identity, ordering, event-tick and utility-lifetime invariants;
- `replay_store.py` — read-only round loading, SHA-256 verification and exact/at-or-before tick access;
- `replay_capabilities.py` — reusable capability assessment helper;
- `Run-ReplayV2Regression.ps1` — explicit private real-demo build and aggregate validation path.

`iy.replay/v1` and its current 2D viewer remain unchanged. Slice B owns migration to the shared controller.

## Physical store

One inspectable manifest references one gzip JSON chunk per round:

```text
<output>/<source-hash-prefix>/
  replay-v2.json
  regression-summary.json       # optional, aggregate and local
  rounds/
    round-001.json.gz
    ...
```

Each descriptor contains its compressed-file SHA-256. `ReplayStore` rejects path escape, hash mismatch, malformed chunks, non-increasing ticks, duplicate player IDs, shifted event ticks and utility states outside their evidenced lifetime.

## Real Anubis result

Input is local/private and identified only by SHA-256 `446eec75822c0cae5ca020296ad900307e573302b81c8beb5b5daa98623058b6`.

Aggregate PASS evidence:

- map `de_anubis`;
- 42 rounds;
- 252,401 canonical frames;
- 2,524,000 player states;
- 10 stable Steam identities;
- 8,429 normalized exact-tick events;
- 300,424 active utility states derived from evidenced lifetimes;
- 22 Analyzer scene references;
- 43 files / approximately 56.9 MB compressed store before the optional summary;
- 42/42 round chunks loaded, hash-checked and validated.

Normalized events currently include kills, damage, weapon fire, bomb plants and bomb defuses. Utilities currently include Smoke and Inferno/Molotov lifetime state.

## Capability result and limitations

The real source truth is deliberately reported as:

```text
positions              partial
view_yaw               partial
view_pitch             partial
alive_state            partial
weapon_state           partial
velocity               partial
utility_lifetimes      partial
utility_trajectories   partial
flash_effect           unavailable
sound                  unavailable
map_geometry           unavailable
tick_rate              unavailable (null)
```

Reasons:

- individual tick rows contain null values, so complete fields are not claimed;
- health describes observed active rows, but absent/dead rows are not reconstructed;
- 3,479,155 observed grenade trajectory points are not materialized in Slice A;
- player-specific flash effect is not established;
- `player_sound` is absent;
- map geometry belongs to the later asset gate;
- Awpy/header supplies no trusted tick rate for this demo, so no `64` default is invented.

The last point is the next playback blocker: Slice B cannot promise correct wall-clock speeds until tick rate is derived from an evidenced source or playback is explicitly unavailable.

## Reproduce locally

```powershell
.\tools\dev\Run-ReplayV2Regression.ps1 `
  -Demo '<private demo.dem.zst>' `
  -Analysis '<matching iy.analysis/v1.json>'
```

Outputs remain ignored below `results/`. No raw demo, player details or replay chunks are committed.

## Slice A COMPLETE criteria result

- immutable logical contract: PASS;
- full-match round/tick/player build: PASS;
- stable identity and quality: PASS for the real reference (10 Steam identities, zero unresolved snapshots);
- capability disclosure: PASS;
- exact event tick: PASS;
- utility lifetime invariant: PASS;
- indexed, hash-verified read-only store: PASS;
- real private Anubis regression: PASS;
- existing `iy.analysis/v1` / `iy.replay/v1` regression: PASS;
- renderer dependency added: NO;
- private/generated result committed: NO.

## Next slice gate

Before or at the beginning of Slice B, establish and test the canonical tick-rate source for the real Anubis demo. Then implement `ReplayController` and migrate the existing 2D view to consume `iy.replay/v2` without adding 3D rendering yet.
