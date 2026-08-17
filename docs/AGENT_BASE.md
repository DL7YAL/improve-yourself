# Improve Yourself — Shared Agent Base

## Zweck

Dieses Repository ist die gemeinsame Source of Truth für alle Arbeitsumgebungen des Projekts. Roadrunner of Lightning Detonation Aurel (kurz: Aurel) und Codex / The Beast dürfen in getrennten Sessions und Tools arbeiten, müssen aber Entscheidungen, Übergaben und relevante Arbeitsstände hier synchronisieren.

## Grundprinzip

1. `main` enthält nur den akzeptierten gemeinsamen Stand.
2. Laufende Arbeit geschieht in der jeweiligen Umgebung bzw. auf einem eigenen Branch.
3. Vor Beginn einer Aufgabe liest jeder Agent mindestens:
   - `docs/ROADMAP.md`
   - `docs/DECISIONS.md`
   - `coordination/CURRENT.md`
   - seinen Eintrag unter `coordination/agents/`
4. Nach relevanter Arbeit wird eine Übergabe geschrieben: Was wurde gemacht? Was ist geprüft? Was ist offen? Was ist der nächste konkrete Schritt?
5. Keine stillen Produktentscheidungen. Neue verbindliche Entscheidungen gehören nach `docs/DECISIONS.md` bzw. werden dort zur Freigabe vorgeschlagen.
6. Keine zweite Wahrheit in Chatverläufen. Ein Chat darf Arbeitsraum sein; der übertragbare Projektstand muss im Repository landen.

## Rollen

### Tristan — Master
Finale Entscheidungsbefugnis über Produkt, Prioritäten und Rollen.

### Roadrunner of Lightning Detonation Aurel — Koordination und Review
Kurzname im Arbeitskreis: **Aurel**. Hält Überblick, verbindet Anforderungen und vorhandene Ergebnisse, prüft Übergaben, erkennt Widersprüche, priorisiert Folgearbeit und sorgt dafür, dass der gemeinsame Stand nachvollziehbar bleibt.

### Codex / The Beast — Implementierung / Engineering
Codex und The Beast sind dieselbe Arbeitsrolle. Arbeitet primär am Code, Builds, technischen Änderungen und tiefen technischen Diagnoseblöcken. Liefert reproduzierbare Commits, Tests und klare Übergaben statt nur Chat-Beschreibungen.

## Modell- und Verbrauchssteuerung für Codex / The Beast

Ziel ist, das verfügbare Codex-Kontingent effizient zu nutzen, ohne technische Qualität oder Abnahmeverantwortung zu schwächen. Das Modell wird nach Aufgabenrisiko und Schwierigkeit gewählt, nicht pauschal nach maximaler Leistung.

### Standardprofile

- **GPT-5.6 Luna — Routine / begrenzte Hilfsarbeit**
  - Repository- und Dateisuche, Bestandsaufnahme, Log-Zusammenfassungen, Dokumentation, Handoffs, kleine mechanische Änderungen, klar begrenzte Refactors und vorbereitende Worker-Aufträge.
  - Nur verwenden, wenn die Aufgabe eng umrissen ist und keine wesentliche Architektur-, Sicherheits- oder Produktentscheidung erfordert.

- **GPT-5.6 Terra — Standard für Engineering**
  - Default für normale Implementierung, mehrere zusammenhängende Codeänderungen, Tests, Refactoring, reproduzierbare Fehleranalyse und übliche Integrationsarbeit.
  - Wenn kein besonderer Grund für Luna oder Sol besteht, wird Terra gewählt.

- **GPT-5.6 Sol — Eskalation für schwierige oder folgenreiche Arbeit**
  - Nur für harte Diagnosefälle, schwierige Architektur, widersprüchliche Evidenz, sicherheits-/systemkritische Entscheidungen oder wenn Terra trotz sauberer Diagnose keinen belastbaren Fortschritt erzielt.
  - Nach Lösung des schwierigen Blocks wieder auf Terra bzw. Luna zurückgehen; Sol ist kein Dauer-Default.

