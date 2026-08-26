# System Check / Optimizer boundary

System Check is an independent, local, read-only diagnosis basis. It is not a
subsystem of Demo Analyzer, Tactical Replay, 2D replay, or a later 3D replay.

```text
explicit iy-system-check
          |
          v
  iy.system_check/v1  -- explicit conversion -->  iy.optimizer_input/v1
                                                   |
                                                   v
                                      future Optimizer planning only

explicit iy-demo-workflow --> iy.analysis/v1 --> iy.replay/v2
                                               --> ReplayStore / ReplayController
                                               --> 2D / 3D / review consumers

separate legacy-compatible iy-workflow --> iy.replay/v1 --> its own local viewer/review artifacts
```

`iy-optimizer-input` accepts only an explicit `iy.system_check/v1` document
whose policy states `read_only: true` and `changes_applied: false`. The output
keeps the System Check summary and checks as reviewable planning evidence. It
does not add a recommendation engine, apply/restore function, Windows change,
driver change, registry write, BIOS/UEFI action, or demo/replay data.

The analyzer workflow deliberately does **not** invoke System Check. Its review
page contains only demo analysis and replay evidence unless a caller explicitly
uses the reusable review renderer with a System Check document. This preserves
existing combined-review capability for an explicitly selected artifact while
removing it as an automatic product dependency.

`iy-workflow` continues to document the explicit legacy-compatible
`iy.replay/v1` workflow. It is not an active fallback for the canonical
`iy.replay/v2` path and does not authorize a second replay store/controller.
Other V1 replay references are historical/compatibility context. For the
broader current-versus-future distinction, see
[`PRODUCT_ROADMAP_ALIGNMENT.md`](PRODUCT_ROADMAP_ALIGNMENT.md).

## Explicit local use

```powershell
.venv\Scripts\iy-system-check --output results\system-check.json
.venv\Scripts\iy-optimizer-input results\system-check.json --output results\optimizer-input.json
```

Both commands are local and read-only. `iy-optimizer-input` is an input handoff
for a future optimizer planner, not permission to apply a profile.

The complete V1 coverage and the AMD/NVIDIA evidence boundary are maintained in
[`SYSTEM_CHECK_V1_MATRIX.md`](SYSTEM_CHECK_V1_MATRIX.md).
