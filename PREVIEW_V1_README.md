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
- Read-only System Check and Optimizer Input preview
- Read-only Optimizer Preview with Performance- und Quality-Ansicht; sie zeigt
  ausschließlich vorhandene Systemdaten und Empfehlungen

## Start

Unpack `Improve-Yourself-Preview-V1.zip`, then double-click **Improve
Yourself.exe**. Select a local `.dem`, `.dem.zst` or `.dem.bz2` file in the
dialog. Improve Yourself starts a local-only review page in the default browser.
Choose the profile, inspect the preflight, then select **Analyse starten**. The
resulting Match Review links to the relevant Tactical Replay scenes. Original
demos remain local.

The original-demo/tick review requires Counter-Strike 2 to be installed and is
a transparent manual review step. The System Check and Optimizer Input are
read-only technical preview components. They can be generated locally with
`Improve Yourself.exe --system-check`; the resulting JSON files stay in the
local `Improve Yourself Data` folder. This Preview does not present a finished
Optimizer Apply/Restore function.

The Analyzer Match Review includes **Excel-Report exportieren**. The report is
created locally by the packaged application; no Microsoft Office, Node.js or
additional runtime is required.

## Important limits

- No 3D/POV viewer, cloud sync, optimizer Apply/Restore, overclocking or
  undervolting is included.
- My Improvement is documented as a future Analyzer path, not shipped as a
  complete user interface in this preview.
- My Improvement, 3D POV and Benchmark appear only as clearly marked future
  areas in the Preview navigation.
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
