# Analyzer Review <-> Tactical Replay V1

## Product contract

The embedded Analyzer Review and Tactical Replay are two presentations of one
validated local workflow. They do not parse, analyze, or create scenes again.

`demo-workflow.json -> analysis-flow -> iy.replay/v2 -> existing tactical projection`

- `EmbeddedReviewSession` owns review-state persistence and delegates CS2 opens
  to the existing fail-closed coordinator.
- `EmbeddedTacticalSession` validates the workflow/source hash, supplies the
  existing ReplayStore and ReplayController to `build_tactical_2d_projection`,
  and indexes the resulting projection by the canonical analysis `scene_id`.
- `AnalyzerShellApp` keeps the currently visible scene synchronized when moving
  between Review and Tactical Replay. No second parser, rule engine, scene
  detector, NetCon endpoint, or review-state format exists.

## Preserved context

The transition carries the canonical scene ID and presents, where present in
the validated artifacts: demo/source hash, map, round, review tick, timecode,
players, focus player, analysis profile, selection mode, review state and note.
Changing scenes in Tactical Replay updates the selected Review scene. Returning
to Review selects and scrolls to that exact scene.

## UI and fallback boundary

The normal flow remains in the Midnight/Metallic desktop shell. Tactical Replay
uses a scene rail, dominant map/canvas, frame timeline, zoom/pan/reset and direct
CS2 action. The existing generated HTML viewer remains an explicit browser
export/fallback only.

The page structure follows the binding concept master without restoring its
illustrative data: compact persistent sidebar, module header/context band,
dominant map surface, nearby scene/timeline context and bottom action strip.

## Safety and failure behavior

- All workflow and artifact integrity checks remain fail-closed.
- CS2 opens still pass through `EmbeddedReviewSession.open_in_cs2` and the
  existing `Cs2ReviewCoordinator`; only an allowed scene/tick can reach
  `demo_gototick`.
- No listener is exposed beyond the existing loopback-only path.
- Missing frames render an explicit empty state; unknown timecode stays
  `Zeit nicht belegt` rather than being invented.
- Unknown scene IDs, mismatched source hashes and invalid schemas stop the
  transition and are surfaced in the embedded Review status.

## COMPLETE criteria

1. A validated real workflow opens in the desktop shell.
2. Review selects a canonical scene and Tactical Replay opens the same scene.
3. Scene, round, players, tick, profile and review state remain traceable.
4. Tactical scene stepping, zoom, pan and reset work without re-analysis.
5. Returning to Review preserves the exact currently selected scene.
6. The existing coordinator opens that scene tick in the active matching CS2 demo.
7. Browser output is not used in the normal path.
8. Full tests, compile, diff check and Portable packaging pass.
