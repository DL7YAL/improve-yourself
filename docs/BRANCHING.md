# Branching Policy

## Purpose

Keep development understandable, reversible and reviewable without creating unnecessary process overhead.

## Permanent branch

### `main`

`main` represents the cleanest known project state.

Rules:
- Do not use `main` as a scratchpad.
- Experimental work does not start directly on `main`.
- Merge only coherent, reviewable changes.
- Prefer a pull request before merging development work into `main`.

## Current development branch

### `dev/v1-foundation`

This is the first real development branch for V1.

Its job is to consolidate the useful parts of the existing prototypes into one clean codebase and establish the first runnable V1 baseline.

## Optional short-lived branches

Use these only when they make the work clearer:

- `feature/<name>` — new functionality
- `fix/<name>` — bug fixes
- `docs/<name>` — documentation-only work
- `experiment/<name>` — isolated experiments that must not contaminate the active V1 baseline

Examples:

```text
feature/system-check
feature/demo-scene-ranking
fix/replay-timing
docs/audio-design
experiment/mouse-movement-analysis
```

## Merge rule

1. Work is developed and tested away from `main`.
2. The change must have a clear purpose.
3. Generated files, local dumps, demos and secrets must not be included.
4. A pull request is used to review the change before it reaches `main` whenever practical.
5. `main` should remain usable and understandable.

## Commit messages

Use short messages with a simple prefix where helpful:

- `feat:` new functionality
- `fix:` bug fix
- `docs:` documentation
- `refactor:` restructuring without intended behavior change
- `test:` tests
- `chore:` repository/tooling maintenance

## V1 discipline

A good V2/V3 idea does not automatically become V1 work. If it is not necessary for the agreed V1 scope, document it and defer it.
