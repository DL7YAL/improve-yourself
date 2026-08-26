# ACTIVE WORK

Shared coordination state for parallel Codex and Azure work.

GitHub `main` is the canonical source of truth.

## Codex

Task: replay-v1-retirement-assessment
Branch: codex/replay-v1-retirement-assessment
Base HEAD: verify current `main` immediately before branch creation
Owned files:
- docs/**
- coordination/** (except files explicitly owned by Azure during this task)
Status: READY
Depends on Azure: NO
Handoff required: NO

## Azure

Task: harden-iac-ci-phase2-design
Branch: azure/harden-iac-ci-phase2-design
Base HEAD: verify current `main` immediately before branch creation
Owned files:
- azure/**
- config/azure_config.py
- services/azure_*.py
- requirements-azure.txt
- coordination/** (only Azure-specific coordination notes if explicitly needed)
Status: READY
Depends on Codex: NO
Handoff required: NO

## Rules

- Read this file before starting parallel Codex/Azure work.
- Verify current GitHub `main` immediately before creating a task branch; use that exact HEAD as the task base.
- Do not modify files owned by the other active agent.
- Codex branches use `codex/<task-name>`.
- Azure branches use `azure/<task-name>`.
- If file ownership overlaps, STOP and coordinate before continuing.
- Use status values: `READY`, `IN PROGRESS`, `BLOCKED`, `PASS`.
- Keep entries short and current. This file tracks active work, not project history.
- Codex must not modify Azure-owned files during this task.
- Azure must not modify protected local product-core files during this task.
- Region/data-residency choice remains unresolved; do not switch regions without explicit authorization.
- Azure Phase 2 design must remain repo-only. No live deployment or live Azure resource modification is authorized.
