# Improve Yourself — Archive / Safe Plan

Stand: 2026-08-29
Mode: non-destructive plan; no source deletion performed

## Reason

GitHub file moves require creating the destination and deleting the source. Project policy for this maintenance pass explicitly forbids deleting historical material. Therefore no fake or partial move is performed. This document records what should leave the active surface and where it belongs once a true non-destructive move/archive mechanism or explicit move authorization is available.

## Safe target structure

archive/safe/
- coordination/completed/
- coordination/superseded/
- handoffs/codex-history/
- benchmark/parked/
- prototypes/reference-only/
- ui/superseded/
- pov/completed-slices/
- azure/completed-or-superseded/

## Confirmed active-surface cleanup candidates

### coordination/ACTIVE_WORK.md
The file currently mixes active work with completed/stale history, contradicting its own rule that it tracks active work rather than project history.

Planned extraction:
- completed/stale Codex entry `v2-local-review-replacement` -> `archive/safe/coordination/completed/active-work-codex-v2-local-review-replacement.md`
- completed Optimizer Golden Master V2 entry -> `archive/safe/coordination/completed/active-work-optimizer-golden-master-v2.md`
- Azure `harden-iac-ci-phase2-validation` -> `archive/safe/azure/completed-or-superseded/harden-iac-ci-phase2-validation.md`
- Azure `complete-2d-map-overview-dataset` -> `archive/safe/azure/completed-or-superseded/complete-2d-map-overview-dataset.md`
- Azure `3d-pov-anubis-render-ready-prep` -> `archive/safe/azure/completed-or-superseded/3d-pov-anubis-render-ready-prep.md`

The currently BLOCKED Mirage prep entry is historical/current-state evidence but no agent can execute it at present; do not classify it as active implementation until resources/ownership are restored. Preserve its handoff in Safe if ACTIVE_WORK is later reduced.

### coordination/agents/codex.md
This file is approximately 311 KB and functions as accumulated handoff history rather than a compact current handoff. Planned target:
- full historical snapshot -> `archive/safe/handoffs/codex-history/codex-full-history.md`
- active `coordination/agents/codex.md` should later contain only the latest unresolved/active handoff state plus links to Safe history.

No truncation is authorized until the historical snapshot is preserved and verified.

### Benchmark
Benchmark is parked because of the documented SDK/Valve blocker. Benchmark design decisions remain valid historical/locked decisions, but benchmark execution should not occupy the active V1 completion surface.

When reorganized, benchmark runtime/handoff material that is not needed for current product work should be indexed under:
- `archive/safe/benchmark/parked/`

Do not move source/runtime files merely because the workstream is parked; archive planning here primarily concerns coordination, handoffs and obsolete working documents.

### 3D/POV documentation
`docs/` contains numerous implementation slices, preflights, renderer-session and evidence-gate documents. They are valuable evidence and must not be deleted. Once the current canonical 3D/POV contract is identified from the locked decision plus latest active spec, completed/superseded slice documents should move to:
- `archive/safe/pov/completed-slices/`

Keep active only the current canonical contract/spec, current unresolved evidence/blocker document(s), and any file required by active implementation/tests.

Exact per-file classification is still to be verified before any move; filename alone is insufficient evidence of supersession.

## Files that should remain active

- `coordination/PROJECT_MASTER_CONTEXT.md` — canonical high-level current truth.
- `coordination/CURRENT.md` — current cockpit until deliberately reduced/reconciled.
- `docs/DECISIONS.md` — locked/current decisions; old decisions should only be archived when explicitly superseded, never merely because they are old.
- `WORKFLOW_RULES.md` and agent-base/roadmap documents referenced by CURRENT, provided they remain current after content verification.
- Product source, tests, runtime assets and build files that are part of the current codebase. This archive pass must not treat code as stale solely from naming/history.

## Required next cleanup pass

1. Reconcile `coordination/CURRENT.md` against `PROJECT_MASTER_CONTEXT.md`; remove active-cockpit emphasis on DONE items only after preserving their evidence in Safe/index.
2. Verify every 3D/POV doc by content before classifying active vs completed/superseded.
3. Snapshot the full Codex handoff history into Safe before reducing the active handoff.
4. Reduce `ACTIVE_WORK.md` to genuinely executable/current ownership only.
5. Add a Safe index with source path, target path, classification, reason, last-known status and preservation check.
6. Never delete historical content as cleanup. Any actual GitHub move must preserve content at target and verify it before source removal, and source removal requires explicit authorization under the project policy.

## Classification vocabulary

- ACTIVE — required for current V1 work.
- LOCKED_REFERENCE — current decision/spec that constrains work.
- DONE_EVIDENCE — completed proof/history.
- SUPERSEDED — replaced by a newer confirmed authority.
- PARKED — valid work intentionally inactive pending condition/decision.
- REFERENCE_ONLY — prototype/reference, not an active product path.
- BLOCKED — unresolved and cannot currently progress.
- UNVERIFIED — classification requires content inspection.

This plan intentionally prefers `UNVERIFIED` over guessing.