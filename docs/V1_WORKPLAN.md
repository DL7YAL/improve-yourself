# V1 Work Plan

> **Historical consolidation plan.** This document records the earlier
> `dev/v1-foundation` migration intent. It is not the current capability
> inventory and does not authorize an Apply/Restore path. The current local
> architecture and roadmap boundary are in
> [`PRODUCT_ROADMAP_ALIGNMENT.md`](PRODUCT_ROADMAP_ALIGNMENT.md).

Branch: `dev/v1-foundation`

## Phase 1 — Inventory

Review each saved prototype and document:
- what it does
- what already works
- dependencies
- known problems
- whether it is KEEP / REVISE / DISCARD / DEFER

## Phase 2 — Consolidation

Move only approved components into the clean module structure:
- `app/system_check/`
- `app/optimizer/`
- `app/demo_analyzer/`
- `app/tactical_replay/`

## Phase 3 — First runnable baseline

Goal: one reproducible local V1 build that can start cleanly and expose the first integrated workflow without relying on unrelated legacy folders.

## Phase 4 — Stabilization

- remove dead code
- normalize configuration
- add tests for critical paths
- document setup and dependencies
- future only: verify backup/restore behavior before any separately approved
  system-change capability

## Exit condition for V1 foundation

The branch is ready to merge toward `main` when the consolidated project has a coherent structure, a reproducible setup and a runnable baseline that no longer depends on the legacy prototype folders as active code.
