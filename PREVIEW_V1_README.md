# Improve Yourself — Preview V1

Improve Yourself is a local-first toolkit for reviewing Counter-Strike 2 demo
matches and understanding a PC's gaming-readiness. It produces transparent
facts and review cues; it does not make automated cheat allegations or change
system settings.

## Included in this preview

- Demo Analyzer with the Improve Default V1 profile selector
- Demo preflight: map, match overview, T/CT roster and available data limits
- Match Review grouped by player, round and tick
- 2D Tactical Replay with positions, view direction, documented kills, utility
  evidence and map zoom controls
- Copyable original-demo/tick review command for Counter-Strike
- Analyzer Excel report
- Read-only System Check and Optimizer Input preview

## Start

Install Python 3.13, then open PowerShell in this folder and run:

```powershell
.\tools\dev\Setup-V1.ps1
.\tools\dev\Start-V1Review.ps1 -Demo 'C:\Path\to\match.dem.zst'
```

The analyzer starts a local-only review page. Choose the profile, inspect the
preflight, then select **Analyse starten**. The resulting Match Review links to
the relevant Tactical Replay scenes. Original demos remain local.

For an Excel report, run the analyzer and use:

```powershell
node tools\report\Build-AnalyzerExcelReport.mjs <analysis.json> <report.xlsx>
```

For the read-only System Check / Optimizer Input preview, see
`docs/SYSTEM_CHECK_OPTIMIZER_BOUNDARY.md`.

## Important limits

- No 3D/POV viewer, cloud sync, optimizer Apply/Restore, overclocking or
  undervolting is included.
- My Improvement is documented as a future Analyzer path, not shipped as a
  complete user interface in this preview.
- Only technically supported Analyzer criteria are evaluated. Missing demo data
  is disclosed and never treated as a negative finding.
- The 2D map uses local map-overview assets when available and falls back to a
  neutral grid otherwise.
- Original-demo tick navigation is a transparent manual review workflow, not
  an automatic in-game controller.

## Privacy

This preview does not include demos, generated analyses, review notes, system
results, credentials or personal configuration. Those stay local and are
ignored by version control.
