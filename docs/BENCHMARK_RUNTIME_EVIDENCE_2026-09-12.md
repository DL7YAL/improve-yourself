# Benchmark runtime evidence — 2026-09-12

Benchmark: `iy-benchmark/v1.2-candidate.2`

Windows is the runtime authority. This record contains only safe textual
metadata; the local runtime artifact itself is not committed.

## Measured completion save

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

Artifact metadata:

- size: 126 bytes;
- SHA-256: `2A336BBAB6572FFF66821A94181821DD9141EE63D1D209361CCA91D669D67A3B`;
- save-contract validation: `PASS`.

The controller writes this record only in the measured branch of `endPass()`,
after emitting the final Inferno report and
`PASS_END type=measured runtime_status=complete measurement_status=unverified`.
This is direct evidence that the Windows runtime reached measured completion.
It correctly does not claim a verified performance measurement.

## Console-contract status

The subsequently supplied complete Windows VConsole capture has SHA-256
`9D5295BC4441C461D1BF74B4F487111479026086C030699CEE28CD992F57FABF`.
Its authoritative `cs_script` channel contains one `READY` segment and exactly
all 39 required canonical events in order. The quoted `Console` channel echoes
are duplicates and are ignored. Runtime-contract validation is `PASS`, with
no `[IYBENCH] ERROR`, `runtime_status=complete` and
`measurement_status=unverified`.

The validator now accepts both plain `[IYBENCH]` lines and the actual VConsole
`[ cs_script ]: [IYBENCH]` form while continuing to reject quoted console
echoes. Seven focused validator assertions pass after that correction.

The earlier 139-line excerpt remains useful restart evidence at SHA-256
`619FEFBFC04A5C83CA70A4951ABFE896F9D9E4D7EFCE1F3366D1D217B9F90A7E`,
but its latest segment is only 21 of 39 events and does not supersede the
complete capture.

## Engine findings from the complete capture

The contract pass proves controller sequencing, not world acceptance. The
same capture contains the following material findings:

- the compiled cubemap array is missing once, followed by 35,501 unresolved
  `env_cubemap_fog` warnings; Ancient water/reflection cannot be approved;
- four nav-generation parameter warnings require a map re-export;
- 33 player/bot vertical-velocity warnings affect all nine bots present before
  warmup and the local player; fixed floor placement is not proven;
- the server-side bot setup visibly removes the first bot population and nine
  bots are then present before `PASS_START`; the intended ten-bot audience is
  therefore not proven;
- 78 client-command/convar attempts are rejected for a missing FCVAR flag.
  Of these, the companion audit identifies 47 rejected calls from the
  controller's client-only command set, including attack and VProf commands,
  so the markers do not prove that those actions ran;
- the Vulkan pipeline cache cannot be written twice. This is a local Windows
  runtime warning and reinforces the honest unverified measurement status;
- two missing camera-node and four missing overview messages are ancillary,
  but remain recorded for cleanup.

There is no `[IYBENCH] ERROR` or VScript exception. These engine findings do
not revoke the runtime-contract `PASS`; they prevent an overall assignment or
world `PASS`.

`audit_benchmark_vconsole.py` records this distinction mechanically. For the
capture above it reports runtime contract `PASS`, overall `NEEDS_WORK`, nine
bots at first warmup and the exact blocker/warning counts without storing the
private raw-log path.

## Remaining acceptance gates

- five post-compile visual captures and actual world review;
- repair and recompile the cubemap/nav state, then confirm the repeated
  cubemap and nav warnings are absent;
- prove the intended bot count and fixed floor transforms without vertical
  velocity failures, and verify which server commands actually took effect;
- replace or remove rejected client-only effect/profiler calls without
  changing the locked route, marker order or timings;
- a second clean cinema restart comparison;
- a stable, deterministic one-bot cheer prototype before audience rollout;
- complete Windows pytest, `compileall`, `pip check` and read-only sync output
  for the final continuation branch.

Assignment status remains **PARTIAL**.
