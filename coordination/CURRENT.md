# CURRENT

## Fokus
V1 konsolidieren und bestehende funktionierende Komponenten zu einem sauberen gemeinsamen Entwicklungsstand zusammenführen.

## Rollen
- Tristan: finale Entscheidungen und Prioritäten.
- ChatGPT / Koordination: Gesamtbild, Status, Handoffs, Konflikte, Reviews und unabhängige Parallelvorbereitung.
- Codex / The Beast: Implementierung, technische Änderungen, Builds und Tests in seinem jeweils übernommenen Arbeitsobjekt.

## Arbeitsregel
Vor Beginn relevanter Arbeiten `docs/AGENT_BASE.md`, `docs/ROADMAP.md`, `docs/DECISIONS.md` und diese Datei lesen. Nach Abschluss oder Blockade den eigenen Übergabestand unter `coordination/agents/` aktualisieren.

Ein Arbeitsobjekt hat genau einen Owner. Keine unkoordinierten Änderungen an `LOCKED`-Objekten. Übergaben ändern den Owner ausdrücklich.

Statusfolge: `FREE` -> `LOCKED` -> `REVIEW` -> `DONE`; bei Hindernissen `BLOCKED`.

## Ereignisbasierte Übergaben
Keine unnötigen Kurzintervall-Statusabfragen. Ein Handoff ist besonders sinnvoll bei:
- Blocker oder fehlendem Erkenntnisfortschritt,
- reproduzierbarem PASS/FAIL,
- erreichtem Meilenstein,
- notwendiger Entscheidung,
- Übergabe eines Arbeitsobjekts.

## Aktuelles Cockpit
| Arbeitsstrang | Owner | Status | Ziel / nächster belastbarer Schritt |
| --- | --- | --- | --- |
| Benchmark Runtime / frühe Nuke-Kamera | Codex / The Beast | DONE | Reparierte Quellen sind versioniert; `tools/benchmark/Sync-BenchmarkAddon.ps1` prüft standardmäßig read-only und deployt nur explizit, zielbegrenzt, mit Backup und Hash-Nachprüfung. |
| Benchmark Multi-Map-Transitions | Codex / The Beast | WAITING_FOR_TRISTAN (geparkt) | Steam-Dateiprüfung für CS2 (730) und SDK (745) ist abgeschlossen; Workshop Tools und Hammer starten wieder. Die Benchmark-VMAP lädt. Full Compile endet vor der eigentlichen Build-Pipeline am Hammer-Dialog `GPU Lightmap Baking`. Der isolierte VRAD-Preflight erkennt die RX 7900 XTX als `Vulkan Physical Device`, endet aber mit Exitcode 1, weil `check_raytracing_support.vrad3` im CS2-Gamepfad nicht lesbar ist. Das ist ein SDK-/Preflight-Asset- oder Mount-Kontext-Blocker, nicht fehlendes DXR/Vulkan-RT. Steam meldet sich selbst sowie den SDK-Eintrag als aktuell; nach kontrolliertem Steam-Neustart stehen CS2 auf Build `24701871` und SDK 745 unverändert auf `11399846`, jeweils ohne ausstehende Bytes. Keine Smoke-, Geometrie-, Controller-, Treiber-, Registry-, Adrenalin- oder Hammer-/CS2-Konfigurationsänderung wurde vorgenommen. Der kopierfertige Valve-/Steam-Support-Befund liegt im Codex-Handoff; bis zu einer offiziellen SDK-/Valve-Klärung bleibt der Strang geparkt. |
| Demo Analyzer / reproduzierbare Entwicklungsbaseline | Codex / The Beast | DONE | `tools/dev/Setup-V1.ps1` stellt Python 3.13 aus dem Lockfile her, prüft Abhängigkeiten, alle 33 Tests und die fünf öffentlichen CLI-Einstiegspunkte reproduzierbar. |
| Demo Analyzer / reale Demo-Regression | Codex / The Beast | DONE | Die vollständige `iy.pipeline/v1`-Pipeline besteht auf einem lokalen echten `de_anubis`-Input (Hash `446eec75822c…`): Analysevertrag/Invarianten gültig, 307 Kills, 22 rundenweite Multikills; die fehlende Footstep-Quelle wird korrekt als limitierte Datenqualität offengelegt. Rohdemo und Detailresultate bleiben ignoriert/lokal. |
| 2D Analyzer / Viewer | Codex / The Beast | DONE | Tristan hat den manuellen Sichtcheck aller sieben realen Mirage-Szenen bestanden: Positionen und Blickrichtungen plausibel, keine erkennbare Spiegelung, Fehlrotation, starke Verschiebung oder falsche Skalierung; keine Szene beanstandet. Der temporäre Loopback-Viewer wurde danach kontrolliert beendet. |
| 3D Viewer / World / Assets | Codex / The Beast | SLICE_B_DONE | `ReplayController` und bestehende 2D-Ansicht konsumieren die validierte `iy.replay/v2`-Wahrheit; V1 bleibt kompatibel. Reale Anubis-Projektion: 42 Runden/22 Szenen, selbsttragender 11,0-MiB-Viewer in 5,93 s, 55 Tests grün; fehlende Tickrate sperrt Play sichtbar. NEXT: Slice C Asset Gate — akzeptiertes/distributables Anubis-Manifest, Hashes, Transform und Known-Point/LOS-Beleg; noch kein Renderer. |
| Sandbox / reproduzierbare Testpipeline | Codex / The Beast | DONE | `tools/dev/Run-V1Pipeline.ps1` liefert aus Lockfile-Setup, Tests, CLI-Smoke-Test und realer Demo-Regression ein lokales, nicht personenbezogenes `iy.pipeline/v1`-PASS/FAIL-Artefakt. |
| V1 Prototypinventur | Codex / The Beast | DONE | Alle sieben dokumentierten Referenzstände sind als REVISE oder DEFER klassifiziert; aktuelle Analyzer-/Replay-Schemas bleiben einzige Parserbasis, maschinenspezifische Optimizerwerte werden nicht als Defaults übernommen. |
| System Check / read-only Baseline | Codex / The Beast | DONE | `iy.system_check/v1` erkennt Windows, CPU, RAM, Mainboard/BIOS, GPU-Treiber, Refresh Rate, Secure Boot und TPM ohne Änderungen oder Elevation; nicht belegbare Sicherheitswerte bleiben REVIEW. |
| Integrierter lokaler V1-Ablauf | Codex / The Beast | DONE | `iy-workflow` erzeugt lokal System Check, Analyse, Replay, selbsttragenden Viewer und ein hashgebundenes `iy.workflow/v1`-Manifest; realer Mirage-Lauf mit 7 Szenen und 1.792 Frames validiert. |
| Reduzierte lokale Review-Oberfläche | Codex / The Beast | DONE | `review.html` zeigt Systemstatus, verständliche Datenqualität, alle Szenen und den Tactical-Replay-Einstieg; realer 1440x1200-Headless-Render geprüft, interne Parserausnahmen werden nicht angezeigt. |
| Lokale Review-Persistenz | Codex / The Beast | DONE | `iy-review-server` speichert vier neutrale Benutzerzustände und begrenzte Notizen als separates `iy.review_state/v1`; Loopback-only, origin-/größen-/szenen-/hashgeprüft und atomar, realer 7-Szenen-Dienst-/Rendercheck bestanden. |
| Unterstützter lokaler V1-Start | Codex / The Beast | DONE | `Start-V1Review.ps1` validiert Eingaben, stellt die gesperrte Python-3.13-Basis her, startet Workflow und Loopback-Review sichtbar; realer Mirage-NoServe- und Vordergrundtest samt HTTP-200/State-Check bestanden. |
| Internes Avatar-System | gemeinsam, getrennte Eigenentwürfe | FREE | Nur interne Personalisierung; keine Produkt-/Firmenmarke. Siehe `coordination/agents/avatar-brief.md`. |

