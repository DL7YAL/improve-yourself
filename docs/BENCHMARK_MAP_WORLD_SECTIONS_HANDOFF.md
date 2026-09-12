# Benchmark map world sections — implementation handoff

Authoritative detailed assignment:
[`AUFTRAG_BENCHMARK_MAP_WELTENBAU_ANCIENT_INFERNO.md`](../AUFTRAG_BENCHMARK_MAP_WELTENBAU_ANCIENT_INFERNO.md)

## Scope lock

This branch implements the approved world-building phase on top of
`559b67315634cdf3a6c77a698f84c128aec070a0`. The existing
`iy-benchmark/v1.2-candidate.2` controller, camera coordinates, event order and
64-second timing remain byte-identical. Camera composition and the performance
collector are later assignments.

Original world-build branch: `codex/benchmark-map-world-sections-v1`

Current continuation branch: `codex/benchmark-v1.2-runtime-evidence`

Runtime authority: the Windows machine running Codex, CS2 Workshop Tools,
Hammer and the normal CS2 viewer. Linux/WSL is used only for the SSH/Git
connection; its checks are not Windows build or runtime evidence.

The source-only checkpoint was later promoted to `main` by explicit owner
authorization in PR #43 (`b56aa34`). On 2026-09-12 this continuation branch
restored the matching provenance records, reproducible authoring helpers,
focused world-section tests and this handoff without merging the stale branch
wholesale.

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

The historically compiled VPK was located under:

