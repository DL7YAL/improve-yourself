# Benchmark runtime evidence — 2026-09-12

Benchmark: `iy-benchmark/v1.2-candidate.2`

Windows is the runtime authority. This record contains only safe textual
metadata. The VPK, raw VConsole capture and save record are not committed to
this repository. Their hashes, contents and the validation results derived
from those contents are therefore documented runtime evidence, not artifacts
that can be independently recomputed or inspected from this checkout.

The versioned source files are independently checkable. At the current
post-compile source checkpoint they are:

```text
VMAP SHA-256: B80C9111043DDB68ADF4CE5CB0C157050EE3AA470AA99F8BA6FCCCF5A2062AEF
Controller SHA-256: 0038BAACB132A907654E03FE3B42B27BF198D5D1A23F4F9F0D8C87B5DF16723E
```

## Historical pre-repair evidence

The following artifacts belong to the earlier pre-repair/pre-probe VMAP at
SHA-256
`74AE13F43EDA0FC213330A30D9714D16B2897710C5409378A9D4BF1294E4BEB6`.
They must not be presented as the current post-compile artifacts.

### Historical measured-completion save

The installed addon wrote its relative save-data artifact at
`cfg/workshop_saves/save_local.txt` on 2026-09-12 at 02:28:48 CEST.

```json
{
  "version": "iy-benchmark/v1.2-candidate.2",
  "runtimeStatus": "complete",
  "measurementStatus": "unverified",
  "completedAt": 135.1875
}
```

Historical artifact metadata:

- size: 126 bytes;
- SHA-256: `2A336BBAB6572FFF66821A94181821DD9141EE63D1D209361CCA91D669D67A3B`;
- documented save-contract validation: `PASS`.

The controller writes this record only in the measured branch of `endPass()`,
after emitting the final Inferno report and
`PASS_END type=measured runtime_status=complete measurement_status=unverified`.
This documents that the historical Windows runtime reached measured
completion. It does not claim a verified performance measurement.

### Historical VConsole capture

The historical complete Windows VConsole capture has SHA-256
`9D5295BC4441C461D1BF74B4F487111479026086C030699CEE28CD992F57FABF`.
Its documented authoritative `cs_script` channel contains one `READY` segment
and exactly all 39 required canonical events in order. The quoted `Console`
channel echoes are duplicates and are ignored. The historical runtime-contract
result is `PASS`, with one segment, no `[IYBENCH] ERROR`,
`runtime_status=complete` and `measurement_status=unverified`.

The validator accepts both plain `[IYBENCH]` lines and the actual VConsole
`[ cs_script ]: [IYBENCH]` form while continuing to reject quoted console
echoes. The earlier 139-line excerpt remains useful restart evidence at
SHA-256
`619FEFBFC04A5C83CA70A4951ABFE896F9D9E4D7EFCE1F3366D1D217B9F90A7E`,
but its latest segment is only 21 of 39 events and does not supersede the
historical complete capture.

The historical capture recorded a missing cubemap-array resource and 35,501
follow-on `env_cubemap_fog` warnings. That missing-resource finding was tied to
the pre-repair VPK and does not describe the current post-compile VPK.

## Current post-compile checkpoint

The owner-operated Hammer Full Compile is documented with this result:

```text
Full Compile: 58 compiled, 0 failed, 1 skipped
VPK SHA-256: D15D2D879DD317B4276461AD7346280BBA790C18C71FB3F0518EF5ADB2426DEC
VConsole SHA-256: B97C260A3673A17EC78C3DB5ED41DB23E0C3E0CEA6291366A03C15BCC4DF18AC
save_local.txt SHA-256: C691BB7F52026B0E6AE230D44F70C1E1C9D1412C21D1CC2BF8CCCD96B2220DF9
```

The VPK, VConsole capture and `save_local.txt` are outside this repository.
Their bytes and the claims below cannot be independently verified from this
checkout. The retained post-compile review documents that structured VPK-index
inspection found the rebuilt `.nav`, `.vmap_c` and
`cubemaps/env_cubemap_array.vtex_c`. The cubemap array is therefore documented
as present in the current VPK; this does not resolve the cubemap-fog blocker.

The current runtime contract is documented as `PASS`: 39/39 canonical events
in order, one segment and no `[IYBENCH] ERROR`. Runtime status is `complete`.
`measurement_status` remains `unverified`; neither runtime completion nor the
markers prove a verified performance measurement.

## Current engine findings

The contract pass proves controller sequencing, not world acceptance. The
post-compile evidence retains these material findings:

- 49,247 unresolved cubemap-fog messages remain even though the VPK inspection
  documents the cubemap-array resource as present;
- four nav-generation parameter warnings remain;
- 33 player/bot vertical-velocity failures affect all nine bots present before
  warmup and the local player, so fixed floor placement is not proven;
- nine bots are present at the first warmup marker; ten issued `bot_add_*`
  commands do not prove ten simultaneous bots;
- 78 client-command/convar attempts are rejected for a missing FCVAR flag.
  The companion audit assigns 47 of them to the known controller client-command
  set, including attack and VProf commands, so their markers do not prove that
  those actions ran.

These findings do not revoke the runtime-contract `PASS`; they keep the engine
and world result at `NEEDS_WORK`. Cubemap fog, navigation, bot count/floor state
and rejected client commands remain unresolved. Overall assignment status is
therefore **PARTIAL**.

## Bounded nav hypothesis — review only

This documentation checkpoint does not execute the nav hypothesis. A later,
separately authorized Hammer attempt must remain within these bounds:

1. keep `Use Custom Generation Params` disabled;
2. do not use `ResetGenParams`;
3. invoke `Nav Preview` / `GenerateNavPolyclip` at most once;
4. save only if that action creates new observable preview or dirty-state
   evidence, then record the new VMAP hash;
5. run at most one newly justified Full Compile after that new evidence;
6. do not repeat the existing compile unchanged.

Stop `BLOCKED` if the one preview attempt produces no new observable evidence
or Hammer asks to delete or replace unknown data.

## Remaining acceptance gates

- five post-compile visual captures and actual world review;
- resolve cubemap-fog binding and confirm the repeated fog warnings are absent;
- test the bounded nav hypothesis and confirm the four nav warnings are absent;
- prove the intended bot count and fixed floor transforms without vertical
  velocity failures, and verify which server commands actually took effect;
- replace or remove rejected client-only effect/profiler calls without
  changing the locked route, marker order or timings;
- a second clean cinema restart comparison;
- a stable, deterministic one-bot cheer prototype before audience rollout.

Assignment status remains **PARTIAL** and measurement status remains
**UNVERIFIED**.
