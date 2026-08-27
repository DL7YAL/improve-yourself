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

## Supported map set

The current repository provides concrete product/runtime evidence for exactly
three CS2 maps relevant to this static dataset:

- `de_ancient`: current Tactical MapRegistry proof and real Analyzer/Replay V2
  evidence.
- `de_mirage`: real 2D Viewer/V1 workflow evidence and an existing documented
  Awpy overview transform. Inclusion here is static metadata only and does not
  add a V1 runtime fallback.
- `de_anubis`: real Replay V2 and 3D/POV evidence plus a local map-asset gate.

Benchmark-only Nuke/Inferno references and maps that appear only as generic or
synthetic test strings are not silently declared supported Tactical maps.

Every supported map has one package under `maps/`. A package may be valid but
have an `UNVERIFIED` transform when a required source value cannot be verified.
That state is intentionally non-transformable.

## Layout

- `schema/iy.map_overview_metadata.v1.schema.json` — versioned JSON contract.
- `maps/de_ancient.json` — verified zero-rotation transform.
- `maps/de_mirage.json` — verified zero-rotation transform.
- `maps/de_anubis.json` — valid package with unresolved transform because its
  tracked descriptor omits an explicit rotation value.
- `../../tools/map_overview_data/validate.py` — deterministic, standard-library
  validator and transform reference implementation.
- `../../tests/map_overview_data/test_map_overview_data.py` — contract and
  map-specific tests.

No Valve radar image or other proprietary map asset is committed. The dataset
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
  unresolved and must not be inferred.
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
axis conversion and before clipping. This V1 contract accepts only verified
zero rotation. Non-zero or missing rotation is not guessed.

The transform returns floating-point coordinates without rounding. Bounds are
inclusive: `0 <= x <= width` and `0 <= y <= height`. Out-of-bounds values are
returned unchanged with `in_bounds = false`; they are never clamped or promoted
to valid positions.

Z does not participate in the X/Y transform. A viewer may select a layer only
when verified Z thresholds exist. None of the current packages claims verified
Z thresholds, so layer selection remains unresolved.

## Per-map transform status

### de_ancient — VERIFIED

- origin: `(-2953, 2164)`
- scale: `5`
- rotation: `0`
- canvas: `1024 x 1024`
- anchors:
  - `(-2953, 2164) -> (0, 0)`
  - `(-393, -396) -> (512, 512)`
  - `(2167, -2956) -> (1024, 1024)`

### de_mirage — VERIFIED

- origin: `(-3230, 1713)`
- scale: `5`
- rotation: `0`
- canvas: `1024 x 1024`
- anchors:
  - `(-3230, 1713) -> (0, 0)`
  - `(-670, -847) -> (512, 512)`
  - `(1890, -3407) -> (1024, 1024)`

### de_anubis — UNVERIFIED TRANSFORM

The tracked descriptor verifies `pos_x=-2796`, `pos_y=3328`, and `scale=5.22`,
but contains no explicit `rotate` field. The existing V1 contract requires an
explicitly verified zero rotation before numeric transform values become
trusted. Therefore the package keeps all active transform numbers `null`, uses
`UNRESOLVED` orientation, contains no transform reference points, and records
the observed source values only in provenance. A future task may activate them
only after rotation/orientation is independently verified.

Transform anchors validate projection bases only. They are not claims about a
player, bombsite, spawn, tick, event, or navigable geometry.

## Provenance and distribution

Projection descriptors are pinned to the tracked CS2 overview files at
SteamDatabase/GameTracking-CS2 commit
`8651ef311b783fee253fc15c30966e4a15a3cacb`.

The formula and 1024-pixel plotting convention are cross-checked against Awpy
commit `007b119a6a5b4b8ee7d3011d96ce00bed7323c12`, especially
`awpy/plot/utils.py` and `awpy/plot/plot.py`.

SteamDatabase GameTracking is a public tracker of shipped game files, not a
license to redistribute Valve artwork. Therefore no overview texture is copied.
Only the small numeric metadata required for projection is committed.

## Beast/Codex integration handoff

1. Data lives under `resources/map_overviews/`.
2. The supported dataset is exactly `de_ancient`, `de_mirage`, and `de_anubis`
   until a separate product-scope decision adds another map.
3. Validate `iy.map_overview_metadata/v1` before consuming a package.
4. Use only packages whose transform status is exactly `VERIFIED`.
5. Apply the formula above to canonical Replay/Analyzer world X/Y values.
6. Preserve float coordinates and the explicit `in_bounds` result.
7. Do not infer Z layers when thresholds are unresolved.
8. Load any future visual asset only through a separately approved asset path;
   this dataset intentionally ships none.
9. **Current tick and entity state MUST come from the existing canonical
   Replay/Analyzer path.**
10. **This package is data/projection metadata only.**
11. Do not add a V1 fallback, second parser, second ReplayStore, second
    ReplayController, second AnalyzerDataHub, or viewer-owned tick authority.

## Remaining unknowns

- No distributable overview images are included.
- No Z thresholds or multi-level selection rules are verified.
- No named landmark has a verified world-coordinate pair in this dataset.
- `de_anubis` rotation/orientation remains unresolved.
- Non-zero overview rotation is not implemented or asserted.
- Visual alignment against legally supplied runtime assets remains a future
  Beast/Codex acceptance step.
