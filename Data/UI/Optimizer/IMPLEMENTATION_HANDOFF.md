# Optimizer MASTER Implementation Handoff

> **SUPERSEDED 2026-09-05:** Do not execute this handoff. It has zero visual
> priority. Use `docs/design/CANVA_UI_MIGRATION_HANDOFF.md` and Canva design
> `DAHUBn5D2aM`, revision 25.

## Package location

`Data/UI/Optimizer/`

## Mandatory pre-implementation read order

1. `MASTER_MANIFEST.json`
2. `VISUAL_SOURCE_PRECEDENCE.md`
3. Matching screen specification
4. Matching `*_MASTER.png`
5. `BEAST_ACCEPTANCE_CONTRACT.md`

## Implementation boundary

Implement only the approved Overview and System Optimizer Detail presentation.
Do not change backend, Optimizer evaluation, recommendation semantics,
backup/restore, settings, system-data collection, safety behavior, or technical
contracts unless a separately authorized technical defect requires it.

## Required completion evidence

- Full runtime screenshot for each approved screen.
- Existing relevant tests and `git diff --check`.
- Explicit reporting of a real blocker; no replacement visual reference.
- Stop at `READY_FOR_HUMAN_REVIEW`; do not build a release or begin follow-up
  work.
