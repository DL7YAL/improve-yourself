# 3D / POV V1 — Slice B1 shared ReplayController

Status: `SLICE_B_COMPLETE`

Date: 2026-08-20

This bounded slice adds the sole mutable playback authority for `iy.replay/v2`. It does not add or alter a renderer, map asset, camera implementation, sightline implementation, benchmark, Optimizer or System Check.

## Implemented behavior

- immutable observable `ReplayContext` snapshots;
- atomic seek, scene seek, player selection, view switch and speed changes;
- canonical requested and resolved tick reporting;
- exact event/scene navigation across rounds;
- speed set restricted to `0.25`, `0.5`, `1.0` and `2.0`;
- wall-clock advancement derived only from an evidenced positive replay tick rate;
- deterministic round and match boundaries without collapsing global demo-tick gaps;
- preserved round, tick, player, scene, speed and play state during view switches;
- listener subscription without allowing views to mutate frame truth.

## Timing evidence result

The real private Anubis demo was inspected directly through `demoparser2.parse_header()`. Its header contains the demo format/version, patch, server, map and game directory, but no tick rate, playback duration or equivalent trusted timing field. The generated real `iy.replay/v2` manifest therefore correctly retains `source.tick_rate=null`.

Consequences:

- seek, scrub, scene selection, exact-tick event navigation and view switching are available;
- `play()` and wall-clock `advance()` fail explicitly with `PlaybackTimingUnavailable`;
- no 64 Hz default or FACEIT assumption is introduced;
- a UI can present timing as unavailable rather than silently playing at a fabricated speed.

## Validation

- 51/51 repository tests pass;
- seven focused controller tests cover resolved seek, state-preserving view switches, tick-rate/speed advancement, end-of-match pause, missing-timing refusal, relevant navigation, observation and invalid-state atomicity;
- full `Setup-V1.ps1` passes, including dependency consistency and all five existing public CLI help smokes;
- Python `compileall` and `git diff --check` pass;
- real ignored Anubis store smoke: 42 rounds, 22 scenes, scene seek resolves to its exact observed tick, timing unavailable, `play()` correctly blocked;
- existing `iy.replay/v1` viewer remains unchanged and green.

## 2D migration result

The existing `iy-replay-viewer` now accepts either the compatibility `iy.replay/v1` JSON artifact or the canonical `iy.replay/v2` manifest. For V2 it constructs an `iy.tactical_2d_projection/v1` through `ReplayStore` and `ReplayController`; the browser receives renderer-ready coordinates and never parses or reinterprets demo state.

The V2 view exposes scene and focus-player selection, requested/resolved tick labels, the shared-truth source marker and the explicit timing-unavailable state. Scene projection preserves the first frame, last frame and all event-bearing frames; additional frames are uniformly sampled to a maximum target of 256 per scene. This keeps canonical event identity while avoiding an impractical full-state HTML export.

Real Anubis result: 42-round/22-scene store rendered to a self-contained 11.0 MiB viewer in 5.93 seconds. The prior unsampled prototype was approximately 91.9 MB and was not retained as a repository artifact. Generated HTML remains ignored/local.

The local machine does not expose an installed Edge, Chrome or Firefox binary for an automated screenshot, so this slice has structural/HTML/runtime-generation validation but no new human visual acceptance claim. The already accepted V1 canvas projection/drawing code is preserved.

## Next

Begin Slice C only: establish an accepted, distributable Anubis asset manifest with checksums, coordinate transform and known-point/LOS proof. Do not begin the renderer until that asset gate passes.
