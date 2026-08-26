# 3D / POV Blueprint V1 — Closed Implementation Specification

Status: `3D_POV_V1_SPEC_COMPLETE`

Date: 2026-08-20

This specification closes the architecture and acceptance boundary for the first implementation. It does not authorize a merge to `main`, select a permanent renderer, or relax the asset-provenance gate documented in `3D_POV_V1_PREFLIGHT.md`.

## 1. Settled product contract

Tactical Replay has one replay truth and three mandatory V1 views:

```text
Demo
  -> AwpyAdapter / normalization
  -> iy.replay/v2 (canonical, full match, tick identity)
  -> ReplayController (the only mutable playback state)
       -> 2D Tactical View
       -> First Person POV
       -> Fixed Third-Person Analysis Camera
            + optional-on-by-default sightline overlay
```

The views do not parse demos, infer independent state, maintain independent clocks, or recalculate analyzer metrics. The original CS2 demo remains the final original-engine reference.

Mandatory V1 behavior:

- full analyzed match and round selection;
- one canonical demo tick and round across all views;
- play, pause, scrub and `0.25x / 0.5x / 1.0x / 2.0x`;
- selected player persists across view changes;
- analyzer and My-Improvement scenes resolve to the same canonical context;
- First Person POV from observed position and view angles;
- one fixed, deterministic Third-Person Analysis Camera preset;
- evidence-qualified sightline visualization;
- player, weapon/alive state and utility only when present;
- explicit unavailable/partial states instead of fabricated data;
- native embedded desktop surface for the product build;
- original-demo-in-CS2 route preserved.

## 2. Proposed module and file structure

The first implementation extends the existing package without importing legacy runtime code:

```text
src/improve_yourself/
  replay_contract.py       # immutable iy.replay/v2 types and serialization
  replay_builder.py        # Awpy rows -> canonical full-match artifact
  replay_validation.py     # structural, temporal and identity invariants
  replay_store.py          # indexed/chunked round and tick access
  replay_controller.py     # sole mutable playback/view selection state
  replay_capabilities.py   # evidence and availability rules
  map_assets.py            # asset manifest, checksums and availability gate
  sightlines.py            # qualified LOS results, never renderer-owned
  cameras.py               # deterministic FP and fixed TP camera transforms
  renderer.py              # ReplayRenderer protocol and NullRenderer
  renderers/
    panda3d_renderer.py     # optional integration slice after asset gate
  tactical_replay.py       # product-facing orchestration, no parsing logic

tests/
  fixtures/replay_v2/      # synthetic, non-private contract fixtures only
  test_replay_contract_v2.py
  test_replay_builder_v2.py
  test_replay_validation_v2.py
  test_replay_store.py
  test_replay_controller.py
  test_replay_capabilities.py
  test_map_assets.py
  test_sightlines.py
  test_cameras.py
  test_renderer_contract.py
  test_replay_v1_compatibility.py

assets/maps/<map_id>/<asset_version>/
  manifest.json
  render_mesh.<approved-format>
  visibility_mesh.tri
  materials/               # original Improve Yourself materials only

tools/dev/
  Run-ReplayV2Regression.ps1
  Run-3DPovAcceptance.ps1
```

`src/improve_yourself/replay.py` remains the `iy.replay/v1` compatibility path until all existing 2D tests consume `iy.replay/v2`. No in-place schema mutation is allowed.

## Block 1 — Asset Specification

### 3. Asset bundle contract

Every 3D-capable map requires one `MapAssetManifest`:

```json
{
  "schema": "iy.map_asset/v1",
  "map_id": "de_anubis",
  "asset_version": "<project version>",
  "source_kind": "local_cs2_extraction | controlled_derivative",
  "source_build_id": "<CS2 build or explicit unknown>",
  "source_description": "<auditable origin>",
  "coordinate_space": "cs2_world",
  "units": "source_unit",
  "axis": {"x": "east-west", "y": "north-south", "z": "up"},
  "transform_to_replay": {"scale": 1.0, "rotation_deg": [0, 0, 0], "translation": [0, 0, 0]},
  "render_mesh": {"path": "render_mesh...", "sha256": "..."},
  "visibility_mesh": {"path": "visibility_mesh.tri", "sha256": "..."},
  "dynamic_geometry": "unsupported",
  "distribution": "local_only | approved_derivative | prohibited",
  "validation": {
    "status": "verified | version_mismatch | unverified | unavailable",
    "reference_demo_sha256": "...",
    "verified_at_utc": "..."
  }
}
```

