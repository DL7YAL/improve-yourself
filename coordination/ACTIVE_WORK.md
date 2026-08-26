# ACTIVE WORK

Shared coordination state for parallel Codex and Azure work.

GitHub `main` is the canonical source of truth.

## Codex

Task: product-roadmap-alignment
Branch: codex/product-roadmap-alignment
Base HEAD: verify current `main` immediately before branch creation
Owned files:
- docs/**
- coordination/** (except files explicitly owned by Azure during this task)
Status: READY
Depends on Azure: NO
Handoff required: NO

## Azure

Task: harden-iac-ci-phase1
Branch: azure/harden-iac-ci-phase1
Base HEAD: verify current `main` immediately before branch creation
Owned files:
- azure/**
- config/azure_config.py
- services/azure_*.py
- requirements-azure.txt
- .env.example (only if required by the approved Azure task)
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
- Azure Phase 1 must not deploy or modify live Azure resources. Repo-only changes, validation, and dry-run/what-if preparation are allowed when explicitly authorized.
