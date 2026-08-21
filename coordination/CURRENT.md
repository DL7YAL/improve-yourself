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
| Demo Analyzer / echter neutraler Szenenfluss | Codex / The Beast | DONE | Neuer Flow auf kanonischem Replay v2: echte Namen/Start-Line-ups, Full Demo oder deduplizierte Multi-Player-Auswahl mit CT/T/Reset, neutrale Profile/Regeln, objektive Kill-/Headshot-/Wallbang-/Smoke-/Entry-/Multi-Kill-Anker, Kontextfenster und Szenen-Merge. Runtime-kompatibler Realnachweis mit `fut-vs-mouz-m2-ancient.dem`: 18 Runden, 10 Spieler, 235 Marker/Regelresultate → 54 Szenen. JSON/Timeline/HTML erzeugt; `demo_gototick 3654` sprang im installierten CS2 nach vollständiger Demo-Bereitschaft sichtbar in den ersten Rundenkontext und wurde stabil pausiert. 97 Tests/7 CLIs grün. Die ältere Mirage-Demo bleibt als Awpy-, nicht als CS2-Runtime-Evidenz erhalten, da normale Wiedergabe dort mit `Failed to parse message` endet. |
| Improve Yourself – Experimental | Codex / The Beast | REVIEW | Funktionaler E2E-Ablauf, visuelle Masterreferenz und gebrandete Portable-Distribution sind zusammengeführt. Die kanonische Variant-3-Quelle ist hashgesichert; Vollwortmarke sowie kompakte Balken-/I-Marke steuern Shell, EXE und Taskleiste. Frischer echter Ancient-Lauf: Awpy PASS, 18 Runden, 10 benannte Spieler, 3.179 grundlegende Events, 235 Marker/Regelresultate und 54 Szenen samt Review/Timeline/Tactical/Report. Portable startet und alle sieben Reiter öffnen crashfrei; der gefundene gepackte Defaultpfad wurde auf `%LOCALAPPDATA%\Improve Yourself\Experimental\results` korrigiert. 125/125 Tests PASS. Setup bleibt bewusst offen, weil noch kein akzeptierter Installer-/Signingvertrag oder Toolchain existiert. |
| 2D Analyzer / Viewer | Codex / The Beast | DONE | Tristan hat den manuellen Sichtcheck aller sieben realen Mirage-Szenen bestanden: Positionen und Blickrichtungen plausibel, keine erkennbare Spiegelung, Fehlrotation, starke Verschiebung oder falsche Skalierung; keine Szene beanstandet. Der temporäre Loopback-Viewer wurde danach kontrolliert beendet. |
| 3D Viewer / World / Assets | Codex / The Beast | RENDERER_SESSION_DONE | Der Einwegadapter konsumiert ausschließlich committed ReplayController-Snapshots, prüft Frame-Tick gegen `resolved_tick`, typisiert über den gemeinsamen Vertrag und spiegelt Spieler/FP/feste TP ohne eigene Zeit/Seek/Parsing-Autorität. Realer Anubis-Tick 6401 floss durch FP und TP; 93 Tests grün. NEXT: bereits evaluierte Sichtlinien nur über injizierten Coordinator mit expliziten Target-IDs in dieselbe Session geben und bei 2D/no-selection/tick change löschen; keine UI-Zielpolitik/Utility-Overlays. |
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
1. Improve Yourself – Experimental steht auf `REVIEW`: Funktion und die verbindlichen Referenzen unter `docs/design/` sind im Desktop-Build vereint. Tristan prüft den vollständigen Produktfluss; keine freie Neugestaltung und keine automatische Merge-/Gesamtproduktfreigabe.
2. Tristan: `WAITING_FOR_TRISTAN` für eine gezielte SDK-/Valve-Asset-Klärung. Der einmalige Preflight `vrad3.exe -script check_raytracing_support.vrad3 -vulkan -gpuraytracing` hat die RX 7900 XTX in VRAD erkannt, aber beim Lesen des Script-Assets mit Exitcode 1 abgebrochen. CS2/SDK 730/745 wurden bereits geprüft; nach Steam-Neustart gibt es kein neues Update (CS2 Build `24701871`, SDK Build `11399846`, keine ausstehenden Bytes). Der Assetname ist weder als lose Datei noch im lesbaren VPK-Verzeichnisindex auffindbar. Keine Treiber-, Registry-, Adrenalin-, Smoke-, Geometrie- oder Controller-Änderung ist vorgeschlagen. Erst nach einer belegten offiziellen Reparatur/SDK-Aktualisierung oder Valve-Klärung Full Compile und marker-synchronisierten Kameraabgleich fortsetzen; bis dahin ist der Benchmark-Strang geparkt.
3. 3D-Viewer/World/Assets nur als getrennte, nicht-benchmarkbezogene Vorbereitung inventarisieren; keine Benchmark-Runtime-Änderungen.
