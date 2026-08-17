# Prototype Inventory

Purpose: review the existing saved development states before any legacy code is copied into the clean V1 branch.

## Classification

Each prototype component is classified as one of:

- **KEEP** — works and fits the agreed V1 direction
- **REVISE** — useful, but must be cleaned up or adapted
- **DISCARD** — not suitable for the consolidated product
- **DEFER** — useful idea or implementation for V2/V3, not V1

## Saved reference states

- `CS2_Demo_AutoAnalyzer`
- `improve-yourself-experimental`
- `replay-punkt-0.2-alpha3`
- `TacticalReplay_MVP_v0.3`
- `Treiber_Check_Final`
- `FACEIT_PRO_BRIX_CS2_v1.0(1)`
- `BRIX_Windows11_CS2_FACEIT_Diagnose`

Canonical reviewed source: `Improve_Yourself_V1_Workspace_2026-08-12` on the
local development machine. The source workspace remains read-only reference
material; approved ideas are reimplemented and tested in this repository.

## Review table

| Source | Component / feature | Status | Decision | Notes |
|---|---|---|---|---|
| `CS2_Demo_AutoAnalyzer` | Awpy demo import, player/round/kill extraction, HTML/CSV reports, voice-slot helpers | reviewed | **REVISE** | Useful provenance for the import/report workflow and the explicit “marker, not verdict” boundary. Its parser is superseded by the tested `iy.analysis/v1` implementation; do not copy the standalone script. |
| `improve-yourself-experimental` | Tkinter review UI, scene list, exact rule combinations, review states, exports and CS2 navigation helpers | reviewed | **REVISE** | Strongest review-workflow reference, but implemented as a 1,300+ line monolith with its own partial parser and legacy packaging. Reuse only selected workflow concepts behind current schemas and tests; do not import the monolith. MPL-2.0 obligations apply to copied source. |
| `TacticalReplay_MVP_v0.3` | Awpy round export, Canvas replay, follow/head-up modes, view cone, local map layer and optional triangle-geometry LOS | reviewed | **REVISE** | Strong interaction reference. The active `iy.replay/v1` exporter and `iy-replay-viewer` now replace its parser/serving baseline. Follow modes, event rendering and LOS may be reimplemented only when required by V1 and validated against current contracts. |
| `replay-punkt-0.2-alpha3` | Earlier review UI, exact unweighted rule model and generated review package | reviewed | **DEFER** | Historical provenance for transparent rule combinations. Experimental is the later workflow source; no separate runtime or second product is retained. |
| `TacticalReplay_MVP_v0.1` | Minimal demo-to-browser top-down replay | reviewed | **DEFER** | Confirms the original heartbeat and fallback grid approach, but v0.3 and the current renderer supersede it. |
| `Treiber_Check_Final` | Read-only C# driver/firmware inventory and official vendor links | reviewed | **REVISE** | Conservative behavior fits V1 System Check: detect and explain, never install or flash. Hardware-specific vendor routing and the bundled executable are not portable product code; review the source per check and reimplement behind a structured result contract. |
| `FACEIT_PRO_BRIX_CS2_v1.0(1)` | Machine-specific Windows, AMD, network, CS2 and benchmark profile | reviewed | **REVISE** | Valuable test/evidence profile for Tristan's current PC, not a generic preset. Treat every `apply` value as candidate evidence requiring detection, safety policy, backup/restore design and system-specific validation. Never apply BIOS/security/overclocking items automatically. |
| `BRIX_Windows11_CS2_FACEIT_Diagnose` | Elevated PowerShell collection of hardware, drivers, network, power, security, storage, services and event evidence | reviewed | **REVISE** | Broad diagnostic coverage is useful for System Check, but the script requires administrator rights, emits sensitive machine data and runs long external collectors. Split safe read-only checks from privileged/slow/identifying checks; require explicit scope and disclose output sensitivity. |

## Consolidation order

1. Keep the current tested `iy.analysis/v1` and `iy.replay/v1` implementations
   as the only active parser contracts.
2. Finish the bounded visual validation of `iy-replay-viewer`; then add only
   replay events required by the V1 review flow.
3. Define a structured, read-only System Check result contract and implement
   non-elevated detection first. Privileged checks remain explicit and separate.
4. Integrate a reduced review workflow over the current analysis/replay
   artifacts. Do not copy the legacy Tkinter monolith or create a second parser.
5. Design Optimizer apply/backup/restore only after System Check can determine
   applicability and safety. The BRIX profile is regression evidence, not a
   default configuration.

## Explicitly not approved for direct consolidation

- bundled legacy executables and installers;
- machine-specific presets as automatic defaults;
- automatic driver installation, BIOS/firmware changes or security changes;
- unreviewed registry/network tuning or undocumented AMD settings;
- duplicate parser, rule-engine or viewer runtimes beside the current package;
- real demos, personal reports, local radar binaries or sensitive diagnostics.

## Rule

Nothing from the legacy prototypes becomes part of the active V1 codebase merely because it already exists. It must first survive this review.
