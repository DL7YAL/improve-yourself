# Preview V1 Windows packaging

`tools/build/Build-Preview-V1.ps1` creates the supported Preview V1 Windows
build. It uses the project virtual environment and the version pinned in
`requirements.lock`; do not use a global PyInstaller installation as the build
authority.

## Build

1. From the repository root, run `tools/dev/Setup-V1.ps1` to create/update the
   project environment from the lock file.
2. Run `tools/build/Build-Preview-V1.ps1`.
3. The onedir result is `dist/Improve-Yourself-Preview-V1/Improve Yourself/`.
   Its user entry point is `Improve Yourself.exe`.

The build collects the application modules, their Python runtime dependencies,
the bundled local map-overview resources and the external Preview README. It
does not collect repository metadata, virtual environments, demos, local
reports/results, logs, coordination files or archives.

## Required distribution gate

Copy the `Improve Yourself` directory to a new location which has no
repository or `.venv` parent. From that copied directory verify:

- `Improve Yourself.exe --demo <local-demo> --port <free-loopback-port>` starts
  a loopback-only Analyzer preflight;
- `POST /api/start-analysis` returns JSON and reaches the Match Review;
- the Tactical Replay opens from that review; and
- `Improve Yourself.exe --system-check` emits `iy.system_check/v1` and
  `iy.optimizer_input/v1` locally.

Then scan the actual distribution for private paths, names, raw demos, system
reports, credentials and generated artifacts before creating a ZIP.

## Current packaging boundary

The Analyzer Excel report generator currently imports
`@oai/artifact-tool` from the development Node environment. It is not a
runtime dependency shipped by this PyInstaller build. Do not label a ZIP as a
complete Preview V1 distribution until that generator is replaced or packaged
as an ordinary external runtime dependency and passed through the same clean
distribution gate.
