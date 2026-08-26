# 3D / POV Blueprint V1 — Technical Preflight

Status: `3D_POV_V1_BLOCKED — the existing scene-only replay contract must be extended to full-match shared playback, and a versioned, distributable Anubis geometry asset is not yet available`

Date: 2026-08-20

This is a read-only implementation preflight. It does not authorize or add a 3D renderer, does not replace the existing 2D replay, and does not modify the benchmark addon.

## A. Replay data already present

### Active V1 repository

The active analyzer foundation currently provides:

- demo identity through source name and SHA-256;
- map name and tick rate when present in the demo header;
- kill events with round, tick, attacker, victim, weapon, and headshot state;
- round-based multi-kill markers;
- independent availability reporting for rounds, kills, damage, shots, bomb, smokes, infernos, grenades, and footsteps.

The current branch also has an `iy.replay/v1` artifact and a validated 2D viewer. The replay exporter provides hash-bound, uniformly sampled Multi-Kill scene windows with CS2 world-space player `x/y/z`, `pitch`, and `yaw`. A real Mirage workflow with seven scenes and 1,792 frames has passed both automated validation and Tristan's bounded visual position/direction check.

This is a strong reusable 2D foundation, but it remains a selected-scene artifact rather than full-match replay state.

### Legacy Tactical Replay evidence

`TacticalReplay_MVP_v0.3` proves that Awpy 2.0.2 can parse real per-tick replay data when explicitly requested with `player_props=["health", "armor_value", "pitch", "yaw"]`.

The preserved real Mirage round artifact contains:

- 1,734 sampled frames from tick 42,258 through 49,187;
- 10 real player names;
- per-player `x/y/z`, `yaw`, `pitch`, side, health, and armor;
- frame-local shots and kills;
- a geometric line-of-sight enrichment based on Awpy triangles.

The legacy parser is evidence and reference material only. It hardcodes a nominal 64 Hz rate, samples every fourth tick, omits dead players, identifies players by display name, and has no shared 2D/3D controller.

## B. Replay data still missing from the active contract

The combined active `iy.analysis/v1` and `iy.replay/v1` contracts do not currently contain:

- canonical `ReplayFrame` / `ReplayState`, `PlayerState`, `UtilityState`, and replay event contracts;
- full-match per-tick player states (`iy.replay/v1` contains sampled Multi-Kill windows only);
- stable player identity (`steam_id` or another demonstrated stable key);
- selected round, tick, scene, player, speed, and play state in one `ReplayController`;
- alive/inactive state without dropping the player row;
- weapon, velocity, health, and armor in replay frames;
- demonstrated view-angle availability and conventions for the real Anubis input (the current Anubis proof covers `iy.analysis/v1`, while the human replay check used Mirage);
- utility lifetime and trajectories normalized onto the same tick basis;
- scene references that resolve back to the exact replay state;
- a data-quality capability matrix at match/map/channel level;
- regression tests proving that 2D and 3D resolve the same tick and player state;
- a native desktop view host: the active viewer is a generated HTML artifact served locally, while the specification forbids an external-browser product surface.

There is also a documentation/code mismatch to close before 3D work: `docs/2D_VIEWER_FOUNDATION.md` describes shots, kills, smoke lifetimes, and inferno lifetimes in `iy.replay/v1`, but the current `build_replay_payload()` serializes only frame ticks and player snapshots. Those event/utility fields must be added and contract-tested or the documentation must be corrected; a 3D renderer must not assume them.

Sound is not a 3D V1 prerequisite. The tested corpus previously lacked `player_sound`; it must remain an explicitly unavailable capability rather than a parse failure.

## C. Map and geometry source

Awpy 2.0.2 has a local `de_anubis.tri` file at `%USERPROFILE%/.awpy/tris/de_anubis.tri`:

- size: 29,088,000 bytes;
- 808,000 raw triangles;
- bounds: X `-3202.50..2816.51`, Y `-3456..4736`, Z `-704..1012`;
- already usable by Awpy's `VisibilityChecker` and convertible into a reduced render mesh.

This is the strongest local geometry candidate for a technical spike because it is measured triangle data rather than invented geometry. It is not yet an accepted V1 asset:

