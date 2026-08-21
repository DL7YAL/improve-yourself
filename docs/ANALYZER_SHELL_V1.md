# Analyzer desktop shell V1

Date: 2026-08-21  
Branch: `dev/v1-foundation`

## Boundary

`iy-analyzer-shell` is a thin local desktop adapter. It does not parse demos, interpret replay state or evaluate rules itself. The first import calls the proven `run_demo_workflow`; every later player selection calls `rerender_demo_workflow`, which rebuilds output only from the already canonical replay-v2 store.

## User flow

```text
Select real .dem/.dem.zst
  -> background Demo Workflow import
  -> named CT/T starting line-ups
  -> Full Demo or Player Select
  -> dropdown + Add Player / CT / T / Reset
  -> rerender selection from the same ReplayStore
  -> open the existing self-contained review
```

An existing result has a second, explicit entry point:

```text
Select demo-workflow.json
  -> validate exact workflow schema/status/policy and lowercase source SHA-256
  -> contain every required relative artifact below the selected workflow root
  -> validate analysis, replay-v2, every hashed round chunk, flow and timeline against the same source hash
  -> restore roster, selection, scenes and review without Awpy
```

The shell never scans result folders, chooses a recent run, infers a missing source file or repairs an invalid manifest. Legacy workflows without `source_demo_name` may still restore their analysis, but CS2 readiness remains fail-closed because the exact active filename cannot be proven. The persisted hash is cross-checked across generated artifacts; because the source path is intentionally not persisted, reopening alone does not prove that the original `.dem` is still present.

For such a legacy workflow, `Quelldemo zuordnen` accepts one explicitly selected `.dem` or `.dem.zst`. It streams the file through SHA-256 and requires an exact match before atomically adding only the basename as `source_demo_name`. A mismatch leaves the manifest byte-for-byte unchanged. A successful link clears stale readiness and immediately repeats the local CS2 preflight; it never reparses, copies, renames or stores the private source path.

Reset clears Player Select. It does not silently turn an empty selection into Full Demo; the user must choose Full Demo explicitly. Already selected players are removed from the dropdown and cannot be added twice.

## Evidence

- 111/111 complete tests pass.
- Locked dependency check and eight public CLI help smokes pass.
- The visible Windows shell showed the required controls and closed cleanly.
- The existing real Ancient replay-v2 store was reused for player `steam:76561198063336407`; no Awpy reparse occurred and 22 real selected scenes were generated. Full Demo was then restored from the same store.
- No fake result, suspect verdict, Optimizer/System Check concern, video/OBS feature or alternate replay truth was added.

## Deferred

Final branding and installer packaging remain separate product work. Manifest integrity should next be revalidated at every later state-changing rerender/review action so a file altered after opening cannot cross the established trust boundary.
