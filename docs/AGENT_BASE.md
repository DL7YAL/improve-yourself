# Improve Yourself — Shared Agent Base

> **Current visual authority — 2026-09-05:** Canva design `DAHUBn5D2aM`
> (`Versuch.nr1`), revision 25, is the sole binding UI reference. All earlier
> PDF, UI Reference Pack and Optimizer `MASTER` statements later in this file
> are historical snapshots and have zero implementation priority. Functional
> and safety contracts in current code remain binding over illustrative Canva
> values.

## Zweck

Dieses Repository ist die gemeinsame Source of Truth für alle Arbeitsumgebungen des Projekts. Roadrunner of Lightning Detonation Aurel (kurz: Aurel) und Codex / The Beast dürfen in getrennten Sessions und Tools arbeiten, müssen aber Entscheidungen, Übergaben und relevante Arbeitsstände hier synchronisieren.

## Synchronisierter Basisstand — 2026-08-21

Dieser Abschnitt ist der gemeinsame Einstiegspunkt für den aktuell gepushten Arbeitsstand. Die operative Detailwahrheit bleibt `coordination/CURRENT.md`; vollständige technische Verlaufsnachweise stehen in `coordination/agents/codex.md`. Der Stand liegt auf `dev/v1-foundation`; `main` wurde nicht verändert und bleibt einer ausdrücklichen Review-/Merge-Entscheidung vorbehalten.

### Versionierter Stand und Qualitätsgate

- Branch: `dev/v1-foundation`
- Letzter vor dieser Basissynchronisierung gepushter Implementierungscommit: `4d4c161cf3dc10a6202253a7ee3ebf49fe31ecf3`
- Reproduzierbares Gate: 119/119 Tests, Abhängigkeitsprüfung, acht öffentliche CLI-Smokes, Python-Compile und `git diff --check` PASS.
- Öffentliche Einstiege: `iy-analyze`, `iy-system-check`, `iy-workflow`, `iy-replay-viewer`, `iy-review-server`, `iy-analysis-flow`, `iy-demo-workflow`, `iy-analyzer-shell`.
- Generierte Demo-, Replay-, Ergebnis- und lokale Runtime-Dateien bleiben ignoriert und werden nicht als personenbezogene oder maschinenspezifische Repository-Artefakte gepusht.

### Analyzer und echter End-to-End-Nachweis

- Die einzige Replay-Wahrheit ist `iy.replay/v2`. Analyzer, Analysefluss, 2D Tactical Replay und 3D/POV dürfen Demo-Zustand nicht unabhängig neu interpretieren.
- Verbindlicher Fluss: Demo -> Awpy-Parser -> benannte Teams/Spieler -> Full Demo oder Player Select -> neutrales Analyseprofil -> objektive Regelkombinationen -> zusammengeführte Szenen -> Timeline/JSON/HTML -> CS2-Review-Tick.
- V1-Szenenanker sind objektiv belegbare Kills, Headshots, Wallbangs, Smoke-Kills, Entry-Kills und begrenzte Multi-Kill-Kombinationen. Unzureichend belegte Trade-/Sound-/Informationsregeln bleiben deaktiviert; es gibt keine Suspect-, ML- oder Cheat-Klassifikation.
- Reale Runtime-Evidenz: `fut-vs-mouz-m2-ancient.dem`, SHA-256 `c183dd61fc6a619f7af435d45eab374cd6f0097a7bd0da779971b15ef6746f7f`, Ancient, 18 Runden, 10 benannte Spieler, 235 Marker/Regelresultate und 54 zusammengeführte Szenen. Der erzeugte erste Szenentick 3654 wurde im installierten CS2 sichtbar angesprungen und stabil pausiert.
- Die ältere reale Mirage-Demo bleibt gültige Awpy-/Analyse-Evidenz, ist aber keine CS2-Runtime-Abnahme, weil ihre normale Wiedergabe reproduzierbar mit `Failed to parse message` endet.

### Lokale Analyzer-Shell und Review-Sicherheit

