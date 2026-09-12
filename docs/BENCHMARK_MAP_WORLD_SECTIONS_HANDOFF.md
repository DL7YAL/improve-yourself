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

## Runtime review completed on 2026-09-12

The direct `cs2.exe` launch still reports an empty active addon set. The
reliable validation path is:

1. open `csgocfg.exe`;
2. select the default `improve_yourself_benchmark` project;
3. choose `Edit Addon Map`;
4. press F9 in Hammer;
5. choose `Run ( Skip Build )` for the already compiled VPK.

This path ran the map and the byte-identical controller. One full run reached
`[IYBENCH] STATUS phase=complete pass=measured event=60`; no matching
`[IYBENCH] ERROR` line was found in the reviewed VConsole log. Measurement
status remains unverified.

Free post-compile inspection was also completed for the cinema and all four
required marker poses. The evidence and per-area findings are in
`docs/BENCHMARK_MAP_WORLD_SECTIONS_RUNTIME_REVIEW.md`.

Overall visual result is **PARTIAL**. Every area is `WORLD NEEDS WORK`:

- cinema text is mirrored and too small, the URL is unreadable, the display is
  grey, seat/bot placement clips and no cheering pose is active;
- Ancient Water does not read as water or reflection;
- Ancient Red Room does not read red;
- Inferno stairs exist but remain overexposed and externally open;
- Inferno Apps lacks a recognizable layered apartment interior.

Continue from the compiled VPK at:

```text
E:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo_addons\improve_yourself_benchmark\maps\improve_yourself_benchmark.vpk
```

Continue by correcting `tools/benchmark/upgrade_benchmark_world_sections.py`,
regenerating the binary VMAP from the candidate.2 keyvalues2 source, deploying
through `Sync-BenchmarkAddon.ps1`, forcing a full Resource Compiler build and
repeating the same five free-inspection captures. Preserve candidate.2 camera
data and controller hash throughout.

The first correction pass should address these concrete faults:

1. cinema world text facing and scale, dark screen separation, seat/back sizes
   and bot stand clearances;
2. a continuous visible Ancient water plane and a materially red enclosed Red
   Room;
3. closed Inferno stair/Apps volumes with visible warm facades and props;
4. one-bot cheering prototype before changing audience runtime logic.

Real player bots expose no stable animation/gesture method in the installed
`point_script.d.ts`. Do not claim the cheering criterion until an in-engine
prototype demonstrates a stable method. The team-spawn layout also does not yet
prove a deterministic rear user viewpoint distinct from bot audience slots;
resolve that in the later intro/controller assignment without changing the
current 64-second camera route in this branch.
