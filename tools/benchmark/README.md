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