### 4. Asset acceptance rules

A map is 3D-capable only when all of these pass:

1. manifest schema is valid;
2. render and visibility hashes match;
3. `map_id` equals the replay map;
4. build/version status is `verified`;
5. coordinate transform has passed known-point checks;
6. floor, height, openings and representative sightlines pass visual comparison;
7. distribution is `local_only` or `approved_derivative` for the requested run;
8. normal load, dispose and missing-file behavior pass.

Otherwise `MapAvailability` is one of:

- `available`;
- `missing`;
- `version_mismatch`;
- `integrity_failed`;
- `distribution_blocked`;
- `unsupported_map`.

The UI shows `3D POV für diese Map nicht verfügbar: <reason>`. It does not display placeholder walls.

### 5. Required V1 assets

- one verified `de_anubis` render mesh and visibility mesh;
- simple original Improve Yourself neutral/dark materials;
- CT and T capsule/silhouette proxies with team colors;
- own simple crosshair;
- own utility primitives: smoke volume, detonation marker and fire footprint;
- no Valve textures, player models, weapon models, sounds or trademarks required by the renderer;
- optional weapon label/icon only when the data is present and the asset is distributable.

The current Awpy `de_anubis.tri` is an input candidate, not an accepted bundle, until build currency and distribution are recorded.

## Block 2 — Shared ReplayFrame data model

### 6. Schema version and storage

The canonical contract is `iy.replay/v2`. It is intentionally new because full-match state, identity, events and capabilities are incompatible additions to scene-only `iy.replay/v1`.

The logical contract is independent of physical storage. The initial artifact is JSON for inspectability, indexed per round by `ReplayStore`. If size becomes material, round chunks may move to a compressed representation without changing the logical schema.

Top-level shape:

```json
{
  "schema": "iy.replay/v2",
  "source": {
    "sha256": "...",
    "map_id": "de_anubis",
    "tick_rate": 64.0,
    "parser": {"name": "awpy", "version": "2.0.2"}
  },
  "coordinate_space": "cs2_world",
  "capabilities": {},
  "players": [],
  "rounds": [],
  "scenes": [],
  "data_quality": {}
}
```

### 7. Identity

`PlayerIdentity`:

```text
player_id: str                 # stable within this replay artifact
steam_id: str | null           # only if parsed and validated
entity_id: int | null          # parser/demo-scoped identity if present
display_name: str
team_at_tick: T | CT | unknown # frame state, not identity
identity_quality: steam | entity | scoped_slot | unresolved
```

`player_id` priority:

1. `steam:<steam_id>` when valid;
2. `entity:<source_hash_prefix>:<entity_id>` when the demo entity key is stable;
3. `slot:<source_hash_prefix>:<stable_slot>` only when stability is verified for the match;
4. unresolved identity cannot be selected as persistent POV across discontinuities.

Display names never form identity. Duplicate names must remain distinct.

### 8. ReplayFrame

```text
ReplayFrame
  tick: int                    # canonical technical identity
  round_number: int
  time_in_round_seconds: float | null  # derived display value
  players: tuple[PlayerState, ...]
  utilities: tuple[UtilityState, ...]
  events: tuple[ReplayEvent, ...]
```

Invariants:

- frames are strictly increasing by tick inside a round;
- one `(round_number, tick)` maps to exactly one canonical state;
- event tick is never rounded to a sampled display frame;
- seconds are derived from tick metadata and never used as identity;
- absent parser rows are represented through capability/quality state, not zero coordinates;
- no duplicate `player_id` exists in one frame.

### 9. PlayerState

```text
PlayerState
  player_id: str
  active: bool
  alive: bool | null
  team: T | CT | unknown
  position: Vec3 | null
  view_yaw_deg: float | null
  view_pitch_deg: float | null
  velocity: Vec3 | null
  health: int | null
  armor: int | null
  weapon: str | null
  availability: frozenset[str]
```

Rules:

