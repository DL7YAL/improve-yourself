# 3D/POV V1 — Slice D renderer/embed spike

Date: 2026-08-21
Branch: `dev/v1-foundation`

## Result

Slice D is complete as a bounded integration proof. `ReplayRenderer` is now a backend-neutral protocol; First Person and the single fixed Third-Person Analysis Camera are deterministic functions of one canonical `ReplayFrame`. Missing position, yaw, pitch, activity or alive evidence makes the camera unavailable rather than inferred.

The disposable `PandaReplayRenderer` proves that the verified, ignored local-only Anubis GLB can be loaded into a real Panda3D viewport parented to a native Tk child window. The spike consumed canonical replay tick `4659`, selected player `steam:76561198009555616`, resized through `1100x700` and `900x560`, rendered the fixed Third-Person pose, and disposed without an orphaned window or process.

## Files and dependency boundary

- `src/improve_yourself/renderer.py`: stable protocol, camera contracts and headless lifecycle backend.
- `src/improve_yourself/panda_renderer.py`: disposable renderer candidate behind that protocol.
- `tools/dev/Run-RendererEmbedSpike.py`: local manual proof tool; it never packages the map.
- `tests/test_renderer.py`: deterministic camera/unavailable-state/protocol lifecycle tests.
- optional extra `renderer-spike`: exact local proof dependencies; the default V1 install remains unchanged.

The local GLB, visibility mesh, replay result and screenshot remain under ignored `results/`. No Valve-derived geometry or machine-specific output is tracked or distributable.

## Validation

- complete repository suite: `71 passed`;
- renderer-focused suite: `8 passed`;
- Python compilation: PASS;
- local Anubis asset gate during load: `available`;
- native child-window creation: PASS;
- canonical frame/player camera update: PASS;
- observed resize sizes: `1x1` startup, `1100x700`, `900x560`;
- dispose/automatic close: PASS;
- ignored screenshot visually inspected: geometry is present in the real fixed-TP frustum as an untextured cyan wireframe against the dark viewport.

Expected non-blocking warnings: the derived physics GLB contains primitives without materials. The spike deliberately applies a diagnostic wireframe override; this is not a production art/material decision.

## Fixed, adaptable and still open

Fixed by V1: one replay truth, the protocol surface, no freecam, evidence-only availability, FP pose, and the deterministic TP formula.

Still adaptable through acceptance: eye height and the two TP numerical offsets. Panda3D remains a candidate behind the protocol, not a settled product/UI-stack decision.

Not implemented in this slice: visibility-mesh camera obstruction correction, players/models, sightline overlay, utility/events, interpolation, product controls, asset distribution or packaging.

## NEXT

Implement only the verified visibility-mesh query boundary and the fixed Third-Person camera-to-anchor obstruction adjustment, including `camera_adjusted=true` and clear/blocked/unknown tests. Do not add overlays, smoke interpretation, player models, free camera, packaging or independent replay parsing.
