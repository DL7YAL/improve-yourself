# Arbeitsauftrag: CS2 Benchmark Map visuell und technisch weiterbauen

## Ziel

Die bestehende Improve-Yourself-CS2-Benchmark-Map wird auf Basis des aktuellen
V1.2-Kandidaten weiterentwickelt. Der Auftrag ist ausdrücklich **kein
Neuaufbau**. Vorhandene Geometrie, Kameraroute, Übergänge, Marker,
Authoring-Helfer, Runtime-Referenzen und Provenienzdateien bleiben die
Ausgangsbasis und werden nur aufgrund konkreter visueller oder technischer
Evidenz geändert.

Das Ergebnis soll die drei vorhandenen Szenen im normalen CS2-Viewer klarer,
authentischer und als zusammenhängenden Benchmarklauf erkennbar machen:

1. `nuke_outside`;
2. `ancient_b`;
3. `inferno_apps_a`.

Die Benchmark Map bleibt ein eigenständiger CS2-Workshop-Bereich. Sie wird
nicht mit Optimizer, System Check, Analyzer, Replay, Azure, Accounts, Discord,
Steam-Identitäten oder einer öffentlichen Rangliste verbunden.

## Verbindliche Ausgangsbasis

Vor jeder Änderung sind live zu verifizieren:

- aktueller `origin/main`-HEAD;
- der neueste gepushte Benchmark-Branch und dessen HEAD;
- der V1.2-VMAP- und Controller-Stand aus
  `assets/maps/improve_yourself_benchmark/source-manifest.json`;
- `coordination/ACTIVE_WORK.md` und mögliche Pfadüberschneidungen;
- vorhandene uncommitted Arbeitsstände und lokale Addon-Abweichungen;
- `assets/maps/improve_yourself_benchmark/ASSET_RIGHTS.md`;
- beide vorhandenen Asset-Provenienzdateien;
- die fünf bestehenden Authoring-Helfer unter `tools/benchmark/`;
- `tests/test_benchmark_transitions.py` und
  `tests/test_benchmark_results.py`.

Falls der Benchmark-Stand noch nicht nach `main` integriert ist, ist ein neuer
dedizierter Branch vom exakten letzten gepushten Benchmark-HEAD anzulegen. Der
Stand darf nicht aus veralteten Arbeitskopien rekonstruiert werden. Empfohlener
Branchname: `codex/benchmark-map-visual-fidelity-v1`.

## Rechte- und Asset-Grenze

Die LOCKED-Regeln aus `ASSET_RIGHTS.md` gelten ohne Ausnahme:

- Originale Nuke-, Ancient- und Inferno-Bereiche sind visuelle, räumliche und
  Workload-Referenzen.
- Valve-/CS2-Assets dürfen nur als Referenzen auf Ressourcen verwendet werden,
  die über das installierte Spiel und die offiziellen Workshop Tools
  verfügbar sind.
- Keine VPK-Payload extrahieren.
- Keine Valve-Modelle, -Materialien, -Texturen, -Sounds oder sonstigen
  Binär-/Quelldateien in das Repository kopieren.
- Keine Valve-Assets in das eigenständige Improve-Yourself-Produkt oder ein
  separates Downloadpaket aufnehmen.
- Kein Eigentums-, Zertifizierungs-, Partnerschafts- oder
  Valve-Endorsement-Eindruck.
- Drittanbieter-Assets bleiben gesperrt, solange Rechte, Lizenz, Herkunft und
  vorgesehene Distribution nicht vollständig belegt sind.
- Unbekannte Herkunft ist fail-closed.

Improve-Yourself-eigene Geometrie, Marker, Schilder oder Materialien sind nur
zulässig, wenn sie wirklich projekt-eigenständig erstellt, im eigenen
Namespace abgelegt und als `IMPROVE_ORIGINAL` mit belastbarer Herkunft
dokumentiert werden.

## Unveränderliche Benchmark-Verträge

Ohne einen eigenen, ausdrücklich genehmigten Designwechsel dürfen nicht
verändert werden:

- Reihenfolge Nuke Outside → Ancient B → Inferno Apps/A;
- gemessene Gesamtdauer von 64 Sekunden;
- deterministischer Warmup- und Messpass;
- Smoke-Übergang von Nuke nach Ancient;
- Flash-Übergang von Ancient nach Inferno;
- fünf bestehende `CAPTURE_WINDOW`-Zeitpunkte bei 9, 27, 38, 48 und 53
  Sekunden;