- `active=false` produces no invented camera;
- `position=null` prevents spatial rendering for that player at that tick;
- missing pitch disables First Person POV for that player/tick but may allow 2D position;
- health zero does not by itself invent a death tick; use parsed alive/death evidence;
- renderer consumes the state but never fills missing values.

### 10. UtilityState

```text
UtilityState
  utility_id: str
  utility_type: flash | smoke | he | molotov | incendiary | decoy
  owner_player_id: str | null
  start_tick: int
  end_tick: int | null
  position: Vec3 | null
  trajectory: tuple[TrajectoryPoint, ...] | null
  active: bool
  evidence: trajectory | lifetime | detonation_only
```

Rules:

- trajectories render only when parsed;
- smoke/fire volumes exist only during evidenced lifetime;
- detonation-only data renders a short event marker, not a trajectory or lifetime;
- no assumed effectiveness radius;
- flash overlay is allowed only for a player-specific, evidenced blind duration; otherwise show event text only.

### 11. ReplayEvent and SceneReference

`ReplayEvent` supports V1 types:

- `kill`;
- `damage`;
- `bomb_plant`;
- `bomb_defuse`;
- `utility_detonation`;
- `weapon_fire`;
- `scene_marker`.

Required fields are `event_id`, `type`, `tick`, involved player IDs, optional position and an evidence reference. Analyzer results are referenced, not recalculated.

`SceneReference`:

```text
scene_id
match_sha256
round_number
tick
focus_player_id | null
event_ids[]
criterion_id
```

Opening a scene is a single atomic `ReplayController.seek(scene.round_number, scene.tick, focus_player_id)` operation.

### 12. ReplayCapabilities and data quality

Capabilities are explicit per match and may be narrowed per player/tick:

```text
positions: full | partial | unavailable
view_yaw: full | partial | unavailable
view_pitch: full | partial | unavailable
alive_state: full | partial | unavailable
weapon_state: full | partial | unavailable
utility_lifetimes: full | partial | unavailable
utility_trajectories: full | partial | unavailable
flash_effect: full | partial | unavailable
sound: full | partial | unavailable
map_geometry: verified | mismatch | unavailable
```

Missing `player_sound` remains `sound=unavailable`; it does not fail replay construction.

### 13. ReplayController

This is the only mutable playback authority:

```text
ReplayController
  current_round: int
  current_tick: int
  play_state: paused | playing
  playback_speed: 0.25 | 0.5 | 1.0 | 2.0
  selected_player_id: str | null
  selected_scene_id: str | null
  view_mode: tactical_2d | first_person | analysis_third_person

  load(replay_store)
  seek(round_number, tick)
  seek_scene(scene_id)
  select_player(player_id)
  set_view_mode(mode)
  set_speed(speed)
  play()
  pause()
  step_relevant(direction)
  snapshot() -> ReplayContext
```

State transitions are atomic and observable. A view subscribes to `ReplayContext`; it does not mutate frame data.

### 14. Timing and interpolation rules

- demo tick is canonical;
- round/time labels are derived display data;
- playback advances against tick rate, not wall-clock frame count;
- slow rendering may skip visual draws but never canonical ticks/events;
- scrub resolves the nearest existing canonical frame at or before the requested tick and reports the resolved tick;
- event navigation lands on the exact event tick;
- optional visual interpolation uses two adjacent observed states and a render-only fraction;
- no interpolation across round boundaries, death/inactive transitions, teleports, missing data or identity changes;
- First Person view angles use shortest valid angular interpolation only for rendering;
- sightlines, analyzer metrics, utility activity and events are evaluated at canonical ticks only;
- switching 2D/FP/TP preserves round, tick, scene, player, speed and play/pause state.

### 15. Camera contracts

#### First Person POV

- origin: observed player position plus one fixed documented eye-height transform;
- orientation: observed yaw and pitch;
- roll: zero unless parser evidence later adds it;
- no cinematic smoothing;
- no POV if position, yaw or pitch is unavailable;
- selected inactive/dead player shows `Spieler zu diesem Zeitpunkt nicht aktiv.`.

Eye height is an adaptable renderer constant validated against the reference demo; it is not written into replay truth.

#### Fixed Third-Person Analysis Camera

