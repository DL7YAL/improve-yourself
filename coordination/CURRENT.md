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
| Demo Analyzer / reproduzierbare Entwicklungsbaseline | Codex / The Beast | DONE | `tools/dev/Setup-V1.ps1` stellt Python 3.13 aus dem Lockfile her und prüft Abhängigkeiten, 7 Tests sowie den CLI-Start reproduzierbar. |
| Demo Analyzer / reale Demo-Regression | Codex / The Beast | DONE | Repräsentative reale `de_mirage`-Demo besteht den End-to-End-Lauf und alle `iy.analysis/v1`-Invarianten; nicht personenbezogene Evidenz ist im Codex-Handoff dokumentiert. |
| 2D Analyzer / Viewer | Codex / The Beast | BLOCKED | Renderer und automatisierte Projektionstests sind fertig. Der reale Mirage-Viewer ist lokal erzeugt; der abschließende Sichtcheck wartet auf Tristan, weil die Windows-Browsersteuerung lokale Navigation an ihrer URL-Sicherheitsgrenze beendet. |
| 3D Viewer / World / Assets | ChatGPT / Koordination | FREE -> Vorbereitung | Architektur, benötigte Daten/Assets/Texturen, Schnittstellen und reproduzierbare Visual-Checks inventarisieren; keine Benchmark-Runtime-Änderungen. |
| Sandbox / reproduzierbare Testpipeline | Codex / The Beast | DONE | `tools/dev/Run-V1Pipeline.ps1` liefert aus Lockfile-Setup, Tests, CLI-Smoke-Test und realer Demo-Regression ein lokales, nicht personenbezogenes `iy.pipeline/v1`-PASS/FAIL-Artefakt. |
| V1 Prototypinventur | Codex / The Beast | DONE | Alle sieben dokumentierten Referenzstände sind als REVISE oder DEFER klassifiziert; aktuelle Analyzer-/Replay-Schemas bleiben einzige Parserbasis, maschinenspezifische Optimizerwerte werden nicht als Defaults übernommen. |
| System Check / read-only Baseline | Codex / The Beast | DONE | `iy.system_check/v1` erkennt Windows, CPU, RAM, Mainboard/BIOS, GPU-Treiber, Refresh Rate, Secure Boot und TPM ohne Änderungen oder Elevation; nicht belegbare Sicherheitswerte bleiben REVIEW. |
| Internes Avatar-System | gemeinsam, getrennte Eigenentwürfe | FREE | Nur interne Personalisierung; keine Produkt-/Firmenmarke. Siehe `coordination/agents/avatar-brief.md`. |

## Koordinationsprinzip
Parallel arbeiten, wenn die Stränge unabhängig sind. Nicht dieselbe Schraube gleichzeitig drehen. Wenn ein Owner wiederholt denselben Testkreis ohne neue Information durchläuft, Problemraum aufteilen und eine zweite Diagnoseachse übernehmen.

## Nächste Schritte
1. Codex / The Beast seinen aktuellen Runtime-Diagnoseblock ohne unnötige Unterbrechung abschließen lassen.
2. Parallel 2D- und 3D-Bestand, Schnittstellen und offene Abhängigkeiten erfassen.
3. Aus realen Arbeitsabläufen die kleinste sinnvolle Sandbox/Testpipeline ableiten; kein großes Dashboard vor dem Prozess bauen.
4. Später aus den Handoffs eine kompakte Projektleiter-Sicht ableiten: Was funktioniert, was ist blockiert, wer besitzt was, was hat sich geändert, wo ist Tristans Entscheidung nötig?
