# 2D Tactical Game-Map Coverage

Status: **PARTIAL_2D_GAME_MAP_COVERAGE_WITH_MATRIX**

Internal-use authorization: **GRANTED BY PROJECT OWNER**
Public upload/release authorization: **NOT GRANTED**

Base: GitHub `main` `ef3e96aad0675b963d66b10ecdc8e40613af17b5`

## Product scope

The Tactical Replay target is data-driven game-map coverage for every map in
the currently evidenced competitive product set, not a hard-coded four-map
implementation. The current evidenced set is:

- `de_ancient`
- `de_anubis`
- `de_dust2`
- `de_inferno`
- `de_mirage`
- `de_nuke`
- `de_overpass`
- `de_train`
- `de_vertigo`

New canonical map IDs may be added through the same manifest and validation
contracts when product or replay evidence establishes them. Tactical code must
not require a map-specific branch for each addition.

## Authority boundary

Map images are presentation assets only. Map ID, scene, tick, player state and
playback remain on the existing canonical path:

```text
AnalyzerCore -> AnalyzerDataHub -> iy.replay/v2 -> ReplayStore
             -> ReplayController -> Tactical Replay
```

World-to-overview coordinates come only from the matching verified
`iy.map_overview_metadata/v1` package. An image must not supply, modify or
override origin, scale, intrinsic rotation, tick or layer truth.

## Bounded local inventory

The authorized read-only inventory covered the Improve Yourself repository,
known Improve Yourself worktrees, and the one bounded local project tree named
by the project owner. It did not search complete drives, extract VPK content,
download assets or modify historical worktrees. No private absolute path is
retained in this handoff.

### Candidate 1: Anubis local test surface

- Map ID: `de_anubis`
- File: `de_anubis.png`
- Dimensions: `877 x 807`
- Mode: `RGBA`
- Bytes: `163993`
- SHA-256: `6c2a543b49d7cc3047db5f02d6547eee2dff5029ec32bd56183d40554da6bf0d`
- Existing manifest: `iy.local_test_map_surfaces/v1`
- Distribution: `LOCAL_ONLY`
- Registration: `FULL_OVERVIEW_CANVAS_UNVERIFIED_LOCAL_TEST`
- Assessment: visually recognizable and hash-bound, but its existing contract
  explicitly does not prove pixel registration against the logical 1024 x 1024
  overview canvas. It is not ready for silent packaging as a verified product
  map.

### Candidate 2: Ancient base overlay

- Map ID: `de_ancient`
- File: `base_overlay.png`
- Dimensions: `1024 x 1024`
- Mode: `RGBA`
- Bytes: `1502116`
- SHA-256: `55da4f041436e50a4a788f2e1bbf5de2652c20e621dfd89c3ca344c8139f3914`
- Existing image manifest in the inspected source: none
- Assessment: visually suitable as a dark Tactical background candidate, but
  the inspected historical asset directory does not bind it to a 2D
  `iy.map_asset/v1` manifest, provenance record or verified runtime alignment.
  It is not ready for silent packaging.

### Rejected as product artwork: Ancient collision preview

The separate `de_ancient_preview.png` is a deterministic collision/debug
visualization. It is not a product-ready game-map surface and must not be used
as a substitute merely because it is 1024 x 1024.

## Coverage matrix

| Map ID | Transform metadata | Image candidate | Image registration | Layer status | Internal package status | Exact next evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `de_ancient` | VERIFIED | found | local hash-bound surface visibly exercised; alignment remains non-product | UNRESOLVED | INTERNAL SOURCE FLOW READY | establish landmark-based product registration |
| `de_anubis` | VERIFIED | found | local hash-bound full-canvas fit visibly exercised; alignment remains non-product | UNRESOLVED | INTERNAL SOURCE FLOW READY | establish landmark-based pixel registration |
| `de_dust2` | VERIFIED | not found | unavailable | UNRESOLVED | BLOCKED | provide or create an authorized map image |
| `de_inferno` | VERIFIED | not found | unavailable | UNRESOLVED | BLOCKED | provide or create an authorized map image |
| `de_mirage` | VERIFIED | not found | unavailable | UNRESOLVED | BLOCKED | provide or create an authorized map image without touching Azure-owned 3D files |
| `de_nuke` | VERIFIED | not found | unavailable | UNRESOLVED; source sections recorded | BLOCKED | provide authorized layer images and approve an evidence-based layer policy |
| `de_overpass` | VERIFIED | not found | unavailable | UNRESOLVED | BLOCKED | provide or create an authorized map image |
| `de_train` | VERIFIED | not found | unavailable | UNRESOLVED; source sections recorded | BLOCKED | provide authorized layer images and approve an evidence-based layer policy |
| `de_vertigo` | VERIFIED | not found | unavailable | UNRESOLVED; source sections recorded | BLOCKED | provide authorized layer images and approve an evidence-based layer policy |

## Current reusable implementation evidence

A historical, unmerged `codex/2d-viewer-local-minimaps-v1` commit contains a
generic fail-closed loader for an explicitly selected external
`iy.local_test_map_surfaces/v1` manifest. It preserves the canonical replay
boundary, validates relative paths, PNG limits and SHA-256, and falls back to
the image-free verified projection. Its old commit also changes current
coordination and UI files and is therefore reference material, not something
to merge wholesale.

The generic loader may be ported in a later implementation slice after the
image-registration decision. It must be adapted to current `main` and tested;
it must not make `FULL_OVERVIEW_CANVAS_UNVERIFIED_LOCAL_TEST` equivalent to a
verified packaged game map.

## Internal-test authorization and remaining gate

The project owner explicitly authorizes all intended map images for local
development and packaging to a controlled, limited internal tester group. No
separate per-image internal-use approval is required once an image has been
identified. This permission does not turn an unverified transform into a
verified one, does not establish third-party ownership, and is not a public
upload or release authorization.

Public builds must exclude these assets unless a later release-specific gate
records the necessary complete approval, including Valve or other third-party
permission where applicable. Internal and public packaging therefore remain
separate explicit build policies.

Packaging remains blocked until each included image has:

1. an unambiguous canonical map ID;
2. a relative, hash-bound asset manifest;
3. a validated pixel registration to its verified transform metadata;
4. an explicit layer result;
5. a visible real Replay V2 alignment check;
6. a package inventory proving that only approved map assets were included.

The source application now loads Ancient and Anubis from one explicitly
selected external `LOCAL_ONLY` manifest. Both real workflow paths were visibly
exercised through Analyzer, Review, and Tactical Replay. This source-flow proof
does not upgrade either provisional image registration to product-verified.

Missing maps must continue to show the honest neutral grid or
`GAME MAP NOT AVAILABLE FOR THIS MAP ID`. A missing image must never select a
different map or guessed transform.

## Next decision

The smallest safe continuation is landmark-based registration of the exercised
Ancient and Anubis images. In parallel, the remaining seven map images and the
Nuke/Train/Vertigo layer policy must be supplied or explicitly commissioned.
Complete nine-map packaging cannot be claimed from the current local asset
inventory.
