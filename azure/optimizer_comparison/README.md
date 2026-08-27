# Independent Optimizer Comparison Matrix V1

## Scope

This package is an **independent, synthetic, read-only comparison cohort**. It
is intentionally separate from the canonical 150-system Golden Master matrix.
It neither imports nor changes the Optimizer core, defines product
recommendations, evaluates real machines, applies settings, or claims a
performance result.

The matrix is a future challenge input for the canonical Golden Master V2
runner. A future adapter may compare canonical output against the expectations
in this document, but this package must never become a second recommendation
engine or a source of real evidence.

## Contents

- `comparison_matrix.json` — 60 synthetic systems with expectation-oriented
  challenge records.
- `validate_comparison_matrix.py` — standard-library integrity validator only.

Run locally when an execution environment is available:

```text
python azure/optimizer_comparison/validate_comparison_matrix.py \
  --matrix azure/optimizer_comparison/comparison_matrix.json
```

## Cohorts

| Cohort | Count | Purpose |
| --- | ---: | --- |
| `realistic` | 20 | Plausible ordinary desktop/laptop systems and normal state variation. |
| `edge_stress` | 20 | Sparse evidence, OEM boundaries, capability mismatch, stale state, constrained hardware. |
| `adversarial` | 20 | Deliberate paired controls that expose generic, context-insensitive output. |

## Coverage and expected comparison behavior

The cohort covers AMD, Intel, NVIDIA, AMD Radeon, Intel integrated/Arc, desktop,
laptop/OEM, 8/16/32/64 GB RAM, 60/120/144/165/240/360 Hz targets, 1080p/1440p,
older platforms, high-end aligned systems, missing driver data, multi-display
ambiguity, unknown observations, unsupported APIs, OEM limitations, stale
configuration, and conflicting provenance.

The adversarial controls are the principal diversity probes:

- `cmp-a01` vs `cmp-a02`: identical hardware; aligned versus observed
  display/game-state mismatch.
- `cmp-a03` vs `cmp-a04`: identical hardware; competitive versus quality goal.
- `cmp-a07` vs `cmp-a08`: same platform class; NVIDIA-specific capability
  supported versus unsupported.
- `cmp-a09` vs `cmp-a10`: identical hardware; CPU versus GPU bottleneck.
- `cmp-a11` vs `cmp-a12`: unknown observation versus measured mismatch.
- `cmp-a13` vs `cmp-a14`: known optimal vendor state versus unknown state.
- `cmp-a17` vs `cmp-a18`: same laptop issue; OEM control absent versus explicitly
  supported adapter.

A canonical evaluator should not be expected to produce the same result for
both members of these controls when the recorded observation/capability context
is materially different. Conversely, it must not manufacture work for the
already-aligned high-end cases (`cmp-r03`, `cmp-r11`, `cmp-r12`, `cmp-a01`,
`cmp-a05`, `cmp-a15`, `cmp-a20`).

## Existing-150 overlap and unique challenge value

The existing canonical source (`synthetic_system_matrix()` in
`src/improve_yourself/optimizer_evidence.py`) already provides 150 deterministic
AMD/Intel CPU plus AMD/NVIDIA GPU profiles, controlled RAM/refresh/driver
variation, motherboard/BIOS absence cases, NIC observations, and explicitly
non-measured synthetic evidence. This package deliberately does not replace,
renumber, or modify those identities.

Unique cases supplied here include:

1. explicit paired controls where only current state, declared goal, bottleneck,
   observation completeness, or adapter availability differs;
2. Intel GPU / Arc and integrated-graphics cases, preventing a forced AMD/NVIDIA
   binary;
3. laptop OEM/MUX/embedded-controller capability boundaries;
4. multi-display target-identity ambiguity;
5. conflicting observations and weak/stale provenance;
6. a technically writable but safety-constrained state;
7. no-work and irrelevant-unknown controls, which reveal tweak-list inflation.

## Likely canonical-matrix blind spots worth evaluating later

These are **candidate additions for a later Codex-owned canonical matrix task**,
not changes made by this package:

- immutable explicit cohort IDs, if the canonical 3×50 grouping is intended as
  a formal contract;
- Intel GPU support and capability-not-available paths;
- paired same-hardware tests for settings, goal, bottleneck, and evidence state;
- laptops with explicit OEM adapter availability versus OEM lockout;
- active-game-display identity in multi-monitor configurations;
- stale-vs-current observation provenance/conflict states;
- high-end and low-end controls where the honest outcome is no safe
  recommendation;
- explicit distinction between `UNKNOWN`, `UNSUPPORTED`, and `NOT_AVAILABLE`;
- safety traps for firmware, drivers, arbitrary launch options, and NIC/service
  tuning.

## Safety contract

The data contains expectations, not exact product recommendations. It must not
be interpreted as instruction to change Windows, firmware, drivers, GPU control
panels, Steam launch options, CS2 settings, services, NIC configuration, MTU,
or registry values. Any future canonical evaluation must preserve missing
information as unknown, unsupported hardware as unsupported, and OEM/firmware
boundaries as read-only or recommendation-only unless a separately approved
safe adapter and restore model exists.
