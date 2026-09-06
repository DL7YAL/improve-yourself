# UI V1 Visible Closure — Runtime Status

Status: **UI_V1_READY_FOR_TRISTAN_REVIEW**

Visual authority: Canva `DAHUBn5D2aM` (`Versuch.nr1`), revision 25
Base: GitHub `main` `88ce9179668f127b09c1485f121ac4ed805603db`

## Visible shell and route evidence

- The existing local desktop shell displayed a responsive, branded `Improve Yourself – Experimental` window in approximately 970 ms during the 2026-09-07 visible-start check.
- A fresh local Capture-CanvaUi run rendered all eight routes at both contractual viewports: `1536x1024` and `1080x720`.
- The captured routes were Dashboard, Analyzer, Tactical Replay, My Improvement, System Check / Optimizer, Benchmark, Reports, and Settings.
- Dashboard, Analyzer, Tactical Replay empty state, read-only Optimizer, and Settings were visually inspected. They retain one shared Canva-R25 shell and explicit local/unknown/read-only states.
- The fresh capture outputs had the expected dimensions. PNG byte hashes differed from the versioned capture set despite visually consistent output; Win32/DWM capture bytes are therefore not treated as deterministic replacement evidence without a reviewed manifest refresh.

## Real local workflow proof

- The project-owner-approved Ancient demo was used exactly once from the bounded local `Demos` folder. Its SHA-256 matched the already documented source identity; the full local path and full hash are not repeated here.
- A fresh ignored result root produced one `iy.demo_workflow/v1` fixture with parser status `PASS`, map `de_ancient`, 18 rounds, full-demo selection, 54 merged scenes, and status `READY_FOR_REVIEW`.
- The existing fail-closed shell validator accepted the fixture, all required artifact references remained relative, replay chunks and artifact hashes validated, and no private absolute path marker was present in the workflow manifest.
- The visible runtime opened the existing workflow without reparsing, displayed Analyzer Review, selected the first canonical scene at tick 3654, opened that same scene and tick through the existing Tactical Replay path, and returned to the same embedded Review state.
- The real-flow screenshots and workflow artifacts remain local under the ignored result root. No demo, player data, source hash, private path, workflow result, or screenshot from that private run is committed or pushed.

## Portable external test candidate

- `tools/dev/Build-Experimental.ps1` completed normally without `-SkipTests`.
- The build gate reported 432 passed and 1 explicitly optional skipped test, followed by dependency, compile, PyInstaller, ZIP, and build-manifest completion.
- `experimental-build.json` matched the generated EXE and ZIP SHA-256 values.
- The portable ZIP contains the application executable and external-test-candidate notice. Its entry inventory contains no demo, workflow result, `.venv`, cache, local profile, database, or replay source artifact.
- The packaged EXE exposed the branded Home window in approximately 720 ms. The captured early window was already fully branded rather than white or empty, and the process subsequently reported responsive.
- This artifact is an **external test candidate**, not a release or installer.

## Architecture and scope confirmation

- No product code fix was necessary: the authorized visible checks produced no reproducible UI, startup, or packaging defect.
- The canonical path remains Demo -> Awpy Adapter -> AnalyzerCore -> AnalyzerDataHub -> `iy.replay/v2` -> ReplayStore -> ReplayController -> Tactical / Viewer / Review.
- System Check / Optimizer remains read-only. No Apply, Restore, backup, system-change, Demo-input, or Replay-input authority was added.
- No parser, data hub, replay store, replay controller, viewer-owned playback truth, V1 fallback, Azure dependency, cloud change, benchmark work, Hammer work, or 3D-Panda work was introduced.
- No merge to `main` was performed.

## Review decision

The source shell, all routes, one real hash-bound workflow, Analyzer Review, canonical 2D Tactical Replay, return navigation, and the portable test candidate have now been visibly exercised. The remaining action is Tristan's review of PR #37 and the local external test candidate; merge and release remain separate decisions.
