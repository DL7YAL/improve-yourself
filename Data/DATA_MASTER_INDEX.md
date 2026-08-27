# DATA MASTER INDEX

Status legend: `MASTER`, `REVIEW`, `UPDATE REQUIRED`, `LOCAL NEWER`, `UNRESOLVED`, `ARCHIVED`.

## UI
Status: PARTIAL
Authority: `Data/UI/UI_MASTER_INDEX.md`
Confirmed current material: Optimizer MASTER package already versioned under `Data/UI/Optimizer/`.
Local/newer material: to be consolidated without replacing confirmed masters blindly.

## Analyzer
Status: UNRESOLVED
Authority: `Data/Analyzer/`
Current code remains under `app/`; only maintained reference data belongs here.

## Tactical
Status: LOCAL NEWER / PARTIAL
Authority: `Data/Tactical/Tactical_MASTER_INDEX.md`
2D and 3D POV are subareas of one Tactical module.
Existing runtime/code paths remain unchanged during soft reset.

## Optimizer
Status: MASTER / PARTIAL
Confirmed UI masters already exist under `Data/UI/Optimizer/`.
Golden-master and reference datasets are to be consolidated under `Data/Optimizer/` when verified.

## Benchmark
Status: PARTIAL
Versioned benchmark implementation/assets currently remain under existing project paths; Data stores maintained blueprints, branding references, specs and review material as they are consolidated.

## Demos
Status: TO CONSOLIDATE
Neutral shared pool: `Data/Demos/`
No module-specific duplicate demo pools.

## Test Data
Status: TO CONSOLIDATE
Central location for verified fixtures, golden-master cases, expected results, and system/reference datasets.

## Shared
Status: PARTIAL
Only genuinely cross-module manifests, specifications, branding and references belong here.

## Soft-reset rule
Current production/runtime paths are not moved or deleted. Data is built in parallel and becomes the maintained authority for new/updated reference assets. Runtime migrations happen only deliberately and with tests.
