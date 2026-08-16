# Codex

STATUS: blocked
TASK: Establish the technical 2D Analyzer / Viewer foundation
BRANCH: `dev/v1-foundation`
CHANGED: Added `docs/2D_VIEWER_FOUNDATION.md` with the verified real-demo capability, current schema gap, proposed separate `iy.replay/v1` boundary, and explicit prerequisites. No parser, analysis schema, 3D, benchmark, smoke, geometry, or product UI source changed.
VERIFIED: The representative `de_mirage` demo exposes 872,450 in-play player/tick rows with world `X/Y/Z`, 2,320 positioned shots, 102 positioned kills, 64 smoke lifetimes, and 43 inferno lifetimes. Locally installed Awpy supports requested `pitch` and `yaw`, although the current adapter does not request or persist them. Neither the repository nor bundled Awpy data contains a radar image or map transform for reproducible Mirage rendering. The current `iy.analysis/v1` payload has no positional/view/utility telemetry and cannot support tactical reconstruction by itself.
DECISIONS: Real demos and detailed results remain local and uncommitted. Regression evidence records source SHA-256 and aggregate map/tickrate/count/channel/quality facts, not player names or kill details. Missing `footsteps`/`player_sound` is a disclosed source-capability limitation, not a damaged-demo verdict. Do not commit a real binary fixture unless it is deliberately generated or licensed, non-sensitive, small, and provenance-documented.
OPEN: A visual 2D implementation needs a legally usable versioned radar asset plus world-to-radar transform, an approved first scene-selection rule, and an explicit sampling budget/temporal resolution. Choosing these silently would create product and evidence-policy decisions and could produce an unnecessarily huge artifact.
NEXT: Coordination/Tristan approve the three prerequisites in `docs/2D_VIEWER_FOUNDATION.md`; then Codex can implement and validate `iy.replay/v1` against the real demo without changing `iy.analysis/v1`.
COMMIT/PR: Validated V1 pipeline `5d33d6e`; 2D foundation evidence is the next documentation commit on `dev/v1-foundation`.