- Die Tk-Shell ist ein dünner Adapter über `run_demo_workflow`, `rerender_demo_workflow` und den kanonischen ReplayStore; sie besitzt keinen zweiten Parser und keine zweite Regel-/Szenenlogik.
- Sie bietet reale `.dem`/`.dem.zst`-Auswahl, benannte CT-/T-Line-ups, Full Demo, deduplizierten Player Select, Dropdown + Add Player sowie CT/T/Reset.
- `Vorhandene Analyse öffnen` akzeptiert nur ein ausdrücklich gewähltes `demo-workflow.json`. Schema, Status, Real-/Local-/No-Fake-Policy, 64-stelliger Source-Hash, relative eingeschlossene Pflichtartefakte, Analysis/Replay/Flow/Timeline-Hashkonsistenz, Auswahl/Zähler und sämtliche Replay-Chunk-Hashes werden fail-closed geprüft. Es gibt keinen Ordnerscan und kein Recent-Autoselect.
- `Quelldemo zuordnen` akzeptiert nur eine ausdrücklich gewählte Demo mit exakt passendem SHA-256. Erst dann wird atomar ausschließlich ihr Basename gespeichert; kein privater absoluter Pfad, kein Kopieren, Umbenennen, Suchen oder Reparse.
- Die vollständige Integrität wird unmittelbar vor jedem Auswahl-Rerender und vor jeder CS2-Koordinator-Erstellung erneut geprüft. Nachträgliche Änderungen blockieren den Downstream-Aufruf und löschen alte Readiness.
- CS2-Review ist loopback-only und fail-closed: Netcon muss auf `127.0.0.1:21212` erreichbar sein, CS2 muss `[DEMO]` melden und `demo_info` muss den exakt erwarteten Dateinamen ausweisen. Browserdaten dürfen nur eine kanonisch erlaubte Scene-ID/Tick-Kombination auslösen; der einzige schreibende CS2-Befehl ist der daraus erzeugte `demo_gototick`.

### Weitere V1-Komponenten

- 2D Tactical Replay: Der manuelle Sichtcheck aller sieben realen Mirage-Szenen bestand; Positionen und Blickrichtungen waren plausibel, ohne erkennbare Spiegelung, Fehlrotation, starke Verschiebung oder falsche Skalierung.
- 3D/POV: Gemeinsamer ReplayFrame-Vertrag, ReplayStore/Controller, First-Person POV, feste Third-Person-Analysekamera, Player-Renderzustand, kamera-relative Waffen-Proxys, Sichtlinienauswertung, Smoke-Evidenzgate und Einweg-Renderer-Session sind implementiert und getestet. Produkt-UI, finale Assetqualität und vollständige Runtime-Integration bleiben getrennte Folgearbeit.
- System Check: read-only Baseline für Windows, CPU, RAM, Mainboard/BIOS, GPU-Treiber, Refresh Rate, Secure Boot und TPM. Nicht belegbare Werte bleiben REVIEW; keine automatischen Firmware-, Treiber-, Registry- oder Windows-Änderungen.
- Lokaler V1-Ablauf: System Check, Analyse, Replay, selbsttragender Viewer, lokaler Review-Server und hashgebundene Manifeste sind reproduzierbar verbunden. Reviewzustände werden loopback-only, origin-/größen-/szenen-/hashgeprüft und atomar gespeichert.

### Benchmark, Blocker und Grenzen

- Nuke-Graybox-/frühe-Kamera-Reparaturen und der zielbegrenzte, backup-/hashgeprüfte Benchmark-Sync sind versioniert und abgeschlossen.
- `check_raytracing_support.vrad3` ist ein lokales, von den installierten Workshop Tools/Hammer bereitgestelltes VRAD-Artefakt. Es wird nicht in GitHub kopiert oder versioniert. Eine fehlende Datei vor dem Hammer-Start ist kein Hardware- oder SDK-Blocker; der begrenzte lokale Ablauf ist in `assets/maps/improve_yourself_benchmark/HAMMER_RAYTRACING_PREFLIGHT.md` festgehalten.
- Azure, Foundry, Cloud-CI und MCP ignorieren diesen lokalen Hammer-Preflight vollständig. Erst bei einer ausdrücklich wiederaufgenommenen Benchmark-Arbeit wird nach Hammer-Initialisierung ein lokaler VRAD-Nachweis erfasst; daraus folgen keine Treiber-, Registry-, Adrenalin-, Controller-, Szenengeometrie-, Smoke- oder Benchmark-Runtime-Änderungen ohne neuen Auftrag.
- Nicht in diesen V1-Stand gezogen werden OBS, Clip-/Videoeditor-Workflows, automatisches Rendering, Windowed-/Borderless-Zwang, ML-/Anti-Cheat-Klassifikation, vollständige Standard-Angle-Erkennung sowie Optimizer-/System-Check-Arbeit innerhalb des Replay-Strangs.

