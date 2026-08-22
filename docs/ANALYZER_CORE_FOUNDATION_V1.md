# Improve Analyzer Core Foundation V1

**Status:** Implemented, versioned foundation.  This contract owns the path
from a locally selected CS2 demo to validated, consumer-neutral match data.
It does not change the existing objective analysis, scene, Tactical or review
semantics.

## One canonical path

```text
CS2 demo -> Analyzer -> AnalysisRequestV1 -> AnalyzerCore -> AwpyAdapter
-> raw Awpy parser result -> ImproveMatchNormalizer -> ImproveMatchDataV1
-> AnalyzerDataHub
```

`AnalyzerCore` is the only Improve layer that creates an `AwpyAdapter` for an
`AnalysisRequestV1`.  The adapter is the only module importing Awpy.  Raw Awpy
objects remain opaque Core internals and are not a UI, Tactical, Review, report
or consumer data contract.

## Versioned contracts

| Contract | Schema | Required role |
| --- | --- | --- |
| Request | `iy.analysis_request/v1` | `request_id`, local `demo_path`, requested profile; default `METRICS_V1` |
| Metrics | `iy.metrics/v1` | actual inline facts, per-channel availability and explicit references to canonical large state data |
| Validation report | `iy.validation_report/v1` | processed players/rounds/events, warnings, unknown records, dropped duplicates and critical errors |
| Match data | `iy.improve_match_data/v1` | request, Metrics V1, validation result and a projection of the canonical `iy.replay/v2` dataset |

## Metrics V1 data surface — Clarification Pass

Metrics V1 is a **data-location and availability contract**, not a list of
possible Awpy columns. It uses the deliberately non-duplicating Variant B:

| Contract projection | Representation | Actual V1 surface |
| --- | --- | --- |
| `iy.metrics.match/v1` | inline | source hash/name, map ID and tick rate |
| `iy.metrics.rounds/v1` | inline | normalized round number, start tick and end tick |
| `iy.metrics.events/v1` | inline | normalized referencable kills and per-channel availability |
| `iy.replay/v2` | validated reference | player identity, round descriptors, ticks, time-in-round, player states, positions, view angles, weapons and utility context |

The `contract` object names the schema and representation of every group. The
`channel_availability` map says `available`, `unavailable`, `unknown` or,
until replay finalization, `via_replay_v2`; it is never a positive claim based
on a missing field. Match/map/teams/players/rounds, tick/time/state/position/
view angle, kills/deaths/assists/damage/shots/weapons/utility/grenades/smokes/
infernos/bomb/footsteps and economy have only these declared locations. A
future datum requires an explicit contract expansion or V2; a consumer must
not search raw parser structures.

## Validation and normalization gate

The normalizer checks readable header data, usable round identifiers,
non-contradictory round tick ranges, positive tick rate when supplied, source
binding and duplicate event identity. Warm-up or otherwise unassigned events
are counted as `unknown_records` and dropped without interpretation. Missing
gameplay channels, including a match with no referencable kills, are **not** a
Core failure: they are capabilities such as `kills: unavailable`. A request
fails closed only for structural/integrity errors, for example unreadable parse
data, no usable round/time structure, inconsistent source/replay binding or a
normalization failure. The existing replay builder continues to validate every
replay chunk and source hash.

The workflow persists both `improve-match-data-v1.json` and
`validation-report-v1.json`.  Reuse and existing-workflow opening require both
artifacts, their source hash and a PASS validation report.  Older/incomplete
artifacts therefore fall back to the normal local import rather than becoming
a best-effort cache hit.

## Data Hub boundary

`AnalyzerDataHub` accepts only PASS `ImproveMatchDataV1`. It does not parse a
demo and it cannot expose an Awpy object. The stable minimal consumer contract
now has versioned projections:

| Consumer | Schema | Minimal data |
| --- | --- | --- |
| Analyzer | `iy.analyzer_projection/v1` | overview plus factual event availability |
| Tactical | `iy.tactical_projection/v1` | player identity, round context and explicit replay-v2 state reference |
| Review | `iy.review_projection/v1` | source/match/rounds/events and replay reference |
| Report | `iy.report_projection/v1` | counts, channel availability and validation facts |

Legacy technical names `overview`, `analysis` and `replay` remain read-only
compatibility projections. Each Hub call returns a mutation-isolated deep copy,
so one consumer cannot alter Analyzer truth or another consumer's view.
Tactical and Review continue to use the existing canonical `iy.replay/v2`
path; this is a named projection/reference from Match Data, not a second parser
or replay truth.

## Explicitly out of scope

No Tactical/2D/3D/POV implementation, new scene criteria, evaluation,
recommendation, report feature, Optimizer change, Benchmark work or network
authority belongs to this foundation.  New metrics require an explicit Metrics
V1 expansion or a new version; consumers may not improvise parser fields.
