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

Task: complete-2d-map-overview-dataset
Branch: azure/2d-map-overview-data-prep
Base HEAD: 9ea1a9d0d5126c615a1a9f3b02cab91ca826fba5
Owned files:
- coordination/ACTIVE_WORK.md
- resources/map_overviews/**
- tools/map_overview_data/**
- tests/map_overview_data/**
Status: BLOCKED
Depends on Codex: NO
Handoff required: YES — future consumer must use canonical Replay/Analyzer current-tick state
Scope: Extend the validated iy.map_overview_metadata/v1 pilot only to maps evidenced by the current repository/product context. No runtime, parser, Replay, Analyzer, controller, store, DataHub, V1, cloud, or Azure changes.
Prepared dataset: de_ancient VERIFIED, de_mirage VERIFIED, de_anubis UNVERIFIED because its tracked overview descriptor omits an explicit rotation value.
Blocker: This MCP session cannot execute pytest, validator CLI, compileall, or git diff --check for the newly added map packages. Beast execution validation is required before PASS or PR creation.

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
