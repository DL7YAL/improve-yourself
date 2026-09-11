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
- Static searches of the mounted Windows drives did not reveal `hammer.exe`,
  `vrad3.exe`, or `check_raytracing_support.vrad3` at accessible paths.
- No Hammer, VRAD, Steam, or CS2 process was running when checked.
- The historic `cs2-workshop-tools-pre-reinstall-20260905-001` backup is
  accessible but contains only `SHA256SUMS.csv`, not Valve/Workshop Tools files.
- This WSL environment has no `powershell.exe` bridge, so it cannot read the
  Windows Steam registry entry or launch Hammer by itself.

## Next bounded action

On the fixed benchmark machine, start CS2 Workshop Tools and Hammer. After
Hammer has initialized, provide the actual Workshop Tools install path or the
non-secret VRAD preflight result. Then perform the existing local-only preflight
and record the outcome here. Do not change Azure configuration, drivers,
registry settings, benchmark geometry, controller logic, or copied Valve assets
as part of this preflight.
