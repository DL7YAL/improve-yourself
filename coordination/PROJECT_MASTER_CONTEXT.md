# Improve Yourself — Project Master Context

Stand: 2026-08-29
Status: canonical coordination truth for active V1 planning

## Visual authority override — 2026-09-05

Canva design `DAHUBn5D2aM` (`Versuch.nr1`), revision 25, is the sole binding
visual source. Page 1 is the shell/Dashboard template; pages 2–7 are the module
visual family and page 8 is the brand reference. Every prior PDF, UI Reference
Pack and Optimizer `MASTER` is SUPERSEDED and must not be implemented. Current
tested functionality, canonical data authority and safety boundaries still
override illustrative Canva values and unsupported actions.

## 1. Current product direction

V1 is in consolidation, not feature-expansion mode. Existing functionality is to be bounded, simplified where justified, integrated, verified, and completed. No broad UI redesign is active now; final visual alignment is deferred until the V1 module outputs are fixed.

Benchmark is outside the active product-completion path while its SDK/Valve blocker remains unresolved.

## 2. Hard core and data authority

The intended hard core is Core + Analyzer around one canonical demo/replay truth.

Data-flow rule:

Demo -> one Awpy-backed parse/workflow -> canonical replay/analyzer data -> consumers

Confirmed canonical runtime authorities already present in the project are AnalyzerCore / AnalyzerDataHub / iy.replay/v2 / ReplayStore / ReplayController. No second parser, store, controller, data hub, or competing replay truth may be introduced.

Awpy remains the V1 parser path. Direct demoparser2 replacement/hybridization is not an active V1 task: isolated comparison found no end-to-end advantage sufficient to justify migration and additional normalization/regression work.

Consumers request/use only the data required for their responsibility. They must not reparse the source demo or independently reinterpret canonical playback state.

## 3. Analyzer boundary

Analyzer remains a primary product component and the fachliche analysis layer. Current locked V1 scene flow remains the baseline until explicitly revised:

Demo -> Parser -> Teams/Player Selection -> Analysis Profile -> Rule Engine -> Merged Scenes -> Review

Current evidenced V1 anchors include objective kill/headshot/wallbang/through-smoke/blind qualifiers, entry and bounded multi-kill combinations. Overlapping markers from one situation merge into one scene. Weak standalone indicators do not emit standard scenes.

Open product simplification decision: whether the broad/free filter concept should remain active in V1 or be reduced to a small curated set of understandable highlight/situation categories. No filter implementation is to be removed until its current dependencies and required retained behavior are explicitly checked.

## 4. Tactical / 2D / 3D / POV

2D, First-Person POV and fixed Third-Person analysis views consume the canonical replay truth. The viewer/rendering side owns presentation, not parsing or playback authority.

The current locked 3D/POV V1 boundary remains: tick-preserving comparison, First Person, one deterministic Third-Person analysis camera, and evidence-qualified sightlines. Freecam/orbit/cinematic direction, inferred missing geometry/state, and renderer-owned playback are outside V1.

The viewer may be treated as a strongly encapsulated module, but it receives canonical replay/analyzer data; it does not become a second backend or source of truth.

My Improvement may consume canonical analysis/replay results and scene references. It should not depend on renderer/viewer internals as its data authority.

## 5. Optimizer / System Check

Optimizer/System Check is functionally separate from demo analysis and is the strongest candidate for a clean module boundary inside the common Improve Yourself application.

V1 remains read-only: evidence/measurement and recommendations must not create Apply authority or uncontrolled system changes. Existing System Check baseline remains read-only.

Current architectural proposal to verify before implementation: encapsulate Optimizer behind a small Shell/Core-facing interface with its own checks, evidence/recommendation logic, tests and UI components, without fachliche dependencies on Analyzer/Tactical/My Improvement. A separate executable is not an active V1 requirement.

## 6. UI and navigation freeze

Do not perform another broad visual rebuild now. Existing UI remains functional working UI while module/output contracts are completed.

What may be specified now: navigation, module hierarchy, tab structure, mandatory contents, loading/ready/error/empty states, output/viewer windows and binding to approved visual references.

Analyzer navigation currently intended: Übersicht | Analyse | Review.

Final visual alignment is one later pass against the approved MASTER/reference material after Analyzer, Review, Tactical/2D/3D/POV, My Improvement and other required V1 outputs are fixed.

## 7. Resource discipline

Fast/Codex/Work usage is limited and must not be spent on broad exploratory improvement loops. Static product work—scope definitions, navigation, contracts, tables, asset rules, manifests, README/reference consolidation and Beast task preparation—should be prepared without expensive broad agent runs where possible.

Implementation tasks for The Beast must be narrow: one owned slice, fixed goal, confirmed contracts, acceptance criteria, explicit non-goals and STOP. No open-ended orders such as “improve Analyzer” or “make UI better.”

## 8. Active priorities

P0 — preserve one canonical data/replay authority and prevent duplicate parsing/state ownership.

P0 — finish/verify already-started V1 module work without adding new feature branches of thought.

P0 — define Analyzer V1 scope, including explicit decision on free-filter complexity versus curated situation/highlight categories.

P0 — finish the required Tactical/2D/3D/POV output contract and remaining POV work against canonical replay state.

P1 — verify Optimizer coupling read-only before deciding whether any code movement is justified.

P1 — manifest navigation and output contracts while visual UI remains frozen.

P1 — after functional V1 outputs are fixed, perform one final UI alignment pass.

P2 — Candidate packaging, end-to-end acceptance and external test after P0/P1 completion.

PARKED — Benchmark multi-map/runtime work until the documented SDK/Valve blocker has a new evidenced resolution path.

## 9. Archive / Safe policy

Nothing historical is to be destroyed merely because it is stale, superseded, duplicated or no longer active. Such material belongs under a clearly marked archive/safe hierarchy and remains searchable.

Target hierarchy:

archive/safe/
  coordination/completed/
  coordination/superseded/
  handoffs/codex-history/
  benchmark/parked/
  prototypes/reference-only/
  ui/superseded/
  pov/completed-slices/
  azure/completed-or-superseded/

Moving existing repository files requires a create-at-target plus delete-at-source operation in GitHub. Because deletion is explicitly forbidden by the maintenance policy, this run does not perform pseudo-moves. See coordination/ARCHIVE_PLAN.md for the exact cleanup plan and classification rules.

## 10. Consistency rules

- Current confirmed architecture beats older handoff prose.
- Locked decisions remain valid until explicitly superseded.
- Completed evidence stays historical; it does not remain an active task merely because its report still exists.
- Parked work is not active work.
- Prototype/reference material is not a parallel product.
- Missing evidence is marked open; it is never filled by assumption.
- No destructive cleanup.
