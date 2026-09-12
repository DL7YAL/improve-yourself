# Benchmark map resume preflight — 2026-09-12

## Task

Resume the local CS2 Workshop benchmark-map work without involving Azure,
Foundry, cloud CI, or MCP.

## Base and scope

- Branch: `codex/benchmark-map-resume-preflight`
- Base `main`: `6c5ed23703c90a7312f22fd1669b403c372e0802`
- Benchmark sources are read-only until a local Hammer/VRAD observation exists.
- The local `check_raytracing_support.vrad3` behavior is not a GitHub source
  artifact and must not be copied, packaged, or made an Azure dependency.

## Evidence collected

- The workspace is on the stated base and has no uncommitted changes.
- Steam is installed under `E:\Program Files (x86)\Steam`.
- App 730 is installed as `Counter-Strike Global Offensive`, build `25218825`;
  its manifest reports no remaining download or staging bytes.
- App 745 is installed as `Counter-Strike Global Offensive 745`, build
  `11399846`, with no remaining download or staging bytes.
- `vrad3.exe` is present at
  `E:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\bin\win64\vrad3.exe`.
- The only loose `hammer.exe` found is the SDK executable at
  `E:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive 745\bin\hammer.exe`.
- After the user reported Hammer open, a read-only search found no persistent
  loose `check_raytracing_support.vrad3` in either installed tree or the recent
  user temp files. Therefore file absence alone does not prove the initialized
  Hammer/VRAD preflight result; the command outcome remains required evidence.
- The user then confirmed that the correct current CS2 Hammer instance was
  open. An immediate repeated search still found no loose script or current
  Hammer/VRAD log in the CS2, SDK, or user-temp trees. This rules out a durable
  loose file created merely by opening Hammer; resolution may be virtual or
  build-time, so only the real VRAD command/build output can close the gate.
- The historic `cs2-workshop-tools-pre-reinstall-20260905-001` backup is
  accessible but contains only `SHA256SUMS.csv`, not Valve/Workshop Tools files.
- This WSL environment has no `powershell.exe` bridge, so it cannot read the
  Windows process list or execute `vrad3.exe` by itself.

## Local source divergence — resolved by owner decision

The installed addon's active sources differed from the repository manifest:

| Source | Repository SHA-256 | Installed SHA-256 | Installed state |
| --- | --- | --- | --- |
| `maps/improve_yourself_benchmark.vmap` | `9d7be49fd2fa9f720267e5fd155054f478f64416408ac681ef02b578274276ce` | `74ae13f43eda0fc213330a30d9714d16b2897710c5409378a9d4bf1294e4beb6` | 1,205,304 bytes, modified 2026-09-11 23:31 local time |
| `scripts/benchmark_controller.js` | `45d2cf2c0efb05454304b2f46630239d6b7998bc0f3172b8b71dd405dc07b4bd` | `0038baacb132a907654e03fe3b42b27bf198d5d1a23f4f9f0d8c87b5df16723e` | 16,613 bytes, `iy-benchmark/v1.2-candidate.2` |

The controller difference includes changed Nuke camera coordinates, explicit
capture-window markers for Nuke/Ancient/Inferno, team-intro timing controls,
and a fail-honest `measurement_status=unverified`. The VMAP is also materially
larger than the 401,300-byte previous repository source.

On 2026-09-12 the project owner explicitly selected the installed
`iy-benchmark/v1.2-candidate.2` as the authoritative continuation for GitHub.
The VMAP and controller were imported byte-for-byte, their manifest hashes were
updated, and equality with the installed sources was verified immediately
after import. No repository-to-addon deployment occurred and the installed
files were not modified.

## Next bounded action

With source authority resolved and CS2 Workshop Tools and Hammer initialized on
the fixed benchmark machine, run the existing local
`vrad3.exe -script check_raytracing_support.vrad3 -vulkan -gpuraytracing`
preflight from the discovered CS2 `game\bin\win64` directory. Record the
complete non-secret output and exit code here. Do not change Azure
configuration, drivers, registry settings, benchmark geometry, controller
logic, or copied Valve assets as part of this preflight.