### Aktuell nächster freigegebener Engineering-Schritt

Der zusammenhängende Stand `Improve Yourself – Experimental` verbindet objektiven Demo-Preflight, Auswahl, lokale Profile/Rules, zusammengeführte Szenen, neutrales Embedded Review, Tactical Replay, Report und CS2-Tick. `docs/design/Improve_Yourself_Concept_Preview_Discord_Q98.pdf` ist die verbindliche visuelle und strukturelle Master-Referenz; der aktuelle Branch bleibt die funktionale Wahrheit. Analyzer-Einstieg, Review und Tactical Replay bilden die Master-Komposition nun mit kompakter Sidebar, mehrspaltigen Panels, Szenenrails, dominanter Kartenfläche und kontextnahen Aktionen erkennbar ab. Variant-3-Wortmarke und Compact-Icon bleiben kanonisch. Review und Tactical Replay verwenden denselben validierten Szenenkontext und dieselbe Replay-Wahrheit; der HTML-Viewer ist nur Export/Fallback. Nicht belegte Radar-, Utility-, Score- oder Eventdaten wurden nicht erfunden. System Check/Optimizer bleibt read-only und teilreferenziert; keine Optimizer-Funktion wurde in Replay-Arbeit gezogen. Status: `WAITING_FOR_TRISTAN`; nächster Schritt ist Tristans Abnahme des gepushten Portable-Flows. `main` bleibt ohne ausdrückliche Review-/Merge-Freigabe unverändert.

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

## Foundry-Regel — Verantwortung und effiziente Worker-Abnahme

Für jede an ein Mainzelmännchen bzw. einen Worker delegierte Aufgabe trägt das zuständige Brain — aktuell The Beast — weiterhin die Verantwortung für das finale Ergebnis.

**Abnahme bedeutet ausdrücklich nicht, dass The Beast die vollständige Arbeit des Workers erneut durchführen muss.** The Beast wählt die kleinste ausreichend belastbare Prüfmethode, die Art und Risiko der Aufgabe angemessen ist.

Zulässige Prüfmethoden sind insbesondere:

- automatisierte Tests, Validatoren und Invarianten;
- Prüfung von Diff, Logs, Input/Output und Artefakten;
- gezielte Stichproben;
- Plausibilitäts- und Konsistenzprüfungen;
- Hashes und reproduzierbare Nachweise;
- bei erhöhtem Risiko eine unabhängige Gegenprüfung, gegebenenfalls durch einen anderen Worker;
- vollständige manuelle Wiederholung nur dann, wenn Risiko, fehlende Evidenz oder Auffälligkeiten dies tatsächlich erforderlich machen.

Worker sollen ihre Ergebnisse grundsätzlich mit prüfbarer Evidenz zurückgeben und nicht lediglich `DONE` melden.

Zielprinzip:

**Worker erledigt die Arbeit → Worker liefert Evidenz → Beast prüft effizient → Beast übernimmt Verantwortung und erteilt die fachliche Abnahme.**

Nicht:

**Worker erledigt die Arbeit → Beast erledigt dieselbe Arbeit noch einmal.**

Die Prüftiefe darf mit wachsender nachgewiesener Zuverlässigkeit eines Workers angepasst werden. Auffälligkeiten, neue Aufgabentypen und risikoreiche Änderungen erhöhen die Prüftiefe wieder.

Ziel ist ein geringerer Prüfaufwand bei weiterhin ausreichend belastbarer Qualitätssicherung. Effizienz hebt die Verantwortlichkeit des Brains niemals auf.

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
6. **Qualität bleibt Pflicht.** Ein günstigeres Modell ändert nichts an der Foundry-Regel: delegierte oder erzeugte Ergebnisse müssen vom zuständigen Brain ausreichend geprüft und ausdrücklich abgenommen werden. Die Prüfung soll dabei gemäß der Foundry-Regel effizient und risikoadäquat erfolgen, nicht durch pauschale vollständige Wiederholung der Worker-Arbeit.

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

## Aktueller Experimental-Abnahmestand (2026-08-21)

