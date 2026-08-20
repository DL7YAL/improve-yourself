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
- `dev/Run-DemoRegression.ps1` — local real-demo analysis plus portable
  `iy.analysis/v1` contract validation and a non-sensitive aggregate summary
- `dev/Run-ReplayV2Regression.ps1` — build the chunked canonical full-match
  `iy.replay/v2` store from one explicit local demo/analysis pair, validate every
  round hash and invariant, and write a non-sensitive aggregate summary
- `dev/Run-V1Pipeline.ps1` — one-command locked setup, tests, CLI smoke check,
  real-demo regression, and local aggregate PASS/FAIL evidence
- `dev/Start-V1Review.ps1` — supported local product entry point: locked Python
  setup, integrated workflow, explicit review URL and loopback-only review
  service; it never applies system or Optimizer changes
