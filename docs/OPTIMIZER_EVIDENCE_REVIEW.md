# Optimizer Evidence Review MVP

Run the local, read-only workflow:
```powershell
.\tools\dev\Start-OptimizerEvidenceReview.ps1
```
It writes `system-check.json` and `optimizer-evidence-review.html` below the chosen output root. The review projects only `iy.system_check/v1` through `iy.optimizer_input/v1`; it shows KNOWN, UNKNOWN or NOT AVAILABLE with existing evidence details and, where the canonical evidence provides one, a separately labelled evidence source.

## Local report / read-only boundary

The generated artifacts remain local and no user evidence is uploaded. The
System Check itself may query fixed official vendor HTTPS sources for supported
driver comparisons; it neither uploads the collected facts nor installs or
changes anything. A failed official request remains fail-safe: its comparison
evidence is represented as UNKNOWN or NOT AVAILABLE, never as a confirmed
result. The review has no Apply or Restore action, accepts no Demo/Replay data,
and makes no system change.

For Brix: run the command, open the printed HTML file, confirm unknown BIOS/driver/setting evidence remains UNKNOWN or NOT AVAILABLE, and confirm the page says LOCAL REPORT / READ-ONLY.