## Koordinationsprinzip
Parallel arbeiten, wenn die Stränge unabhängig sind. Nicht dieselbe Schraube gleichzeitig drehen. Wenn ein Owner wiederholt denselben Testkreis ohne neue Information durchläuft, Problemraum aufteilen und eine zweite Diagnoseachse übernehmen.

## Nächste Schritte
1. V1-Foundation ist `READY_FOR_REVIEW` Richtung `main`: konsolidierte Struktur, reproduzierbares Setup, startfähige Baseline ohne aktive Legacy-Abhängigkeit, 33/33 Tests, fünf CLI-Smokes, reale End-to-End-Pipeline und Tristans 2D-Radar-PASS sind belegt. Das ist keine automatische Merge- oder Gesamt-V1-Produktfreigabe; Tristan entscheidet über Review/Merge und die weitergehende Roadmap.
2. Tristan: `WAITING_FOR_TRISTAN` für eine gezielte SDK-/Valve-Asset-Klärung. Der einmalige Preflight `vrad3.exe -script check_raytracing_support.vrad3 -vulkan -gpuraytracing` hat die RX 7900 XTX in VRAD erkannt, aber beim Lesen des Script-Assets mit Exitcode 1 abgebrochen. CS2/SDK 730/745 wurden bereits geprüft; nach Steam-Neustart gibt es kein neues Update (CS2 Build `24701871`, SDK Build `11399846`, keine ausstehenden Bytes). Der Assetname ist weder als lose Datei noch im lesbaren VPK-Verzeichnisindex auffindbar. Keine Treiber-, Registry-, Adrenalin-, Smoke-, Geometrie- oder Controller-Änderung ist vorgeschlagen. Erst nach einer belegten offiziellen Reparatur/SDK-Aktualisierung oder Valve-Klärung Full Compile und marker-synchronisierten Kameraabgleich fortsetzen; bis dahin ist der Benchmark-Strang geparkt.
3. 3D-Viewer/World/Assets nur als getrennte, nicht-benchmarkbezogene Vorbereitung inventarisieren; keine Benchmark-Runtime-Änderungen.
