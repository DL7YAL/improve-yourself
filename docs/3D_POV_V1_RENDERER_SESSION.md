# 3D/POV V1 — ReplayController renderer session

Date: 2026-08-21

## Result

`ReplayRendererSession` is a one-way adapter from the existing sole mutable `ReplayController` to any `ReplayRenderer`. It subscribes to committed controller snapshots and never parses demos, resolves ticks, advances time, selects scenes, or owns playback state.

For every snapshot it:

1. requires serialized `frame.tick == resolved_tick`;
2. restores the typed frame through shared `replay_frame_from_dict`;
3. supplies that canonical frame to the renderer;
4. maps controller `first_person` to renderer `first_person`;
5. maps controller `analysis_third_person` to renderer `third_person`;
6. supplies the selected player when present;
7. records both requested and resolved ticks without collapsing them.

The session is render-active only for FP/fixed-TP with a selected player. Tactical 2D and no-selection states do not render 3D. Disposal unsubscribes from the controller and disposes the renderer exactly once.

## Validation

- focused controller/session tests: 9 passed;
- complete repository suite: 93 passed;
- requested tick 14 resolving to canonical tick 12 is preserved in tests;
- mismatched controller frame/resolved tick is rejected;
- Tactical 2D/no player remains inactive;
- real Anubis round 1/tick 6401 and player `steam:76561198009555616` flowed through the real ReplayStore and ReplayController into both FP and fixed TP;
- real proof retained requested/resolved `6401/6401`, rendered twice and disposed cleanly;
- full Setup-V1 and five public CLI smoke checks: PASS.

## Boundary

No product UI, playback loop, timer, parser, new state authority, sightline target-selection policy, smoke/utility rendering, asset packaging or benchmark change was added.

## NEXT

Connect the already evaluated sightline pipeline to `ReplayRendererSession` only through an injected, explicit-target coordinator: same typed frame, selected observer, caller-supplied target IDs, verified geometry and capability-gated smoke evidence. The session must pass ready `SightlineSegment` values to the renderer and clear them on Tactical 2D/no selection/tick change. Do not invent a target-selection UI/policy or add utility/event rendering.
