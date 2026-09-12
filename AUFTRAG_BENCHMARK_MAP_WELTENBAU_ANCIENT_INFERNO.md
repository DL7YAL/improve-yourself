# Arbeitsauftrag: Benchmark-Map – Marken-Startbereich, Ancient B und Inferno Apps/A

Status: **FREIGEGEBEN**
Freigabedatum: **11. September 2026**

## Repository-Nachtrag vom 12. September 2026

Dieser Auftrag wurde aus der vom Auftraggeber bereitgestellten Fassung in das
Repository übernommen. Ein privater absoluter Pfad zur Markenreferenz wurde
entsprechend der eigenen Asset- und Datenschutzgrenze nicht übernommen.

Die ursprüngliche Vorgabe „kein PR, kein Merge, main unverändert“ wurde später
durch die ausdrückliche Freigabe des Auftraggebers für den Source-Checkpoint
über PR #43 überholt. Der Merge-Commit auf main ist
`b56aa34`. Diese spätere Freigabe ändert keine visuellen oder technischen
Abnahmekriterien dieses Auftrags.

## Ausgangslage

Der zuletzt abgeschlossene Stand ist:

- Repository: `DL7YAL/improve-yourself`
- Ausgangsbranch: `codex/benchmark-map-visual-fidelity-v1`
- Verbindlicher Ausgangs-Commit: `559b67315634cdf3a6c77a698f84c128aec070a0`
- Benchmark-Version: `iy-benchmark/v1.2-candidate.2`
- Nuke Outside / Yard ist als erster Weltabschnitt sichtbar geprüft.
- Der bestehende Benchmark-Kameralauf, seine Route, Marker, Capture-Zeiten und Übergänge dienen vorerst ausschließlich als Arbeitsreferenz.
- Verbindliche Markenreferenz: vom Auftraggeber bereitgestellte Darstellung; der frühere private absolute Dateipfad wird bewusst nicht versioniert.

Die nächsten Schritte sind der Bau beziehungsweise die visuelle Ausarbeitung der noch vorgesehenen Weltabschnitte einschließlich eines gebrandeten Startbereichs. Eine endgültige Kameraabstimmung erfolgt erst, wenn alle Welten fertiggestellt sind.

## Ziel

Erstelle und vervollständige die folgenden Benchmark-Weltabschnitte mit nachvollziehbarer räumlicher Struktur und ausreichender visueller Wiedererkennbarkeit:

1. Gebrandeter Startbereich
   - industrieller, dunkler Kinosaal entsprechend der Markenreferenz
   - großformatige Leinwand mit `IMPROVE BENCHMARK` und `www.improve-yourself.com`
   - feste Sitzreihen mit allen bereits für die Benchmark-Map vorgesehenen Bots als stehendes, jubelndes Publikum
   - vorgesehene Nutzerperspektive hinter den Bots mit Blick über das Publikum zur Leinwand
2. Ancient B
   - Water / Reflection im Bereich des Markers `ancient_b/water_reflection@27`
   - Red Room im Bereich des Markers `ancient_b/red_room@38`
3. Inferno Apps/A
   - Stairs im Bereich des Markers `inferno_apps_a/stairs@48`
   - Apps Details im Bereich des Markers `inferno_apps_a/apps_details@53`

Die Marker bezeichnen die fachlich relevanten Zielbereiche. Sie sind keine Aufforderung, die Kamera jetzt auf diese Bereiche neu auszurichten.

## Verbindliche Arbeitsreihenfolge

1. Sichere und prüfe den Ausgangsstand `559b67315634cdf3a6c77a698f84c128aec070a0`.
2. Arbeite in einem neuen, eindeutig benannten Branch auf Basis dieses Commits, zum Beispiel `codex/benchmark-map-world-sections-v1`.
3. Untersuche die vorhandene VMAP, die bereits genutzten Assets und die Provenienzdateien.
4. Setze den gebrandeten Kino-Startbereich einschließlich der vorhandenen Bots als Publikum um, ohne Route oder Laufzeit zu verändern.
5. Fertige danach Ancient B vollständig aus.
6. Fertige anschließend Inferno Apps/A vollständig aus.
7. Prüfe den Startbereich und beide Map-Abschnitte im tatsächlichen CS2-In-Game-Viewer des installierten Workshop-Addons.
8. Nutze den bestehenden Kameralauf nur, um den Weltenbau zu kontrollieren. Dokumentiere Sichtprobleme für den späteren Kameraauftrag, ohne sie in diesem Auftrag durch Kameraänderungen zu lösen.
9. Führe nach den Weltänderungen einen vollständigen Compile- und Runtime-Kontrolllauf aus.
10. Committe und pushe ausschließlich den autorisierten Arbeitsbranch. Erstelle keinen PR und führe keinen Merge durch.

