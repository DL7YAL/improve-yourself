# Optimizer Evidence Foundation V1

## Fixed boundary

This foundation is read-only. It implements no optimizer apply path and no
Windows, graphics-driver, network, BIOS/UEFI, registry or CS2 change. The
later safety boundary remains `READ → SNAPSHOT → APPLY → VERIFY → RESTORE`.

All four product areas use one canonical recommendation infrastructure:

`Improve Empfehlungen → System Optimizer | Graphics Optimizer | Network Optimizer | BIOS Optimizer`

They are domains on the same rule/evidence engine, not independent engines.

## Versioned entities

| Entity | Contract / role |
| --- | --- |
| `SYSTEM_PROFILE` | `iy.system_profile/v1`: actual read-only system state plus explicit unknown fields. |
| `OPTIMIZATION_RULE` | Stable rule ID, domain, setting, possible states, goal, readability/changeability, restore/restart/risk and maturity. |
| `RULE_COMPATIBILITY` | Required and explicit exclusion conditions with rationale. |
| `EVIDENCE_RECORD` | Stable evidence ID, source/type, affected system class, outcome, quality and provenance. |
| `RECOMMENDATION_RESULT` | Deterministic result for one rule against one profile. |
| `VALIDATION_RESULT` | Reserved `iy.optimizer_validation_result/v1` record for later real A/B evidence; no values are simulated. |

Recommendation states are `RECOMMENDED`, `ALREADY_RECOMMENDED`, `CONDITIONAL`,
`NO_CHANGE` and `INSUFFICIENT_EVIDENCE`. Rule maturity is separate:
`VERIFIED`, `CONDITIONAL_VERIFIED`, `EXPERIMENTAL`, `REJECTED`, `NO_BENEFIT`.
Experimental, rejected and no-benefit rules cannot become an Improve
recommendation through this foundation.

## Current evidence collection

`iy-system-profile --output results/system-profile.json` calls the existing
Windows System Check collector and normalizes its read-only facts into the
canonical profile. It currently reads where Windows exposes an authoritative
value:

- CPU name, manufacturer, architecture/family and logical processors;
- GPU name, adapter vendor and driver version;
- RAM capacity; RAM speed remains `null` when not reliably read;
- mainboard manufacturer, product and version; BIOS version, date and vendor;
- Windows caption, version and build;
- display resolution and refresh rate reported by the adapter;
- physical network adapter name, manufacturer, driver, link speed and MAC
  address as local inventory evidence.

CS2 configuration, GPU driver-option state and current CPU/GPU limitation
remain explicit unknown/not_available values. Network MTU and advanced adapter
features are not guessed; they remain unavailable until a dedicated safe
reader is approved. The profile is local, read-only and contains no claim that
an observed adapter is the active game route.

## BIOS special handling

BIOS remains a domain in the shared engine but has high-risk metadata:
automatic changeability is false for the fixture, manual action is required,
guidance and later screenshot verification are separate flags. Compatibility
can require Mainboard → revision → BIOS version → CPU/platform → hardware
configuration without changing the schema for individual boards or releases.
The existing guided BIOS concept is not duplicated; this module only supplies
the later handoff metadata.

## Fixtures, harness and UI contract

Five fixture-only rules cover System, Graphics, Network, BIOS and a conditional
System exclusion. Their evidence records are marked `FIXTURE` / `SYNTHETIC` /
`TEST_ONLY`; they contain no real performance claim and are never changeable.

`iy-system-profile --fixture-harness --output results/optimizer-foundation-fixtures.json`
runs the existing 150 synthetic profiles through the same evaluator. Its label
is `SYNTHETIC / DECISION LOGIC ONLY / NOT MEASURED`. It tests matching,
exclusions, conditional handling and unknown evidence only; future real
benchmark data belongs solely in `VALIDATION_RESULT`.

`recommendation_detail_view_model()` provides the later shared explanation
panel with title, current state, Improve recommendation, status, explanation,
why-for-this-system, changes, evidence/validity, risk, restore metadata and
manual guidance flags. It deliberately exposes no Apply action.
