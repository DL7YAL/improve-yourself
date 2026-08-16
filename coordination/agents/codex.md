# Codex

STATUS: partial
TASK: V1 consolidation: supported local launcher and startup validation
BRANCH: `dev/v1-foundation`
CHANGED: Added `tools/dev/Start-V1Review.ps1` as the supported Windows entry point. It validates demo/radar/numeric limits, prepares the locked Python 3.13 environment, runs `iy-workflow`, validates `iy.workflow/v1`, prints the exact review URL and starts `iy-review-server` visibly in the foreground. `-NoServe` supports deterministic artifact smoke tests; `-SkipSetup` is explicit. Setup now verifies every shipped CLI entry point. No browser is silently opened and no system/Optimizer change is performed.
VERIFIED: 28/28 tests pass. Locked setup and dependency consistency pass. Real Mirage `-NoServe` run returned a valid READY_FOR_REVIEW manifest and left no service. Normal launcher mode served `review.html` with HTTP 200 and `iy.review_state/v1` with seven scenes on `127.0.0.1:8877`, then stopped cleanly via Ctrl+C. Git diff check passes.
DECISIONS: Real demos and detailed results remain local and uncommitted. Regression evidence records source SHA-256 and aggregate map/tickrate/count/channel/quality facts, not player names or kill details. Missing `footsteps`/`player_sound` is a disclosed source-capability limitation, not a damaged-demo verdict. Do not commit a real binary fixture unless it is deliberately generated or licensed, non-sensitive, small, and provenance-documented.
OPEN: WAITING_FOR_TRISTAN: Open the generated local `results/replay/732855381761.viewer.html` in a browser and confirm that the six real Mirage scenes place players plausibly on the radar and that their direction lines align with expected sight directions. Windows Computer Use stopped at its browser URL-policy boundary, so Codex did not claim visual validation. Radar redistribution provenance remains unresolved; the binary stays local.
NEXT: Tristan performs the bounded real Mirage sight check when available. Independently, audit the branch against the documented V1-foundation exit condition and close only concrete gaps before preparing review toward `main`; Optimizer mutation/restore remains a separate, later safety boundary requiring explicit design and verification.
COMMIT/PR: Review persistence `e187175`; supported launcher is `659a5e6` on `dev/v1-foundation`.

## 2026-08-17 — Benchmark multi-map transition runtime check

STATUS: blocked
TASK: Implement and validate the locked Nuke -> Ancient -> Inferno transition sequence.
BRANCH: `dev/v1-foundation`
CHANGED: Controller V1.1 adds explicit transition metadata/markers, retains the controlled first Nuke smoke wall, removes the obsolete Ancient-end/Inferno-start smokes, adds the Red Room landmark marker and flash/white-fade handoff, and stages camera turns inside the occlusion windows. README, manifest and transition tests describe and enforce the source contract.
VERIFIED: Source/addon sync was hash-verified with backups before deployment. Automated suite passed 32/32 before the second Full Compile. The second Full Compile produced `game/csgo_addons/improve_yourself_benchmark/maps/improve_yourself_benchmark.vpk` at 2026-08-17 00:27:16. Real normal-viewer observation is FAIL: the white/occluded phase clears to empty sky and later effects render without surrounding geometry; a red-tinted empty view is not accepted as Red Room or Inferno validation.
DIAGNOSIS: A read-only DMX conversion of the versioned VMAP shows authored solids/entities centered near the origin (observed origins roughly -1760 through +1377, plus local mesh extents), while the controller sends Ancient to approximately x=+7850..8580 and Inferno to x=-8676..-7756. The transition timing can hide the teleport but cannot create the missing scene geometry. This explains the floating/isolated effects and empty-sky result.
OPEN: BLOCKED on map authoring, not on Steam/Workshop Tools. The locked product design still requires an actual Ancient B ramp/water/reflection scene, visibly red Red Room, and Inferno Apps/stairs. Do not mark the transition complete and do not continue blind camera-yaw tuning.
NEXT: Author or import project-owned graybox geometry for the two missing environments at deliberate coordinates (or rebase paths only after identifying real existing bounds), then re-run Full Compile and capture both occlusion exits. Preserve the first Nuke smoke wall until that comparison is complete.
COMMIT/PR: Pending an intentional checkpoint commit after final diff/test review; no successful runtime claim.
