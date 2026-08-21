# Improve Yourself – Experimental

Date: 2026-08-21
Branch: `dev/v1-foundation`

## Product boundary

Experimental is the first connected tester-facing V1 state. It reuses the existing Awpy adapter, canonical `iy.replay/v2` store, neutral rule engine, merged scenes, review coordinator and Tactical Replay. It is not a new parser or parallel product.

```text
Start program
  -> select real .dem/.dem.zst
  -> objective demo preflight only
  -> see map, rounds, parser PASS, basic events and named CT/T line-ups
  -> Full Demo or Player Select
  -> Review / Highlight / Coaching / Custom local profile
  -> indicators -> named rules -> profile -> merged scenes
  -> Review
  -> Tactical Replay / neutral JSON report / exact CS2 tick
```

No scene exists during `READY_FOR_SELECTION`. The rule engine runs only after the explicit `Analyse starten` action. Generated outputs remain local and ignored by Git.

## Demo preflight

The preflight performs real parse/replay export but no rule matching or scene emission. It discloses map ID, evidenced round count, parser name/version and PASS, named players and observed starting CT/T line-ups, normalized basic event count, source basename and abbreviated SHA-256. It does not score, rank or interpret a player.

## Profiles and rules

Built-in purposes are `review`, `highlight`, `coaching` and `custom`. Review enables every objective V1 anchor. Highlight and Coaching are deliberately small rule subsets, not different parser interpretations. Custom toggles persist as `iy.analysis_profile/v1` JSON below the path shown in the UI (`<output>/profiles`). There is no account, cloud sync or hidden profile directory.

Supported anchors remain kill, multi-kill, headshot, wallbang, smoke-kill, blind-kill and entry. The engine retains all evidenced indicators, then applies the profile's named-rule allowlist. Weak incomplete information conditions cannot emit standard scenes. Overlapping rule matches merge into one situation.

## Outputs and interpretation boundary

Each completed analysis writes `analysis-flow.json`, `timeline.json`, neutral `review.html`, self-contained `tactical-replay.html`, neutral `report.json` and `cs2-review-commands.txt`. Review states that the scene matches selected criteria and interpretation remains with the user. Current states are Unreviewed, Reviewed, Discarded and Follow-up/Näher ansehen. Legacy `clip-worthy` remains read-compatible only so existing local state is not destroyed; it is no longer presented.

## Visual/UI acceptance

The shell uses one dark Midnight/Metallic surface, native dark title bar, `Improve Yourself` and the fixed claim `Make Up Your Mind.`. Workflow-dependent controls are disabled until a real workflow is loaded. The UI shows local manifest/source/hash identity and the disclosed local profile path. No new logo or branding source is introduced.

## Real evidence

The unchanged real Ancient source truth remains SHA-256 `c183dd61fc6a619f7af435d45eab374cd6f0097a7bd0da779971b15ef6746f7f`: Awpy 2.0.2, Ancient, 18 rounds, 10 named players and 235 objective markers/rule matches merged into 54 scenes. The current Experimental downstream rerun restored the same 54 scenes, produced Timeline, Review, a 28,335,824-byte Tactical Replay and `iy.analysis_report/v1`, and retained first scene `r1-t3654-0` / `demo_gototick 3654`. That tick was already visibly accepted in installed CS2 for the same source truth. The original `.dem` is no longer present at the known direct paths, so this consolidation does not claim a new Awpy parse; it preserves and revalidates the existing real parse/replay evidence.

## Explicit exclusions

No OBS, clip creation, video editor, automated rendering, forced window mode/resolution, ML/anti-cheat verdict, complete standard-angle system, 3D POV work, benchmark extension or Optimizer feature is part of Experimental consolidation. CS2 keeps the user's existing display settings.

## Acceptance status

The engineering gate is complete. Further feature development stops here. Status is `WAITING_FOR_TRISTAN` for the first complete product review.
