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

Task: 3d-pov-mirage-prep-v2
Branch: azure/3d-pov-mirage-prep-v2
Status: PASS / STALE — static prep and builder generalization are now present on main; PR #23 generalized the runtime map gate.

## Azure — current task

Task: 3d-pov-remaining-mapset-prep-v3
Branch: azure/3d-pov-remaining-mapset-prep-v3
Base HEAD: 75bfa3e6218cc26ddcfa89352111666785787bb7
Owned files:
- coordination/ACTIVE_WORK.md
- resources/3d_pov/de_ancient/**
- resources/3d_pov/de_dust2/**
- resources/3d_pov/de_inferno/**
- resources/3d_pov/de_nuke/**
- resources/3d_pov/de_overpass/**
- resources/3d_pov/de_train/**
- resources/3d_pov/de_vertigo/**
- resources/map_overviews/maps/de_inferno.json
- resources/map_overviews/maps/de_nuke.json
- resources/map_overviews/maps/de_overpass.json
- resources/map_overviews/maps/de_train.json
- resources/map_overviews/maps/de_vertigo.json
- tools/pov_prep_data/validate_mapset.py
- tests/pov_prep_data/test_remaining_mapset_prep.py
- tests/map_overview_data/test_map_overview_data.py
Status: READY — static prep and handoffs are committed; executable pytest/validator/compile/diff checks remain BLOCKED_FOR_BEAST because GitHub MCP has no command runner.
Depends on Codex: NO
Handoff required: YES — Beast performs current-build VPK extraction, local-only map derivatives, Replay V2 recovery and visible viewer smoke.
Scope: Static preproduction for Ancient, Dust2, Inferno, Nuke, Overpass, Train and Vertigo only. No protected runtime, renderer, parser, Replay, Analyzer, controller, store, DataHub, Optimizer, cloud or Azure-resource change.

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
