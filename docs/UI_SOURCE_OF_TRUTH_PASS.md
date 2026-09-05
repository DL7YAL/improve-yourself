# UI Visual Source-of-Truth Pass

> **HISTORICAL / SUPERSEDED 2026-09-05:** The visual targets in this report
> have no current authority. Canva design `DAHUBn5D2aM`, revision 25, is the
> sole visual source for new implementation and acceptance.

Status: **final Portable runtime inspected; not accepted as a global visual PASS** on `dev/v1-foundation`.

The current branch remains the functional truth.  Pages 03 (Home), 05 (Demo
Analyzer) and 07 (Improve Optimizer) of
`docs/design/Improve_Yourself_Concept_Preview_Discord_Q98.pdf` are the
binding visible structure.  Illustrative values, unsupported actions and old
concept-only features are not product data.

## Current -> target -> gap -> implementation

| Area | Current before this pass | Binding target | Observed gap | Implemented presentation change |
| --- | --- | --- | --- | --- |
| Sidebar | Cyan outlined, cut-out active item | Quiet filled active surface with an unmistakable current page | Looked like a focused native/developer control | Shared `SidebarNavItem` now uses a dark rounded active plane, a short cyan leading accent and wider icon/text spacing; routing is unchanged. |
| Dashboard action | `Zum Analyzer` used a separate filled ttk button | Main actions share a visible, deliberate action language | The progress action did not belong to the module-action family | It now uses the same reusable rounded, outlined `RoundedHomeAction` component as the six module cards. |
| Analyzer | Workflow and criterion truth already present | Demo-preflight led analyzer with clear profile/rule state | No structural contradiction found | Existing preflight/selection/profile layout is retained. The semantic `Aktive Kriterien: X / Y` hook remains in the profile block and reports the real 7-rule contract. |
| Optimizer landing | Four domains appeared as passive text columns before the System Check | Selected system view first, four clear selectable areas below, user understanding before technical details | The entry read as a long technical page rather than an Optimizer product surface | `SYSTEM OPTIMIZER` is now the visible current main view. Four quiet, equally sized selection cards beneath it carry state and a visible action; the active area has a restrained leading accent instead of a cut-out developer frame. |
| System Check and results | Technical evidence matrices were part of the main linear page | System facts, state and uncertainty first; evidence/details intentionally secondary | Raw matrix wording competed with ordinary user information | System Check and `Dein System im Überblick` are the primary flow. The Evidence Matrix is preserved behind `Technische Evidenz & Pack-Details anzeigen`; per-setting details remain explicit. |
| Optimizer assessment | Domain buttons and Pack-01 language occupied the primary assessment | State, recommendation/uncertainty and next interpretation first | Internal Pack terminology and evidence validity were too prominent | The selected domain is driven by the selection cards. Main rows show title, status, current state and why; evidence/provenance remains in the detail path. |
| Scroll surface | Native light scrollbar could cut through the dark Optimizer surface | No white foreign surface in the Midnight shell | Bright scrollbar trough visible in the acceptance check | Shared vertical scrollbar style now has dark trough, slider and active state. |

## Fixed boundaries

- No parser, replay, analysis profile, rule, scene, CS2/NetCon, evidence or
  recommendation decision logic changed.
- No new optimizer rule, hardware mapping, Apply/Write, registry, firmware,
  driver or network change exists.
- Existing unknown, conditional, insufficient-evidence and exclusion results
  remain fail-closed.
- The former matrix/provenance data was not removed.  It is merely no longer a
  default landing surface.

## Required visual proof

Before completion, capture current screenshots for Dashboard, Analyzer,
Optimizer start, selected System Optimizer and Sidebar, then compare them with
master pages 03, 05 and 07.  PASS requires the visible hierarchy to match the
master intent; element presence alone is insufficient.

## Final Portable runtime evidence — 2026-08-22

The final Portable artefact recorded in `dist/experimental/experimental-build.json`
was opened directly.  Runtime screenshots were captured through the Windows
application surface; no data, setting or system state was changed during this
inspection.

| Runtime screen | CURRENT vs. binding target | Result | Concrete visible deviation / scope classification |
| --- | --- | --- | --- |
| Dashboard / Home | Page 03's sidebar, command-centre hierarchy, six entry cards, three central panels and lower information panels are recognisable in the real shell. `Zum Analyzer` now has the same outlined action language as the top-card actions; the active navigation item is a dark filled surface, not a cyan cut-out. | **FINAL POLISH** | The real card/button chrome still reads more technical/Tk-like than the depth and material hierarchy of the artwork. There is no missing Home structure or action, but this is not a pixel-level master reproduction. |
| Analyzer | Page 05's dark app shell and preflight-first information hierarchy are present. The actual no-demo state visibly keeps the source action, inactive downstream actions, empty CT/T line-ups, profile and `Aktive Kriterien: 7 / 7` together. | **FINAL POLISH** | The empty CT/T line-up panels are necessarily sparse before a real demo is loaded. Their visual weight is higher than the target's populated example, but no fake data was added to fill them. |
| Optimizer overview | Page 07's product order now applies: current `SYSTEM OPTIMIZER` first, then four equal selectable areas, then the safe System Check. Raw evidence is behind an explicit details action. | **PASS for hierarchy** | The selected and System-Check actions are still more solid blue than the target's restrained primary-action treatment. This is a style polish point, not a missing card, route or safety boundary. |
| System Optimizer detail view | The runtime view clearly communicates state, read-only boundary, unknowns and the available System Check. Evidence/pack details are not expanded by default. | **ÄNDERN** | With an already loaded local scan, the captured viewport did not expose a distinct `Dein System im Überblick` / per-setting result region as a directly reviewable visible detail state. The scroll interaction did not move this page in the runtime capture. This must be diagnosed in a later, separately authorised UI pass; no UI change was made in this inspection. |
| Tactical Replay / empty state | The real empty state is clear: no scene selected, no invented replay truth, and a three-step path from Analyzer to selected review scene to Tactical Replay. Active sidebar state is visible. | **PASS for empty state** | The lower half is intentionally sparse. It is honest for an empty state but has less visual guidance/detail than a populated Master reference; not a functional inconsistency. |

### Visual result

- **PASS:** Optimizer entry hierarchy and Tactical Replay's truthful empty state.
- **ÄNDERN:** System Optimizer needs a separately scoped visible-result/scroll
  review before the page can receive an overall visual acceptance.
- **FINAL POLISH:** Dashboard and Analyzer surface material, action treatment
  and populated-vs-empty visual density.

This is intentionally not a product-wide visual acceptance.  The branch keeps
the working implementation checkpoint for Tristan's review; no follow-on UI,
Optimizer, benchmark or infrastructure work is authorised by this document.
