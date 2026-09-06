# Improve Yourself — Canva UI Migration Handoff

Status: **BINDING VISUAL AUTHORITY / IMPLEMENTATION PREPARED**  
Decision owner: **Tristan**  
Prepared: **2026-09-05**

## Confirmed source

The approved working source is Canva design `DAHUBn5D2aM`, titled
`Versuch.nr1`, revision `25`, with eight pages. Tristan confirmed that page 1
was created as the intended UI template and may be adjusted where necessary.

- Canva view: <https://www.canva.com/d/N5EMb2oiYndTeOo>
- Last Canva update: `2026-09-02T08:26:31Z`
- Machine-readable page mapping:
  `docs/design/CANVA_UI_AUTHORITY_CANDIDATE.json`

Tristan activated this Canva revision as the sole visual authority on
2026-09-05. This handoff does not delete historical files or edit Canva, but it
does revoke all implementation priority from the former PDF, UI Reference Pack
and Optimizer MASTER sources.

## Product decision to carry forward

Page 1 is the primary target for the application shell and Dashboard. Its
composition is intentionally stronger than the current runtime shell and is to
be preserved as closely as the real product contracts allow:

- persistent dark left navigation;
- compact top status row;
- six clearly differentiated primary module cards;
- progress, recent analyses and quick-access middle row;
- lower product idea and community/information panels;
- near-black/navy surfaces, restrained cyan contours and deliberate per-module
  accent colours.

Pages 2–7 are module-level visual candidates. Page 8 is a brand presentation
reference. They inherit page 1's shell language; they do not establish new
functional contracts.

## Non-negotiable functional boundary

Canva controls intended layout, hierarchy, proportions, spacing, surface
language, icon treatment and visual emphasis after activation. Current tested
code remains the functional truth.

The implementation must therefore replace all illustrative Canva values with
real runtime values or explicit neutral/unavailable states. It must not revive:

- fake progress, rank, streak, achievement, match or benchmark values;
- unsupported AI claims or black-box verdicts;
- automatic system, BIOS, driver, registry or network changes;
- Apply/Restore authority, one-click recovery or backup claims that are not
  implemented and validated;
- unsupported AMD-Adrenalin import/export;
- inferred Tactical events, heatmaps, map data or longitudinal improvement;
- a second parser, replay store, controller, data hub or analysis truth.

Optimizer remains read-only. Benchmark remains parked. Tactical, Analyzer and
Review continue to consume the canonical replay/analyzer authority.

## Completed authority switch and remaining export protocol

The repository authority switch is complete: the former manifests and policy
documents are marked `SUPERSEDED`, while
`CANVA_UI_AUTHORITY_CANDIDATE.json` is binding. The later implementation task
must preserve this single-source rule while adding verified local exports.

1. Export the approved Canva pages at their original dimensions.
2. Give every export a stable, descriptive repository filename.
3. Record Canva design ID, page ID, revision, dimensions and SHA-256 for every
   exported file in a new binding manifest.
4. Preserve the existing superseded metadata and historical assets; do not
   restore their priority or destroy the audit trail.
5. Confirm that no new or edited document reintroduces authority for:
   - `docs/design/ui-reference/UI_REFERENCE_MANIFEST.json`
   - `docs/design/ui-reference/README_UI_REFERENCE.md`
   - `docs/UI_REFERENCE_PACK_POLICY.md`
   - `docs/design/README.md`
   - `docs/design/MOCKUP_INDEX.md`
   - `docs/design/UI_SPEC.md`
   - `docs/UI_SOURCE_OF_TRUTH_PASS.md`
   - `docs/UI_TARGET_ALIGNMENT_V1_1.md`
   - `docs/OPTIMIZER_VISUAL_FIDELITY_PASS.md`
   - `Data/UI/Optimizer/MASTER_MANIFEST.json` and its linked handoff/spec files.
6. Activate exactly one new Canva-derived manifest as the visual authority.
7. Only after the authority switch, refactor the runtime UI against the new
   targets.

The checked-in concept PDF stays historical. Existing logos/fonts remain active
unless the later task explicitly replaces them with approved exported assets.

## Recommended implementation slices

Each slice must preserve callbacks and product contracts and end in a fresh
runtime screenshot at `1536x1024` and `1080x720`.

1. **Reference activation only** — export, hash, archive status, manifest and
   documentation consistency. No runtime code.
2. **Shared shell** — page-1 sidebar, header, navigation states, surfaces,
   typography, spacing and reusable component tokens.
3. **Dashboard** — implement page 1 with real/neutral data and responsive
   reflow; no fabricated metrics.
4. **Analyzer** — adapt page 2 while keeping `Übersicht | Analyse | Review`,
   demo preflight, selection, profiles, rules and scenes.
5. **Tactical Replay** — adapt page 5 around the canonical selected scene and
   available map/replay evidence.
6. **Optimizer** — adapt page 6 while removing every Apply/Restore implication
   and keeping the existing read-only evidence path.
7. **My Improvement, Benchmark, Settings** — adapt pages 3, 4 and 7 with honest
   disabled/empty states wherever data or capability is absent.
8. **Global visual acceptance** — compare every live route with its activated
   Canva export and verify dark controls, overflow, focus, text clipping and
   navigation at both target viewports.

## Structural engineering warning

`src/improve_yourself/analyzer_shell.py` currently contains the full desktop
shell and multiple page-specific component families in one large module. The
visual migration should first extract shared visual tokens/components or place
new reusable components behind stable interfaces. It must not mix a broad
visual replacement with parser, replay, Optimizer or System Check logic.

The current special Optimizer canvas and its duplicated navigation language
must be folded back into the shared page-1 shell instead of becoming a second
application shell.

## Acceptance gate

The migration is complete only when all of the following are true:

- the runtime is immediately recognizable as Canva page 1 and its module
  family at comparable viewport sizes;
- one shared shell and component language is used across every route;
- no current function or safety boundary regresses;
- no illustrative data is presented as real;
- unavailable functions are clear without making the product look broken;
- screenshots for all routes and both target viewports are stored as review
  evidence;
- automated tests, Python compile and `git diff --check` pass;
- Tristan performs the final visual acceptance.

## Explicit non-actions in this preparation

- No Canva content was edited.
- No historical image asset was modified or removed.
- Old manifests and policies were changed only to revoke their visual authority.
- No runtime source code was changed.
- No merge, build or release was performed.
