# Optimizer Evidence Review MVP

Run the local, read-only workflow:
```powershell
.\tools\dev\Start-OptimizerEvidenceReview.ps1
```
It writes `system-check.json` and `optimizer-evidence-review.html` below the chosen output root. The review projects only `iy.system_check/v1` through `iy.optimizer_input/v1`; it shows KNOWN, UNKNOWN or NOT AVAILABLE with existing evidence provenance. It has no Apply/Restore action, accepts no Demo/Replay data, uploads nothing and changes no system setting.

For Brix: run the command, open the printed HTML file, confirm unknown BIOS/driver/setting evidence remains UNKNOWN or NOT AVAILABLE, and confirm the page says READ-ONLY / LOCAL-ONLY.
