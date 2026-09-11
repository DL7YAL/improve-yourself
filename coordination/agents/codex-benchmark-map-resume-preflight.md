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

## Next bounded action

With CS2 Workshop Tools and Hammer initialized on the fixed benchmark machine,
run the existing local `vrad3.exe -script check_raytracing_support.vrad3
-vulkan -gpuraytracing` preflight from the discovered CS2 `game\bin\win64`
directory. Record the complete non-secret output and exit code here. Do not
change Azure configuration, drivers, registry settings, benchmark geometry,
controller logic, or copied Valve assets as part of this preflight.
