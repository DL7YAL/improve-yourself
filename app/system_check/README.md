# System Check

V1 responsibility: detect relevant system components and present a clear readiness assessment without drowning the user in raw telemetry.

## Read-only baseline

```powershell
.venv\Scripts\iy-system-check --output results\system-check.json
```

The `iy.system_check/v1` result currently covers Windows, CPU, memory,
motherboard/BIOS, graphics driver, active refresh-rate information, Secure Boot
and TPM. It reports `OK`, `REVIEW` or `ACTION_REQUIRED` and explicitly records
that it applied no changes, requested no elevation and performed detection only.

This baseline does not install drivers, change firmware/security settings or
apply Optimizer values. Unknown values remain `REVIEW`; they are never silently
treated as healthy or defective.
