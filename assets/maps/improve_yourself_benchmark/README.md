# Improve Yourself Benchmark authoring sources

This directory versions the project-authored sources that produced the validated
CS2 benchmark runtime. It intentionally preserves the paths used inside the
local addon:

```text
maps/improve_yourself_benchmark.vmap
scripts/benchmark_controller.js
```

## Provenance

Imported on 2026-08-15 from the authoritative local addon
`content/csgo_addons/improve_yourself_benchmark` after the successful rebooted
Full Compile and runtime-camera revalidation recorded in
`coordination/agents/codex.md`.

| Source | SHA-256 |
| --- | --- |
| `maps/improve_yourself_benchmark.vmap` | `A37273C6E27AB8357068DC3FF064888EF82C2C11C84C668B85CB1FE910036572` |
| `scripts/benchmark_controller.js` | `41BA031586C168CB368875CE275B02DE7BB0B2879B2CBD0115EA47CE8778DCFA` |

The map hash also matches the local
`maps/backups/improve_yourself_benchmark.post-corridor-floor-20260814.vmap`
backup. The controller hash also matches the local
`scripts/backups/benchmark_controller.post-camera-health-20260814.js` backup.

## Scope

Only the authoritative project-authored map and controller are versioned here.
Compiled VPKs, caches, logs, older backups, Valve example content, Valve type
definitions, post-processing defaults, sound events, and audio files remain
outside this repository.

Use `tools/benchmark/Sync-BenchmarkAddon.ps1` to verify an installed Workshop
Tools addon against `source-manifest.json`. Its default mode is read-only; the
explicit `-Deploy` mode creates verified backups before replacing only missing
or different manifest files. Do not edit the repository copy and installed
addon independently.
