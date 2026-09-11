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

## Intended supported map set

The intended competitive/tactical data set is exactly:

- `de_ancient`
- `de_anubis`
- `de_dust2`
- `de_inferno`
- `de_mirage`
- `de_nuke`
- `de_overpass`
- `de_train`
- `de_vertigo`

The five newly prepared maps were explicitly requested for the product map set.
No additional real competitive map was found in current repository/product
evidence. Benchmark-only scene names and synthetic/test-only map strings are not
silently added.

Every supported map has one package under `maps/`. No Valve radar image or
other proprietary map asset is committed.

## Contract and intrinsic transform

Schema identifier: `iy.map_overview_metadata/v1`.

A consumer must validate a package before use. A transform is usable only when
`transform.verification_status` is exactly `VERIFIED`.

For every currently verified package:

```text
overview_x = (world_x - origin_world.x) / world_units_per_pixel
overview_y = (origin_world.y - world_y) / world_units_per_pixel
```

The canvas is logical `1024 x 1024`, starts at the upper-left, increases right
and down, preserves floating-point output, classifies bounds inclusively, and
does not clamp out-of-bounds values.

`rotation_deg_clockwise` describes intrinsic coordinate rotation only and is
`0` for every package. A Source/CS2 `rotate` flag is presentation metadata only;
it is recorded in provenance and MUST NOT be converted into intrinsic rotation.
Presentation behavior remains a later viewer concern and cannot alter Replay,
Analyzer, tick, or entity truth.

Z does not participate in X/Y projection. Layer metadata is independently
qualified. Nuke, Train, and Vertigo descriptors expose vertical-section values,
but this dataset keeps runtime layer selection `UNRESOLVED` because boundary
inclusivity, asset selection, and viewer policy are not part of the validated V1
contract. The observed source values remain available in provenance only.

## Per-map summary

| Map | Origin | Scale | Source rotate flag | Intrinsic rotation | Layers |
| --- | --- | ---: | ---: | ---: | --- |
| `de_ancient` | `(-2953, 2164)` | `5` | `0` | `0` | UNRESOLVED |
| `de_anubis` | `(-2796, 3328)` | `5.22` | absent | `0` | UNRESOLVED |
| `de_dust2` | `(-2476, 3239)` | `4.4` | `1` | `0` | UNRESOLVED |
| `de_inferno` | `(-2087, 3870)` | `4.9` | absent | `0` | UNRESOLVED |
| `de_mirage` | `(-3230, 1713)` | `5` | `0` | `0` | UNRESOLVED |
| `de_nuke` | `(-3453, 2887)` | `7` | absent | `0` | UNRESOLVED; source sections recorded |
| `de_overpass` | `(-4831, 1781)` | `5.2` | `0` | `0` | UNRESOLVED |
| `de_train` | `(-2308, 2078)` | `4.082077` | absent | `0` | UNRESOLVED; source sections recorded |
| `de_vertigo` | `(-3168, 1762)` | `4` | absent | `0` | UNRESOLVED; source sections recorded |

Each package contains top-left, center, and bottom-right deterministic projection
anchors. These are transform-basis checks only, not landmark or gameplay claims.

## Provenance and distribution

Projection descriptors are pinned per map to SteamDatabase/GameTracking-CS2.
Train uses commit `bff8fbc0e8558515aeed5d1db762889953c1d05a`;
the other current descriptors use commit
`8651ef311b783fee253fc15c30966e4a15a3cacb`.

Intrinsic formula and 1024-pixel plotting behavior are cross-checked against
Awpy commit `007b119a6a5b4b8ee7d3011d96ce00bed7323c12`.

GameTracking is a public tracker of shipped game files, not a license to
redistribute Valve artwork. No overview texture, executable content, demo, or
game asset is included.

## Beast/Codex integration handoff

1. Load packages only from `resources/map_overviews/maps/`.
2. Validate `iy.map_overview_metadata/v1` before consumption.
3. Use only a transform whose status is exactly `VERIFIED`.
4. Apply only the documented intrinsic X/Y formula.
5. Preserve float coordinates and the explicit `in_bounds` result.
6. Treat all current layer/floor selection as unresolved.
7. Do not convert Source presentation rotate flags into intrinsic rotation.
8. Supply visual assets only through a separately approved asset path.
9. **Current tick and entity state MUST come from the existing canonical
   Replay/Analyzer path.**
10. **This dataset is projection/map metadata only.**
11. Do not add a V1 fallback, parser, ReplayStore, ReplayController,
    AnalyzerDataHub, or viewer-owned tick authority.

## Remaining limitations

- No overview artwork is bundled.
- Layer/floor source observations are not an approved runtime selection policy.
- No named landmark world coordinates are claimed.
- Visual alignment against legally supplied runtime assets remains a future
  Beast/Codex acceptance step.
