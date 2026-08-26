# Product roadmap alignment

## Purpose and status

This document is the current documentation-level alignment of the local
product core. It describes what the checked-in local implementation does
today, what remains a future roadmap item, and how historical contracts are
to be read. It does not authorize a product, system, cloud, or architecture
change.

## Current implemented local architecture

```text
explicit local demo
  -> Awpy adapter
  -> AnalyzerCore
  -> AnalyzerDataHub
       -> iy.replay/v2 -> ReplayStore -> ReplayController
            -> Tactical Replay / Viewer / Review presentation

explicit local System Check
  -> iy.system_check/v1
  -> Optimizer Evidence / Optimizer Foundation
  -> iy.optimizer_input/v1 (thin, read-only export view)
```

- `AnalyzerCore` is the canonical producer of validated match data.
- `AnalyzerDataHub` is the single canonical distributor of consumer
  projections. It does not parse demos and is not a second parser path.
- `iy.replay/v2` is the active replay truth. `ReplayStore` is the validated,
  hash-checking artifact reader and `ReplayController` is the sole mutable
  playback authority for replay consumers.
- System Check is a separate, explicit, local evidence source. Unknown or
  unreadable evidence remains unknown; it is not inferred from demo or replay
  data.

The repository also retains `iy-workflow` / `iy.replay/v1` as a separate,
supported legacy-compatible local workflow. It is not the canonical V2 path;
it must not be silently routed into V2 consumers or treated as a fallback for
`ReplayStore` or `ReplayController`.

## Optimizer authority: current versus future

### Implemented now

The current Optimizer-related local path is evidence-only and read-only.
`iy-optimizer-input` accepts an explicit `iy.system_check/v1` artifact only
when its policy says `read_only: true` and `changes_applied: false`. It exports
planning evidence and cannot accept or copy demo/replay data.

There is no current Apply, Restore, Registry, BIOS/UEFI, driver, Windows,
network-adapter, MTU, or automatic configuration authority in the local
product core. A recommendation view is not permission to make a change.

### Future roadmap only

Curated configuration, reversible changes, backups, restore workflows,
before/after measurement, and any optimizer action authority remain future
product work. They require a separately approved design, explicit evidence
requirements, user-visible confirmation, and validation; this roadmap does not
claim that any such capability exists today.

## V1 and V2 contract status

`iy.analysis/v1`, `iy.system_check/v1`, `iy.optimizer_input/v1`, and other V1
schemas identify their respective stable artifact contracts. The schema suffix
does not make every older replay path an active architecture.

The canonical integrated replay path is `iy.replay/v2`, produced by the
Demo-Workflow path. `iy.replay/v1` remains an explicitly separate legacy-
compatible workflow contract; other V1 replay references are historical or
compatibility context unless a document explicitly identifies that workflow.
Neither case may be wired into an active V2 consumer as a fallback or second
replay store/controller.

## Azure boundary

Azure infrastructure and its optional SDK dependencies are not required by the
local Analyzer, AnalyzerDataHub, Replay V2, Tactical Replay, System Check, or
Optimizer Evidence paths. Local/offline operation must remain available when
Azure is unavailable.

Azure code and deployment decisions are separate infrastructure work. A future
cloud integration must use an explicit interface and must not silently become a
required dependency of the local core. This document neither specifies nor
authorizes Azure resources, deployment, region selection, credentials, or
data transfer.

## Documentation reading rule

Where a historical plan, prototype note, or UI reference conflicts with this
document and the checked-in local contracts, the current implementation and
the canonical architecture above take precedence. Historical documents remain
valuable as provenance, but are not capability claims or implementation
authorization.
