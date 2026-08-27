# Optimizer Evidence Review MVP

Run the local, read-only workflow in normal mode:
```powershell
.\tools\dev\Start-OptimizerEvidenceReview.ps1
```
Run the same workflow without official vendor comparison requests:
```powershell
.\tools\dev\Start-OptimizerEvidenceReview.ps1 -Offline
```
It writes `system-check.json` and `optimizer-evidence-review.html` below the chosen output root. The review projects only `iy.system_check/v1` through `iy.optimizer_input/v1`; it shows KNOWN, UNKNOWN or NOT AVAILABLE with existing evidence details and, where the canonical evidence provides one, a separately labelled evidence source.

The direct System Check CLI supports the same explicit offline mode:
```powershell
iy-system-check --offline --output results\optimizer-evidence-review\system-check.json
```

## Local report / read-only boundary

The generated artifacts remain local and no user evidence is uploaded. In
normal mode, System Check may query fixed official vendor HTTPS sources for the
supported GPU and chipset driver comparisons. In offline mode, only those fixed
official comparison requests are suppressed; local machine collection still
runs. The report records `OFFLINE` only when the validated System Check policy
proves that those comparisons were disabled, and `OFFICIAL COMPARISON` only
when it proves they were enabled.

A missing or malformed network-policy field renders `UNKNOWN`. `UNKNOWN` must
not be interpreted as OFFLINE or as proof that no network request occurred. A
failed official request remains fail-safe: comparison evidence is represented
as UNKNOWN or NOT AVAILABLE, never as a confirmed result. The review has no
Apply or Restore action, accepts no Demo/Replay data, and makes no system
change.

For Brix: run the command, open the printed HTML file, confirm unknown BIOS/driver/setting evidence remains UNKNOWN or NOT AVAILABLE, and confirm the page says LOCAL REPORT / READ-ONLY.
