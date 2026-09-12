# Benchmark source synchronization

`Sync-BenchmarkAddon.ps1` compares the repository's validated benchmark sources
with an installed CS2 Workshop Tools addon. Its default mode is read-only.

## Verify

```powershell
.\tools\benchmark\Sync-BenchmarkAddon.ps1
```

The default target is resolved from Steam's current-user registry entry. An
explicit target can be supplied when CS2 is installed in another library:

```powershell
.\tools\benchmark\Sync-BenchmarkAddon.ps1 -AddonRoot 'E:\...\content\csgo_addons\improve_yourself_benchmark'
```

Verification exits `0` when both installed sources match the versioned
manifest and `2` when either source is missing or different.

## Deploy

```powershell
.\tools\benchmark\Sync-BenchmarkAddon.ps1 -Deploy
```

Deployment is one-way: repository to installed addon. The script refuses an
unexpected addon name, a reparse-point addon root, a target outside
`content/csgo_addons`, unsafe manifest paths, unexpected manifest cardinality,
or repository sources whose hashes do not match the manifest.

Only missing or different manifest files are changed. Each existing different
target is copied first to
`backups/deploy-<yyyyMMdd-HHmmss>/<relative-path>` inside the addon and the
backup hash is checked before overwrite. Every deployed file is checked again
against the manifest. If the addon already matches, `-Deploy` is a no-op.

## Validate a Windows CS2 runtime log

After an uninterrupted normal-viewer run on the Windows benchmark machine,
validate the CS2-generated log from a Windows terminal at the repository root:

```powershell
py -3.13 .\tools\benchmark\validate_benchmark_runtime.py `
  'E:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\iy_benchmark_console.log' `
  --json
```

The validator is read-only, uses only the Python standard library and checks
the latest `READY` segment. It ignores quoted duplicate console echoes, but it
fails on a partial/restarted latest run, duplicate or reordered contract
events, missing captures/reports, and every `[IYBENCH] ERROR`. A runtime `PASS`
continues to report `measurement_status=unverified`; it does not manufacture a
performance result. Preserve the emitted input SHA-256 and the JSON result in
the handoff, but keep the raw local log outside Git.

The controller also writes a compact save record only after measured-pass
completion. Validate that independent Windows artifact with:

```powershell
py -3.13 .\tools\benchmark\validate_benchmark_save.py `
  '<ADDON_ROOT>\cfg\workshop_saves\save_local.txt' `
  --json
```

This can prove measured runtime completion even when VConsole text was copied
too early. It cannot replace the full console-order or visual checks.

After the five required captures exist, create a path-safe evidence manifest:

```powershell
py -3.13 .\tools\benchmark\collect_benchmark_evidence.py `
  --log '<LOG_PATH>' `
  --intro '<CAPTURE_DIR>\intro.png' `
  --ancient-water '<CAPTURE_DIR>\ancient-water-27.png' `
  --ancient-red-room '<CAPTURE_DIR>\ancient-red-room-38.png' `
  --inferno-stairs '<CAPTURE_DIR>\inferno-stairs-48.png' `
  --inferno-apps '<CAPTURE_DIR>\inferno-apps-53.png' `
  --output '<EVIDENCE_DIR>\benchmark-world-evidence.json'
```

The collector first requires a runtime `PASS`, then verifies all five files
are present, non-empty, supported image types and have distinct hashes. Its
manifest stores only filenames, hashes, sizes and UTC timestamps—never local
absolute input paths. Every visual result remains `UNREVIEWED` until the images
are actually inspected; file hashes alone cannot create a `WORLD PASS`.
