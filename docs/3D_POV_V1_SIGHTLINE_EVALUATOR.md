# 3D/POV V1 — canonical sightline evaluator

Date: 2026-08-21

## Result

`SightlineResult` is now produced outside the renderer from exactly one canonical `ReplayFrame`, exact observer/target player IDs, the frame tick, and the same verified `VisibilityGeometry` used by the fixed Third-Person camera.

The result records `geometry_state`, `smoke_state`, `visible / occluded / unknown`, and explicit evidence. Missing/inactive player state, same-player requests, unknown geometry, or missing relevant smoke coverage never become visible by fallback.

Decision table:

| Geometry | Smoke | Result |
| --- | --- | --- |
| blocked | any | occluded |
| unknown | any | unknown |
| clear | blocked | occluded |
| clear | clear | visible |
| clear | unknown | unknown |

Smoke evaluation is deliberately behind a separate evidence provider. The default is `unknown`; this slice does not invent a smoke radius, lifetime or clear state from partial utility data.

The shared replay contract now owns `replay_frame_from_dict`, so the renderer spike and sightline evaluator restore the same validated serialized replay truth rather than maintaining local field mappings.

## Real Anubis validation

At canonical round 1/tick `6401`, observer `steam:76561198009555616`:

- target `steam:76561198263389260`: verified geometry `clear`, smoke `unknown`, final `unknown`;
- target `steam:76561198066871323`: verified geometry `blocked`, smoke `unknown`, final `occluded`.

The first result intentionally does not claim visibility. The second is occluded from verified geometry regardless of unavailable smoke evidence.

## Automated validation

- focused sightline/geometry/camera tests: 17 passed;
- complete suite: 81 passed;
- full reproducible setup and all five CLI smoke checks: PASS;
- local map derivative, replay and visual artefacts remain ignored and unchanged.

## Boundary

No overlay, rendering primitive, smoke-volume approximation, utility/event visualization, player model, interpolation, free camera, packaging or second replay interpreter was added.

## NEXT

Implement only the renderer presentation boundary for already evaluated `SightlineResult` values: draw eye-to-eye segments from the same canonical frame with fixed visible/occluded/unknown colors, never recompute geometry or smoke in the renderer. Prove FP and fixed-TP view switching preserves the same tick/player/result. Do not add smoke approximation or other utility/event overlays in that slice.
