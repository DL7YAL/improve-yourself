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
| `scripts/benchmark_controller.js` | `E6A434872460C0F0562D10E08C9D95542FE10B592DBC65E2B7FCCC1B45E70C09` |

The map hash also matches the local
`maps/backups/improve_yourself_benchmark.post-corridor-floor-20260814.vmap`
backup. The earlier controller baseline hash
`41BA031586C168CB368875CE275B02DE7BB0B2879B2CBD0115EA47CE8778DCFA`
matches the local
`scripts/backups/benchmark_controller.post-camera-health-20260814.js` backup.
The current controller hash differs intentionally because V1.1 adds the locked
multi-map transition contract described below.

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

## Locked multi-map transition contract

Controller V1.1 implements the source-side transition design from
`docs/DECISIONS.md`:

- the Nuke camera enters the existing first smoke wall before the hidden swap;
- Ancient begins inside smoke with camera height and yaw matched to the Nuke
  endpoint, then emerges around B ramp/water;
- the Ancient camera approaches the Red Room path and emits an explicit
  landmark marker before transition occlusion;
- a flashbang creates the second white-out; the hidden swap occurs during that
  flash rather than an Ancient-end smoke;
- Inferno begins around Apps with height/yaw matched to the Ancient endpoint
  and turns into its scene only after the hidden swap.

Runtime markers `TRANSITION_APPROACH`, `TRANSITION_ENTER`, `TRANSITION_SWAP`
and `TRANSITION_EXIT` make capture/log correlation reproducible. These source
constraints do not by themselves prove that the transitions are visually
seamless. A Full Compile and normal-viewer runtime capture remain required.

## 2026-08-17 runtime result

The current V1.1 source contract is **not runtime-approved**. A successful Full
Compile produced a fresh VPK, but two normal-viewer observations showed the
occlusion clearing to empty sky with isolated effects instead of a complete
destination environment. The red-tinted empty view is not accepted as a Red
Room pass.

A read-only text conversion of the versioned VMAP confirmed that its authored
geometry is centered near the map origin, whereas the Ancient and Inferno
camera paths currently target areas around positive and negative 8,000 units.
The next change must therefore establish real destination geometry or re-author
the paths from measured existing bounds before another Full Compile. More blind
smoke, fade, or yaw timing changes are not an acceptable substitute.
