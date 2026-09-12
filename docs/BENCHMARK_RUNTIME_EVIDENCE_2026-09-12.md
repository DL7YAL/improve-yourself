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

The supplied 139-line console excerpt has SHA-256
`619FEFBFC04A5C83CA70A4951ABFE896F9D9E4D7EFCE1F3366D1D217B9F90A7E`.
It was copied before the completed run's later console events were included.
Its latest `READY` segment contains 21 of 39 required canonical contract
events and therefore validates as `PARTIAL`.

The completion save closes the runtime-end gate, but it does not prove from
the supplied text that all measured markers and three reports appeared exactly
once. Preserve and validate the later VConsole lines to close that independent
event-order gate.

## Remaining acceptance gates

- five post-compile visual captures and actual world review;
- a second clean cinema restart comparison;
- a stable, deterministic one-bot cheer prototype before audience rollout;
- complete Windows pytest, `compileall`, `pip check` and read-only sync output
  for the final continuation branch.

Assignment status remains **PARTIAL**.