## Marke und Kino-Startbereich

Die beigefügte Darstellung legt die visuelle Identität der Benchmark-Map fest. Sie ist als verbindliche Art-Direction-Referenz zu verwenden, nicht als ungeprüfte niedrig aufgelöste Produktionstextur.

Der Startbereich ist als kleiner industrieller Kinosaal beziehungsweise Benchmark-Vorführraum zu gestalten. Er soll folgende Merkmale übernehmen:

- Wortmarke `IMPROVE` in Weiß,
- Bezeichnung `BENCHMARK` in Cyan/Blau,
- stilisierte cyanfarbene Performance-Balken mit ansteigender Linie,
- URL `www.improve-yourself.com` als gut lesbare sekundäre Zeile auf der Leinwand,
- dunkles Anthrazit bis Schwarz als Grundfläche,
- gezielte cyanblaue Akzente,
- industrieller Saal mit Metall, Beton und zurückhaltender warmer Umgebungsbeleuchtung,
- gestaffelte Sitzreihen mit klarer Sichtachse zur Leinwand und ausreichend Standfläche für das Publikum,
- großformatige, glaubwürdig in die Frontarchitektur eingelassene Kino-Leinwand,
- klare Lesbarkeit ohne übermäßiges Leuchten, Bloom oder Whiteout.

Das Logo beziehungsweise die Displaygrafik ist für die reale Zielauflösung sauber neu aufzubauen. Die Leinwand zeigt das Logo als primären Inhalt und darunter beziehungsweise in einer klar getrennten sekundären Zone die exakte URL `www.improve-yourself.com`. Seitenverhältnis, Schutzraum, Kontrast sowie die Lesbarkeit von Logo und URL sind im In-Game-Einsatz zu prüfen. Das Nutzerbild ist in der Provenienz als bereitgestellte Markenreferenz zu dokumentieren; daraus abgeleitete neue Texturen oder Materialien benötigen eigene nachvollziehbare Quelldateien und Hashes.

### Vorgesehene Nutzerperspektive

Der Kinosaal ist für eine Perspektive aus dem hinteren Zuschauerbereich zu komponieren. Der Nutzer blickt von hinter den Bots in Richtung Leinwand. Im Bild müssen gleichzeitig erkennbar sein:

- Rücken beziehungsweise Silhouetten mehrerer jubelnder Bots,
- die Staffelung der Sitzreihen,
- eine freie zentrale oder leicht versetzte Sichtachse,
- das vollständige `IMPROVE BENCHMARK`-Logo,
- die vollständig lesbare URL `www.improve-yourself.com`,
- genug seitliche Raumarchitektur, damit der Ort als Kinosaal wahrgenommen wird.

Kein Bot darf Logo oder URL wesentlich verdecken. Die Leinwand darf weder durch Blickwinkel noch durch perspektivische Verzerrung unlesbar werden. Die Komposition soll den Nutzer als Teil des Publikums wirken lassen und zugleich die Leinwand als klaren visuellen Fokus behalten.

Diese Perspektive ist in diesem Weltenbauauftrag durch freie In-Game-Inspektion zu prüfen und als Zielposition für den späteren Kameraauftrag zu dokumentieren. Controller, gespeicherte Kamerapositionen, Kameraziele und Zeiten bleiben weiterhin unverändert.

Der Startbereich darf die bestehende Route, Spawn-/Startlogik, Marker, Zeiten oder Kameradaten nicht verändern. Wenn die Bestandskamera Leinwand oder Publikum nicht ideal zeigt, wird die nötige Einstellung ausschließlich für den späteren Kameraauftrag dokumentiert.

### Bots als Kinopublikum

