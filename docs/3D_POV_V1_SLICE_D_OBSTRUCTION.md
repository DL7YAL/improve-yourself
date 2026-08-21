# 3D/POV V1 — verified camera obstruction follow-on

Date: 2026-08-21

## Result

The fixed Third-Person Analysis Camera now consumes a verified visibility-geometry boundary. The boundary returns only `clear`, `blocked` or `unknown`, plus the last verified intersection fraction when blocked.

For `blocked`, the camera moves from its fixed base position only along the original camera-to-eye-anchor segment. It lands after the last intersecting surface plus a fixed 8 Source Unit safety margin and reports `camera_adjusted=true`. It never changes the target, chooses another angle, or falls back to freecam. For `clear` or `unknown`, the fixed pose is preserved and `camera_adjusted=false`; unknown evidence is not treated as clear.

`TriVisibilityMesh` reads the previously verified, hash-gated local-only `.tri` derivative as a read-only NumPy memory map. Segment/triangle intersections are evaluated in bounded chunks, so the 673,869-triangle Anubis file is not copied into tracked output or expanded into an unbounded temporary structure.

## Validation

- focused renderer/visibility tests: 12 passed;
- complete repository suite: 75 passed;
- local verified Anubis visible control pair: `clear`;
- local verified Anubis blocked control pair: `blocked`, last intersection fraction `0.9189757397145473`;
- real native renderer check at canonical tick `4659`: `obstruction_state=clear`, `camera_adjusted=false`, resize and dispose PASS;
- local GLB, `.tri`, replay and screenshots remain ignored and unmodified.

Synthetic tests additionally prove multiple-wall handling uses the last rather than first intersection, clear and unknown preserve the base pose, blocked adjustment remains collinear, and invalid/zero-length evidence remains unknown or fails closed.

## Boundary

This change does not add sightline overlays, smoke-volume interpretation, player models, utility/event rendering, interpolation, packaging, a free camera, or another replay-state interpreter.

## NEXT

Implement only the canonical `SightlineResult` evaluator over `ReplayFrame` plus the same verified `VisibilityGeometry`: observed eye-to-eye/center segment, exact tick/player identity, and `visible / occluded / unknown` evidence rules. Keep smoke `unknown` unless canonical utility evidence can prove the selected V1 approximation; do not draw the overlay yet.
