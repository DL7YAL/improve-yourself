# Benchmark Candidate 2 — runtime repair plan

Status: **PARTIAL POST-COMPILE — NAV/FLOOR/FOG REPAIR STILL REQUIRED**

This plan follows the world-build assignment after the complete Windows
VConsole capture. Windows Hammer/CS2 remains the runtime authority. Linux/WSL
is used only for Git, textual inspection and validation of supplied evidence.
Azure is excluded.

## Locked evidence

- benchmark: `iy-benchmark/v1.2-candidate.2`;
- complete VConsole SHA-256:
  `9D5295BC4441C461D1BF74B4F487111479026086C030699CEE28CD992F57FABF`;
- event contract: `PASS`, 39/39, one segment, no `[IYBENCH] ERROR`;
- engine/world audit: `NEEDS_WORK`;
- VMAP SHA-256:
  `74AE13F43EDA0FC213330A30D9714D16B2897710C5409378A9D4BF1294E4BEB6`;
- controller SHA-256:
  `0038BAACB132A907654E03FE3B42B27BF198D5D1A23F4F9F0D8C87B5DF16723E`.

## 2026-09-12 post-compile checkpoint

The owner added and visually checked the bounded cinema
`env_combined_light_probe_volume` in Hammer. The saved source is now versioned
at VMAP SHA-256
`B80C9111043DDB68ADF4CE5CB0C157050EE3AA470AA99F8BA6FCCCF5A2062AEF`.
The controller remains byte-identical at the locked hash above.

Hammer Full Compile completed once with world, standard-quality 1024
lightmaps, physics, visibility, navigation and Steam Audio enabled. The normal
viewer then ran `buildcubemaps`. Results:

```text
58 compiled, 0 failed, 1 skipped
VPK SHA-256: D15D2D879DD317B4276461AD7346280BBA790C18C71FB3F0518EF5ADB2426DEC
VConsole SHA-256: B97C260A3673A17EC78C3DB5ED41DB23E0C3E0CEA6291366A03C15BCC4DF18AC
save_local.txt SHA-256: C691BB7F52026B0E6AE230D44F70C1E1C9D1412C21D1CC2BF8CCCD96B2220DF9
```

The VPK directory contains the rebuilt `.nav`, `.vmap_c` and
`cubemaps/env_cubemap_array.vtex_c`. The formerly missing cubemap-array resource
is therefore repaired. Runtime contract and save-contract validation both
pass; the VConsole segment contains 39/39 ordered events and no
`[IYBENCH] ERROR`.

Engine acceptance remains `NEEDS_WORK`: 49,247 unresolved cubemap-fog
messages, four nav-generation mismatch warnings, 33 vertical-velocity
failures, nine rather than ten bots at first warmup, and 78 missing-FCVAR
rejections remain. The strict audit identifies 47 of those rejections in the
controller's client-only command set. No performance measurement is verified.

The compile proves that `Build nav` packages a nav resource, but it did not
clear the generation-parameter warnings. The next bounded hypothesis is to run
Hammer's `Nav Preview` / internal `GenerateNavPolyclip` exactly once while
`Use Custom Generation Params` remains disabled, save and hash the VMAP, then
perform at most one newly justified Full Compile. Do not repeat the current
compile unchanged.

Create a target-limited backup before changing either source. Do not overwrite
the authoritative addon manually in parallel with the sync workflow.

## Repair 1 — cubemap and probe coverage

The map contains a base combined light/reflection probe and a second expanded
probe for the positive-Y Ancient/Inferno corridor. The later cinema was built
around `-4000 -4000` and requires its own bounded
`env_combined_light_probe_volume`; a single map-wide probe would be needlessly
large and expensive.

In Hammer on the disposable source copy:

1. inspect the two existing `env_combined_light_probe_volume` entities;
2. add a separate cinema probe centered on the cinema room, covering its floor,
   walls, ceiling, screen, seats and all audience spawn positions;
3. keep the probe bounds local to the cinema rather than spanning all three
   disconnected worlds;
4. run a Full Compile with lighting/reflection generation enabled;
5. verify the compiled addon contains the generated cubemap resource and that
   a fresh viewer run has neither `cubemap_resource_missing` nor
   `cubemap_fog_unresolved`.

The current authored cinema envelope supports this initial Hammer transform:

```text
origin:   -4000 -4000 176
box_mins: -640 -480 -240
box_maxs:  640  480  272
```

Those local bounds cover world space `x=-4640..-3360`,
`y=-4480..-3520`, `z=-64..448`, including the authored room shell. Confirm
the entity gizmo encloses the complete cinema before compiling; do not apply
these bounds to either existing probe.

Do not approve Ancient water/reflection until the fresh visual capture is
reviewed after this repair.

## Repair 2 — nav export and bot floor state

The complete capture records four nav-generation parameter mismatches and 33
vertical-velocity failures. Re-export nav from the current saved VMAP and Full
Compile again. Then verify all staged bot positions have a solid floor at the
required pawn origin height.

Candidate 2 requests five T and five CT bots, but the captured Workshop launch
uses `numSlots=10`. With the local human player occupying one slot, only nine
bots are present at first warmup. The intended ten-bot workload therefore
requires at least eleven total slots and must be checked explicitly rather than
inferred from the ten `bot_add_*` calls.

For a disposable one-bot freeze probe, the current CS2 editor type definition
exposes `CSMoveType`, `GetMoveType()` and `SetMoveType()`. The addon-local type
definition is older. Refreshing a type declaration does not itself change the
runtime, and `SetMoveType(CSMoveType.NONE)` is only a candidate mechanism to
test fixed movement/floor behavior. It is not a cheering animation and must
not be deployed without two clean runtime proofs.

## Repair 3 — Workshop command boundary

The controller deliberately emits server commands and, for some calls, a
client command. The capture contains 78 missing-FCVAR rejections; the strict
audit attributes 47 to the controller's client-only command set. In particular,
attack and VProf calls are not confirmed by their markers.

Treat this separately from the world repair:

- do not weaken the 39-event contract or change route/timing;
- do not claim performance measurement while
  `measurement_status=unverified`;
- remove redundant client copies of server-side commands only after proving
  the server path still performs the intended action;
- replace a rejected client-only action only with a documented Workshop-safe
  mechanism and compare its workload before deployment;
- keep a missing replacement explicit instead of manufacturing success.

## Required verification order

1. Full Compile with cubemap/light generation and current nav export.
2. Read-only repository/addon source sync.
3. One uninterrupted normal-viewer run through measured `PASS_END`.
4. Runtime contract validator: `PASS`, 39/39.
5. VConsole audit: no cubemap/nav/vertical-velocity/bot-count blocker.
6. Five post-compile world captures and visual review.
7. Second clean cinema restart and bot-state comparison.
8. Isolated one-bot cheer prototype; retain `INSUFFICIENT_EVIDENCE` if no
   documented live-pawn method succeeds.
9. Full repository checks, final clean worktree, commit and push.

The assignment remains `PARTIAL` until every applicable gate above is closed.
