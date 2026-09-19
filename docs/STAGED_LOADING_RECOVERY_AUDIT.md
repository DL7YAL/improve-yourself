# Staged loading recovery audit — 2026-09-20

Status: FOUND LOCALLY; NOT YET INTEGRATED. Shared baseline: `eeda402`.
Benchmark-map development remains frozen. This concerns demo loading only.

## Preserved local sources

Read-only inspection of the existing Windows NEW_Try workspace found:

- `validation-scratch/codex-demo-readiness-contract-v1`, branch
  `codex/demo-readiness-contract-v1`, commit
  `26d5f689fe887d0a023a1fb2df263acab7b664ec` (2026-09-04).
  Worktree clean during inspection. Parent `d238dcc` integrates progress and
  local minimap surfaces; that parent's base is `7b9764c`.
- `validation-scratch/codex-replay-zstd-codec-v1`, branch
  `codex/replay-zstd-codec-v1`, commit `1db7e39`, based on `26d5f68`.
  Worktree clean during inspection. This is a separate codec experiment.
- `validation-scratch/demo-readiness-benchmark-20260904/BENCHMARK_REPORT.md`,
  aggregate JSON, three run summaries and replay validation records.
- `validation-scratch/replay-zstd-codec-v1-benchmark-20260904/` contains the
  codec experiment's measurements, including `final-run-1-benchmark.json`.

These existing source worktrees were not edited, switched, cleaned or deleted.
No new product checkout was created. One older Linux project directory could
not be read due to permissions; the useful Windows sources above were readable.

## Measured historical reference

The report identifies commit `26d5f68`, AWPy 2.0.2, Python 3.13.15, Windows 11,
and the real Ancient demo `furia-vs-vitality-m2-ancient.dem`:
511,363,016 bytes, 23 rounds, 10 players, source SHA-256
`a423d8fa9bcd7724118cccdde81bc99dac9b0de37ec3692822bc4427d638a2ae`.

| Milestone | Run 1 | Run 2 | Run 3 | Mean |
| --- | ---: | ---: | ---: | ---: |
| Analyzer/player selection ready | 3.981 s | 3.984 s | 3.959 s | 3.975 s |
| First validated replay round ready | 5.831 s | 5.832 s | 5.811 s | 5.825 s |
| Full replay ready | 57.950 s | 57.899 s | 57.901 s | 57.917 s |

Each run used a fresh output folder, but Windows filesystem caches were not
cleared. All 23 rounds were subsequently loaded with strict validation;
159,099 frames and 1,590,980 player states were reported in every run.
These are recovered historical measurements, not new measurements this turn.
The user's recollection of a roughly 30-second intermediate step is not yet
matched to a distinct usability milestone. The report does list about 29.887
seconds spent writing GZIP, but that is a duration, not evidence of that stage.

## What BRIX1 is missing

The recovered contract exposes ANALYSIS_READY / READY_FOR_SELECTION before
replay completion, explicitly marks replay-backed fields PENDING, and emits
REPLAY_ROUND_READY only after a durable validated hash-bound round is written.
An explicit allow_incomplete consumer can read only such ready rounds. Normal
strict consumers remain blocked until FULL_REPLAY_READY. Review/scenes require
the subsequent READY_FOR_REVIEW analysis; an early round is not full UI readiness.

BRIX1 still writes GZIP level 6 and lacks the recovered progress callback and
partial-round consumer contract. The measured source uses level 1 and avoids
immediately rereading/decompressing all newly written rounds by carrying
validated summaries forward. This is an integration gap, not a reason to
remove validation. The local Zstandard follow-up measured 55.098 seconds in
its final run and did not meet its own 52-second target; do not silently adopt
it as a proven replacement.

The recent slow Anubis test reopened an existing workflow and revalidated its
rounds. The historical Ancient timings measure fresh demo import/build.
Different inputs and operations must not be presented as a measured regression.

## GitHub check and integration boundary

Exact live `git ls-remote origin` checks returned no branch refs for
codex/demo-readiness-contract-v1, codex/replay-zstd-codec-v1,
codex/demo-progress-minimap-integration-v1 or codex/packaged-responsive-startup.
Commit `26d5f68` is absent from BRIX1's current object database. The public
GitHub commit endpoint returned HTTP 422 for its full SHA. This does not prove
that the work was never uploaded or exists in no other remote/PR; it does mean
the current shared checkout is not carrying this implementation.

Next integration must be selective: `26d5f68` alone changes 16 files, and its
parent includes another minimap implementation and packaging changes. Do not
blindly cherry-pick or overwrite analyzer_shell/replay_store/replay_validation.
Preserve the current round-integrity checks, direct Tactical navigation repair,
current local map loader and source-bound workflow validation. Back up the
recovered source before integration. Bring across the staged readiness contract
and its tests first; reconcile UI callbacks with the shared shell. Defer codec,
packaging and unrelated UI changes. Re-measure the same Ancient demo milestones
and separately time existing-workflow reopening before declaring equivalence.

Only this audit is added by the recovery investigation; no product behavior or
local source branch has been changed in this slice.
