# ACTIVE WORK

Shared coordination state for parallel Codex and Azure work.

GitHub `main` is the canonical source of truth.

## Completed / stale entries

### Codex

Task: v2-local-review-replacement
Branch: codex/v2-local-review-replacement
Status: PASS / STALE — completed and superseded by merged V2 review work

### Azure

Task: harden-iac-ci-phase2-validation
Branch: azure/harden-iac-ci-phase2-validation
Status: PASS / STALE — completed and merged through PR #14

## Azure — current task

Task: 2d-map-overview-full-mapset
Branch: azure/2d-map-overview-full-mapset
Base HEAD: b5835ac9c7b78f7a61b39e90569181cea90ee51b
Owned files:
- coordination/ACTIVE_WORK.md
- resources/map_overviews/**
- tests/map_overview_data/**
Status: IN PROGRESS
Depends on Codex: NO
Handoff required: YES — future consumer must use canonical Replay/Analyzer current-tick state
Scope: Add static iy.map_overview_metadata/v1 packages for intended competitive maps only. No runtime, parser, Replay, Analyzer, controller, store, DataHub, V1, cloud, Azure, or viewer changes.

## Rules

- Read this file before starting parallel Codex and Azure work.
- Verify current GitHub `main` immediately before creating a task branch; use that exact HEAD as the task base.
- Do not modify files owned by another active agent.
- Codex branches use `codex/<task-name>`.
- Azure branches use `azure/<task-name>`.
- If file ownership overlaps, STOP and coordinate before continuing.
- Use status values: `READY`, `IN PROGRESS`, `BLOCKED`, `PASS`.
- Keep entries short and current. This file tracks active work, not project history.
- Preserve the canonical AnalyzerCore / AnalyzerDataHub / iy.replay/v2 / ReplayStore / ReplayController path. No second parser, store, controller, data hub, or V1 fallback may be introduced.
- Azure must not modify protected local product-core files.
- Map overview preparation is static data/projection metadata only. Current tick and entity state must come from the existing canonical Replay/Analyzer path.
- Region/data-residency choice remains unresolved; do not switch regions without explicit authorization.
- No live deployment or live Azure resource modification is authorized.