Der Analyzer-/Review-/Tactical-Slice bleibt bis zur visuellen Nutzerabnahme auf `WAITING_FOR_TRISTAN`. Der aktuelle Branch `dev/v1-foundation` enthält den gezielten Visual-Master-Conformance-Pass innerhalb der bestehenden nativen Desktop-Shell: Midnight-/Metallic-Flächen, Panelhierarchie, Controls, Navigation und Variant-3-Branding wurden grafisch angeglichen; Analyzer-Inhalt bleibt bei der Mindestgröße 1080x720 per Scroll erreichbar. Parser-, Szenen-, Replay-, NetCon-, System-Check- und Optimizer-Autoritäten wurden nicht erweitert. Kein neuer Product Slice und kein Merge nach `main` vor Tristans Abnahme; genaue Screen-Matrix, Tests, Build und Restabweichungen stehen im neuesten `coordination/agents/codex.md`-Handoff.

Für Home ist Seite 03 der Concept Preview die direkte strukturelle und visuelle Master-Referenz. Die vollständige Command-Center-Hierarchie mit sechs Moduleinstiegen, realen Statuskarten, Fortschritt, letzter Analyse, Schnellzugriff und unteren Informationsflächen ist zu erhalten; eine generische Ersatz-Dashboard-Komposition ist nicht zulässig. Reale Daten und ehrliche Nicht-verfügbar-Zustände ersetzen alle illustrativen Beispielwerte.

Der nachfolgende Home-Korrekturpass bleibt rein grafisch: Die akzeptierte Fensteranordnung, Modulreihenfolge, Datenbindung und Navigation werden nicht erneut umgebaut. Die produktive Umsetzung hat über die generischen Shell-Controls hinaus eigene Midnight-/Metallic-Karten, feine akzentcodierte Konturen, moderne Aktionsflächen sowie zurückhaltende technische Instrument-/Linienelemente zu zeigen. Variant-3-Branding bleibt kanonisch; neue Produktfunktion oder illustrative Kennzahl ist dadurch nicht autorisiert. Status bleibt `WAITING_FOR_TRISTAN`, bis Tristan den frischen Portable-Build gegen Page 03 abgenommen hat.

Für den finalen Home-Korrekturpass gilt ergänzend: Orbitron ist ausschließlich Display-/Technikschrift, Inter ist die reguläre UI-/Leseschrift. Beide werden aus versionierten, lizenzbeigefügten Assets nur für den Prozess registriert; eine systemweite Font-Installation ist nicht erlaubt. Der Dashboard-Scrollbar darf nur erscheinen, wenn der echte Canvas-Inhalt den verfügbaren Viewport überschreitet. Die Page-03-Hierarchie bleibt oben verankert und verteilt die vorhandene Höhe über begrenzte Grid-Mindestgrößen und Abstände; Schrift, Buttons und Icons werden nicht proportional aufgeblasen.

Für die sechs oberen Home-Modul-Cards gilt: Ihre Actions werden ausschließlich über einen gemeinsamen vertikalen Card-Grid-Aufbau in derselben letzten Zeile verankert. Die Beschreibung darf unterschiedlich hoch sein; nur der flexible Zwischenraum absorbiert diese Differenz. Keine individuellen Pixel-Offsets oder Card-spezifischen Button-Höhen. Das gilt ebenso für den responsiven 3x2-Reflow.

Der abschließende Home-Master-Pass verändert ausschließlich gemeinsame visuelle Komponenten: Sidebar-Navigation und Statusfläche verwenden eine eigene gerundete Midnight-Komponente mit ruhigem aktivem Blau-/Glow-Zustand statt nativer rechteckiger Auswahlrahmen. Die gemeinsamen Card-/Panel-Tokens bleiben dunkel und tonal nah beieinander; Konturen sind subtil. Keine Home-Struktur, Action-Grid, Typografie, Viewport-Logik oder Produktfunktion wird dabei verändert.

Der finale Home-Master-Stand verwendet verbindlich die mittlere Informationsfolge **Letzter Systemscan → Dein Fortschritt – Überblick → Letzte Analysen**; der frühere Schnellzugriff ist entfernt. Der Systemscan darf nur bestehende lokale `iy.system_check/v1`-Evidenz in CPU, GPU, RAM, Windows, Treiber und Monitor projizieren. Ohne einen solchen Datensatz bleiben alle sechs Werte und der Gesamtstatus ausdrücklich neutral. Fortschrittsdimensionen sind vorbereitete Darstellung, keine Quelle für Beispielwerte. Theme-Grundwerte sind `#010D19` (App), `#182D4F` (Panel), `#30485A` (Panel soft), `#075C94`/`#0A9AE7`/`#0065DA` (Akzente), `#D0D1D3`/`#8F97A4`/`#627188` (Text); die dunklen Flächen dominieren, Akzente bleiben funktional und zurückhaltend.

