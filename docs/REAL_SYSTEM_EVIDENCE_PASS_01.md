# Real-System Evidence Pass 01

## Scope and privacy

This pass ran Pack 01 against **one locally available tester system** on
2026-08-22. It performed the existing Windows System Check only. The run was
read-only (`changes_applied: false`, `elevation_requested: false`), did not
write registry, BIOS, drivers, network settings or benchmark data, and did not
retain the generated raw local system report in the repository.

This is one real-system evidence observation, not a hardware golden master and
not a performance-validation result.

## Real observation

The live System Check returned a valid `iy.system_check/v1` document with eight
current check entries: `windows`, `cpu`, `memory`, `motherboard`, `gpu`,
`display`, `secure_boot` and `tpm`. Its own summary was `OK: 6`, `REVIEW: 2`,
`ACTION_REQUIRED: 0`.

The Pack-01 evaluation consumed that exact read-only projection:

| Result | Count | Interpretation |
| --- | ---: | --- |
| `NO_CHANGE` | 8 | Read-only facts were available; Pack 01 made no positive recommendation. |
| `CONDITIONAL` | 1 | The GPU driver-currentness mapping was not confirmed for this system's exact supported mapping. |
| `INSUFFICIENT_EVIDENCE` | 3 | Monitor identity, Secure Boot and TPM values were not available in the shared profile. |
| `RECOMMENDED` / `ALREADY_RECOMMENDED` | 0 | Expected for this read-only System-Check basis. |
| Exclusions | 0 | No actual profile fell into an explicit excluded compatibility mapping. |

The resulting UI/ViewModel had 12 Pack-01 cards, `fixture_only: false`, no
normal Improve recommendation and `apply_available: false` on every card. It
rendered the driver mapping as `CONDITIONAL / NOT CONFIRMED` and the three
missing facts as `UNKNOWN / NOT AVAILABLE`, with their exact missing evidence
paths retained in the detail contract.

## Fixed data-path finding

The first real pass revealed that already collected Mainboard/BIOS evidence was
being dropped by `profile_from_system_check()`. The function now projects the
existing `motherboard` evidence into `motherboard` and `bios` profile fields.
No value is inferred; the second real pass confirmed the fields are present.

## Synthetic comparison

The 150-system synthetic matrix remains a deterministic decision-contract test,
not an expected distribution for a real PC. Its controlled Missing/Unknown,
conditional AMD mapping, exclusion and generic fixture-conflict scenarios are
all deliberately broader than this one real observation. The real result
introduces no contradiction: it confirms that unsupported or absent data does
not become a recommendation or a guessed hardware state.

## Current evidence boundary

The active `dev/v1-foundation` System Check emits eight of the twelve Pack-01
check bases. Therefore driver-currentness, chipset-currentness, graphics-profile
state and monitor identity cannot become a confirmed real Pack-01 fact unless
their existing read-only collectors are deliberately brought into this active
contract in a later approved slice. Pack 01 correctly represents this absence
as conditional or insufficient evidence.

## Recommended next fachlicher step

If approved, perform a **read-only active System-Check contract alignment**:
reconcile the already versioned twelve-check System-Check semantics with the
active development branch, then repeat this Evidence Pass on multiple explicitly
provided tester systems. That is not an Apply, driver/BIOS change, rule research
or performance claim.
