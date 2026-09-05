# UI Target Alignment & Consolidation Pass V1.1

> **HISTORICAL / SUPERSEDED 2026-09-05:** Do not reuse the visual priority in
> this report. Canva design `DAHUBn5D2aM`, revision 25, is the sole visual
> authority.

## Authority and boundary

This pass uses the current branch as the functional truth and
`docs/design/Improve_Yourself_Concept_Preview_Discord_Q98.pdf` together with
`UI_SPEC.md`, `BRANDING.md` and `MOCKUP_INDEX.md` as the visual truth.

It does not add a product rule, hardware mapping, Apply/Write path, registry,
BIOS, driver, network-setting or benchmark action. The existing Tk desktop
shell remains the implementation base; no framework or product-tree change was
made.

## CURRENT -> TARGET -> GAP -> IMPLEMENTATION

| Area | Current | Target | Gap type | Implementation in this pass |
| --- | --- | --- | --- | --- |
| Home / Dashboard | Existing Page-03 command-center composition, real local System Check projection and honest unavailable values. | Preserve the approved Home hierarchy and shared Midnight shell. | Design-polish only; no structural mismatch reopened. | Preserved without a new Home redesign. |
| Left navigation | Persistent dark sidebar, Variant-3 mark and rounded selected state already exist. | One coherent application shell with restrained blue focus. | Minor visual polish remains global/deferred. | Preserved; routing is unchanged. |
| Analyzer | Real demo preflight, line-ups, player selection and profile selector work. The profile criterion state was only narrative text. | Clear flow and profile/rule context, with a stable criteria display. | Functional UI bug / hierarchy. | Added the semantic `analysis_profile_criteria_view()` hook and a dedicated profile badge; no positional selector or widget-order dependency. |
| Analyzer Review | Embedded, local review and existing CS2 hand-off already work. | Core workflow with scenes, reasons and direct review actions. | No proven structural defect in this pass. | Preserved; no second review engine. |
| Optimizer main page | Functionally started at System Check, so the four-domain product structure was not visible before local evidence was rendered. | Recognizable overview with System, Graphics, Network and BIOS Optimizer; System Check is part of System Optimizer. | Missing structure / wrong information hierarchy. | Added a fixed four-area overview and separated `1 · System Check` from `2 · Optimizer Assessment`. Non-confirmed areas are visibly Preview, not simulated functionality. |
| System Optimizer | Read-only check and result cards existed. | Facts first, assessment second, clear no-Apply boundary. | Information hierarchy. | Kept collector and contracts; made the two levels explicit and made the page vertically scrollable at small heights. |
| Graphics / Network / BIOS | Shared generic domain contract exists, but no top-level representation existed before a scan. | Visible, understandable, honest areas. | Missing navigation/overview structure. | Added domain cards with no false capability claim. Their state is derived from existing domain models after a scan. |
| Status language | Values existed, but labels mostly repeated implementation status text. | Visible distinction of Evidence, Ready/OK, Conditional, Unknown and Warning. | Information hierarchy. | Added one fail-closed presentation map for existing statuses. It changes labels/colors only, never evaluations. |
| Tactical Replay | Before a scene, a blank viewer chrome and canvas could read as unfinished. | Explain the Analyzer -> Review -> Tactical sequence before a scene exists. | Empty-state UX. | Added a three-step empty state; the existing scene/tick/replay body appears only after a reviewed scene is transferred. |
| Cards / headers | Dark card family, Inter/Orbitron, sidebar and brand already exist. | Cohesive Midnight/Metallic application without white/native foreign surfaces. | Existing visual follow-up, not an architecture issue. | Reused the shared tokens and components; did not invent a second style family. |

## Criteria hook and count contract

The Analyzer now derives its profile display from the selected
`AnalysisProfile`, not from card order, string replacement or positional DOM
selection. The UI uses the stable profile hook:

`Aktive Kriterien: <enabled objective rules> / <available objective rules>`

Examples are truthful to the existing contract: `review_v1` is `7 / 7` and
`highlight_v1` is `5 / 7`. No profile is silently reduced to make a visual
counter look nicer. This maintains correct behavior even if the screen layout
or number of cards changes.

## Status semantics

| Existing state | UI presentation | Meaning |
| --- | --- | --- |
| `OK` | `READY / OK` | A local fact/result is available and the existing check evaluated it. |
| `NO_CHANGE` | `EVIDENCE / NO CHANGE` | Evidence exists; the existing Pack makes no positive recommendation. |
| `REVIEW` / `CONDITIONAL` | `CONDITIONAL / CHECK` / `CONDITIONAL` | A condition or manual verification remains. |
| `INSUFFICIENT_EVIDENCE` / unknown | `UNKNOWN / NOT AVAILABLE` | Evidence is not sufficient; no positive conclusion is made. |
| `ACTION_REQUIRED` | `WARNING / ACTION REQUIRED` | Existing check reports actual attention needed. |

No status label manufactures an Improve recommendation, an Apply action or an
otherwise unavailable technical mode.

## Visual review evidence

The local desktop shell was reviewed in a wide live window for Analyzer,
Optimizer and Tactical Replay. The review confirmed a persistent dark sidebar,
no white foreign surface, read-only Optimizer overview with all four domains,
the separate System Check hierarchy and the Tactical three-step empty state.

The Home command-center composition remains intentionally untouched in this
pass because it is functionally accepted and its remaining final-polish
decision is explicitly deferred. Rules, Reports and Settings retain the shared
shell and no mockup-only controls were added.

## Remaining visual limits

- The master still asks for a later global final-polish decision on metallic
  depth, card/button/border/radius tokens before indiscriminate reuse across
  every product route.
- Real live Analyzer review/replay content requires a user-selected verified
  local demo workflow; this pass did not generate fake scenes merely for a
  screenshot.
- Graphics, Network and BIOS remain data-driven read-only domains. A Preview
  label is intentional until existing evidence actually produces their
  respective view models.
