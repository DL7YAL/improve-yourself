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
| Benchmark Multi-Map-Transitions | Codex / The Beast | BLOCKED | Transform und Fade-Syntax sind behoben; 33/33 Tests und Full Compile (`22 compiled, 0 failed, 1 skipped`) bestehen. Der persistente rote Vollbildzustand kam von veralteten Fade-Argumenten und einem falschen Client-only-Pfad. Die fünf realen Inferno-Stufen sind aus der statisch vermessenen Position `0 3450 600` vollständig sichtbar. Der automatisch interpolierte Lauf zeigte am `TRANSITION_EXIT` jedoch noch nicht denselben Treppenblick. Nächster Schritt: Kameraanwendung/Timing gegen den Marker messen; Smoke und Grundgeometrie unverändert lassen. |
| Demo Analyzer / reproduzierbare Entwicklungsbaseline | Codex / The Beast | DONE | `tools/dev/Setup-V1.ps1` stellt Python 3.13 aus dem Lockfile her und prüft Abhängigkeiten, 7 Tests sowie den CLI-Start reproduzierbar. |
| Demo Analyzer / reale Demo-Regression | Codex / The Beast | DONE | Repräsentative reale `de_mirage`-Demo besteht den End-to-End-Lauf und alle `iy.analysis/v1`-Invarianten; nicht personenbezogene Evidenz ist im Codex-Handoff dokumentiert. |
| 2D Analyzer / Viewer | Codex / The Beast | BLOCKED | Renderer und automatisierte Projektionstests sind fertig. Der reale Mirage-Viewer ist lokal erzeugt; der abschließende Sichtcheck wartet auf Tristan, weil die Windows-Browsersteuerung lokale Navigation an ihrer URL-Sicherheitsgrenze beendet. |
| 3D Viewer / World / Assets | ChatGPT / Koordination | FREE -> Vorbereitung | Architektur, benötigte Daten/Assets/Texturen, Schnittstellen und reproduzierbare Visual-Checks inventarisieren; keine Benchmark-Runtime-Änderungen. |
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
1. Benchmark-Multi-Map-Transitions nicht als fertig behandeln: Fade-Handoff und reale Inferno-Stufen sind einzeln nachgewiesen, aber der automatische Kamera-Keyframe entspricht am Marker noch nicht dem statisch validierten Blick. Als Nächstes Kameraanwendung/Timing messen, dann Wasser/Red Room/Flash/Inferno vollständig marker-synchronisiert abnehmen.
2. Den vertex-gebakten Authoring-Stand und die neue Full-Compile-/Laufzeitevidenz sichern; keine erneute blinde Smoke- oder Grundgeometrieänderung.
3. Parallel 2D- und 3D-Bestand, Schnittstellen und offene Abhängigkeiten erfassen.
4. Aus realen Arbeitsabläufen die kleinste sinnvolle Sandbox/Testpipeline ableiten; kein großes Dashboard vor dem Prozess bauen.
5. Später aus den Handoffs eine kompakte Projektleiter-Sicht ableiten: Was funktioniert, was ist blockiert, wer besitzt was, was hat sich geändert, wo ist Tristans Entscheidung nötig?
