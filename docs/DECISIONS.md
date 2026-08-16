# Product Decisions

This file records decisions that should not be repeatedly reopened without a concrete reason.

## Current decisions

- The product must not become a Leetify/Stats-style clone.
- Prefer a curated product line over many user options.
- Analysis and explanation matter more than raw statistics.
- Avoid feature bloat.
- Avoid unnecessary overclocking and risky system tweaks.
- Changes should be reversible whenever possible.
- Tactical Replay uses an original analysis-oriented sound language.
- There is one fixed analysis mix rather than multiple selectable sound modes.
- V2/V3 ideas are documented and deferred unless they are necessary for V1.
- Existing prototypes are reference material, not parallel active products.

## Benchmark multi-map transition design — locked

- **Decision:** The benchmark sequence remains a visually continuous three-environment run rather than three hard-cut scenes. The intended order is Nuke Outside -> Ancient B -> Inferno Apps/A. Nuke transitions into Ancient by driving the camera into a smoke until vision is fully obscured; the Ancient scene should emerge around the B-ramp/water area so water/reflection rendering is part of the measured workload. The camera then travels through the Ancient B area toward Red Room. Red Room's red visual identity must be consciously visible before a flashbang produces a full white-out; the actual scene switch happens inside that flash and the Inferno sequence begins around the Apps lower stair/entrance area. Camera height, direction, motion and dominant color/texture should be matched across the hidden transitions so the run reads as one continuous movement.
- **Reason:** If three different CS2 environments are used, hard cuts would make the benchmark feel like three unrelated clips and would remove much of the value of choosing multiple environments. Smoke and flash are natural CS2 occlusion events that can hide the technical scene switches while also remaining meaningful rendering workload. Ancient water/reflections add a deliberately distinct graphics stressor.
- **Impact:** These transitions are an essential benchmark design and acceptance criterion, not optional polish. A transition is not considered finished if a normal viewer immediately perceives a hard map cut. The current `nuke_outside`, `ancient_b` and `inferno_apps_a` controller scenes must be refined to implement and validate this continuous camera concept without compromising reproducibility of the measured sections.
- **Date:** 2026-08-16

## Decision format

When a new decision is added, record:

- **Decision**
- **Reason**
- **Impact**
- **Date**

This keeps the project consistent and prevents old questions from being debated from scratch every few weeks.