One deterministic preset, no free camera and no user-adjustable orbit in V1:

```text
anchor = player eye position
forward = vector(view_yaw, view_pitch)
camera = anchor - forward * 160 source_units + world_up * 72 source_units
target = anchor + forward * 320 source_units
```

The numerical offsets are implementation constants and may be calibrated once during acceptance without changing the product contract. After acceptance they are fixed for all users.

If a verified visibility mesh shows camera-to-anchor obstruction, the camera moves only along the defined camera-to-anchor segment to the nearest non-obstructed point with a fixed safety margin. It sets `camera_adjusted=true` for diagnostics. It never chooses a cinematic alternative angle.

If selected-player position, yaw or pitch is unavailable at the canonical tick, this camera is unavailable for that tick; it does not substitute a top-down, yaw-only or last-known transform.

#### Sightline visualization

Sightline source is a canonical `SightlineResult`, not the renderer:

```text
observer_player_id
target_player_id
tick
geometry_state: clear | blocked | unknown
smoke_state: clear | blocked | unknown
result: visible | occluded | unknown
evidence[]
```

Rules:

- ray is eye position to target eye/center using verified visibility geometry;
- verified geometry block -> `occluded`;
- active evidenced smoke intersecting the segment may change clear geometry to `occluded` only when the chosen V1 smoke-volume approximation and its limitation are disclosed;
- missing geometry, player position or relevant smoke evidence -> `unknown`, never visible;
- dynamic doors/props not represented by the asset must downgrade affected results to `unknown` when material;
- overlay colors: clear/visible, blocked/occluded, neutral/unknown;
- sightlines are analytical visualization, not a new cheat or awareness verdict.

## Block 3 — V1 test matrix

### 16. Automated contract tests

| ID | Area | Required proof |
| --- | --- | --- |
| C01 | Schema | Valid `iy.replay/v2` round-trips without loss |
| C02 | Ordering | Duplicate/non-increasing round ticks rejected |
| C03 | Identity | Duplicate names remain separate by stable ID |
| C04 | Missing data | Null position/view values remain null; no zero fallback |
| C05 | Events | Every event retains exact canonical tick |
| C06 | Utility | Active state matches evidenced start/end ticks |
| C07 | Capabilities | Missing optional channel degrades capability, not whole parse |
| C08 | Compatibility | Existing `iy.analysis/v1` and `iy.replay/v1` tests remain green |

### 17. Controller and synchronization tests

| ID | Scenario | Pass condition |
| --- | --- | --- |
| S01 | 2D -> FP -> 2D | Round, tick, player, scene and speed unchanged |
| S02 | FP -> TP during play | Same canonical tick/context; playback continues |
| S03 | Player switch | Tick/round unchanged; camera resolves selected player |
| S04 | Inactive player | Explicit inactive state; no camera invented |
| S05 | Scene jump | Exact scene tick and focus player selected atomically |
| S06 | Scrub | Resolved canonical tick disclosed and all views agree |
| S07 | Relevant-event step | Lands on exact previous/next event tick |
| S08 | Round boundary | No interpolation or state leakage across rounds |

### 18. Camera and sightline tests

| ID | Scenario | Pass condition |
| --- | --- | --- |
| V01 | FP orientation | Known yaw/pitch fixtures produce expected forward vectors |
| V02 | Fast mouse turn | No semantic smoothing or direction overshoot |
| V03 | TP transform | Fixed formula produces deterministic camera/target |
| V04 | TP obstruction | Camera shortens on its fixed segment and reports adjustment |
| V05 | Missing pitch | FP unavailable; 2D/eligible TP state remains explicit |
| V06 | Clear geometry LOS | Result visible with geometry evidence |
| V07 | Wall intersection | Result occluded |
| V08 | Missing geometry | Result unknown, not visible |
| V09 | Active smoke intersection | Qualified occluded result with approximation disclosure |
| V10 | Unknown smoke lifetime | LOS downgraded where material; no assumed lifetime |

### 19. Asset and failure tests

