# Product Decisions

This file records decisions that should not be repeatedly reopened without a concrete reason.

## Current decisions

- **Visual authority (locked 2026-09-05):** Canva design `DAHUBn5D2aM`
  (`Versuch.nr1`), revision 25, is the sole UI visual authority. Page 1 controls
  the shared shell and Dashboard; pages 2–7 control module direction and page
  8 branding. All earlier PDF, UI Reference Pack and Optimizer `MASTER`
  references are `SUPERSEDED` with zero implementation priority. Their files
  remain only for history. Current functional and safety contracts override
  illustrative Canva data or unsupported actions.

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

## Benchmark Workshop asset rights and branding boundary — locked

- **Decision:** The benchmark remains a CS2 Workshop addon. Original Nuke Outside, Ancient B and Inferno Apps / Second Mid are the sole references for their corresponding scenes. For authentic visuals and representative CS2 workload, the addon may reference original Valve/CS2 assets available through the installed game and official CS2 Workshop Tools. Improve Yourself acquires no rights in those assets; all Valve and third-party rights remain with their respective owners.
- **Boundary:** Prefer installed runtime references. Do not extract Valve VPK content for this workflow, copy Valve assets into the repository, package them in the standalone Improve Yourself application, claim ownership, or imply Valve endorsement. Improve Yourself branding and original supplemental content remain visibly distinct and provenance-tracked. Unknown origin is fail-closed.
- **Distribution:** The Workshop benchmark and the standalone Improve Yourself product remain separate. Publication, monetization, commercial integration, or distribution outside the CS2 Workshop context requires a fresh terms and legal/release review. The complete binding policy and Nuke application gate are in `assets/maps/improve_yourself_benchmark/ASSET_RIGHTS.md`.
- **Date:** 2026-09-05

## Benchmark agent-model variety — optional, cost-bounded

- **Decision:** The benchmark may use a fixed, visually varied selection of common CT/T agent models instead of only standard bot models, but only when The Beast judges the change to be low-cost, reliable and free of meaningful new asset, dependency or reproducibility risk. The selection must be deterministic across benchmark runs; no random model assignment. Full coverage of every available agent model is explicitly out of scope.
- **Reason:** A small amount of model/material variety can make the benchmark look more representative and may add modest rendering diversity, but it is not important enough to consume significant implementation time or destabilize the benchmark.
- **Impact:** The Beast has discretion to include a small fixed set of common agent variants when implementation is cheap and clean. If it requires substantial extra work, asset handling, Workshop dependencies or troubleshooting, keep the current standard models and consider the item complete. This is a bonus/polish item and must not delay multi-map transitions, camera work, measurement quality or release readiness.
- **Date:** 2026-08-17

## ChatGPT model selection rule for local work — locked

- **Decision:** For this repository and related local Codex work, use a fixed task-based model selection rule instead of ad hoc model choice. The default is `gpt-5.6-terra` for concept work, ideation and normal planning. Use `gpt-5.6-luna` for lightweight extraction, sorting, short summaries, small routine checks, quick edits and other low-risk preview work. Use `gpt-5.6-sol` with `high` reasoning for complex, multi-step implementation, benchmark planning, camera/layout coordination and other tasks that need higher accuracy without wasting the top-tier budget. Keep `gpt-5.5` only as a fallback.
- **Reason:** The project benefits more from predictable, limit-aware model selection than from always choosing the strongest available model. Concept work needs breadth and clarity, while heavy multi-step work needs accuracy, and simple analysis should stay cheap. This keeps usage efficient and reduces unnecessary limit consumption.
- **Impact:** When a new task arrives, first classify the task and then choose the model by the rule above. Do not jump to the strongest model by default. Do not treat this as a product feature change, cloud change or architecture change. It is a working rule for local Codex/ChatGPT-assisted project work and can be revised only by another explicit decision.
- **Date:** 2026-09-06

## 3D / POV V1 view and replay boundary — locked

- **Decision:** Tactical Replay V1 uses one canonical tick-based replay truth for 2D, First Person POV and one fixed Third-Person Analysis Camera. Evidence-qualified sightline visualization is mandatory V1 functionality. The Third-Person camera is a deterministic analysis preset, not a freecam/orbit/cinematic system. The views do not parse or independently reinterpret demo state, and missing state or map evidence is never invented.
- **Reason:** Tick-preserving comparison across views is the product value of 3D/POV. A single replay contract prevents semantic drift, while fixed analytical cameras and qualified sightlines provide spatial learning value without expanding V1 into a game-engine or cinematic system.
- **Impact:** The incompatible full-match contract is introduced as `iy.replay/v2`; `iy.replay/v1` remains a compatibility path until 2D migration is proven. First Person, fixed Third Person and sightlines are acceptance requirements. Freecam, orbit, cinematic direction, inferred geometry/state and renderer-owned playback are deferred and must not enter V1 implementation.
- **Date:** 2026-08-20

## Demo Analyzer V1 neutral scene-flow boundary — locked

- **Decision:** The V1 analyzer follows `Demo -> Parser -> Teams/Player Selection -> Analysis Profile -> Rule Engine -> Merged Scenes -> Review`. Internally it separates indicators, named rules or rule combinations, profiles and results. The standard engine is neutral for review/highlight/coaching/custom use rather than a suspect-only engine. Full Demo and multi-player selection are the two selection modes; CT/T are quick selectors inside Player Select, not a third team-analysis mode. Only objective evidenced event anchors are enabled in V1, overlapping markers from one situation merge into one scene, and weak standalone information indicators cannot emit standard scenes.
- **Reason:** Stable Awpy/replay evidence and deliberate scene merging provide useful review output without fake data, duplicate situations or premature anti-cheat interpretation.
- **Impact:** Player names and observed starting line-ups remain visible while stable IDs are retained internally. Kill, headshot, evidenced wallbang/through-smoke/blind qualifiers, entry and bounded multi-kill combinations may anchor V1 scenes. Trade and information-review combinations remain disabled unless their required timing/sight/sound/context evidence is complete. Review output retains exact ticks and local CS2 seek commands; OBS/video/ML/anti-cheat classification stays deferred.
- **Date:** 2026-08-21

## Decision format

When a new decision is added, record:

- **Decision**
- **Reason**
- **Impact**
- **Date**

This keeps the project consistent and prevents old questions from being debated from scratch every few weeks.
