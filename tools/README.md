# Tools

Developer and maintenance utilities belong here.

Examples:
- prototype migration helpers
- diagnostics
- data conversion
- build / packaging helpers

Utilities should stay separate from the runtime application unless they are required by the product itself.

Current utilities:
- `benchmark/Sync-BenchmarkAddon.ps1` — read-only verification and explicit,
  backed-up one-way deployment of the versioned CS2 benchmark sources
- `dev/Setup-V1.ps1` — idempotent Python 3.13 bootstrap from the dependency
  lockfile, followed by dependency, test, and CLI baseline checks
