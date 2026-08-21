# 3D/POV V1 — sightline presentation boundary

Date: 2026-08-21

## Result

The renderer can now receive immutable, already evaluated `SightlineSegment` values. Segment construction validates that the `SightlineResult` tick matches the canonical `ReplayFrame`, resolves only the two observed eye positions, and assigns the fixed V1 result color. It never calls visibility geometry or smoke evidence.

Fixed colors:

- visible: green `(0.20, 0.85, 0.42, 1.0)`;
- occluded: red `(0.95, 0.30, 0.22, 1.0)`;
- unknown: neutral gray `(0.62, 0.66, 0.72, 1.0)`.

`ReplayRenderer.set_sightlines` is implemented by both the headless lifecycle backend and the disposable Panda candidate. Panda converts the supplied start/end/color values directly into line primitives. Replacing the set removes the prior node; changing FP/fixed-TP view mode does not change the supplied sightline identities, tick or result.

## Real validation

The native Anubis spike ran at round 1/tick `6401`, observer `steam:76561198009555616`, with two previously evaluated results:

- target `steam:76561198263389260`: unknown, geometry clear, smoke unknown;
- target `steam:76561198066871323`: occluded, geometry blocked, smoke unknown.

The renderer switched `third_person -> first_person -> third_person`, preserved both results, resized `1100x700 -> 900x560`, and disposed cleanly. The ignored screenshot visibly contains the red occluded line and local map wireframe. The nearby neutral line is not claimed as a fully isolated visual proof in that camera composition; its exact gray mapping and persistence are covered deterministically.

## Validation

- focused sightline/renderer tests: 18 passed;
- complete repository suite: 84 passed;
- native exact-tick presentation, view switching, resize and dispose: PASS;
- local asset/replay/screenshot remain ignored and unmodified.

## Boundary

No geometry or smoke recomputation occurs in the renderer. No smoke approximation, player model, utility/event overlay, interpolation, free camera, asset packaging or benchmark change was introduced.

## NEXT

Implement only the canonical smoke-evidence gate needed by `SightlineResult`: require explicit full lifetime/position coverage before a fixed disclosed V1 smoke-volume approximation may return clear or blocked. Partial/unavailable coverage must return unknown. Validate on synthetic boundary cases and report the real Anubis capability without drawing smoke or other utility/event overlays.
