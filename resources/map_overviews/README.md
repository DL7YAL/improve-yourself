# 2D map overview metadata foundation

This directory contains static map geometry/projection metadata only. It does
not contain gameplay state, demo parsing, ticks, interpolation, events, players,
or playback authority.

The future Tactical consumer must obtain the current tick and all entity state
from the existing canonical path:

```text
AnalyzerCore -> AnalyzerDataHub -> iy.replay/v2 -> ReplayStore -> ReplayController
```

The overview package may only transform canonical world-space X/Y values into
2D overview coordinates. It must not become a parser, store, controller, data
hub, or source of gameplay truth.

## Layout

- `schema/iy.map_overview_metadata.v1.schema.json` — versioned JSON contract.
- `maps/de_ancient.json` — first numeric metadata pilot.
- `../../tools/map_overview_data/validate.py` — deterministic, standard-library
  validator and transform reference implementation.
- `../../tests/map_overview_data/test_map_overview_data.py` — contract tests.

No Valve radar image or other proprietary map asset is committed. The pilot
contains only numeric projection metadata and source notes.

## Contract summary

Schema identifier: `iy.map_overview_metadata/v1`.

Important fields:

- `map_id`: canonical CS2 map identifier.
- `asset`: optional overview image reference. `NOT_INCLUDED` plus `null` means
  no distributable asset is shipped.
- `canvas`: logical pixel dimensions and top-left, Y-down convention.
- `transform`: world origin, world-units-per-pixel scale, axis orientation,
  rotation, clipping, and rounding behavior.
- `layers`: Z/layer metadata only when verified. Unresolved thresholds remain
  `null` and must not be inferred.
- `reference_points`: deterministic transform anchors, not gameplay events.
- `provenance`: pinned source records and limitations.
- `verification`: package-level verified and unresolved fields.

A consumer must validate the document before use. A transform is usable only
when `transform.verification_status` is exactly `VERIFIED` and all required
numeric values pass validation. Unverified numeric values are rejected rather
than silently trusted.

## Coordinate transform

For the verified V1 axis-aligned convention:

```text
base_x = (world_x - origin_world.x) / world_units_per_pixel
base_y = (origin_world.y - world_y) / world_units_per_pixel
```

The logical canvas origin is the upper-left corner. Canvas X increases right;
canvas Y increases down. CS2 world X maps to positive canvas X. CS2 world Y is
inverted and maps to negative canvas Y before the subtraction above.

`rotation_deg_clockwise` is defined as clockwise screen-space rotation after
axis conversion and before clipping. This V1 pilot accepts only verified zero
rotation. Non-zero rotation is rejected until a map-specific convention is
verified.

The transform returns floating-point coordinates without rounding. Bounds are
inclusive: `0 <= x <= width` and `0 <= y <= height`. Out-of-bounds values are
returned unchanged with `in_bounds = false`; they are never clamped or promoted
to valid positions.

Z does not participate in the X/Y transform. A viewer may select a layer only
when verified Z thresholds exist. `de_ancient` has no verified layer thresholds
in this package, so its layer remains unresolved and must not be guessed.

## Pilot: de_ancient

`de_ancient` was selected because the repository already contains an explicit
unverified Ancient map-resource placeholder and real Ancient Replay V2 evidence,
while public game-tracking metadata exposes a simple zero-rotation overview
transform.

Verified numeric transform values:

- upper-left world origin: `(-2953, 2164)`
- scale: `5` world units per overview pixel
- rotation source value: `0`
- logical canvas: `1024 x 1024`

Derived deterministic anchors:

- `(-2953, 2164) -> (0, 0)`
- `(-393, -396) -> (512, 512)`
- `(2167, -2956) -> (1024, 1024)`

These anchors validate the projection basis only. They are not claims about a
player, bombsite, spawn, tick, event, or navigable geometry.

## Provenance and distribution

Projection numbers are transcribed from the tracked CS2 overview descriptor at
SteamDatabase/GameTracking-CS2 commit
`8651ef311b783fee253fc15c30966e4a15a3cacb`, file
`game/csgo/pak01_dir/resource/overviews/de_ancient.txt`.

The formula and 1024-pixel plotting convention are cross-checked against Awpy
commit `007b119a6a5b4b8ee7d3011d96ce00bed7323c12`, especially
`awpy/plot/utils.py` and `awpy/plot/plot.py`.

SteamDatabase GameTracking is a public tracker of shipped game files, not a
license to redistribute Valve artwork. Therefore no overview texture is copied.
Only the small numeric metadata required for projection is committed.

## Beast/Codex integration handoff

1. Data lives under `resources/map_overviews/`.
2. Validate `iy.map_overview_metadata/v1` before consuming it.
3. Apply the formula above to canonical Replay/Analyzer world X/Y values.
4. Preserve float coordinates and the explicit `in_bounds` result.
5. Do not infer Z layers when thresholds are unresolved.
6. Load any future visual asset only through a separately approved asset path;
   this pilot intentionally ships none.
7. **Current tick and entity state MUST come from the existing canonical
   Replay/Analyzer path.**
8. **This package is data/projection metadata only.**
9. Do not add a V1 fallback, second parser, second ReplayStore, second
   ReplayController, second AnalyzerDataHub, or viewer-owned tick authority.

## Remaining unknowns

- No distributable overview image is included.
- No Z thresholds or multi-level selection rules are verified for Ancient.
- No named landmark has a verified world-coordinate pair in this package.
- Non-zero overview rotation is not implemented or asserted.
- Visual alignment against a legally supplied runtime asset remains a future
  Beast/Codex acceptance step.