| ID | Scenario | Pass condition |
| --- | --- | --- |
| A01 | Correct Anubis bundle | Hash/version/transform accepted |
| A02 | Wrong map | 3D unavailable with reason |
| A03 | Hash mismatch | Load rejected before rendering |
| A04 | Old build | `version_mismatch`; no geometry shown |
| A05 | Missing mesh | 2D continues; 3D unavailable |
| A06 | Distribution blocked | Product refuses packaged 3D asset |
| A07 | Load/dispose loop | No leaked renderer window/process/handle |

### 20. Real Anubis acceptance matrix

Use the existing local demo with SHA-256 prefix `446eec75822c`. No private demo or detailed output is committed.

Required evidence:

1. parse full match into `iy.replay/v2`;
2. report rounds, ticks, identities, capability matrix and omitted states;
3. choose at least three fixed checkpoints in different rounds;
4. compare each checkpoint in 2D, First Person and Third Person;
5. verify position and view direction against Original CS2;
6. verify one player switch without tick loss;
7. verify one analyzer scene jump;
8. verify at least one clear, blocked and unknown sightline case;
9. verify evidenced smoke/fire timing when available;
10. run a complete round at each supported speed;
11. verify full-match round navigation;
12. verify normal shutdown and reopen.

Screenshots/logs record source hash prefix, branch commit, map asset hash, round, tick, player ID, view mode and result. They do not commit player-sensitive raw data.

### 21. Performance and packaging tests

Initial V1 acceptance budgets, measured on a documented normal Windows target:

- no external browser process;
- first usable replay view within 10 seconds after selecting an already analyzed match;
- scrub response median <= 100 ms and p95 <= 250 ms for an indexed local replay;
- sustained playback without canonical tick drift over one complete round;
- renderer remains responsive at 30 displayed FPS target; lower visual FPS is acceptable only if timeline correctness remains intact;
- memory peak and package-size delta are recorded, not hidden;
- packaged launch, resize, view switch, dispose and normal shutdown pass on a clean test profile.

These are V1 guardrails, not promises of 240 FPS or game-engine parity.

## Block 4 — Implementation handoff and COMPLETE criteria

### 22. Implementation sequence

No later slice starts before the preceding exit gate passes:

1. **Slice A — Canonical truth:** `iy.replay/v2`, builder, validator, store and real Anubis capability report.
2. **Slice B — Shared control:** `ReplayController`; existing 2D view adapted and sync regression green.
3. **Slice C — Asset gate:** accepted Anubis asset manifest, checksums, transform and known-point/LOS proof.
4. **Slice D — Minimal renderer:** renderer protocol, native embed spike, map, FP and fixed TP camera.
5. **Slice E — Analysis overlays:** player proxies and sightlines.
6. **Slice F — Events/utility:** evidence-qualified smoke, flash, HE, fire and event overlays.
7. **Slice G — Product UX:** view toggle, player/round selection, scenes, breadcrumb and Original-CS2 route.
8. **Slice H — Packaging:** clean Windows build, performance, shutdown and full regression.

### 23. Required handoff per slice

```text
STATUS: done | partial | blocked
SLICE: <A-H>
BRANCH/COMMIT: <exact ref>
CHANGED: <files and public contracts>
DATA EVIDENCE: <real/synthetic inputs and capabilities>
ASSET EVIDENCE: <manifest/build/hashes or n/a>
VERIFIED: <test IDs, commands, results>
REGRESSIONS: <2D/analyzer/workflow status>
RISKS: <remaining concrete risks>
DECISIONS: <none or explicit proposal>
OPEN: <bounded remaining work>
NEXT: <one next slice/action>
```

No handoff may claim a view works from a synthetic fixture alone.

### 24. `3D_POV_V1_IMPLEMENTATION_COMPLETE`

The exact completion token may be emitted only when all conditions pass:

- `iy.replay/v2` contains and validates one complete real Anubis match;
- Analyzer, 2D, FP and TP consume that same artifact and `ReplayController`;
- all view switches preserve round/tick/player/scene/playback state;
- FP position and angles pass fixture tests and Original-CS2 checkpoints;
- fixed TP camera is deterministic, obstruction-safe and not user-freecam;
- sightline clear/blocked/unknown states are evidence-qualified and visually accepted;
- player switching and inactive-player behavior pass;
- full round playback and full-match navigation pass;
- required utility/events render only when evidenced;
- missing capabilities and map-unavailable states are explicit;
- verified Anubis asset bundle passes integrity, version, transform and distribution gates;
- no external browser is required by the packaged product;
- renderer load/resize/dispose and normal shutdown pass;
- performance measurements satisfy the guardrails or have an explicit approved exception;
- all old and new automated tests pass;
- real Anubis acceptance matrix passes;
- current 2D workflow, analysis contract and review path do not regress;
- no Optimizer/System Check behavior is changed by the replay implementation;
- reproducible setup/package instructions and final handoff are committed;
- Tristan has approved the implementation result for merge.