- bestehende Trennung von `runtime_status` und `measurement_status`;
- keine zufälligen Assets, Spawnpunkte, Beleuchtungszustände oder
  Kameravarianten;
- keine Dummy-Performancewerte.

Kameraänderungen sind nur zulässig, wenn ein Marker-Capture belegt, dass ein
vorgesehenes Landmark nicht sichtbar oder schlecht komponiert ist. Zuerst
Komposition und Platzierung korrigieren; zusätzliche Effekte dürfen keine
fehlende Geometrie oder falsche Kameraposition verdecken.

## Arbeitsreihenfolge

### 1. Baseline im normalen Viewer sichern

Vor jeder Asset- oder VMAP-Änderung den vorhandenen V1.2-Kandidaten
hash-verifizieren, in das installierte Addon synchronisieren und im normalen
CS2-Viewer ausführen. Für den gemessenen Pass sind exakt die fünf vorhandenen
Marker aufzunehmen.

Für jeden Marker ist festzuhalten:

| Zeit | Szene | Muss sichtbar bzw. bewertbar sein |
| ---: | --- | --- |
| 9 s | Nuke Outside | Yard-Silhouette, Cooling Tower, Silo, Kran sowie Garage-/Secret-/Fahrzeugbezug in plausibler Größe und Tiefe |
| 27 s | Ancient B | B-Rampen-/Wasserbereich, erkennbare nasse Oberfläche beziehungsweise Reflexions-Workload und geschlossene Umgebung |
| 38 s | Ancient B | deutlich erkennbare Red-Room-Identität vor Beginn des Flash-Übergangs |
| 48 s | Inferno Apps/A | nachvollziehbare untere Treppenfolge, Geländer und räumlicher Apps-Einstieg |
| 53 s | Inferno Apps/A | Apps-Details wie Bögen, Türen, Putz-/Ziegelmaterialien und feste Props ohne schwebende oder fehlerhafte Elemente |

Zusätzlich sind beide Übergänge als kurze Sequenz zu prüfen. Ein einzelner
Marker-Screenshot belegt ein Landmark, aber noch keinen nahtlosen Übergang.

Falls die normale Viewer-Oberfläche oder ein belastbarer Capture nicht
verfügbar ist, endet dieser Schritt mit `BLOCKED`. Keine blinden
Asset-, Smoke-, Flash-, Kamera- oder Timing-Änderungen durchführen.

### 2. Lückenmatrix erstellen

Die Baseline pro Szene mit der jeweiligen installierten Originalkarte als
lokaler Referenz vergleichen. Keine Originalkarten-Assets exportieren oder in
den Arbeitsstand kopieren. Pro Befund dokumentieren:

- Marker und Szene;
- sichtbarer Ist-Zustand;
- erwartetes Landmark beziehungsweise Workload-Merkmal;
- Evidenzart und lokaler Capture-Pfad außerhalb des Repositorys;
- vermutete Ursache: Kamera, Transform, Material, Beleuchtung, Geometrie,
  Runtime-Referenz oder Prop-Platzierung;
- kleinste vorgeschlagene Korrektur;
- betroffene Repository-Dateien;
- benötigte Provenienzergänzung;
- Abnahmekriterium.

Nur belegte Lücken werden implementiert.

### 3. Nuke Outside abschließen

Nuke hat Vorrang, weil hierfür bereits ein eigener Anwendungsgate und eine
umfangreiche Runtime-Provenienz existieren. Bestehende Cooling-Tower-, Silo-,
Kran-, Truck-, Forklift-, Garage-, Secret- und Barrier-Referenzen zuerst auf
Auflösung, Transform, Bodenbezug, Sichtbarkeit und Kamerakomposition prüfen.

Neue Referenzen nur ergänzen, wenn die Baseline einen konkreten visuellen oder
Workload-Mangel belegt. Jede Referenz sofort in
`NUKE_OUTSIDE_ASSET_PROVENANCE.json` eintragen. Nach dem Nuke-Slice kompilieren
und Marker 9 sowie den Smoke-Eintritt erneut prüfen, bevor Ancient bearbeitet
wird.

### 4. Ancient B und Red Room abschließen

Danach ausschließlich die belegten Ancient-Lücken bearbeiten:

- Wasser-/Wet-Material und Reflexionswirkung;
- B-Rampen-/Stein-/Holz-Komposition;
- geschlossene räumliche Wirkung statt leerem Himmel;
- crate- und lighting-bezogene Workload;
- erkennbare Red-Room-Farb- und Raumidentität;
- stabiler Weg in den Flash-Übergang.