## Runtime excerpt received — 2026-09-12

The owner supplied a 97-line console excerpt. Counting only canonical unquoted
`[IYBENCH]` lines avoids counting the duplicated quoted console echoes.

- Segment 1: 28 canonical events; warmup completed; all five warmup capture
  windows appeared; measured pass started; `REPORT scene=nuke_outside`
  appeared; the excerpt then reset with a new `READY` before measured end.
- Segment 2: 21 canonical events; warmup completed; all five warmup capture
  windows appeared; measured pass started; the excerpt ended before any
  measured report or measured end.
- Neither segment contains an `[IYBENCH] ERROR` line.
- Neither segment contains `PASS_END type=measured`.
- The expected fail-honest
  `MEASUREMENT_STATUS status=unverified reason=client_commands_require_runtime_confirmation`
  appears.

Assessment: controller startup, scene order, transition order and warmup capture
markers have direct runtime evidence. Measurement completion, client-command
confirmation, visual landmark acceptance, Hammer Full Compile and VRAD success
remain unproven. The next run must remain uninterrupted through measured end
and the Hammer build/VRAD output must be preserved separately.

## GitHub world-sections cross-check — 2026-09-12

The exact local filename
`AUFTRAG_BENCHMARK_MAP_WELTENBAU_ANCIENT_INFERNO.md` is not present on any
fetched GitHub remote branch or tag. The corresponding versioned work order is
`docs/BENCHMARK_MAP_ASSET_REBUILD_WORK_ORDER.md` on
`origin/codex/benchmark-map-world-sections-v1`, final branch commit `6ee32c4`.
The same branch contains `docs/BENCHMARK_MAP_WORLD_SECTIONS_HANDOFF.md`.

That handoff records a forced Full Compile with `59 compiled, 0 failed, 0
skipped` and VPK SHA-256
`F950D9ECA4389F9B1BA98C1D62E9AD925A283D28C70EE938FAC89468E4C232C8`.
It leaves the normal-viewer marker captures and uninterrupted post-build
controller run open. Its VMAP and controller hashes are byte-identical to
current `main` (`74AE13F...E4BEB6` and `0038BAA...16723E` respectively).

The supporting world-section authoring tools, provenance records, focused
tests and handoff remain only on that remote branch; they were not integrated
by the later source-only V1.2 promotion to `main`. Do not merge the stale branch
wholesale over current `main`. Any integration must preserve current main-only
files and review the branch's supporting files as a bounded follow-up.

## Bounded continuity restoration — 2026-09-12

The owner then supplied the complete detailed German assignment. The exact
filename is now versioned as
`AUFTRAG_BENCHMARK_MAP_WELTENBAU_ANCIENT_INFERNO.md`, with its obsolete private
absolute brand-reference path intentionally removed. The matching provenance
records, reproducible authoring helpers, world-section handoff and focused
tests were selectively restored from the proven source commits; the stale
branch was not merged and no Azure-owned file was changed.

Read-only hash comparison still shows exact repository/addon source equality:

- VMAP: `74AE13F43EDA0FC213330A30D9714D16B2897710C5409378A9D4BF1294E4BEB6`;
- controller: `0038BAACB132A907654E03FE3B42B27BF198D5D1A23F4F9F0D8C87B5DF16723E`.

Twelve focused zero-fixture assertions passed under the available system
Python, as did `compileall` and `git diff --check`. A fresh pytest/full-suite
run and `pip check` were not possible in this Linux workspace because neither
pytest nor pip is installed. No new Steam screenshot was found. The assignment
therefore remains `PARTIAL`: visual marker evidence, a complete measured pass,
and the deterministic cheering-animation/two-restart proof are still open.

The owner clarified that Windows is the runtime authority for Codex, Hammer,
Workshop Tools and CS2; Linux/WSL is only the SSH/Git connection. The added
standard-library runtime validator is therefore intended to be executed from
Windows after the next normal-viewer run. Its focused tests raise the local
zero-fixture total to 18, and it correctly rejects the earlier supplied log as
`PARTIAL` because the latest restart contains only 21 of 39 required contract
events.
