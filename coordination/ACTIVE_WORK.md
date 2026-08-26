# ACTIVE WORK

Shared coordination state for parallel Codex and Azure work.

GitHub `main` is the canonical source of truth.

## Codex

Task: v2-local-review-replacement
Branch: codex/v2-local-review-replacement
Base HEAD: verify current `main` immediately before branch creation
Owned files:
- src/improve_yourself/**
- tests/**
- tools/dev/**
- pyproject.toml
- docs/**
Status: READY
Depends on Azure: NO
Handoff required: NO

## Azure

Task: harden-iac-ci-phase2-validation
Branch: azure/harden-iac-ci-phase2-validation
Base HEAD: verify current `main` immediately before branch creation
Owned files:
- azure/**
- config/azure_config.py
- services/azure_*.py
- requirements-azure.txt
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
- Codex must preserve the canonical AnalyzerCore / AnalyzerDataHub / iy.replay/v2 / ReplayStore / ReplayController path. No second parser, store, controller, data hub, or V1 fallback may be introduced.
- Codex must not remove the existing V1 workflow in this sprint. Build the V2 replacement alongside it and preserve fail-closed/local-first behavior.
- Azure must not modify protected local product-core files.
- Region/data-residency choice remains unresolved; do not switch regions without explicit authorization.
- Azure Phase 2 validation remains repo-only. No live deployment or live Azure resource modification is authorized.
