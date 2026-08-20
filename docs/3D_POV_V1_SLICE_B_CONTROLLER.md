# 3D / POV V1 — Slice B1 shared ReplayController

Status: `CONTROLLER_COMPLETE — 2D migration pending`

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

## Next

Migrate the existing 2D tactical view's state consumption to `ReplayController` plus `iy.replay/v2`, initially proving seek/scrub/scene/player/view synchronization. Keep automatic playback visibly unavailable for this real demo until a trusted timebase is added. Do not add 3D rendering in that migration.
