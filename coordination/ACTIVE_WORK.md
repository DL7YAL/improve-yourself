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

Task: complete-2d-map-overview-dataset
Branch: azure/2d-map-overview-data-prep
Status: PASS / STALE — merged through PR #19; rotation clarification merged through PR #20

## Azure — current task

Task: 3d-pov-anubis-prep
Branch: azure/3d-pov-anubis-prep
Base HEAD: b5835ac9c7b78f7a61b39e90569181cea90ee51b
Owned files:
- coordination/ACTIVE_WORK.md
- resources/3d_pov/**
- tools/pov_prep_data/**
- tests/pov_prep_data/**
Status: BLOCKED
Depends on Codex: NO
Handoff required: YES — Beast must consume only through existing ReplayRenderer/ReplayController and iy.map_asset/v1 boundaries
Scope: Static Anubis asset/research/coordinate/camera-input evidence only. No product runtime, parser, Replay, Analyzer, controller, store, DataHub, viewer, cloud, or Azure-resource changes.
Prepared: candidate inventory, identity coordinate contract, canonical camera-input contract, three replay/world/2D anchors, redistribution boundary, validator and deterministic tests.
Blocker: This MCP session cannot execute pytest, validator CLI, compileall, or git diff --check. Beast execution validation is required before PASS.

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
- 3D/POV prep is static data/evidence only. Current tick and entity/POV state must come from the existing canonical Replay/Analyzer path.
- Region/data-residency choice remains unresolved; do not switch regions without explicit authorization.
- No live deployment or live Azure resource modification is authorized.
