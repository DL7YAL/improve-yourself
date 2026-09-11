# Benchmark map world sections — implementation handoff

## Scope lock

This branch implements the approved world-building phase on top of
`559b67315634cdf3a6c77a698f84c128aec070a0`. The existing
`iy-benchmark/v1.2-candidate.2` controller, camera coordinates, event order and
64-second timing remain byte-identical. Camera composition and the performance
collector are later assignments.

Branch: `codex/benchmark-map-world-sections-v1`

## Baseline gap matrix

| Area | Evidence before this pass | Implemented response |
| --- | --- | --- |
| Intro | Isolated dark technical box; no cinema, brand screen or audience layout | Industrial cinema screen and frame, stage, four raised rows, 32 seats, 32 team spawn slots facing the screen, player start behind the rows, `IMPROVE BENCHMARK` lockup and `www.improve-yourself.com` |
| Ancient marker 27 | Oversized empty box; stretched walls; water read was weak | Temple threshold, raised water banks, four wet stepping stones and stone buttresses around the unchanged camera corridor |
| Ancient marker 38 | Camera ended against a flat dark wall; Red Room identity absent | Former end wall moved behind a deeper Red Room with red side/rear surfaces, threshold, ceiling beam, dais, dark niche, candles and crates |
| Inferno marker 48 | Five oversized trench-like blocks in a bright empty box | Existing steps narrowed, railings aligned, brick stringers and landing added |
| Inferno marker 53 | Sparse props and no convincing Apps depth | Orange/yellow Apps facades, recessed windows and sills, stone floor, three overhead beams and repeated provenanced props |

## Reproducible authoring path

The added pass is implemented in
`tools/benchmark/upgrade_benchmark_world_sections.py`. It accepts the
keyvalues2 representation of candidate.2 and refuses to run twice. It clones
the map's existing Hammer mesh/entity templates and references only assets
already covered by `TRANSITION_WORLDS_ASSET_PROVENANCE.json`.

The generated keyvalues2 source was converted back to binary VMAP with the
installed Valve `dmxconvert.exe`. The repository VMAP and installed addon source
then matched SHA-256
`74AE13F43EDA0FC213330A30D9714D16B2897710C5409378A9D4BF1294E4BEB6`.
The controller remains
`0038BAACB132A907654E03FE3B42B27BF198D5D1A23F4F9F0D8C87B5DF16723E`.

## Validation completed on 2026-09-11

The installed CS2 Resource Compiler completed a forced full map build:

```text
OK: 59 compiled, 0 failed, 0 skipped, 0m:54s
VPK SHA-256: F950D9ECA4389F9B1BA98C1D62E9AD925A283D28C70EE938FAC89468E4C232C8
```

Visibility, GPU light baking, navigation, bomb-damage data and VPK packaging all
completed. No controller file was deployed because its manifest hash was
unchanged.

Repository validation also completed:

```text
Focused benchmark-map tests: 17 passed
Full Python suite: 457 passed
compileall: passed
pip check: No broken requirements found
git diff --check: passed
```

## Open runtime gate

Fresh marker screenshots and a full post-build controller run are still
required before visual approval. The direct
`cs2.exe` validation launch used during this session accepted `-addon
improve_yourself_benchmark` on the command line but reported an empty active
addon set and rejected the map name. This is a launcher/mount problem, not a map
compile failure. Do not change camera coordinates to work around it.

Continue from the compiled VPK at:

```text
E:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo_addons\improve_yourself_benchmark\maps\improve_yourself_benchmark.vpk
```

Launch the addon through the CS2 Workshop Tools project selector so the active
host state shows `addons(improve_yourself_benchmark)`. Then capture:

1. the three-second `boot_delay` view for the cinema screen, player position and
   standing bots;
2. measured marker 27 (`ancient_b/water_reflection`);
3. measured marker 38 (`ancient_b/red_room`);
4. measured marker 48 (`inferno_apps_a/stairs`);
5. measured marker 53 (`inferno_apps_a/apps_details`).

The controller provides `iy_benchmark_status` and `iy_benchmark_finish_pass` for
correlation and warmup skipping. Preserve candidate.2 until all world images
are reviewed. After world approval, create a separate camera/intro-animation
assignment. Real player bots expose no stable animation/gesture method in the
installed `point_script.d.ts`; the cheering motion therefore remains in that
later assignment while this branch fixes their map spawn positions and facing.
