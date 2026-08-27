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
Status: BLOCKED / SUPERSEDED — static preparation remains on its branch for a later Beast validation handoff; owner instruction ended this as the active Azure assignment on 2026-08-27.

## Azure — current task

Task: unified-viewer-v1-ancient
Branch: azure/unified-viewer-v1-ancient
Base HEAD: 1605d3c68db00791c9740d389b335cc8d1695c63
Owned files:
- coordination/ACTIVE_WORK.md
- Viewer/product files required for the Ancient 2D vertical slice
- a small read-only shared Viewer-State adapter/contract
- generated Ancient product background assets selectively adapted from PR #26
- focused Viewer-State, map-background, and Viewer tests
Status: IN PROGRESS
Depends on Codex: NO
Scope: one canonical ReplayStore/ReplayController, read-only derived Viewer State, replaceable 2D map background, Ancient player/view-direction product rendering, and future 3D-compatible state. No parser, Replay V2, ReplayStore, ReplayController, AnalyzerCore, AnalyzerDataHub, transform-authority, cloud, or Azure-resource changes.

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
- Azure must not modify protected local product-core files except where the project owner explicitly authorizes a narrowly scoped product slice in the current task.
- 3D/POV prep is static data/evidence only. Current tick and entity/POV state must come from the existing canonical Replay/Analyzer path.
- Region/data-residency choice remains unresolved; do not switch regions without explicit authorization.
- No live deployment or live Azure resource modification is authorized.