```text
<STEAM_LIBRARY>\steamapps\common\Counter-Strike Global Offensive\game\csgo_addons\improve_yourself_benchmark\maps\improve_yourself_benchmark.vpk
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

## Current acceptance status — 2026-09-12

Status: **PARTIAL**

- Repository and installed addon sources match byte-for-byte at VMAP SHA-256
  `74AE13F43EDA0FC213330A30D9714D16B2897710C5409378A9D4BF1294E4BEB6`
  and controller SHA-256
  `0038BAACB132A907654E03FE3B42B27BF198D5D1A23F4F9F0D8C87B5DF16723E`.
- The historical forced Full Compile and test evidence above belongs to those
  exact source hashes and therefore remains valid build evidence.
- The complete supplied Windows VConsole capture has SHA-256
  `9D5295BC4441C461D1BF74B4F487111479026086C030699CEE28CD992F57FABF`.
  Its authoritative `cs_script` stream validates `PASS` with exactly 39/39
  ordered events, one complete segment and no `[IYBENCH] ERROR`.
- No new Steam screenshot was found for the five required post-compile views.
- The 32 deterministic spawn slots and screen-facing placement are statically
  covered. A stable cheering animation and the required two-restart visual
  reproducibility proof are not implemented or evidenced.
- The same complete VConsole capture blocks world approval: the cubemap array
  is missing with 35,501 follow-on fog warnings, four nav-generation warnings
  request re-export, 33 vertical-velocity warnings affect bots/player, and
  only nine bots are present before the warmup begins.
- Workshop client-command restrictions reject 78 calls. Server-side effects
  must not be inferred from those client warnings, but client-only attack,
  fade and VProf calls are demonstrably not confirmed.
- `measurement_status=unverified` remains correct because no active frame
  collector was proven.

The next implementation point is Hammer on Windows: repair the missing cubemap
build and nav export, then isolate the bot floor/count and Workshop-safe
client-effect problems without changing camera coordinates, timings, scene
order or Azure configuration. Only after a fresh Full Compile succeeds should
the five visual captures and second audience restart be recorded.
The evidence-bound sequence is recorded in
[`BENCHMARK_RUNTIME_REPAIR_PLAN.md`](BENCHMARK_RUNTIME_REPAIR_PLAN.md).

Current repository checks on the continuation branch:

```text
Focused assertions without pytest: 12 passed
python3 compileall: passed
git diff --check: passed
pytest / pip check: not rerun; this Linux workspace has no installed pytest or pip
```

After adding the read-only runtime-log validator, the focused zero-fixture
total is 18 passed. The validator correctly classifies the previously supplied
restarted excerpt as `PARTIAL`: its latest segment contains 21 of 39 required
contract events and ends before the first measured capture window.

After adding the path-safe capture evidence collector, the focused
zero-fixture total is 21 passed. The collector refuses partial runtime logs,
missing or empty images, unsupported image extensions and duplicate capture
hashes; it keeps every visual result `UNREVIEWED` until actual inspection.

After adding the independent measured-completion save validator, the focused
zero-fixture total is 25 passed. The actual Windows `save_local.txt` passes
that validator with the hash and completion time recorded below.

After accepting the authoritative VConsole `cs_script` prefix, the focused
total is 26 passed and the complete supplied capture validates 39/39. After
adding the separate engine/world VConsole audit, the focused total is 29
passed. That audit intentionally reports `NEEDS_WORK` while retaining runtime
contract `PASS`.

The earlier 17/17 focused and 457/457 full-suite results remain historical
evidence from the original branch. They must not be represented as a fresh
rerun on the continuation branch.

## Usage-limit checkpoint — owner-reported display at 37%

This checkpoint was requested by the owner so that work can continue without
private chat context. The owner did not specify whether the displayed 37%
means consumed or remaining, so this handoff does not assume either. Commit
and push every new durable evidence slice; if more than 15% remaining capacity
cannot be confirmed, checkpoint immediately and stop before starting another
large slice. Never commit screenshots, logs, compiled VPKs, credentials or
private absolute paths.

The next bearer starts here, in this order:

1. Fetch `origin/codex/benchmark-v1.2-runtime-evidence` and verify a clean
   worktree before changing anything.
2. Read the authoritative root work order and this handoff completely.
   Execute the Windows gate using
   [`BENCHMARK_WINDOWS_RUNTIME_RUNBOOK.md`](BENCHMARK_WINDOWS_RUNTIME_RUNBOOK.md).
3. Confirm the repository and installed-addon VMAP/controller hashes still
   match the two hashes recorded above; use the existing sync workflow in
   read-only mode where PowerShell is available.
4. Preserve the locked route and timing. Repair/rebuild the missing cubemap,
   re-export nav, and prove the intended bot count/floor state plus a
   Workshop-safe replacement for rejected client-only effect/profiler calls.
5. In the normal CS2 viewer, run the addon uninterrupted through
   `PASS_END type=measured`, preserve the full VConsole text, and require both
   the 39-event contract `PASS` and absence of the recorded engine blockers.
6. Capture the intro and markers 27, 38, 48 and 53, then repeat a clean restart
   for the audience-state comparison. Store local captures outside Git and
   create their path-safe hash manifest with
   `py -3.13 .\tools\benchmark\collect_benchmark_evidence.py ...`. Store local
   captures outside Git and commit only their SHA-256, time/marker correlation
   and reviewed result.
7. Keep the assignment `PARTIAL` until every visual gate passes and a stable,
   deterministic cheering implementation is both available and proven. The
   installed `point_script.d.ts` exposes player lookup, teleport and model
   operations but no documented player animation, sequence, activity or
   gesture method; do not invent an unsupported API. Follow the isolated
   one-bot gate in
   [`BENCHMARK_BOT_CHEER_PROTOTYPE.md`](BENCHMARK_BOT_CHEER_PROTOTYPE.md).
8. Before any source change, preserve the locked controller/camera/timing
   hashes and follow READ -> SNAPSHOT -> APPLY -> VERIFY -> RESTORE.

Azure, Foundry and cloud execution are outside this assignment and must remain
untouched.

## Latest supplied Windows runtime capture

Input SHA-256:
`9D5295BC4441C461D1BF74B4F487111479026086C030699CEE28CD992F57FABF`

The complete capture contains one canonical `READY` segment and the entire
39-event contract through measured `PASS_END`. The corrected validator accepts
the authoritative VConsole `cs_script` prefix, ignores quoted `Console`
duplicates and reports `PASS`. The console event-order gate is closed.

The same Windows run later wrote the controller save record with
`runtimeStatus=complete`, `measurementStatus=unverified` and
`completedAt=135.1875`. Its 126-byte artifact SHA-256 is
`2A336BBAB6572FFF66821A94181821DD9141EE63D1D209361CCA91D669D67A3B`,
and its save contract validates as `PASS`. Measured runtime completion and the
full console event order are therefore both proven. The engine and visual
findings listed above remain open.
See [`BENCHMARK_RUNTIME_EVIDENCE_2026-09-12.md`](BENCHMARK_RUNTIME_EVIDENCE_2026-09-12.md).
