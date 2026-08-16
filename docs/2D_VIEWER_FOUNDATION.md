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

## Implemented boundary

`iy.replay/v1` remains separate from `iy.analysis/v1` and contains selected
scene windows in world coordinates:

- source hash, map and explicit sampling metadata;
- round and scene tick bounds;
- sampled players with stable local identity, side, `X/Y/Z`, pitch and yaw;
- shots, kills, smoke lifetimes and inferno lifetimes within the scene;
- data-quality and missing-capability fields.

World coordinates should be preserved in the artifact. A renderer-specific map
transform belongs to the map asset/metadata layer, not to parsed match data.

## V1 selection and sampling

- one scene per existing Multi-Kill marker;
- exact window from the marker's first through last kill tick;
- uniform selection from unique ticks, capped at 256 tick frames per scene;
- the final tick is always retained;
- all rules are embedded as artifact metadata rather than hidden defaults.
- incomplete player snapshots with null position or view values are omitted and
  counted in `data_quality.omitted_incomplete_player_snapshots`; they are never
  rendered at an invented zero position.

Export from an existing matching analysis:

```powershell
.venv\Scripts\python -m improve_yourself.replay '<demo>' '<analysis.json>'
```

## Local map resources

Awpy's official resource downloader provides local map data with `awpy get
maps`. Patch `17595823` supplied `de_mirage.png` and the transform `pos_x=-3230`,
`pos_y=1713`, `scale=5`, `rotate=0`. The downloaded radar remains outside this
repository; it is a rendering dependency, not parsed match data.

The first reproducible renderer still needs to consume this local resource and
visually verify the world-to-radar projection. That visual check is separate
from the replay data-contract tests.
