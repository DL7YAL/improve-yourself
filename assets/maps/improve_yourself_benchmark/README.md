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
| `maps/improve_yourself_benchmark.vmap` | `9D7BE49FD2FA9F720267E5FD155054F478F64416408AC681EF02B578274276CE` |
| `scripts/benchmark_controller.js` | `45D2CF2C0EFB05454304B2F46630239D6B7998BC0F3172B8B71DD405DC07B4BD` |

The earlier map baseline hash
`A37273C6E27AB8357068DC3FF064888EF82C2C11C84C668B85CB1FE910036572`
matches the local
`maps/backups/improve_yourself_benchmark.post-corridor-floor-20260814.vmap`
backup. The earlier controller baseline hash
`41BA031586C168CB368875CE275B02DE7BB0B2879B2CBD0115EA47CE8778DCFA`
matches the local
`scripts/backups/benchmark_controller.post-camera-health-20260814.js` backup.
The current controller hash differs intentionally because V1.1 adds the locked
multi-map transition contract described below.

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

## V1.2 candidate visual-authenticity pass

The current source candidate preserves the locked 64-second route and adds a
bounded visual-authenticity layer without copying Valve assets into the
repository. The Hammer-saved VMAP references installed CS2 runtime materials
and props for Nuke Outside, Ancient B and Inferno Apps/A. The exact references,
rights class, purpose and build evidence are recorded in
`NUKE_OUTSIDE_ASSET_PROVENANCE.json` and
`TRANSITION_WORLDS_ASSET_PROVENANCE.json`.

| V1.2 candidate source | SHA-256 |
| --- | --- |
| `maps/improve_yourself_benchmark.vmap` | `DBBE5A05C541D2AB47354449FC16A1495E6934E85734484CE6E09C2AE27D5645` |
| `scripts/benchmark_controller.js` | `29CC448D423255A7FFE3840333FDD3BECA329D47B0C6F229FE61B665D15B3849` |

The authoring helpers under `tools/benchmark/` document the reproducible source
transformations used for this candidate. Their logical order is:

1. `author_nuke_outside.py` for the Nuke material and prop pass;
2. `author_benchmark_worlds.py` for Ancient/Inferno materials and props;
3. `refine_benchmark_worlds.py` for grounding and enclosure corrections;
4. `cleanup_benchmark_props.py` for props rejected by the runtime composition
   check;
5. `author_intro_room.py` for the isolated technical spawn room.

These tools operate on Valve `dmxconvert` keyvalues2 input. Hammer remains the
serialization authority for the versioned binary VMAP. They are fail-closed
and must not be rerun against an already-authored candidate.

Controller `iy-benchmark/v1.2-candidate.1` emits deterministic
`CAPTURE_WINDOW` markers, including the active `warmup` or `measured` pass, for
the following review points:

| Time | Scene | Review point |
| ---: | --- | --- |
| 9.0 s | `nuke_outside` | yard landmarks |
| 27.0 s | `ancient_b` | water/reflection workload |
| 38.0 s | `ancient_b` | Red Room identity before flash |
| 48.0 s | `inferno_apps_a` | stair sequence |
| 53.0 s | `inferno_apps_a` | Apps environment details |

`CAPTURE_WINDOW` means only that the controller reached the planned review
time. It is not proof that the landmark was visible. Runtime approval still
requires a fresh Full Compile followed by a normal-viewer capture correlated
with all five markers. Any later camera adjustment must be driven by that
evidence and must preserve the locked transition order and timing contract.

The controller also keeps runtime completion separate from performance
evidence. It records `runtime_status=complete` after the full route, but keeps
`measurement_status=unverified` because CS2 can reject client-side `vprof` and
frametime commands under Workshop command filtering. A future measurement
runner must prove that the selected FPS/frametime collector is active before a
performance result can become valid; route completion alone is not enough.

## 2026-09-07 candidate runtime result

The repository sources were hash-verified into the installed local addon and
the V1.2 controller was compiled successfully with the installed CS2 Resource
Compiler. A fresh tools-mode run reached `READY`, completed the warmup and
measured passes, emitted all three scene reports and finished at event 60.

The measured pass emitted all five capture markers in the documented order:
Nuke yard landmarks, Ancient water/reflection, Ancient Red Room, Inferno
stairs and Inferno Apps details. This is controller/runtime correlation only;
no normal-viewer screenshots were captured in this run, so landmark visibility
remains unapproved.

CS2 rejected the requested client-side FPS/frametime and `vprof` commands in
the Workshop context. The final marker therefore correctly reported
`runtime_status=complete measurement_status=unverified`; no FPS, 1%-low or
frametime result was created or inferred.
