# Tactical Integration Skeleton V1

```text
Analyzer Data Hub -> Module Controller -> Tactical Module Adapter
                  -> Tactical Module Skeleton -> MapRegistry -> resources/maps
```

`register_tactical_module()` registers only `tactical`, version 1, with the
generic `iy.module_adapter/v1` contract and the exact required projection
`iy.tactical_projection/v1`. The controller receives the projection through
`AnalyzerDataHubProjectionProvider`; Tactical never calls the Core, parser or
Awpy directly.

`TacticalContextV1` contains only source identity/map id, player identity,
round descriptors and the existing hash-bound `iy.replay/v2` reference. It
does not copy tick/player-position state from the canonical replay. A future
replay consumer may provide an explicit `TacticalPositionSampleV1`; the current
map-transform boundary preserves that CS2-world position and returns
`UNAVAILABLE` until a verified static transform exists.

`resources/maps/de_ancient/map.json` is a static MapRegistry proof of concept.
It deliberately declares its transform `UNVERIFIED`: no radar/render transform
numbers are invented or hardcoded in a Tactical renderer. Dynamic match data
remains owned by Analyzer Data Hub; static map metadata remains owned by
MapRegistry/resources.
