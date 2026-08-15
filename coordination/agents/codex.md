# Codex

STATUS: done
TASK: Implement and validate the minimal V1 Demo Analyzer pipeline
BRANCH: `dev/v1-foundation`
CHANGED: Added `tools/dev/Run-V1Pipeline.ps1` as the minimal orchestration path from locked environment setup through tests, CLI smoke check, real-demo analysis, contract validation, and aggregate `iy.pipeline/v1` evidence. Added `docs/V1_PIPELINE.md` and linked the entry point from the tools overview. Locked only the Sandbox/test-pipeline work object; 2D, 3D, benchmark, smoke, and geometry sources remain untouched.
VERIFIED: Full pipeline PASS on the representative `de_mirage` source SHA-256 `732855381761ad41aaea58dbdb458e8c85cb6e4bccd112f534ad3674f81f00c3`: locked dependency setup, dependency consistency, 11/11 tests, CLI smoke test, 102-kill analysis, 6 Multi-Kill markers, and complete `iy.analysis/v1` validation. A controlled unsupported-extension run writes `iy.pipeline/v1` FAIL evidence with `failed_step: demo_regression`, preserves successful baseline checks, marks analysis/contract false, and still propagates the original failure. Evidence inspection confirms no demo path, player names, or detailed kill data. The new script passes PowerShell AST parsing.
DECISIONS: Real demos and detailed results remain local and uncommitted. Regression evidence records source SHA-256 and aggregate map/tickrate/count/channel/quality facts, not player names or kill details. Missing `footsteps`/`player_sound` is a disclosed source-capability limitation, not a damaged-demo verdict. Do not commit a real binary fixture unless it is deliberately generated or licensed, non-sensitive, small, and provenance-documented.
OPEN: No pipeline blocker remains. This validates the Analyzer workflow only and deliberately does not claim visual CS2/Hammer runtime coverage.
NEXT: Coordination can consume the DONE pipeline and assign the next concrete FREE implementation object; preserve the aggregate local-only evidence boundary.
COMMIT/PR: Real-demo regression evidence `63d0ace`; validated V1 pipeline is the next commit on `dev/v1-foundation`.