Alle Bots, die im bestehenden Benchmark-Map-Stand bereits vorgesehen sind, sollen stehend an den Sitzreihen des Kinosaals platziert werden und zur Leinwand hin jubeln. Sie werden Reihe für Reihe in einer festen Folge angeordnet, beginnend vorne links und fortlaufend bis hinten rechts. Es dürfen allein für die Optik keine zusätzlichen aktiven Bots erzeugt werden.

Die Umsetzung muss deterministisch sein:

- feste Stand- und Blickposition je Bot an den Sitzreihen,
- identische Bot-Anzahl, Teams, Ausrüstung und Reihenfolge in jedem Lauf,
- keine freie Bewegung, Wegfindung, Zielsuche oder zufällige Reaktion,
- keine Kollision, kein Schaden und keine Interaktion mit Kamera oder Benchmark-Ablauf,
- kein wechselnder Spawnzustand zwischen Warmup und Messpass,
- keine unbeabsichtigte Fortsetzung aktiver Bot-KI außerhalb des Kinosaals,
- fest definierte, wiederholbare Jubelanimationen ohne zufällige Auswahl oder Laufzeitabhängigkeit.

Bevor die endgültige Variante gebaut wird, ist ein kleiner In-Engine-Prototyp mit einem Bot zu prüfen. Benötigt wird eine stabile stehende Jubelanimation beziehungsweise Jubelpose. Die Animationen dürfen pro Bot mit festen, reproduzierbaren Phasen versetzt werden, damit das Publikum lebendig wirkt, ohne Zufall einzuführen. Fehlerhafte Skelettposen, schwebende Modelle, Überschneidungen mit Sitzen oder erzwungene Animationen mit Laufzeitfehlern sind nicht akzeptabel.

Die Bots bleiben Teil der gerenderten Startszene, dürfen aber die nachfolgende Benchmark-Messung nicht durch variable KI- oder Simulationslast beeinflussen. Im Abschlussbericht ist deshalb nachzuweisen, welche Bot-Logik während Warmup und Messpass aktiv ist und dass mehrere Kontrollläufe denselben Zustand erzeugen.

## Gestalterische Anforderungen

Die Abschnitte müssen nicht die vollständigen Originalmaps nachbauen. Benötigt werden gezielt komponierte, räumlich plausible Benchmark-Welten entlang der vorgesehenen Route.

Für jeden Zielbereich müssen erkennbar sein:

- charakteristische Silhouette und Raumaufteilung,
- eindeutige Landmarken,
- plausible Größenverhältnisse,
- Boden-, Wand- und Höhenbezug,
- räumliche Tiefe,
- passende Material- und Farbwirkung,
- ausreichend Details für einen sinnvollen Grafik- und Performancevergleich,
- saubere Übergänge innerhalb des jeweiligen Weltabschnitts.

Ancient B soll insbesondere Wasserfläche beziehungsweise Reflexionswirkung und den Red-Room-Charakter zuverlässig abbilden. Inferno Apps/A soll Treppenführung, Innenraumstruktur und die charakteristischen Apps-Details zuverlässig abbilden.

## Strikte Scope-Grenzen

In diesem Auftrag nicht ändern:

- Kamerapositionen, Kameraziele oder Kamerafahrten,
- Markerzeiten und Capture-Zeiten,
- Gesamtdauer, Warmup oder Messpass,
- Route und Reihenfolge der Szenen,
- Smoke-Übergang Nuke → Ancient,
- Flash-Übergang Ancient → Inferno,
- Nuke Outside / Yard, sofern keine zwingende technische Reparatur durch den gemeinsamen VMAP-Aufbau erforderlich ist,
- Benchmark-Ergebnisvertrag und Performance-Status,
- Frame-Collector, FPS-, 1%-Low- oder Frametime-Auswertung,
- AnalyzerCore, AnalyzerDataHub, `iy.replay/v2`, ReplayStore, ReplayController, Tactical Replay, Optimizer, System Check oder Azure,
- 2D-Map-Overview-Daten,
- kanonische Produktkomponenten oder Datenautoritäten.

Falls eine gemeinsame VMAP-Änderung technisch auch Nuke berührt, muss sie minimal bleiben, separat begründet und durch einen sichtbaren Nuke-Regressionscheck abgesichert werden.

## Asset- und Provenienzregeln

