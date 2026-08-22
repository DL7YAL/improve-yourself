# Module Integration Foundation V1

```text
Analyzer Data Hub
        ↓
Module Controller
        ↓
Module Adapter
        ↓
Module
```

This is a small local integration boundary, not a plugin system.  A module is
registered explicitly with `ModuleDefinitionV1` and a `ModuleAdapterV1`.
Definitions declare the stable module id/version, adapter contract, one required
projection, and `enabled`/`optional` state.

- The **Data Hub** owns only explicit, versioned projections. It never parses a
  demo on demand, exposes raw awpy data, or lets a consumer mutate stored data.
- The **Controller** manages registration, enabled state, dependency checks and
  `READY`, `UNAVAILABLE`, `DISABLED`, or `ERROR` resolution. Optional adapter
  failures are isolated from other modules.
- The **Adapter** validates its declared projection contract and constructs a
  narrow, copied module context. It has no parser, analyzer, UI or global
  product-control responsibility.
- The **Module** contains future domain behaviour, but only receives its
  adapter-provided context.

The recognised analyzer-facing projection identifiers are
`iy.analyzer_projection/v1`, `iy.tactical_projection/v1`,
`iy.review_projection/v1`, and `iy.report_projection/v1`. A missing or
incompatible projection resolves to `UNAVAILABLE`; there is deliberately no raw
parser fallback or best-effort reparse.

`My Improvement` remains a future independent consumer/module. It may later
combine explicit results from Analyzer, Tactical, Review, Reports and history;
it is not owned by Tactical.
