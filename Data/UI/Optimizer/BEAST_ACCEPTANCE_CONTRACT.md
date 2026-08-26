# Beast Optimizer Visual Acceptance Contract

## Scope

Visual acceptance covers only Optimizer Overview and System Optimizer Detail.
The Master PNG for each screen is compared at a comparable viewport.

## Required evidence

- Runtime Overview screenshot showing the full, unedited application window.
- Runtime System Optimizer Detail screenshot showing the full, unedited
  application window and `DETAILS & ERKLÄRUNG` panel.
- Direct comparison against the matching MASTER for shell, logo, navigation,
  selected state, Midnight palette, cards, borders, hierarchy, detail panel,
  and local-only scrolling.
- Existing behavior, backend, safety, and Optimizer contracts remain unchanged.

## Pass condition

The runtime is immediately recognizable as the corresponding approved Master
without visual substitution, redesign, unapproved UI additions, global
Optimizer scrolling, or use of prohibited visual sources.

## Stop condition

Stop at `READY_FOR_HUMAN_REVIEW` after the prescribed implementation and
checks. A missing or ambiguous visual source is a blocker, not permission to
improvise.