- Bevorzuge bereits im Projekt vorhandene und dokumentierte Assets.
- Ergänze nur Assets, die für den Marken-Startbereich und die beiden Zielwelten erforderlich sind.
- Dokumentiere Quelle, Lizenz beziehungsweise Herkunft und Einsatz jedes neu aufgenommenen Assets in der vorgesehenen Provenienzstruktur.
- Kopiere keine Valve-Dateien unkontrolliert in das Repository.
- Extrahiere keine zusätzlichen VPK-Inhalte, sofern dies nicht ausdrücklich separat autorisiert wird.
- Vermeide absolute private Pfade, temporäre Build-Dateien und lokale Runtime-Artefakte im Commit.

## Umgang mit bestehendem Arbeitsstand

- Prüfe vor Änderungen Branch, HEAD, Status und vorhandene Worktrees.
- Bestehende fremde oder ältere Dirty-Worktrees dürfen nicht bereinigt, zurückgesetzt oder überschrieben werden.
- Sichere jeden bereits vorhandenen, zum Auftrag gehörenden lokalen Diff vor einer Weiterbearbeitung reproduzierbar als Patch.
- Kein `reset --hard`, `clean`, Stash oder Checkout-Overwrite zur Beseitigung fremder Änderungen.
- Repository-Quelle und installiertes Addon dürfen nicht parallel manuell verändert werden. Verwende für Deploy und Read-only-Abgleich den bestehenden Sync-Workflow.

## Sichtprüfung

Erzeuge für jeden Zielbereich mindestens einen post-compile In-Game-Nachweis:

- Kino-Startbereich – Sicht von hinter den Bots über das jubelnde Publikum auf Logo und URL der Leinwand,
- Ancient B – Water / Reflection,
- Ancient B – Red Room,
- Inferno Apps/A – Stairs,
- Inferno Apps/A – Apps Details.

Die Aufnahmen dienen in diesem Auftrag der Beurteilung der gebauten Welt. Eine ungünstige Bestandskamera ist als späterer Kamera-Arbeitspunkt zu protokollieren und allein kein Grund, den Kameralauf jetzt zu verändern.

Für jeden Bereich dokumentieren:

- sichtbare Landmarken,
- räumliche Lesbarkeit,
- Material- und Lichtwirkung,
- offensichtliche Geometrie-, Clipping- oder Missing-Asset-Fehler,
- Einschränkungen durch die bestehende Kamera,
- Ergebnis `WORLD PASS`, `WORLD NEEDS WORK` oder `BLOCKED`.

Ein `WORLD PASS` darf trotz suboptimaler Bestandskamera vergeben werden, wenn die Welt durch ergänzende freie In-Game-Inspektion vollständig und belastbar geprüft wurde. Diese ergänzende Inspektion darf den gespeicherten Benchmark-Kameralauf nicht verändern.

Für den Kino-Startbereich sind zusätzlich mindestens zwei identische Neustarts zu prüfen. Bot-Anzahl, Reihenfolge, Standpositionen, Blickrichtung und Jubelanimation müssen reproduzierbar sein; es dürfen keine Nav-, AI-, Animations- oder Scriptfehler auftreten.

Zusätzlich ist eine freie In-Game-Aufnahme aus der vorgesehenen späteren Nutzerperspektive zu erstellen. Logo und URL müssen bei der tatsächlichen Zielauflösung ohne Vergrößerung lesbar sein. Die dafür verwendete freie Inspektionsposition ist als Kamera-Hinweis zu dokumentieren, aber nicht in den Benchmark-Controller zu übernehmen.

## Technische Validierung

Mindestens erforderlich:

- VMAP- und Ressourcenvalidierung,
- Provenienzprüfung,
- Controller- und Manifest-Konsistenzprüfung,
- vollständiger Resource-/Map-Compile ohne Fehler,
- Deployment über den vorhandenen Sync-Workflow,
- abschließender read-only Sync ohne Drift,
- vollständiger Warmup- und Messpass,
- alle Marker und Szenenreports genau einmal und in der vorgesehenen Reihenfolge,
- keine `[IYBENCH] ERROR`-Einträge,
- bestehende gezielte Benchmark-Tests,
- vollständige Python-Testsuite,
- `compileall`, `pip check` und `git diff --check`,
- sauberer finaler Worktree,
- keine ungetrackten Build- oder Runtime-Artefakte.

