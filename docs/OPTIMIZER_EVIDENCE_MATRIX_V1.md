# Optimizer Evidence Matrix V1

## Scope and safety boundary

This slice is a local, read-only decision layer. It consumes an existing
`iy.system_check/v1` result, identifies transparent candidates and never
changes Windows, drivers, game settings, BIOS/UEFI, registry entries or CS2.
It does not make performance claims from synthetic data.

The mandatory future action protocol is:

`READ → SNAPSHOT → APPLY → VERIFY → RESTORE`

`APPLY` is deliberately not implemented in V1. A candidate must therefore be
shown as a candidate, with its risk and restore requirement, rather than as an
"optimization" button.

## Data contracts and flow

```text
existing iy.system_check/v1
        ↓ (only confirmed values)
read-only system profile
        ↓
evidence matrix matcher
        ↓
VERIFIED_STABLE | CONDITIONAL | EXPERIMENTAL | excluded | missing data
        ↓
System Check / Optimizer UI and JSON runner report
```

The machine-readable contracts are:

| Contract | Purpose |
| --- | --- |
| `iy.optimizer_evidence_matrix/v1` | Rule metadata, evidence class, selection order and later A/B model. |
| `iy.optimizer_synthetic_matrix/v1` | Exactly 150 deterministic test profiles. |
| `iy.optimizer_runner_report/v1` | Per-profile selection, exclusions, conflicts, missing input, backups and aggregate counts. |
| `iy.optimizer_ab_validation/v1` | Required real-measurement protocol for a future action. |

`iy-optimizer-matrix --output results/optimizer-synthetic-report.json` writes
the runner report. Generated results remain local artifacts; they are not user
performance evidence and must not be committed as hardware claims.

## Rule schema

Each rule has the following required fields:

`rule_id`, `name`, `category`, `description`, `current_state_path`,
`target_state`, `supported_conditions`, `exclusion_conditions`,
`expected_effect`, `possible_side_effects`, `reversible`,
`backup_restore_requirement`, `evidence_class`, `confidence`,
`source_rationale`, `measurement_metrics`, `validation_status`.

The initial V1 rules are deliberately narrow:

| Rule | Class | Why it can appear | What it does not claim |
| --- | --- | --- | --- |
| CS2 Refresh-Rate-Abgleich | `VERIFIED_STABLE` | Confirmed display rate plus a confirmed lower CS2 rate. | A guaranteed FPS increase. |
| AMD-Treiberoption prüfen | `CONDITIONAL` | AMD GPU, driver version and Performance goal are confirmed. | A generic AMD setting or universal latency gain. |
| NVIDIA Reflex-Kompatibilität prüfen | `CONDITIONAL` | NVIDIA GPU, driver and an existing CS2 Reflex state are confirmed. | A guaranteed latency improvement. |
| Performance-Frame-Pacing-Kandidat | `EXPERIMENTAL` | Performance goal, CPU limitation, known CS2 state, at least 16 GB RAM. | Any performance improvement without real A/B evidence. |
| Quality-Frame-Pacing-Kandidat | `EXPERIMENTAL` | Quality goal, GPU limitation, known CS2 state, at least 16 GB RAM. | Better quality or stability without real A/B evidence. |

Unknown CS2, driver-option, game-mode or limitation values remain absent from
the profile. They are reported as `missing_input_data`; no surrogate defaults
are manufactured.

## Deterministic selection and conflicts

Selection is deterministic and explicitly favors:

1. safety,
2. compatibility,
3. evidence,
4. stability,
5. performance.

Within an otherwise compatible conflict the declared rule priority and then
the stable `rule_id` order decide. The engine does not select the candidate
with the largest nominal FPS value because it never receives or fabricates one.
Every selected candidate records its backup/restore requirement. Exclusions
and missing fields are retained in the output so an absent recommendation is
explainable.

## Synthetic system validation

The synthetic corpus contains exactly 150 deterministic systems over AMD and
Intel CPUs (including X3D/non-X3D), AMD/NVIDIA GPU tiers, 8/16/32/64 GB RAM,
RAM speeds, four Windows builds, 60–360 Hz displays, different limitations,
goals and safe configuration-state placeholders.

Every profile and runner report is explicitly labelled:

`SYNTHETIC / EXPECTED / NOT MEASURED`

The corpus validates matching, exclusion, missing-data, backup and conflict
paths. It is not a benchmark and contains no actual FPS, percentile,
frametime, latency or system measurement.

## Future real A/B validation model

A candidate may become a measured result only after repeatable A/B/A/B work:

`A_BASELINE → B_OPTIMIZED → A_REPEAT → B_REPEAT`

The required record fields are `system_profile`, `source_state`, `target_state`,
`scenario`, `runs`, `aggregated_metrics`, `delta`, `variance`,
`software_driver_state` and `result`. The required metrics include average
FPS, 1% lows, frametime percentiles/stability, stutter spikes, CPU/GPU
limitation, reproducible delta and latency where measurable. A future outcome
must distinguish measured evidence from an inconclusive or unstable result.

## V1 limits and next safe extension

The System Check already provides CPU, GPU/driver, RAM capacity, Windows and
active display evidence. It does not yet safely read RAM speed, verified game
state, GPU driver options, CS2 launch/configuration state or current system
limitation. Those fields are intentionally shown as missing instead of guessed.

The next implementation step, if separately authorized, is a narrowly scoped,
read-only evidence collector for those missing sources plus a real, controlled
A/B recorder. No action writer should be added before snapshots, restore,
verification and clear user confirmation are each independently testable.
