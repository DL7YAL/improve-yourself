# Benchmark map world sections — post-compile runtime review

Date: 2026-09-12

Status: **PARTIAL / NEEDS_WORK**

Measurement status: **UNVERIFIED**

## Scope and authority

This review binds the owner-operated Windows Hammer Full Compile and normal
CS2 viewer run to the promoted benchmark sources. Linux was used only for
read-only hashing, VPK-index inspection, validation and Git. Azure and cloud
execution were not used. Codex did not claim to operate or visually observe
the Hammer/CS2 GUI actions performed by the owner.

No controller, camera route, scene timing, bot position, geometry outside the
cinema probe, dependency, lockfile or system configuration changed.

## Source binding

```text
Branch: codex/benchmark-v1.2-runtime-evidence
Base HEAD: c48220d688e41c160ff551451fcba72f959ecd82
VMAP SHA-256: B80C9111043DDB68ADF4CE5CB0C157050EE3AA470AA99F8BA6FCCCF5A2062AEF
Controller SHA-256: 0038BAACB132A907654E03FE3B42B27BF198D5D1A23F4F9F0D8C87B5DF16723E
```

The VMAP adds one cinema-local `env_combined_light_probe_volume`:

```text
origin: -4000 -4000 176
angles: 0 0 0
scale: 1 1 1
box_mins: -640 -480 -240
box_maxs: 640 480 272
client-only: yes
priority: normal
```

Hammer reported 79 entities, four lighting objects and three combined probes.
The owner confirmed the gizmo and saved the source. Static binary inspection
found exactly one new origin triple and the two new bound strings in the saved
VMAP.

## Navigation and build configuration

Both `ToolNavMesh` help entries expose the same commands:

```text
LoadNavPolyclip
GenerateNavPolyclip
CreateWalkableSeed
CreateMarkupNode
ResetGenParams
```

The tool labels map `LoadNavPolyclip` to `Load Nav From VPK` and
`GenerateNavPolyclip` to `Nav Preview`. Before the build, `Save Debug Stages`,
`Save Recast Debug Stages` and `Use Custom Generation Params` were disabled;
no agent-hull preset was visibly selected. No reset, new walkable seed or new
markup node was used.

The selected Full Compile used world build, standard-quality 1024 lightmaps
with noise removal and compression, physics, visibility, nav and the configured
Steam Audio bakes. Loading after build and `buildcubemaps` were enabled.

```text
Build end: 2026-09-12 09:39:27 Europe/Berlin
Result: 58 compiled, 0 failed, 1 skipped
Elapsed: about 40 seconds
VPK SHA-256: D15D2D879DD317B4276461AD7346280BBA790C18C71FB3F0518EF5ADB2426DEC
```

The one skipped item was not identified by the retained screenshot. The build
reported a 20-element `CDataModel` leak warning after the successful compiler
summary. Neither observation changes the zero-failure result, but both remain
explicit.

Structured VPK-directory inspection found 65 entries, including:

```text
maps/improve_yourself_benchmark.nav
maps/improve_yourself_benchmark.vmap_c
maps/improve_yourself_benchmark/cubemaps/env_cubemap_array.vtex_c
```

The cubemap array entry is 1,574,304 bytes. Compiled artifacts and raw build
outputs remain local and are not committed.

## Runtime contract

```text
VConsole SHA-256: B97C260A3673A17EC78C3DB5ED41DB23E0C3E0CEA6291366A03C15BCC4DF18AC
save_local.txt SHA-256: C691BB7F52026B0E6AE230D44F70C1E1C9D1412C21D1CC2BF8CCCD96B2220DF9
Runtime validator: PASS
Save validator: PASS
Segments: 1
Canonical events: 39/39
IYBENCH errors: 0
Runtime status: complete
Measurement status: unverified
Controller completion time: 135.203125
```

The raw VConsole and save record remain outside Git.

## Engine audit

| Finding | New result | Decision |
| --- | ---: | --- |
| Missing cubemap-array resource | 0 | Repaired; resource exists in VPK |
| Unresolved cubemap-fog source | 49,247 | BLOCKER |
| Nav-generation mismatch | 4 | BLOCKER |
| Vertical-velocity failure | 33 | BLOCKER |
| Bots at first warmup | 9 of 10 | BLOCKER |
| All missing-FCVAR rejections | 78 | BLOCKER |
| Known client-only rejected calls | 47 | BLOCKER |

The nine bots at the first plain warmup marker were `Adonis`, `Colin`, `Efe`,
`Frank`, `Rivers`, `Telsen`, `Ulric`, `Uri` and `York`. Vertical failures
affected all nine plus the local player. Ten issued `bot_add_*` commands are
not evidence of ten simultaneous bots.

The strict audit correctly retains runtime-contract `PASS` and overall
`NEEDS_WORK`. Its bot field is `null` only because that helper currently uses
the prefixed VConsole warmup form while this export retained the plain form; a
read-only count using the same create/identity/kick rules and the plain marker
proves nine bots.

## Validation and environment boundary

- runtime-contract validator: passed;
- independent save validator: passed;
- structured VPK index: passed and required entries found;
- VMAP/controller/addon hash binding: passed;
- seven focused benchmark modules through their zero-fixture test functions:
  29 passed, 0 failed;
- `compileall` under available Linux Python 3.14: passed as a supplemental
  syntax check;
- `git diff --check`: passed before documentation update;
- secret-marker and artifact-path check: no new finding;
- fresh pytest and `pip check`: not run because this Linux SSH environment has
  neither the required Python 3.13 environment nor pytest/pip;
- Windows non-interactive SSH validation: unavailable because authentication
  was rejected; no credential or host-key state was changed.

The full pytest suite and `pip check` remain environment-blocked. The older
457-test full-suite result is historical baseline evidence, not a fresh result
for this VMAP.

## Next bounded task

`Build nav` packaged a new nav entry but the four generation-parameter warnings
remained. This supplies one new hypothesis for a single follow-up attempt:

1. verify the branch, source hashes and clean worktree;
2. open the promoted VMAP in Hammer;
3. leave `Use Custom Generation Params` disabled and do not reset parameters;
4. invoke `Nav Preview` / `GenerateNavPolyclip` exactly once;
5. require an observable generated preview or dirty-state change, then save and
   record a new VMAP hash;
6. only with that new evidence, run one Full Compile using the recorded options;
7. compare nav warnings and artifact hashes before any further attempt.

Stop `BLOCKED` if step 4 produces no new evidence or Hammer asks to delete or
replace unknown data. Do not start adjacent feature work. The unresolved
cubemap-fog binding, bot slot/floor state, rejected client commands, five
marker-correlated captures and second clean cinema restart remain separate
gates.
