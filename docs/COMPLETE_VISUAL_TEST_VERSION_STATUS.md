# Complete Visual Test Version — current gate

Status: **PARTIAL_WITH_EXACT_ASSET_AND_OWNERSHIP_BLOCKERS**

## Established foundation

- Nine fail-closed numeric 2D overview projections are present on this branch.
- The Tactical Replay can load explicitly selected, external, local-only PNG
  surfaces without giving an image any replay or transform authority.
- Ancient and Anubis have real Analyzer -> Review -> Tactical source-flow
  evidence. Their image registration remains deliberately non-product.
- The Anubis 3D path already has Replay V2, ReplayStore, ReplayController,
  ReplayRendererSession, PandaReplayRenderer, FP/fixed-TP camera contracts,
  local `iy.map_asset/v1` assessment, and original CC0 fallback assets.
- `iy.asset_rights/v1` now keeps internal-reference permission separate from
  public distribution permission. Unknown and publication-blocked assets fail
  both gates; reference-only assets can pass only the internal gate.

## Bounded local visual inventory

The locally supplied map-named PNG files are complete UI reference mockups, not
standalone minimap surfaces. They contain illustrative players, routes, smoke,
events, scores, navigation, and other UI content. Cropping or loading them as
real replay backgrounds would manufacture gameplay evidence and is prohibited.

Separate usable local surfaces currently remain limited to the previously
validated Ancient and Anubis internal candidates. No standalone surface was
found for Dust2, Inferno, Mirage, Nuke, Overpass, Train, or Vertigo.

## Exact blockers

1. Seven standalone 2D surfaces are absent.
2. Ancient and Anubis still need landmark-based pixel registration.
3. Nuke, Train, and Vertigo need approved multi-level assets and a deterministic
   Z-boundary/layer-selection policy.
4. The Anubis local geometry is technically valid only through a matching
   local `iy.map_asset/v1` bundle and has no public redistribution grant.
5. `tools/dev/Build-LocalAnubisAsset.py` is owned by the active Azure Mirage
   preparation task and cannot be modified in this work item.
6. Product-shell 3D embedding, performance measurement, visible error states,
   and packaged runtime acceptance remain open.

## Release rule

An internal test candidate may reference an explicitly supplied local asset
only after the internal rights gate passes. A public candidate may include only
`OWNED` or `LICENSED_FOR_DISTRIBUTION` assets. A technically successful local
render never upgrades its rights status. No public-release-ready conclusion is
permitted while any packaged asset is `UNKNOWN`, `THIRD_PARTY_REFERENCE_ONLY`,
`LICENSED_INTERNAL_ONLY`, or `PUBLICATION_BLOCKED`.