Anything less is `partial`, `blocked`, or `ready_for_review`, never complete.

## Block 5 — Strict V1/V2 scope boundary

### 25. Fixed V1 decisions

- one parser/normalized replay truth;
- canonical tick identity;
- complete match and round playback;
- 2D Tactical View;
- First Person POV;
- one fixed Third-Person Analysis Camera;
- sightline visualization with visible/occluded/unknown evidence states;
- player selection and view switching without tick loss;
- analyzer/My-Improvement scene jumps;
- evidence-qualified utility/events;
- one real reference map: Anubis;
- simplified original materials and player proxies;
- native embedded desktop product surface;
- Original-CS2 review route preserved;
- explicit data and map availability.

### 26. Adaptable implementation details

These may be calibrated without reopening product scope, provided tests and invariants remain intact:

- physical JSON versus compressed/chunked storage;
- round index and cache strategy;
- Panda3D versus another renderer behind `ReplayRenderer` after the embed spike;
- eye-height constant;
- fixed TP offset constants and safety margin;
- neutral material colors and proxy shape details;
- smoke approximation appearance and disclosed wording;
- visual interpolation implementation;
- internal batching, mesh reduction and cache sizes;
- exact layout spacing within the approved desktop design language.

### 27. Deferred to V2 or later

- freecam, orbit camera and user-adjustable TP camera;
- cinematic camera direction;
- side-by-side 2D/3D;
- third-person animation system beyond functional proxies;
- Source-2-quality textures, shaders, particles, smoke or weapons;
- full sound engine or reconstructed original audio;
- ghost trails and advanced trajectory analysis;
- automated coaching camera;
- AI-generated motion, missing frames, geometry or tactical explanation;
- automatic awareness/cheat conclusions from sightlines;
- multi-map rollout beyond the generic contract and the accepted Anubis reference;
- video export, streaming, sharing, VR or multiplayer replay;
- My-Improvement-specific 3D engine;
- Optimizer/System Check integration into replay state.

Deferred items may be documented but must not enter V1 code paths, dependencies, UI controls or acceptance criteria.

## 28. Risks and mitigations

| Risk | V1 mitigation |
| --- | --- |
| Anubis geometry is stale or non-distributable | Manifest gate; refuse 3D and keep 2D available |
| Identity changes or duplicate names | Stable-ID hierarchy; unresolved identity disclosed |
| Full-match artifact becomes large | Logical schema fixed; indexed round chunks allowed |
| Renderer drives its own clock | Controller-only time; renderer accepts snapshots |
| Smooth visuals corrupt meaning | Render-only interpolation with explicit no-cross boundaries |
| Sightline overclaims awareness | Visible/occluded/unknown plus evidence; no verdict |
| Smoke approximation overclaims exact CS2 behavior | Evidence-qualified volume and permanent simplified-display notice |
| Native packaging grows or breaks | Disposable embed/package spike before renderer commitment |
| Existing 2D regresses | Compatibility adapter and mandatory old-suite regression |
| Scope expands through attractive 3D ideas | Fixed V1/V2 table and slice gates |

## 29. First actual implementation slice

Implement Slice A only:

1. add immutable `iy.replay/v2` contract types;
2. build full-match round/tick/player state from the existing Awpy adapter;
3. preserve exact tick identity and stable identity quality;
4. add capabilities and structural/temporal validation;
5. add an indexed read-only `ReplayStore`;
6. produce a local aggregate capability report for the real Anubis demo;
7. keep every existing analyzer/2D/workflow test green;
8. do not add Panda3D or any renderer dependency in this slice.

Slice A is complete only when its synthetic contract tests and the private real-Anubis regression pass and the handoff states exactly what remains unavailable.
