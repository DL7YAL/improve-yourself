# 2D Minimap Runtime Review

Status: **ANCIENT_AND_ANUBIS_INTERNAL_SOURCE_FLOW_READY; PACKAGED STARTUP PARTIAL**

Base: GitHub `main` `ef3e96aad0675b963d66b10ecdc8e40613af17b5`

## Runtime proof

Two private local PNG candidates were copied into a fresh, non-versioned
internal-test folder and bound by one `iy.local_test_map_surfaces/v1` manifest.
No map image, private path, demo, workflow result, or asset hash is stored in
this repository.

### Ancient

- Existing real `iy.demo_workflow/v1` opened fail-closed.
- Analyzer reported 23 rounds, 10 players, and 65 merged scenes.
- Review opened the selected canonical scene.
- Tactical Replay displayed the local surface with ten canonical player
  markers and view directions.
- The first zoom-in action changed the rendered scale after a focused scaling
  correction.
- Back navigation returned to the same Review scene.

### Anubis

- Historical local fixtures used Zstandard chunks that the current `main`
  ReplayStore does not consume; they were preserved unchanged.
- A fresh workflow was generated from the explicitly authorised local demo
  using the current branch environment and a fresh ignored result folder.
- The fresh workflow passed the complete existing-workflow integrity check.
- Analyzer reported 24 rounds, 10 players, and 67 merged scenes.
- Review and Tactical Replay visibly displayed the selected canonical scene,
  local surface, player markers, and view directions.

## Reproducible defects corrected

1. Integer-only image scaling made the first zoom step visually inert. The
   renderer now uses a bounded rational Tk zoom/subsample ratio.
2. Startup workflow validation ran before the Tk event loop and exposed a
   completely white window during an approximately ten-second integrity check.
   The unchanged fail-closed check is now scheduled after the branded shell is
   visible and reports its honest loading status.

## Internal package check

- A separate internal portable candidate was built with the existing locked
  Python 3.13 environment after the complete test suite passed. No dependency
  was installed or updated during this build.
- The executable and ZIP are SHA-256-bound by a local, non-versioned build
  manifest. The inventory contains no demo, workflow, results directory,
  `.venv`, local surface manifest, private path, or local map artwork.
- The packaged process exposed the expected window title after 0.53 seconds,
  but did not become responsive until 20.04 seconds. This is a reproducible
  packaged-startup defect, so the candidate is **not** classified as ready for
  testers and the overall UI V1 closure gate remains partial.
- The normal build script was not used because it necessarily performs a pip
  install. The task explicitly prohibited package installation as a workaround;
  the existing environment instead passed `pip check` before direct packaging.

## Truth and release boundary

- Map artwork remains presentation-only.
- Map ID, scene, tick, playback, players, and view directions remain owned by
  the canonical ReplayStore and ReplayController path.
- World-to-pixel projection remains owned by verified
  `iy.map_overview_metadata/v1` documents.
- Ancient and Anubis remain labelled as internal test surfaces whose image
  registration is not product-verified.
- The ordinary packaged candidate includes numeric overview metadata but no
  map artwork or local asset manifest.
- Public distribution of the private map folder remains prohibited without a
  separate release-specific rights decision.

## Remaining coverage

Concrete map images are still missing for Dust2, Inferno, Mirage, Nuke,
Overpass, Train, and Vertigo. Nuke, Train, and Vertigo additionally require an
explicit multi-layer decision and validation. No substitute, guessed layer, or
fake map image was introduced.