Der darauf folgende Home-Farb-/Surface-Pass ersetzt für Home die vorstehenden helleren Panelwerte: verbindlich sind `#020A12` (App), `#03101C` (Sidebar), `#071725` (Panel), `#0A1C2D` (raised), `#0D2236` (Hover), ein subtiler Border nahe `#0A2132`/`#071A27`, `#0B79C9`/`#13A7E8` als kontrollierte Akzente und `#E4E8ED`/`#A0ABB8`/`#687789` für Text. Die großen Card-Flächen bleiben damit nahezu schwarz/dunkel-Navy; Cyan, Modulfarben und Glow sind ausschließlich Führung, Status oder Aktion. Struktur, Radien, Typografie und Responsive-Geometrie bleiben unverändert.

## UI Completion Pass — Dark V1 Shared System (2026-08-21)

`HOME DARK V1 – READY FOR FINAL VISUAL ACCEPTANCE` ist ein Abnahme-Kandidat, keine implizite Produktfreigabe. Die verbindliche Home-Komposition, insbesondere **Letzter Systemscan → Dein Fortschritt – Überblick → Letzte Analysen**, bleibt unverändert. Bis zu Tristans ausdrücklicher Sichtabnahme ist weder ein Merge nach `main` noch ein neuer Product Slice autorisiert.

Die bestehende native Shell nutzt dieselben Dark-V1-Oberflächenwerte auch für die vorhandenen Kernrouten: Analyzer / eingebetteter Review, Tactical Replay, System Check / Optimizer, Rules, Reports und Settings. Gemeinsame Card-, Button-, Formular-, Status- und Überschriftsstile dürfen konsistent angepasst werden; Parser-, Replay-, Szenen-, NetCon-, System-Check- und Optimizer-Logik bleiben dabei unverändert. Kein neuer Screen, keine neue Engine und keine frei erfundenen Datenwerte.

## Home final visual template lock (2026-08-21)

Home ist strukturell abgeschlossen. Die kanonische Home-Template-Oberfläche verwendet für die sechs oberen Module die bereits definierte dunkle Panel-Stufe `#071725` statt einer helleren raised-Fläche. Ihre Actions sind eine einzige wiederverwendete, abgerundete Home-Komponente: gleiche Höhe, Breite, Position und Padding, dunkle Innenfläche, feine modulbezogene Kontur und unveränderte bestehende Command-/Disabled-/Keyboard-Anbindung. Diese Regel betrifft ausschließlich Home; sie ist keine stillschweigende Freigabe, die Formsprache ohne einen neuen Auftrag auf weitere Produktseiten auszubreiten.

Nach diesem Pass wird Home als `HOME VISUAL TEMPLATE LOCKED – READY FOR FINAL VISUAL ACCEPTANCE` behandelt. Informationsarchitektur, Datenwahrheit, responsive Geometrie, Sidebar, Typografie, Branding Variant 3 sowie die festgelegte Mittelreihe dürfen nicht erneut verändert werden. Keine weitere UI-Arbeit ohne neuen Auftrag; kein Merge nach `main` ohne ausdrückliche Produktentscheidung.

## Product decision — Home functional acceptance (2026-08-21)

Home ist für die weitere Produktentwicklung **funktional akzeptiert**, aber **visuell nicht final abgenommen**. Der aktuelle Home-Stand bleibt unverändert: Navigation, Modulaufteilung, bestehende Systemscan-Projektion, Fortschritt, letzte Analysen und Informationsbereiche sind die akzeptierte Arbeitsbasis. Ein späterer, bewusster Final-Polish entscheidet global über Farbflächen, Card-/Button-/Border-/Radius-/Akzent-Tokens und erst danach über eine Übertragung auf weitere Seiten. Bis dahin keine isolierte Home-Korrektur und keine ungeprüfte Stil-Vervielfältigung.

Der nächste funktionale Schwerpunkt ist ausschließlich **System Check / Optimizer**: zuerst den vorhandenen read-only `iy.system_check/v1`-Ergebnisfluss mit echten lokalen Daten erfassen und in der bestehenden Route nachvollziehbar darstellen. Keine automatische Firmware-, Treiber-, Registry- oder Windows-Änderung; Fakten, Bewertung, Hinweise und unbekannte Werte bleiben getrennt.