Der Runtime-Abschluss bleibt von der Performance-Messung getrennt. Ohne aktiven Frame-Collector muss `measurement_status=unverified` unverändert bleiben.

## Abnahmekriterien

Der Auftrag ist abgeschlossen, wenn:

- der Kino-Startbereich die definierte `IMPROVE BENCHMARK`-Marke sauber, lesbar und räumlich plausibel integriert,
- die Leinwand die exakte URL `www.improve-yourself.com` gut lesbar zeigt,
- die vorgesehene Perspektive hinter den Bots eine freie Sicht auf Logo und URL bietet,
- alle vorhandenen Bots reproduzierbar und in fester Folge stehend an den Sitzreihen platziert sind und glaubwürdig zur Leinwand jubeln,
- die Bots keine variable KI-, Bewegungs- oder Simulationslast in den Benchmarklauf einbringen,
- Ancient B und Inferno Apps/A als Benchmark-Weltabschnitte vollständig gebaut sind,
- der Kino-Startbereich und alle vier Map-Zielbereiche durch post-compile In-Game-Evidenz geprüft wurden,
- keine erforderliche Weltkorrektur mehr offen ist,
- sämtliche technischen Prüfungen bestanden sind,
- der bestehende Kameralauf unverändert geblieben ist,
- Kameraeinschränkungen als Input für einen separaten Folgeauftrag dokumentiert sind,
- keine Performancebehauptung ohne aktiven Collector erzeugt wurde,
- ausschließlich der neue Arbeitsbranch committed und gepusht wurde,
- weder PR noch Merge erstellt wurde und `main` unverändert blieb.

## Erwarteter Abschlussbericht

Der Abschlussbericht muss enthalten:

- Status `PASS`, `PARTIAL` oder `BLOCKED`,
- Ausgangs- und Final-Commit,
- Branch und Commitliste,
- exakte Liste geänderter Dateien,
- Beschreibung der gebauten Geometrie, Assets, Materialien und Beleuchtung je Weltabschnitt,
- Asset-Provenienz und neue Hashbindungen,
- Compile-, Test-, Sync- und Runtime-Ergebnisse,
- In-Game-Nachweise mit Zeit-/Statusbezug und SHA-256,
- Einzelbefund für den Kino-Startbereich und alle vier Map-Zielbereiche,
- bestätigte Nichtänderung des Kameralaufs,
- Liste der später erforderlichen Kameraanpassungen,
- ehrlicher Performance-Status,
- offene Risiken und klar empfohlener nächster Auftrag.

Nach erfolgreichem Abschluss lautet der nächste separate Auftrag: den Startbereich und den gesamten Kameralauf über Nuke Outside, Ancient B und Inferno Apps/A anhand der fertiggestellten Welten neu komponieren und sichtbar abnehmen. Erst danach folgt die Performance-Messung mit aktivem Frame-Collector.

## Nutzungslimit-Checkpoint und Übergabe

Bevor das verfügbare Nutzungslimit erschöpft ist, muss jeder belastbare
Zwischenstand auf dem Arbeitsbranch committed und zu GitHub gepusht werden.
Unfertige Runtime- oder Build-Artefakte dürfen nicht committed werden. Ein
Handoff im Repository muss Ausgangsstand, Hashes, erledigte Prüfungen, offene
Gates, den genauen Fortsetzungspunkt und die nächsten ausführbaren Schritte
enthalten, sodass ein nachfolgender Bearbeiter ohne erneute Bestandsaufnahme
fortsetzen kann.

Checkpoint vom 11. September 2026:

- Branch: `codex/benchmark-map-world-sections-v1`
- Basis: `559b67315634cdf3a6c77a698f84c128aec070a0`
- Kino-, Ancient- und Inferno-Weltenbau in der VMAP umgesetzt;
- Controller und bestehender Kameralauf byte-identisch belassen;
- Full Compile: `59 compiled, 0 failed, 0 skipped`;
- Prüfungen: 17/17 fokussierte Tests und 457/457 vollständige Python-Suite
  bestanden, `compileall`, `pip check` und `git diff --check` grün;
- offene Abnahme: frische In-Game-Aufnahmen und vollständiger Runtime-Lauf;
- ausführliche Fortsetzung:
  `docs/BENCHMARK_MAP_WORLD_SECTIONS_HANDOFF.md` im Arbeitsbranch.
