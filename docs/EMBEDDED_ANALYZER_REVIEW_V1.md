# Embedded Analyzer Review — Product Slice

## Ziel und Grenze

Der normale Analyzer-Review läuft innerhalb des bestehenden Improve-Yourself-Fensters. Er ist eine native Präsentationsschicht über dem bereits erzeugten `iy.analysis_flow/v1`; er parst keine Demo, erzeugt keine Indikatoren, Regeln oder Szenen und besitzt keine eigene Tick-Autorität.

Nicht Teil dieses Slices sind neue Analyzer-Kriterien, Clip/OBS/Video, Remote-Zugriff, ein neuer Review-Server, ein zweiter Parser oder Änderungen an Benchmark, Optimizer und System Check.

## Datenfluss und Autorität

```text
demo-workflow.json (fail-closed validiert)
  -> analysis-flow.json (Szenen, Spieler, Runden, Regeln, exakter Review-Tick)
  -> EmbeddedReviewSession (nur Präsentationsmodell)
  -> AnalyzerShellApp (Midnight-/Metallic-UI)

review-state.json
  <-> vorhandener iy.review_state/v1-Vertrag (Status und Notiz, atomar, source-/scene-bound)

"In CS2 ansehen"
  -> bestehender Cs2ReviewCoordinator.open_scene(scene_id, tick)
  -> erneuter NetCon-/Demo-/Dateinamen-Preflight
  -> erlaubtes Scene-/Tick-Paar
  -> demo_gototick
```

`Cs2ReviewCoordinator` bleibt die einzige schreibende CS2-Grenze. Der Embedded Review darf keine beliebigen Konsolenbefehle und keine frei eingegebenen Ticks senden.

## UI-Vertrag

- Der Einstieg `Review anzeigen` wechselt innerhalb des bestehenden Analyzer-/Review-Reiters in den Embedded Review.
- Die Szenenliste zeigt Runde, belegten Timecode und objektive Anker.
- Das Detail zeigt Kontextfenster, exakten Tick, Marker, beteiligte Spielernamen und Rule-IDs.
- Review-Status und Notiz werden lokal gespeichert; fehlende oder fremde Scene-IDs und zu lange Notizen werden abgewiesen.
- `In CS2 ansehen` führt den bestehenden sicheren Coordinator-Pfad aus und zeigt Erfolg oder den konkreten Readiness-Fehler im selben Panel.
- `HTML-Export / Browser-Fallback` bleibt eine bewusst benannte Nebenfunktion. Er ist nicht mehr der normale Review-Einstieg.
- Der Rückweg `Analyse` bleibt im selben Fenster. Es wird kein helles oder produktfremdes Review-Fenster erzeugt.

## Fehlerverhalten

- CS2 nicht gestartet: `CS2/NetCon ist nicht erreichbar` mit Workshop-Tools-/Port-Hinweis.
- normales CS2 ohne NetCon: `CS2 läuft, aber NetCon ist nicht erreichbar` mit Workshop-Tools-/Port-Hinweis.
- NetCon erreichbar, keine Demo: CS2 erreichbar, aber keine aktive Demo-Wiedergabe.
- falsche Demo: erwarteter und aktiver Dateiname werden genannt; kein Tick wird gesendet.
- unbekannte oder veränderte Szene/Tick-Kombination: fail-closed; kein Tick wird gesendet.
- unbekannte Tickrate: kein Timecode wird erfunden; der exakte Tick bleibt sichtbar und verwendbar.
- beschädigter/fremder Review-State: Laden scheitert sichtbar; er wird nicht still überschrieben.

## COMPLETE-Kriterien

- Ein realer READY_FOR_REVIEW-Workflow öffnet ohne Browserwechsel im Analyzer.
- Mehrere Szenen sind navigierbar und zeigen Runde, Tick/Timecode, Spieler, Regeln und Marker.
- Status und Notiz überleben ein erneutes Öffnen und bleiben an Source-Hash und vollständige Scene-ID-Menge gebunden.
- Mehrere reale Szenen öffnen über denselben geprüften Coordinator am richtigen Tick in CS2.
- NetCon-, Demo- und Scene-/Tick-Fehler bleiben sichtbar und fail-closed.
- Externer Browser ist nur noch expliziter Export/Fallback.
- Vollständige Testsuite, Compile und `git diff --check` bestehen; reale UI-/CS2-Prüfung wird getrennt dokumentiert.
