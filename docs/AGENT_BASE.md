# Improve Yourself — Shared Agent Base

## Zweck

Dieses Repository ist die gemeinsame Source of Truth für alle Arbeitsumgebungen des Projekts. Roadrunner/ChatGPT, Codex und The Beast dürfen in getrennten Sessions und Tools arbeiten, müssen aber Entscheidungen, Übergaben und relevante Arbeitsstände hier synchronisieren.

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

### Roadrunner / ChatGPT — Koordination und Review
Hält Überblick, verbindet Anforderungen und vorhandene Ergebnisse, prüft Übergaben, erkennt Widersprüche und sorgt dafür, dass der gemeinsame Stand nachvollziehbar bleibt.

### Codex — Implementierung / Engineering
Arbeitet primär am Code und an technischen Änderungen. Liefert reproduzierbare Commits, Tests und klare Übergaben statt nur Chat-Beschreibungen.

### The Beast — unabhängige Analyse / zweite technische Perspektive
Kann Aufgaben eigenständig bearbeiten, Lösungen challengen und alternative Umsetzungswege prüfen. Ergebnisse werden ebenfalls über dieselbe Base übergeben.

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
- `codex/<task>` — Codex-Arbeit
- `roadrunner/<task>` — Roadrunner/ChatGPT-Arbeit, falls Repository-Änderungen nötig sind
- `beast/<task>` — The-Beast-Arbeit
- `experiment/<task>` — ausdrücklich experimentell, nicht automatisch produktiv

Bestehende Regeln in `docs/BRANCHING.md` haben Vorrang, falls sie enger gefasst sind.

## Konfliktregel

Bei widersprüchlichen Änderungen wird nichts still überschrieben. Der Konflikt wird in `coordination/CURRENT.md` sichtbar gemacht und Tristan entscheidet bei Produkt-/Rollenfragen final. Technische Konflikte sollen mit reproduzierbaren Belegen, Tests oder Messdaten geklärt werden.
