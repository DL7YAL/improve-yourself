# ACTIVE WORK

Shared coordination state for parallel Codex and Azure work.

GitHub `main` is the canonical source of truth.

## Completed / stale entries

### Codex

Task: v2-local-review-replacement
Branch: codex/v2-local-review-replacement
Status: PASS / STALE — completed and superseded by merged V2 review work

Task: optimizer-golden-master-v2
Branch: codex/optimizer-golden-master-v2
Status: PASS — canonical V2 result contract, deterministic 150 base, and separate 60-case adapter validated locally.

### Azure

Task: harden-iac-ci-phase2-validation
Branch: azure/harden-iac-ci-phase2-validation
Status: PASS / STALE — completed and merged through PR #14

Task: complete-2d-map-overview-dataset
Branch: azure/2d-map-overview-data-prep
Status: PASS / STALE — merged through PR #19; rotation clarification merged through PR #20

Task: 3d-pov-anubis-render-ready-prep
Branch: azure/3d-pov-anubis-prep
Status: PASS / STALE — merged through PR #21; shared original/permissive fallback assets and render-ready contracts remain reusable static preparation only.

Task: 3d-pov-mirage-prep-v2
Branch: azure/3d-pov-mirage-prep-v2
Status: PASS / STALE — remote branch HEAD `43f9b40` is fully contained in GitHub `main`; the former file ownership and validation handoff are no longer active.

## Current tasks

### Codex

Task: project-truth-sync-v1
Branch: codex/project-truth-sync-v1
Owned files:
- coordination/ACTIVE_WORK.md
- coordination/CURRENT.md
Status: REVIEW — stale PR #7 and Azure Mirage ownership entries are reconciled with GitHub; awaits PR review.

No active Azure task is recorded here.

## Rules

- Read this file before starting parallel Codex and Azure work.
- Verify current GitHub `main` immediately before creating a task branch; use that exact HEAD as the task base.
- Do not modify files owned by another active agent.
- Codex branches use `codex/<task-name>`.
- Azure branches use `azure/<task-name>`.
- If file ownership overlaps, STOP and coordinate.
- Use status values: `READY`, `IN PROGRESS`, `BLOCKED`, `PASS`.
- Keep entries short and current. This file tracks active work, not project history.
- Preserve the canonical AnalyzerCore / AnalyzerDataHub / iy.replay/v2 / ReplayStore / ReplayController path. No second parser, store, controller, data hub, or V1 fallback may be introduced.
- Azure must not modify protected local product-core files.
- 3D/POV prep is static data/evidence only. Current tick and entity/POV state must come from the existing canonical Replay/Analyzer path.
- Region/data-residency choice remains unresolved; do not switch regions without explicit authorization.
- No live deployment or live Azure resource modification is authorized.
