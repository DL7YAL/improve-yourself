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

Task: 3d-pov-anubis-render-ready-prep
Branch: azure/3d-pov-anubis-prep
Status: PASS / STALE — merged through PR #21; shared original/permissive fallback assets and render-ready contracts remain reusable static preparation only.

## Azure — current task

Task: 3d-pov-mirage-prep-v2
Branch: azure/3d-pov-mirage-prep-v2
Base HEAD: ce743519d073a6f2cc09355f89da572753fdc0a4
Owned files:
- coordination/ACTIVE_WORK.md
- resources/3d_pov/de_mirage/**
- tools/pov_prep_data/validate.py
- tools/dev/Build-LocalAnubisAsset.py
- tests/pov_prep_data/test_mirage_pov_prep.py
Status: BLOCKED — static prep and Beast handoff are committed; Azure/MCP has no command-execution capability to run the required pytest/validator/compile/diff checks. Beast must execute the listed static validations before PR readiness.
Depends on Codex: NO
Handoff required: YES — Beast must execute only through existing ReplayStore → ReplayController → ReplayRendererSession → PandaReplayRenderer and iy.map_asset/v1.
Scope: Mirage static provenance/prep, generic local-asset-builder map ID support, targeted static validation, and local execution handoff. No protected replay/runtime/controller/renderer implementation, parser, DataHub, cloud, or Azure-resource changes.

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