- Awpy 2.0.2 identifies the downloaded artifacts with build id `17595823` from March 2025, so equivalence to the current CS2 Anubis revision is unproven;
- the `.tri` file contains only triangle coordinates, not authoritative materials, semantic surfaces, doors, dynamic props, or provenance metadata embedded in the artifact;
- redistribution/licensing of extracted CS2 geometry inside an Improve Yourself package has not been approved;
- no current real Anubis replay artifact has yet been regenerated against this exact geometry and compared with 2D positions and an Original-CS2 reference.

Therefore the map layer must expose `available / unavailable / version-mismatch`, and 3D must remain unavailable when the asset cannot be verified. The existing Nuke benchmark graybox is not a substitute for Anubis replay geometry.

## D. Render technology recommendation

Recommended proof-of-integration candidate: **Panda3D behind `ReplayRenderer`**, without committing the product contract to Panda3D.

Reasons:

- local Python runtime and Windows desktop support;
- first-person camera, procedural triangle meshes, simple materials, transparent utility volumes, and lightweight proxy players;
- native child-window support through `WindowHandle` / `WindowProperties.set_parent_window`, allowing a renderer to be embedded instead of opening an external browser;
- documented Python 3.13-compatible standalone `build_apps` / `bdist_apps` path;
- direct conversion of the raw `.tri` triangle soup without a browser/WebGL layer;
- smaller migration from the demonstrated Tkinter prototype than adopting a second UI and QML stack solely for 3D.

PySide6 + Qt Quick 3D is the fallback if the accepted product shell is first standardized on Qt. It has strong Windows/D3D11 integration and official deployment tooling, but adopting it now would silently decide the entire desktop UI stack and materially enlarge packaging. That is a separate product/architecture decision.

Before selection becomes binding, a disposable integration spike must prove:

1. embedding in the accepted desktop shell;
2. loading a reduced Anubis mesh;
3. deterministic `set_frame()` and first-person camera updates;
4. normal resize and shutdown;
5. a reproducible packaged Windows build;
6. acceptable startup time, memory, and frame pacing on a normal target desktop.

Required renderer boundary:

```text
ReplayRenderer
  load_map(map_asset)
  set_frame(replay_frame)
  set_camera_player(player_id)
  set_view_mode(view_mode)
  render()
  resize(width, height)
  dispose()
```

The renderer must never own replay time or alter analyzer data.

## E. Directly implementable work

The following work is implementable before any renderer is selected:

1. Define versioned, immutable replay contracts and explicit capability metadata.
2. Extend the Awpy adapter to populate per-tick states while preserving the current analysis result.
3. Introduce one tick-based `ReplayController` for both views.
4. Adapt the 2D replay to that controller and add round/tick/player regression tests.
5. Add a map-asset descriptor with source, map/build version, checksum, license/distribution status, coordinate transform, and availability reason.
6. Produce a disposable renderer-spike fixture from a small, verified subset of Anubis geometry only after the asset gate passes.

No 3D utility effect should be implemented until utility start/end ticks and evidence levels are normalized in the common contract.

## F. Concrete blockers

### Blocker 1 — canonical replay state

The active repository has a useful scene-only `iy.replay/v1` contract, but it cannot yet keep complete-match 2D and 3D views synchronized because it has no full-match frame contract or central playback controller. Both active and legacy artifacts still use name-based identity and omit incomplete/dead snapshots rather than retaining explicit inactive state. The legacy JSON additionally hardcodes a tick-rate argument.

### Blocker 2 — verified Anubis asset

The local triangle soup is technically readable but not yet proven current, semantically sufficient, or distributable. Using it as production map geometry now would violate the requirement not to invent or silently assume map truth.

### Blocker 3 — accepted desktop shell and packaging baseline

The active repository is a Python package whose validated review/viewer surface is generated HTML on local loopback; the only demonstrated native UI is a legacy Tkinter reference application. Renderer embedding and final packaging cannot be accepted until a native product shell and its reproducible build path are explicitly selected.

## Exit gate

The next single work item is **Phase A: evolve `iy.replay/v1` into a versioned canonical full-match replay contract and regression-test it against the existing real Anubis input, while recording exact field availability, event/utility coverage, tick identity, and player identity quality**.

After Phase A, approve one geometry provenance route:

- a checksummed local-only extraction tied to the installed CS2 build;
- a controlled, versioned derivative mesh with explicit distribution approval; or
- `3D unavailable` for Anubis until such an asset exists.

Only after both gates pass should the Panda3D integration spike begin. No merge of a renderer is authorized by this preflight.
