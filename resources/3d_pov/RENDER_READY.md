# Render-ready Anubis handoff

The render-ready package is rooted at:

```text
resources/3d_pov/de_anubis/render_ready.json
```

It combines the previously prepared geometry/coordinate/camera evidence with
original CC0 placeholder assets and explicit renderer fallback policies.

## Exact consumer files

- `de_anubis/prep.json` — geometry candidates, hashes, coordinate contract and
  real reference anchors.
- `de_anubis/render_ready.json` — renderer-facing package entry point.
- `de_anubis/semantic_assets.json` — player/weapon/material/sound mapping.
- `de_anubis/render_profile.json` — environment, camera fallback, dynamic and
  floor policy.
- `de_anubis/reference_scene.json` — isolated deterministic setup fixture.
- `original_assets/player_proxy.obj` — original abstract player geometry.
- `original_assets/weapon_proxy.obj` — original unit weapon-direction proxy.
- `original_assets/reference_bounds.obj` — diagnostic bounds only.
- `original_assets/materials.mtl` and `neutral_grid.ppm` — original neutral
  materials/texture.
- `LICENSE.md` — CC0 scope and third-party exclusion.

## Runtime connection sequence

1. Load and validate `render_ready.json` and its referenced metadata.
2. Ask the existing map-asset gate for a matching `iy.map_asset/v1` bundle.
3. If unavailable, show 3D unavailable; do not substitute diagnostic bounds in
   the product.
4. Subscribe through the existing renderer session to committed
   ReplayController snapshots.
5. Use the canonical resolved ReplayFrame and selected player.
6. Apply identity world-to-scene coordinates.
7. Build FP or fixed TP through the existing camera functions.
8. Map canonical team and weapon semantic IDs to the prepared generic assets.
9. Apply renderer fallbacks only where marked `FALLBACK`; never write them into
   Replay or Analyzer data.
10. Pass pre-evaluated sightline segments only; the renderer must not evaluate
    visibility or choose targets.

## Beast work still required

- run the deterministic validation gate;
- select/import these generic formats in the chosen renderer backend;
- load the existing local-only verified Anubis map bundle;
- connect the existing ReplayRenderer session;
- implement product UI state and unavailable messaging;
- measure load time, memory and display FPS;
- perform current-machine visual acceptance;
- package only original assets, never local Valve-derived map geometry.

No map-data research, coordinate derivation, asset-ID design, camera input
analysis, placeholder modeling, semantic mapping or licensing classification
should need to be repeated.