Alle neuen oder geänderten Referenzen in
`TRANSITION_WORLDS_ASSET_PROVENANCE.json` dokumentieren. Nach dem Ancient-Slice
Marker 27 und 38 sowie beide Seiten des Smoke- und Flash-Übergangs prüfen.

### 5. Inferno Apps/A abschließen

Erst danach die belegten Inferno-Lücken bearbeiten:

- untere Treppenfolge und Bodenbezug;
- Apps-Bogen, Türen, Geländer und Balkon-Silhouette;
- orange/gelbe Putz- und Ziegelwirkung;
- feste Barrel-, Kisten-, Planter- und Lampendetails;
- keine schwebenden, kollidierenden oder außerhalb der Kamera liegenden Props;
- räumlich plausibler Austritt aus dem Flash.

Alle Referenzen ebenfalls in
`TRANSITION_WORLDS_ASSET_PROVENANCE.json` pflegen. Danach Marker 48 und 53 und
den vollständigen Flash-Austritt prüfen.

### 6. Vollständigen Lauf abnehmen

Erst wenn alle drei Szenen einzeln bestehen, den kompletten Warmup- und
Messpass ausführen. Dabei müssen gelten:

- `READY` mit der erwarteten Benchmark-Version;
- vollständiger Warmup;
- vollständiger Messpass;
- alle fünf Marker einmal und in richtiger Reihenfolge;
- alle drei Szenenreports einmal und in richtiger Reihenfolge;
- keine `[IYBENCH] ERROR`-Meldung;
- `runtime_status=complete`;
- beide Übergänge ohne sichtbaren harten Szenenschnitt;
- alle fünf Landmark-Abnahmen sichtbar bestanden.

Runtime-Erfolg erzeugt weiterhin keine Performancewerte. FPS, 1%-Low und
Frametime dürfen nur mit einem separat belegten aktiven lokalen Collector in
`iy.cs2_benchmark_capture/v1` überführt werden.

## Technische Umsetzung

- Hammer bleibt Serialisierungsautorität für die versionierte binäre VMAP.
- Reproduzierbare Transformationen sind in den vorhandenen
  `tools/benchmark/`-Helfern zu erweitern, nicht in einem parallelen
  Authoring-System neu zu implementieren.
- Die Helfer müssen fail-closed und idempotenzgeschützt bleiben.
- Das installierte Addon und die Repository-Quelle nie parallel von Hand
  weiterentwickeln.
- `Sync-BenchmarkAddon.ps1` zunächst read-only einsetzen. `-Deploy` erst nach
  expliziter Autorisierung, geprüftem Ziel, Backup und Hashkontrolle.
- Keine kompilierten VPKs, Logs, Screenshots, Captures, Backups oder lokale
  absolute Pfade committen.
- Keine unkontrollierten Physikobjekte, Zufallseffekte oder zeitabhängige
  Lichtvarianten einführen.
- Kleine, szenenbezogene Änderungen durchführen und nach jedem Slice testen.

## Versions- und Ergebnisgrenze

Jede inhaltliche VMAP- oder Controller-Änderung erzeugt einen neuen
Benchmark-Kandidaten. Nach einer akzeptierten Änderung sind atomar zu
aktualisieren:

- Benchmark-Version im Controller;
- VMAP- und gegebenenfalls Controller-SHA-256 in `source-manifest.json`;
- die Hash-/Versionsbindung in `benchmark_results.py`;
- zugehörige Tests und Dokumentation.

Alte und neue Läufe dürfen wegen geänderter Szenengeometrie oder Workload nicht
in derselben lokalen Top 10 erscheinen. Der vorhandene Vergleichsschlüssel
muss sie automatisch trennen.

## Erwarteter Datei-Scope

Änderungen sind grundsätzlich auf diese Bereiche zu begrenzen:

- `assets/maps/improve_yourself_benchmark/maps/improve_yourself_benchmark.vmap`;
- `assets/maps/improve_yourself_benchmark/scripts/benchmark_controller.js`,
  nur wenn Version, Markerbindung oder belegte Kamera-Komposition es erfordert;
- `assets/maps/improve_yourself_benchmark/source-manifest.json`;
- die beiden vorhandenen Asset-Provenienzdateien;
- vorhandene relevante Helfer unter `tools/benchmark/`;
- `src/improve_yourself/benchmark_results.py` ausschließlich für die neue
  Versions-/Hashbindung;
