# Improve Yourself Roadmap

## Reading this roadmap

This file contains product direction, including future ideas. It is not a
capability inventory. For the current implemented local architecture and the
status of historical contracts, read
[`PRODUCT_ROADMAP_ALIGNMENT.md`](PRODUCT_ROADMAP_ALIGNMENT.md) first.

In particular, the present local Optimizer path is read-only evidence and
planning input. Apply/Restore, backups, and automated system configuration are
future work, not current V1 behavior. The active replay truth is
`iy.replay/v2`; older V1 replay references are historical or compatibility
context unless explicitly identified otherwise.

## V1 — Foundation / working product

Goal: a stable, independent first version with real practical value.

### System Check
- Detect and check CPU, GPU, RAM and motherboard
- Check GPU/chipset drivers and Windows version
- Check monitor / refresh-rate basics
- Check TPM / Secure Boot / relevant anti-cheat readiness
- Clear result categories: OK / review / action required

### Optimizer
- **Current V1:** read-only System Check evidence and an explicit read-only
  Optimizer-input export; no Apply/Restore or configuration authority.
- **Future:** curated performance-oriented configuration, only where evidence,
  safety design, explicit approval, and reversible operation have been proven.
- Future action-capability prerequisites include backup/restore design and
  validation, and must not be inferred from current evidence views.

### Demo Analyzer
- Read CS2 demos automatically
- Identify match and player data
- Find relevant or suspicious scenes
- Evaluate line of sight, sound, voice/calls, prior information, game flow, opponent perspective, aim/mouse movement and timing

### Tactical Replay
- Reconstruct relevant scenes visually
- Player positions and movement
- View direction
- Shots and utility
- Relevant sound events
- Timeline of the scene

### Analysis audio
- One fixed analysis mix
- Clear, attack-focused, low-bass footsteps
- Direction, distance, geometry and audibility considered
- Distinguishable abstract weapon categories
- Distinct cues for utility types
- No dependency on original Valve sounds

### UI
- Reduced, clear interface
- Few deliberate user decisions
- No feature bloat
- Prioritized information instead of raw data overload

**V1 rule:** reliability first, expansion second.

## V2 — Intelligence & analytical depth

Goal: not only detect what happened, but explain why it matters.

- Stronger scene context
- Combine multiple events
- Reconstruct the information available to the player
- Joint evaluation of sound, sight, calls and timing
- Better detection of unusual aim/mouse movement
- Automated opponent-perspective analysis
- Automatic scene prioritization
- Stronger Tactical Replay
- Connect system analysis and optimizer results through explicit, evidence-led
  interfaces
- Before/after measurements, if a separately approved measurement design is
  available
- Better reports and explanations

**V2 rule:** context is more important than a single statistic.

## V3 — Improve Yourself

Goal: evolve from an analysis tool into a personal improvement system.

- Long-term player profile
- Learn personal normal behavior
- Detect recurring mistakes, strengths and weaknesses
- Compare the player primarily with their own historical behavior
- Identify meaningful deviations
- Derive concrete training points from real matches
- Track improvement over time
- Combine System Check, Optimizer, Demo Analyzer, Tactical Replay and Player Profile into one system

**V3 rule:** learn how the player plays and use that knowledge to help them improve.

## Idea parking lot

Ideas that are valuable but not required for the current V1 belong here first. A good idea does not automatically become an immediate implementation task.
