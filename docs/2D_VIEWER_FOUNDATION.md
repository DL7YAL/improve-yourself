# 2D Viewer technical foundation

## Verified source capability

The representative real `de_mirage` demo exposes the following Awpy data:

- 872,450 in-play player/tick rows with tick, round, player, side, place and
  world-space `X/Y/Z`;
- 2,320 shot events with shooter position;
- 102 kill events with attacker and victim positions;
- 64 smoke lifetimes and 43 inferno lifetimes with world positions;
- `pitch` and `yaw` are supported Awpy player properties, but the current
  `AwpyAdapter` intentionally requests only the existing analysis fields.

The current `iy.analysis/v1` result contains kill and Multi-Kill timing but no
position, movement, view direction, shot position or utility geometry. It is
therefore sufficient for an event list, not for a tactical 2D reconstruction.

## Proposed boundary

A future `iy.replay/v1` artifact should remain separate from
`iy.analysis/v1`. It should contain selected scene windows in world coordinates:

- source hash, map and explicit sampling metadata;
- round and scene tick bounds;
- sampled players with stable local identity, side, `X/Y/Z`, pitch and yaw;
- shots, kills, smoke lifetimes and inferno lifetimes within the scene;
- data-quality and missing-capability fields.

World coordinates should be preserved in the artifact. A renderer-specific map
transform belongs to the map asset/metadata layer, not to parsed match data.

## Blocking prerequisites

No versioned radar image or map transform for `de_mirage` exists in the
repository or bundled Awpy data. A visual viewer therefore cannot yet be
rendered and validated reproducibly.

Before implementation is locked, coordination must provide or approve:

1. a legally usable, versioned radar asset and its world-to-radar transform;
2. the first scene-selection rule (for example whole round versus bounded
   context around a marker);
3. the sampling budget or target temporal resolution, so 872,450 raw player
   rows are not copied blindly into every output.

These are explicit inputs rather than silent defaults. Until they are resolved,
the existing Analyzer schema and parser behavior should remain unchanged.