- fokussierte Tests und Benchmark-Dokumentation;
- Coordination-Handoff.

Kein Eingriff in AnalyzerCore, AnalyzerDataHub, ReplayStore,
ReplayController, Tactical Replay, Optimizer, System Check oder Azure.

## Validierung nach jedem Szenen-Slice

1. Provenienz-JSON syntaktisch und semantisch prüfen.
2. Authoring-Helfer mit bestehenden Fail-closed-/Idempotenztests prüfen.
3. `tests/test_benchmark_transitions.py` ausführen.
4. `tests/test_benchmark_results.py` ausführen, sobald Version oder Hash
   betroffen ist.
5. Repository→Addon-Synchronisation zunächst read-only prüfen.
6. Zielbegrenztes Backup vor einem autorisierten Deploy nachweisen.
7. frischen Full Compile durchführen; Teilcompile allein reicht nicht.
8. normalen Viewer-Capture am betroffenen Marker und Übergang erzeugen.
9. VMAP-/Controller-Hashes erneut prüfen.
10. `compileall`, vollständige Testsuite und `git diff --check` ausführen.
11. Secret-, Privacy-, Rechte-, absolute-Pfade- und Artefaktprüfung ausführen.

Static Source, erfolgreicher Full Compile, Controller-Log, sichtbarer
Viewer-Pass und gültige Performance-Messung sind getrennte Evidenzstufen und
dürfen nicht miteinander gleichgesetzt werden.

## Definition of Done

Der Auftrag ist abgeschlossen, wenn:

- der vorhandene V1.2-Stand nachweislich als Basis verwendet wurde;
- alle Änderungen aus einer dokumentierten Baseline-Lücke folgen;
- Nuke, Ancient und Inferno jeweils ihre definierten Landmark-Gates im normalen
  Viewer sichtbar bestehen;
- Smoke- und Flash-Übergang als vollständige Sequenzen ohne harten Cut
  abgenommen sind;
- Route, Passdauer und Markerreihenfolge erhalten blieben;
- jede verwendete Referenz vollständig und korrekt klassifiziert ist;
- keine Valve-/Drittanbieter-Assets in das Repository kopiert wurden;
- Full Compile und Runtime-Lauf erfolgreich sind;
- fokussierte und vollständige Tests bestehen;
- Manifest, Versionsbindung und Ergebnisvergleich aktualisiert sind;
- keine echten Benchmarkwerte ohne belegten aktiven Collector behauptet
  werden;
- ein Abschlussbericht mit Dateien, Hashes, Evidenzstufen, offenen Punkten und
  nächstem Schritt vorliegt.

## Sofortiger Stop / BLOCKED

Arbeit sofort stoppen und `BLOCKED` melden, wenn:

- der aktuelle Benchmark-HEAD oder die lokale Addon-Quelle nicht eindeutig
  bestimmt werden kann;
- ein anderer aktiver Agent dieselben Pfade besitzt;
- eine normale Viewer-Abnahme nicht möglich ist;
- der Ursprung oder die Nutzungsgrenze eines Assets unklar ist;
- die Korrektur VPK-Extraktion oder Repository-Kopien von Valve-Assets
  erfordern würde;
- eine funktionierende Route nur durch unkontrollierte Timing- oder
  Effektänderungen erhalten werden könnte;
- Full Compile oder Runtime-Validierung nicht ausgeführt werden kann;
- echte Performanceaussagen ohne aktiven Collector verlangt würden.

## Abschlussbericht

Der Abschluss muss enthalten:

- `STATUS: PASS` oder `BLOCKED`;
- Branch, Base HEAD, Final HEAD und Commits;
- bearbeitete Szene und zugehörige Baseline-Befunde;
- alle geänderten und neu eingeführten Asset-Referenzen;
- Provenienz- und Rechteklassifizierung;
- VMAP-/Controller-Version und SHA-256;
- Ergebnisse von Full Compile, Controller-Log und normalem Viewer-Capture;
- Performance-Evidenz separat oder ausdrücklich `UNVERIFIED`;
- fokussierte und vollständige Testergebnisse;
- ausdrücklich nicht geänderte Produktbereiche;
- offene Risiken und sinnvollster nächster Arbeitsschritt;
- `Azure handoff required: NO`, solange keine neue ausdrücklich genehmigte
  Azure-Anforderung entsteht.
