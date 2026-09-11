# Improve Yourself Benchmark authoring sources

This directory versions the project-authored sources that produced the validated
CS2 benchmark runtime. It intentionally preserves the paths used inside the
local addon:

```text
maps/improve_yourself_benchmark.vmap
scripts/benchmark_controller.js
```

## Provenance

Initially imported on 2026-08-15 from the authoritative local addon
`content/csgo_addons/improve_yourself_benchmark` after the successful rebooted
Full Compile and runtime-camera revalidation recorded in
`coordination/agents/codex.md`.

On 2026-09-12 the project owner explicitly selected the materially newer
installed `iy-benchmark/v1.2-candidate.2` sources as the authoritative
continuation. They were imported byte-for-byte from the fixed benchmark
machine before any repository-to-addon sync or new compile. This promotion is
a source checkpoint, not runtime approval.

| Source | SHA-256 |
| --- | --- |
| `maps/improve_yourself_benchmark.vmap` | `74AE13F43EDA0FC213330A30D9714D16B2897710C5409378A9D4BF1294E4BEB6` |
| `scripts/benchmark_controller.js` | `0038BAACB132A907654E03FE3B42B27BF198D5D1A23F4F9F0D8C87B5DF16723E` |

The earlier map baseline hash
`A37273C6E27AB8357068DC3FF064888EF82C2C11C84C668B85CB1FE910036572`
matches the local
`maps/backups/improve_yourself_benchmark.post-corridor-floor-20260814.vmap`
backup. The earlier controller baseline hash
`41BA031586C168CB368875CE275B02DE7BB0B2879B2CBD0115EA47CE8778DCFA`
matches the local
`scripts/backups/benchmark_controller.post-camera-health-20260814.js` backup.
The current controller hash differs intentionally because the V1.2 candidate
extends the locked V1.1 multi-map transition contract with explicit capture
windows and fail-honest measurement status.

## Scope

Only the authoritative project-authored map and controller are versioned here.
Compiled VPKs, caches, logs, older backups, copied Valve source/binary assets,
Valve type definitions, post-processing defaults, sound events, and audio files
remain outside this repository. The versioned VMAP may reference original
Valve/CS2 runtime assets available through the installed game and official CS2
Workshop Tools; those references do not transfer ownership and must not become
independently packaged product assets.

The binding rights, provenance, branding, packaging, and Nuke authoring boundary
is defined in [`ASSET_RIGHTS.md`](ASSET_RIGHTS.md). It applies before introducing
or changing any visually relevant Workshop asset reference.

Use `tools/benchmark/Sync-BenchmarkAddon.ps1` to verify an installed Workshop
Tools addon against `source-manifest.json`. Its default mode is read-only; the
explicit `-Deploy` mode creates verified backups before replacing only missing
or different manifest files. Do not edit the repository copy and installed
addon independently.

## Locked multi-map transition contract

Controller V1.2 candidate 2 preserves the V1.1 source-side transition design from
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

## 2026-08-17 V1.1 runtime result

The historical V1.1 source contract was **not runtime-approved**. A successful Full
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

### Graybox correction under revalidation

The follow-up authoring pass adds two project-owned destination corridors
without changing the validated Nuke geometry: an Ancient-style ramp/water
section with a reflective floor and enclosed Red Room endpoint, and an
Inferno-style Apps corridor with five ascending stair blocks. The controller
now targets these real map areas rather than the invalid +/-8,000-unit paths.
`tools/benchmark/author_transition_graybox.py` makes this addition
reproducible from Valve's keyvalues2 VMAP representation and refuses to add it
twice. This correction still requires Full Compile and normal-viewer approval.
The same authoring pass extends the existing upper light/reflection probe over
both corridors so their faces remain lit outside the former Nuke-only bounds.
Both corridors are roofed so their visual identity does not disappear into the
bright exterior sky during the normal-viewer camera pass.

The subsequent Full Compile completed and loaded the rebuilt map, but the
normal-viewer recheck still showed the beige-gray origin test area and its
orange/white guide lines throughout the sampled moving-camera phase. None of
the new enclosed Ancient corridor, reflective water, Red Room endpoint or
Inferno stair corridor was visible. This narrows the blocker: source geometry
and source-side camera coordinates now exist, but their compiled runtime
placement has not yet been reconciled. The next pass must inspect mesh/object
transform semantics and prove one compiled target position before any further
smoke, fade, yaw or blind geometry change.

### Compiled transform correction

The transform audit found that the cloned primitive is a flat mesh whose
runtime dimensions were not reliably established by the non-unit object scale.
The authoring tool now multiplies the `position:0` vertex stream by the intended
box dimensions and resets the generated object scale to `1 1 1`. This makes the
compiled dimensions explicit while preserving the same origins, controller
coordinates, transition effects and timing.

A fresh Full Compile completed with `22 compiled, 0 failed, 1 skipped` in 26
seconds. A clean normal-viewer run then showed the first smoke inside enclosed
destination geometry and later camera frames inside the baked corridors. This
resolves the earlier empty-sky/runtime-placement blocker. The transition is
still not approved: sampled frames did not yet prove the reflective water,
recognizable Red Room and all five Inferno stair blocks as a coherent sequence.
The next runtime pass must correlate those landmarks with the existing markers
and adjust only camera composition if required.

## 2026-09-12 V1.2 candidate checkpoint

The promoted local candidate adds explicit `CAPTURE_WINDOW` markers for the
Nuke yard landmarks, Ancient water/reflection and Red Room, and Inferno stairs
and Apps details. It also records measurement status as `unverified` instead of
claiming that successful runtime completion proves measurement validity.

The promoted VMAP and controller are byte-identical to the installed addon at
the time of import. They still require a fresh Hammer Full Compile, VRAD result,
and marker-correlated normal-viewer review before runtime approval.

### Partial runtime evidence

A user-supplied console excerpt from the fixed benchmark machine proves that
`iy-benchmark/v1.2-candidate.2` loads without a reported controller error. Two
separate runtime segments each completed the warmup pass. The first emitted all
five scene/landmark capture windows, both ordered transitions, started the
measured pass and reported `nuke_outside` before a new `READY` reset. The second
again completed warmup and started the measured pass before the excerpt ended.

This is useful controller-flow evidence, but it is not a completed measurement
or visual/runtime approval. Neither segment contains `PASS_END type=measured`;
the controller correctly reports `MEASUREMENT_STATUS status=unverified`. The
submitted text also contains no Hammer Full Compile or VRAD output. A clean,
uninterrupted measured pass, the build/VRAD result, and marker-correlated visual
captures remain required.