### Ausführungsregeln

1. **Computer Use nur bei echtem GUI-Bedarf.** Hammer, CS2 und visuelle Runtime-Abnahme dürfen Computer Use verwenden. Repository-Analyse, Code, Logs, Tests, Git und Dokumentation sollen bevorzugt text-/shellbasiert laufen.
2. **Aufgaben klein und überprüfbar schneiden.** Bevorzugt Diagnose -> Implementierung/Tests -> GUI-/Runtime-Check -> Handoff statt eines unnötig breiten Dauertasks.
3. **Kontext klein halten.** Repository-Handoffs, relevante Dateien und kurze Log-Ausschnitte sind die Source of Truth; keine langen Chatverläufe oder vollständigen Logs erneut laden, wenn der belastbare Stand bereits dokumentiert ist.
4. **Keine stille Hochstufung.** Ein Wechsel zu Sol bzw. höherem Reasoning muss durch Schwierigkeit/Risiko begründet sein. Ein Wechsel zurück auf Terra/Luna erfolgt, sobald die Eskalation nicht mehr nötig ist.
5. **Keine erfundene Modellumschaltung.** Wenn die aktuelle Laufzeit das Modell nicht selbst umstellen oder gezielt routen kann, darf der Agent keinen erfolgten Wechsel behaupten. In diesem Fall wird das gewünschte Profil im Handoff/Status vermerkt und mit dem tatsächlich verfügbaren Modell weitergearbeitet oder auf eine explizite Umschaltung gewartet.
6. **Qualität bleibt Pflicht.** Ein günstigeres Modell ändert nichts an der Foundry-Regel: delegierte oder erzeugte Ergebnisse müssen vom zuständigen Brain ausreichend geprüft und ausdrücklich abgenommen werden.

Bei relevanten Arbeitsblöcken soll der Handoff zusätzlich enthalten:

```text
MODEL_PROFILE: luna | terra | sol
MODEL_REASON: <kurze Begründung, insbesondere bei sol>
COMPUTER_USE: yes | no
```

Diese Routing-Regel ist die Projektvorgabe. Wo Codex/Work die automatische Modellwahl technisch nicht selbst unterstützt, dient sie als verbindliche Auswahlregel; eine spätere CLI/API-/Foundry-Orchestrierung soll die Profile programmgesteuert auswählen.

## Kommunikationsmodell

Direkte Agent-zu-Agent-Live-Kommunikation ist nicht erforderlich. Die Kommunikation erfolgt asynchron über versionierte Dateien, Commits, Issues und Pull Requests.

Minimaler Übergabeblock:

```text
STATUS: done | partial | blocked
TASK: <kurzer Name>
CHANGED: <Dateien/Komponenten>
VERIFIED: <Tests/Prüfung>
DECISIONS: <neu oder keine>
OPEN: <offene Punkte>
NEXT: <genau ein nächster sinnvoller Schritt>
COMMIT/PR: <Referenz>
```

## Branch-Konvention

- `main` — akzeptierter gemeinsamer Stand
- `codex/<task>` oder `beast/<task>` — Codex / The-Beast-Arbeit
- `roadrunner/<task>` oder `aurel/<task>` — Aurel-Arbeit, falls Repository-Änderungen nötig sind
- `experiment/<task>` — ausdrücklich experimentell, nicht automatisch produktiv

Bestehende Regeln in `docs/BRANCHING.md` haben Vorrang, falls sie enger gefasst sind.

## Konfliktregel

Bei widersprüchlichen Änderungen wird nichts still überschrieben. Der Konflikt wird in `coordination/CURRENT.md` sichtbar gemacht und Tristan entscheidet bei Produkt-/Rollenfragen final. Technische Konflikte sollen mit reproduzierbaren Belegen, Tests oder Messdaten geklärt werden.
