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

Trust is action-bound, not carried forward from the open dialog. Immediately before a selection rerender and before creating the CS2 coordinator, the controller repeats the complete workflow/artifact/chunk validation. A changed artifact prevents the downstream operation from being called. CS2 validation runs off the UI thread, clears every prior readiness indicator before it starts and remains disabled on any integrity error. There is no watcher, directory poller or separate cached trust state.

Reset clears Player Select. It does not silently turn an empty selection into Full Demo; the user must choose Full Demo explicitly. Already selected players are removed from the dropdown and cannot be added twice.

## Evidence

- 113/113 complete tests pass.
- Locked dependency check and eight public CLI help smokes pass.
- The visible Windows shell showed the required controls and closed cleanly.
- The existing real Ancient replay-v2 store was reused for player `steam:76561198063336407`; no Awpy reparse occurred and 22 real selected scenes were generated. Full Demo was then restored from the same store.
- No fake result, suspect verdict, Optimizer/System Check concern, video/OBS feature or alternate replay truth was added.

## Deferred

Final branding and installer packaging remain separate product work. The next small shell usability slice may explicitly disable workflow-dependent controls until a workflow is loaded and display the currently trusted workflow/source identity; it must not change parsing, review or trust semantics.
# Reproduzierbarer Produktreview

Ein ausdrücklich gewählter vorhandener Workflow kann ohne erneutes Parsen direkt beim Start geöffnet werden:

```powershell
iy-analyzer-shell --workflow <pfad-zur-demo-workflow.json>
```

Der Parameter verwendet dieselbe fail-closed Prüfung wie `Vorhandene Analyse öffnen`: exakt eine benannte Datei, kein Ordnerscan, kein Recent-Autoselect und keine Umgehung der Schema-, Hash-, Artefakt- oder Replay-Chunk-Validierung. Der native Dateidialog bleibt der normale interaktive Einstieg.
