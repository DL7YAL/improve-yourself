# Synthetic Matrix Validation V1

## Purpose and hard boundary

The canonical `iy.optimizer_synthetic_matrix/v1` is a deterministic
compatibility and recommendation test matrix, not a benchmark. Each of its
150 `iy.system_profile/v1` profiles is labelled `SYNTHETIC / EXPECTED / NOT
MEASURED` and has `real_evidence_allowed: false`.

It contains no FPS, low-percentile, frametime, latency-improvement, ping-
improvement or percentage-performance data. It cannot create a real
`VALIDATION_RESULT`, change rule confidence or promote evidence quality.

## Profile composition

The profiles vary AMD/Intel CPU families and generations, AMD/NVIDIA GPU
classes and driver states, 8/16/32/64 GB RAM, four Windows builds,
60/120/144/165/240/360 Hz classes, mainboard and BIOS states, NIC vendor/link
speed/MTU/RSS/unknown feature states, current recommendation state, missing
GPU driver data, missing mainboard/BIOS data and missing network-adapter data.

This is decision diversity rather than a catalog of every product ever sold.
Unknown and absent facts remain absent; no profile fills them with a default.

## Rule-pack interface

`validate_synthetic_rule_pack(rule_pack)` accepts later curated
`OptimizationRule` records without altering either the 150 profiles or the
test harness. It returns a deterministic per-profile Rule Compatibility,
Evidence Sufficiency and Recommendation Result trace, plus state and domain
counts. Its output is marked:

`SYNTHETIC / DECISION LOGIC ONLY / NOT REAL EVIDENCE`

The matrix proves RECOMMENDED, ALREADY_RECOMMENDED, CONDITIONAL, NO_CHANGE,
INSUFFICIENT_EVIDENCE, explicit exclusion and security/performance trade-off
behavior through fixture rules. It is intentionally ready for a future
read-only tester/shadow-recommendation build: real profiles use the same
canonical schema but remain local and never upload automatically.
