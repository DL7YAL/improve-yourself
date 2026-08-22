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
| Metrics | `iy.metrics/v1` | declared metric groups, source hash, match facts, event availability and normalized referencable kills/rounds |
| Validation report | `iy.validation_report/v1` | processed players/rounds/events, warnings, unknown records, dropped duplicates and critical errors |
| Match data | `iy.improve_match_data/v1` | request, Metrics V1, validation result and a projection of the canonical `iy.replay/v2` dataset |

`METRICS_V1` declares the stable V1 groups: match/map/teams/players/rounds,
ticks/time/player state/positions/view angles, kills/deaths/assists/damage/shots/
weapons/utility/grenades/smokes/infernos/bomb/footsteps and economy.  A channel
is only available when parser data supplies it.  Missing, unsupported or
unreferencable information remains unavailable; it is never inferred.

## Validation and normalization gate

The normalizer checks readable header data, usable round identifiers, positive
tick rate when supplied, referencable kill ticks/rounds and duplicate events.
Warm-up or otherwise unassigned events are counted as `unknown_records` and
dropped without interpretation.  A request fails closed if it has no usable
rounds or no referencable kill events after that gate.  The existing replay
builder continues to validate every replay chunk and source hash.

The workflow persists both `improve-match-data-v1.json` and
`validation-report-v1.json`.  Reuse and existing-workflow opening require both
artifacts, their source hash and a PASS validation report.  Older/incomplete
artifacts therefore fall back to the normal local import rather than becoming
a best-effort cache hit.

## Data Hub boundary

`AnalyzerDataHub` accepts only PASS `ImproveMatchDataV1` and offers the three
read-only projections `overview`, `analysis` and `replay`.  It does not parse a
demo and it cannot expose an Awpy object.  The Analyzer controller loads this
Hub after the existing fail-closed workflow validation.  Tactical and Review
continue to use the established canonical `iy.replay/v2` path; this is a
projection from Match Data, not a second parser or replay truth.

## Explicitly out of scope

No Tactical/2D/3D/POV implementation, new scene criteria, evaluation,
recommendation, report feature, Optimizer change, Benchmark work or network
authority belongs to this foundation.  New metrics require an explicit Metrics
V1 expansion or a new version; consumers may not improvise parser fields.
