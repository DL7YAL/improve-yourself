# Codex

## 2026-08-22 — Portable Candidate Executable Metadata Correction

STATUS: `DONE — WAITING_FOR_TRISTAN`

TASK: Ausschließlich den vorhandenen Portable-Candidate-Pfad auf direkt startbare EXE, Anwendungssymbol, Windows-Versionsinformationen und vollständige Runtime prüfen und, falls nötig, ohne Installer-Technologie korrigieren.

BRANCH / IMPLEMENTATION COMMIT: `dev/v1-foundation` / `765b47a build: polish portable candidate metadata`. Der nachfolgende Handoff-Commit dokumentiert nur diesen Zustand.

FINDING / FIX: Der vorherige Candidate enthielt die vollständige Runtime und ein eingebettetes Symbol, führte jedoch noch `Improve Yourself Experimental.exe` und leere Windows-Versionseigenschaften. Der unveränderte vorhandene PyInstaller-Pfad erzeugt nun direkt `Improve Yourself.exe` im Portable-Wurzelordner. `packaging/windows-version-info.txt` übernimmt ausschließlich die vorhandene Projektversion `0.1.0` aus `pyproject.toml`/Paket: `ProductName=Improve Yourself`, `FileDescription=Improve Yourself External Test Candidate`, `FileVersion=0.1.0`, `ProductVersion=0.1.0`, `OriginalFilename=Improve Yourself.exe`. Das Variant-3-ICO bleibt unverändert eingebettet. Keine Anwendung-, Daten-, Analyzer-, Optimizer- oder Installerfunktion geändert.

PACKAGE CHECK: Der frische ZIP enthält unmittelbar `Improve Yourself/Improve Yourself.exe`, `Improve Yourself/_internal/` mit der vollständigen PyInstaller-Runtime und `Improve Yourself/EXTERNAL_TEST_CANDIDATE_README.txt`. Die Build-Manifest-Referenz wurde auf den neuen EXE-Pfad aktualisiert. Direkter manueller Start der neuen EXE aus `dist/experimental/Improve Yourself/Improve Yourself.exe` im Windows-Runtimefenster: PASS; ehrlicher Analyzer-Empty-State sichtbar, danach sauber geschlossen.

BUILD / INTEGRITY: Vollständiger bestehender Build-Gate: **189 passed**, `pip check` PASS, `compileall` PASS, PyInstaller-COLLECT PASS, ZIP/Manifest PASS, `git diff --check` PASS. Frische Artefakte: EXE SHA-256 `54F094A15EE5F1379D48C3F26E8023874D1000E50046007F0064492A2EA20E6A` (19.881.203 Bytes); ZIP SHA-256 `7DDF941BBB38776699A8B6285805F51325100DEE1034291E3D96169527038ECC` (168.800.258 Bytes). Der Portable-ZIP bleibt der einzige zulässige externe Candidate; kein Setup/Installer, Updater oder Signiervertrag wurde eingeführt.

NEXT: `WAITING_FOR_TRISTAN`. Tester entpackt nur `dist/experimental/Improve-Yourself-Experimental-Portable.zip` vollständig und startet anschließend `Improve Yourself/Improve Yourself.exe`. Keine weitere Arbeit ohne neuen Auftrag.

## 2026-08-22 — External Test Candidate

STATUS: `DONE — WAITING_FOR_TRISTAN`

TASK: Den laufenden Unified-Analyzer-Auftrag in einen stabilen externen Test Candidate überführen. Zulässig waren ausschließlich finale Sidebar-Sortierung, kritische Navigationskorrekturen, Portable-/Testerpaket, End-to-End-Smoke und Handoff. Keine neue Produktfunktion, kein zusätzlicher UI-Polish, keine Benchmark-, Replay-, Parser-, Optimizer- oder Architekturarbeit.

BRANCH / IMPLEMENTATION COMMIT: `dev/v1-foundation` / `42347d1 chore: prepare external test candidate`. Der nachfolgende Handoff-Commit dokumentiert nur diesen Zustand.

CHANGED: Die Sidebar wird nun tatsächlich über die explizite Workflow-Reihenfolge gerendert — **Dashboard → Analyzer → Tactical Replay → My Improvement → Reports → System Check / Optimizer → Settings → Improve Benchmark** — statt implizit über die technische Seiten-Registrierungsreihenfolge. Es bleibt genau ein Top-Level-`Analyzer`; `Demo Analyzer` und `Rules` bleiben nicht in der Sidebar. Die zwei Dashboard-Einstiege in den Analyzer führen zuverlässig zur internen **Übersicht** (Demo-Preflight), unabhängig vom zuletzt aktiven Analyzer-Tab. Die Karte **My Improvement** öffnet die passende bestehende Entwicklungsübersicht statt der separaten Reports-Seite. Es wurden keinerlei Analyzer-Daten, Rules, Szenen, Ticks, CS2-/NetCon-Logik oder Replaypfade verändert.

TESTER PACKAGE: `packaging/EXTERNAL_TEST_CANDIDATE_README.txt` liegt im Portable-Verzeichnis direkt neben der EXE und ist im ZIP enthalten. Es beschreibt den lokalen/read-only Testweg, die Datenablage, den optionalen vorhandenen CS2-/NetCon-Pfad, die zu meldenden Fehler und den Manifest-Hash. Der Packaging-Gate prüft das Staging der Datei vor dem ZIP-Erstellen. Das Paket ist absichtlich weiter ein **Portable Experimental**: Es existiert kein akzeptierter Inno-/WiX-/NSIS-/MSIX-Installervertrag. Deshalb ist `Setup: not generated` kein Buildfehler und es wurde kein unfreigegebener Installer, Updater, Signier- oder Installationspfad ergänzt.

PORTABLE / INTEGRITY: Voller frischer Build erfolgreich. Artefakte: `dist/experimental/Improve Yourself Experimental/Improve Yourself Experimental.exe`, `dist/experimental/Improve-Yourself-Experimental-Portable.zip`, `dist/experimental/experimental-build.json`. EXE SHA-256: `3E476A0F6D3D0362313BCA21A6BD08B883DCC2EE89C0FFD7E021F5465A571B56`; ZIP SHA-256: `82B2727307CE346CB9DFF9FDFA7FBCC326F9F142F00E68B2079BCCBD3D0F8707`; ZIP-Größe: `168870493` Bytes. Die Anleitung wurde sowohl im extrahierten Portable als auch im ZIP direkt nachgewiesen.

RUNTIME SMOKE: Der **frische** Portable startete auf dem ehrlichen Analyzer-Empty-State ohne automatische Demoauswahl. Die finale Sidebar wurde praktisch geprüft: Dashboard aktiv, Analyzer direkt darunter, Tactical direkt als nächster Workflow-Schritt; der Dashboard-My-Improvement-Einstieg öffnet die reale `Meine Entwicklung`-Ansicht. Für den echten lokalen Nachweis wurde das vorhandene hashgebundene Ancient-Workflowartefakt im frischen Portable geöffnet: `de_ancient`, **18 Runden**, **10 benannte Spieler**, **3179** Basis-Events und **54** zusammengeführte Szenen. Der Analyse-Tab zeigte Full-Demo/CT/T/Spielerauswahl, Profil `review_v1` und sieben objektive Kriterien. Der Review-Tab öffnete den eingebetteten echten Szenenreview; ausgewählt war `Runde 01 · Tick 3654 · 3 Marker` mit tatsächlichem Kontext `3526–3961`, Spielern und objektiven Regeln `entry`, `headshot`, `kill`. Das ist dieselbe bereits praktisch getestete lokale Demo-/Szenenbasis des Unified-Analyzer-Handoffs; weder Demo- noch Analyseergebnisse wurden für den Smoke erfunden. Der bestehende Tactical-Übergang und die CS2-Tick-Sicherheitsgrenzen wurden in diesem Candidate nicht geändert; ihre erfolgreiche Runtime-Evidenz bleibt im unmittelbar vorherigen Unified-Analyzer-Handoff festgehalten. Ein optionaler CS2-Sprung wurde nicht ausgelöst.

TESTS / CLEANLINESS: Fokussierter Shell-Test zuvor **29 passed**; der finale vollständige Packaging-Gate: **189 passed**, `pip check` PASS, PyInstaller PASS, Portable PASS, ZIP PASS, Manifest PASS. `compileall` PASS und `git diff --check` PASS. Das frische Portable-Fenster wurde nach dem Smoke kontrolliert geschlossen. Keine generierten Resultate oder Buildartefakte werden versioniert.

KNOWN BOUNDARY: Für einen echten Installer bräuchte das Projekt eine separate Produktentscheidung zu Installationsbereich, Upgrade-/Uninstall-Identität, Verknüpfungen und Signierung. Das wäre ausdrücklich außerhalb dieses Candidate-Scope. Der zulässige Tester-Deliverable ist daher der hashgebundene Portable-ZIP mit Anleitung, nicht ein nur behaupteter Setup-Installer.

NEXT: `WAITING_FOR_TRISTAN`. Tristan kann den Portable-ZIP extrahieren, die direkte Testeranleitung neben der EXE verwenden und den lokalen Ablauf prüfen. Keine weitere Produkt-, UI-, Optimizer-, Benchmark-, Replay- oder Infrastrukturarbeit ohne neuen Auftrag.

## 2026-08-22 — Unified Analyzer Final Integration

STATUS: `DONE — WAITING_FOR_TRISTAN`

TASK: UI Reference Pack v1.1.0 anwenden und den Analyzer als einziges Top-Level-Modul mit exakt den internen Bereichen `Übersicht | Analyse | Review` abschließen. Keine Parser-, Szenen-, Rule-, NetCon-, CS2-, Optimizer-, Benchmark- oder Replay-Logik ändern.

BRANCH / HEAD: `dev/v1-foundation` / `a20b72a feat: unify analyzer workflow tabs` (pushed to `origin/dev/v1-foundation`).

REFERENCE AUTHORITY: Die vom Nutzer bereitgestellten v1.1.0-Dateien `D:\downloads\Improve Yourself\Demos\README_UI_REFERENCE.md` und `UI_REFERENCE_MANIFEST.json` wurden vor der Umsetzung gelesen. `analyzer_unified_MASTER.png` (SHA-256 im Manifest: `e17a646d…`) ist der alleinige Analyzer-`MASTER`; `analyzer_legacy_SUPERSEDED.png` und `demo_analyzer_legacy_SUPERSEDED.png` sind ausschließlich historisch und wurden nicht als Ziel verwendet. Der Checkout enthielt zu Beginn noch den v1.0.0-Referenzordner; für diesen Slice war daher die bereitgestellte v1.1.0-Quelle maßgeblich. Das Master-PNG selbst wurde nicht als neue Produktdatei kopiert oder verändert.

CHANGED: `src/improve_yourself/analyzer_shell.py` und `tests/test_analyzer_shell.py`. Die Sidebar enthält nun genau einen Analyzer-Einstieg `Analyzer`; weder `Demo Analyzer` noch `Rules` sind Top-Level-Navigation. Die vorhandene, lokale UI wird in drei sichtbaren internen Tabs gehalten: **Übersicht** bündelt Bibliothek/Import, ausgewählte Demo, Import-/Analyse-Status und reale Matchfakten; **Analyse** enthält unverändert Datenquelle, CT/T/Full-Demo/Player-Select, Profil, Objektiv-Regelset, Start und CS2-Readiness; **Review** enthält die vorhandene Ergebnisprojektion sowie den eingebetteten Szenenreview. Review-Ticks werden unverändert an den bestehenden Tactical-Viewer übergeben. Keine zweite Review-/Replay-Engine, keine Mockupwerte und keine neue Analyseentscheidung wurden ergänzt.

RUNTIME EVIDENCE: Frischer Portable praktisch mit echter `fut-vs-mouz-m2-ancient.dem` geprüft. Übersicht nach Parserabschluss: `de_ancient`, **18 Runden**, **10 Spieler**, **3.179** grundlegende Events, SHA-Präfix und Parser `PASS`; danach wurde der vorhandene lokale `demo-workflow.json` desselben Evidenzlaufs geladen: **54** zusammengeführte Szenen, Status `Review bereit`. Analyse-Tab zeigt bestehende Auswahl, Profil `review_v1`, sieben objektive Kriterien und Regelset. Review-Tab zeigt reale Situationen/Ticks; der eingebettete Review listet reale Szenen wie `Runde 01 · Tick 3654 · 3 Marker`, mit Spieler-, Regel-, Kontext-, Status- und Notizdaten. Die ausgewählte Szene wurde über den bestehenden Pfad erfolgreich in den eigenständigen `Tactical Replay` übernommen: Runde 1, Tick 3654, Frame 1/256, ohne neue Analyse. Kein CS2-Tick-Sprung wurde in diesem reinen UI-Slice ausgelöst.

VIEWPORT / VISUAL: Wide-Runtime-Captures zeigen die verbindliche Unified-Hierarchie auf einen Blick: Variant-3-Shell, nur aktiver Analyzer-Navigationseintrag, Tabs, Demo-Bibliothek, ausgewählte Demo, Statusflächen und Workflow. Der native Portable wurde manuell auf **1084×752 Capture** (entspricht der geforderten 1080×720-Client-Mindestgröße plus Fensterrahmen) gesetzt und geprüft: Unified-Review, Szenenliste, Details, Statuswahl, Notiz und Tactical-Handoff bleiben erreichbar; echter vertikaler Inhaltsüberlauf bleibt scrollbar. Tactical bleibt eigenständiger Tab und zeigt die übernommene reale Szene. Keine helle/native Fremdfläche, keine doppelte Analyzer-/Rules-/Demo-Navigation.

TESTS / BUILD: Fokussierter Shell-Gate **29 passed**; `compileall` PASS; `git diff --check` PASS. Der vollständige finale Packaging-Gate lief nach geschlossenem Testfenster mit **189 passed**, `pip check` PASS, PyInstaller-COLLECT PASS sowie frischem Portable-, ZIP- und Manifest-Schritt PASS. Ein vorheriger ZIP-Dateilock wurde durch den sauberen Wiederholungslauf behoben; der aktuelle Archivstand ist `Improve-Yourself-Experimental-Portable.zip` mit 168.869.016 Bytes (22.08.2026 07:43).

KNOWN LIMITS: Der neue v1.1.0-Reference-Pack-Ordner ist im Repository noch nicht synchron vorhanden; die explizit bereitgestellte Demos-Quelle ist im Handoff belegt. Die MASTER-Beispielbild-/Score-/Matchdaten wurden nicht in Produktdaten umgedeutet. Kartenbasis/Zeit bleiben im Tactical weiterhin ehrlich nur angezeigt, wenn die gemeinsame Replay-Wahrheit sie belegt.

NEXT: Checkpoint-Commit und Push. Danach `WAITING_FOR_TRISTAN`; keine weitere UI- oder Produktarbeit.

## 2026-08-22 — UI Master Alignment Sequence (laufend)

STATUS: `DONE — WAITING_FOR_TRISTAN`

TASK: Die sechs nicht-Optimizer `MASTER`-Screens in der verbindlichen Reihenfolge abgleichen: Dashboard, Improve Analyzer, Demo Analyzer, Tactical Viewer, My Improvement, Benchmark. Die beiden Optimizer-MASTER bleiben unverändert.

BRANCH: `dev/v1-foundation`

REFERENCE: `README_UI_REFERENCE.md` und `UI_REFERENCE_MANIFEST.json` erneut gelesen. Alle sechs genannten Dateien sind `MASTER`; die einzige Legacy-Optimizerdatei bleibt `SUPERSEDED`. PDF und frühere Zwischenstände werden nicht als Ersatzreferenz verwendet. Variant 3 bleibt die gemeinsame Shell-Regel.

CHANGED SO FAR: Die bestehende Dashboard-/Analyzer-/Tactical-Shell bleibt erhalten. `My Improvement`, die interne Demo-Übersicht und `Improve Benchmark` sind Master-orientierte Ansichten mit derselben Variant-3-Shell, aktiver Navigation und dunklen Karten. Sie zeigen ausschließlich ehrliche lokale Bereitschafts-/Unknown-Zustände: keine erfundenen Verlaufswerte, Demos, Ergebnisse, FPS, Benchmark-Maps oder Produktaktionen. Der echte `READY_FOR_REVIEW`-Analyzerzustand erhält zusätzlich eine reine Ergebnisprojektion aus demselben validierten `analysis-flow.json`: Übersicht, objektive Szenenanker, erste Szenen, Mustergrenze, neutraler Strength-/Weakness-Status und der vorhandene eingebettete Review-Einstieg. Nach einer fertigen Analyse führt diese Master-Hierarchie sichtbar; der bestehende Import-/Auswahlfluss bleibt über `Analyse konfigurieren` erreichbar. **Demo Analyzer ist kein eigener Sidebar-Reiter mehr:** `Analyzer / Review` ist der einzige Analyzer-Einstieg; `Demo-Übersicht öffnen` macht die MASTER-konforme Bibliothek-/Import-/Ergebnisansicht intern im selben Workflow erreichbar. Die gemeinsame Card-Komponente besitzt die nötige Mindesthöhe. Für Tactical wurde ausschließlich die sichtbare MASTER-Hierarchie ergänzt: Seitentitel `2D Tactical`, eine rechte `SZENENDETAILS`-Spalte mit derselben ausgewählten Szene, bestätigtem Frame/Tick und lokaler Review-Notiz sowie eine klar gekennzeichnete Kartenbasis-Grenze. Es gibt ausdrücklich keine erfundene Ereignis-Timeline, kein Kartenasset und keine neue Replay-Autorität. **My Improvement** folgt jetzt dem MASTER mit Titel-/Evidenzzeile, fünf gleichwertigen Entwicklungskarten, drei Fokuspanels und Szenenbereich. Scores, Trends, Verlaufslinien, Stärken, Schwächen und Szenen-Einflüsse bleiben sauber unbekannt, bis mehrere lokale Analysen dies belegen. **Improve Benchmark** folgt jetzt dem MASTER mit Start-/Profil-, Ergebnis-/Kennzahlen-, Map-, Szenenablauf- und Erklärflächen; alle Werte bleiben ungemessen, der Lauf sichtbar gesperrt und jede Map-/Mess-/Systemaktion unterbleibt. Im finalen kompakten Review wurden nur drei sichtbare Benchmark-Textflächen korrigiert: `Ø FPS` statt einer abgeschnittenen langen Kennzahl, ein kurzer ehrlicher Verlauf-Empty-State sowie ein Master-näheres 3:1-Erklärungsraster, damit der Hinweis vollständig in seiner Card bleibt. Neue UI-Ansichten ändern weder Parser, Replay, Regeln, Evidence, Hardware-Support noch Apply-/Write-Verhalten.

VERIFIED SO FAR: `compileall` PASS; fokussierte Shell-Tests **29 passed**; vollständiger Build-Gate **189 passed**; `pip check` PASS; `git diff --check` PASS; frischer Portable-Build samt Manifest/ZIP PASS. Runtime-Captures im frischen Portable: Dashboard, My Improvement, echter Analyzer-Ergebniszustand, interne Demo-Übersicht, Tactical-Empty-State und finaler Improve-Benchmark-Screen. Der erste erneute Build traf einmal auf einen abgebrochenen bestehenden Loopback-Socket-Test (`WinError 10053`); dessen isolierte Wiederholung sowie die komplette Suite bestanden danach, und der folgende finale Build-Gate lief mit **189 passed** vollständig grün. Dashboard folgt bereits dem sechsmoduligen Command-Center mit realen lokalen Statuswerten. My Improvement entspricht sichtbar dem MASTER-Raster (fünf Dimensionen plus drei Fokuspanels), zeigt aber bewusst nur fehlende lokale Vergleichsevidenz.

CURRENT ASSESSMENT: **My Improvement: PASS im Empty-/Unknown-Daten-Scope.** Der frische Portable zeigt auf den ersten Blick die MASTER-Komposition: Titel-/Evidenzleiste, fünf Akzentkarten, drei untere Fokusbereiche und Szeneneinflussfläche. Die nicht vorhandenen Beispiel-Scores, 30-Match-Trends, Profilwerte, Szenenbilder und Verbesserungsurteile wurden bewusst nicht übernommen. **Improve Benchmark: PASS im gesperrten Evidenz-Scope.** Der frische Portable zeigt die MASTER-Hierarchie: Start-/Profilfläche, Ergebnis mit Durchschnitt-FPS/1%-Low/Frametime, Map-Status, Szenenablauf und Erklärung/Hinweis. Alle real nicht vorhandenen Werte sind `–`/nicht gemessen; die Map bleibt unbestätigt und der Lauf ist klar als `LAUF GESPERRT` sichtbar. Keine Benchmark-Map- oder Produktarbeit wurde gestartet. **Analyzer: PASS im freigegebenen Ergebnis-Scope.** Der Runtime-Ergebniszustand führt jetzt mit `Übersicht → Schlüsselbefunde → erkannte Situationen → wiederkehrende Muster → nächste Schritte → Stärken/Schwächen/Regelset`; reale Fakten ersetzen die Mockupwerte. **Demo Analyzer: PASS im freigegebenen Daten-Scope.** Der neue Portable-Capture bestätigt die einzige Analyzer-Sidebar sowie die interne echte Übersicht mit Auswahl, Quelle, Map, Runden, Spielern, SHA-Präfix, Parserstatus, 54 deduplizierten Szenen und Review-Bereitschaft; beide unteren Aktionen liegen vollständig innerhalb der gemeinsamen Card. **Tactical Viewer: PASS für Shared-Replay-Truth und sichtbare MASTER-Hierarchie.** Der frische Empty-State zeigt korrekt nur die drei belegten Vorbereitungsschritte; der echte Review-/Tactical-Check bestätigte Runde 1, Tick 3654, Frame 1/256 und zehn reale Spielerpositionen/Blickrichtungen. Master-Elemente, die echte Kartenassets oder eine separate Event-Timeline verlangen würden, bleiben ehrlich ausgeschlossen.

REAL ANALYZER CHECK: Ein bestehender fail-closed lokaler Workflow wurde am 2026-08-22 erfolgreich in der Shell geöffnet (nur gelesen): Quelle `fut-vs-mouz-m2-ancient.dem`, `de_ancient`, 18 Runden, 10 benannte Spieler, 3.179 grundlegende Events und 54 Szenen, Status `Review bereit`. Der echte Datenpfad ist sichtbar korrekt. Die neue Laufzeitansicht zeigt genau diese Fakten an erster Stelle und listet objektive Anker (`kill`, `headshot`, `multi_kill`, `smoke_kill`) sowie die ersten realen Runden/Ticks. Der Button `Szenen im Review öffnen` bleibt an den vorhandenen eingebetteten Review gebunden. Die Beispiel-Scores, Muster, Bilder und Verbesserungsaussagen des MASTER wurden nicht kopiert; fehlende produktive Bewertungen bleiben sichtbar nicht abgeleitet. Runtime-Capture erfolgte nur lokal, nicht versioniert und ohne private Pfadangabe im Produkt.

NEXT: `WAITING_FOR_TRISTAN`. Der Screen-MASTER-Abgleich ist für alle sechs vorgesehenen Nicht-Optimizer-Screens durchgeführt. Nur nach neuer ausdrücklicher Freigabe folgt der dokumentierte Wide-/1080×720-Review; keine neue Produkt-, Architektur-, Replay- oder Benchmark-Map-Arbeit.

FINAL WIDE-/COMPACT-REVIEW (2026-08-22): Wide-Runtime-Captures des frischen Portable wurden für alle sechs Nicht-Optimizer-Screens geprüft: **Dashboard** – Sidebar/Header, sechs Karten und mittlere/untere Panels ohne Überlagerung oder angeschnittene Actions; **Analyzer (echter Ergebniszustand)** – reale 54-Szenen-/18-Runden-/10-Spieler-Projektion, Befundkarten und Review-Einstieg vollständig; **Demo Analyzer** – Bibliothek, ausgewählte echte Demo, Statuskarten und beide Actions innerhalb ihrer Card; **Tactical Viewer** – Empty-State sowie zuvor der echte ausgewählte Frame/Tick mit rechter Szenendetails-Spalte, ohne zweite Replay-Wahrheit; **My Improvement** – gleichhohe fünf Entwicklungskarten, drei Fokuspanels und Unknown-Flächen ohne Mockupwerte; **Benchmark** – Start, Ergebnis, Map, Szenenablauf und Erklärung/Hinweis vollständig. Über alle sechs: dunkle Variant-3-Shell, aktive Sidebar, Header, Card-Höhen und Scroll-Surfaces blieben konsistent; keine helle/native Fremdfläche und kein sichtbar abgeschnittener Inhalt nach der Benchmark-Korrektur. Tabellen-/Listen- und rechte Detailbereiche wurden nur dort geprüft, wo der jeweilige reale Zustand sie besitzt (Analyzer/Demo/Tactical); keine erfundene Tabelle oder Szene zur Sichtprüfung erzeugt.

COMPACT 1080×720: Der Produktvertrag bleibt explizit `root.minsize(1080, 720)`; die Suite deckt diesen Shell-Vertrag ab. Der automatisierte Windows-Fenster-Resizer konnte die frische Portable im laufenden Test auf Mindestbreite bringen, lieferte bei der Höhenänderung jedoch inkonsistente Capture-Geometrien und beendete einmal ausschließlich die Testinstanz. Deshalb wird **keine** unbewiesene pixelgenaue 1080×720-Runtime-PASS-Behauptung abgegeben. Es gab dabei keinen Produktfehler, keine Datenänderung und keinen sichtbaren Layoutbruch im tatsächlich erreichbaren kompakten Capture. Die unmittelbare Restabnahme ist ein manueller 1080×720-Sichtcheck des frischen Portable; es ist kein Anlass, funktionale oder strukturelle UI-Arbeit zu starten.

MODEL_PROFILE: terra

MODEL_REASON: Mehrere zusammenhängende native UI-Umsetzungen mit echten lokalen Daten und strikter Produktgrenze.

COMPUTER_USE: yes

COMMIT/PR: Finaler Wide-/Compact-Review-Checkpoint wird nach Arbeitsbaum-/Diff-Check auf `dev/v1-foundation` gesichert und gepusht.

FOLLOW-UP — ANALYZER / REVIEW + 1080×720 (2026-08-22): Die zuvor offene Abnahme wurde gezielt nachgearbeitet, ohne Parser-, Rule-, Szenen-, Replay-, CS2- oder Produktlogik anzufassen. Der geladene Ergebniszustand besitzt nun eine sichtbare, reine Präsentationsleiste **ANALYSE → REVIEW**, echte Kontextangaben (Map, Runden, Profil, Szenenzahl) sowie die vorhandenen Aktionen `Analyse konfigurieren` und `Review öffnen`. Die Ergebnisansicht nutzt für die Mindestbreite kompakte Wrapbreiten; damit passen Übersicht, Schlüsselbefunde und wiederkehrende Muster als drei vollständige Cards sowie Situationen, nächste Schritte und die unteren Faktenkarten ohne horizontalen Anschnitt. Keine Score-, Stärke-/Schwäche- oder Musterwerte wurden erfunden.

EMBEDDED REVIEW: Die echte `de_ancient`-Analyse mit **54** Szenen wurde im frischen Portable geöffnet. Die linke Liste verwendet nun nur echte kompakte Angaben `Runde NN · Tick NNNN · N Marker`; vollständiger Kontext, Spieler, Regeln und Notiz bleiben im rechten Detailbereich. Die Actionfläche ist bei Mindestbreite als responsives 3+2-Raster umgesetzt: `Status & Notiz speichern`, `In CS2 ansehen`, `Tactical Replay`, `← Vorherige`, `Nächste →`. Somit sind Tick-Sprungpfad, Tactical-Übergang und Szenennavigation sichtbar erreichbar, ohne sie in diesem UI-Pass auszuführen oder ihre abgesicherten Grenzen zu verändern.

RUNTIME / VIEWPORT: Frischer Portable-Build praktisch geöffnet und per nativer Fenstergröße auf **1080×720 Client** gesetzt (Capture **1082×752** einschließlich Fensterrahmen). Lokal erzeugte, nicht versionierte Runtime-Captures wurden für (a) Analyzer-Setup, (b) reale Ergebnisansicht und (c) eingebetteten Review gesichtet. Ergebnis: keine horizontale Überlagerung/kein Kartenanschnitt; die rechte Detailfläche, Szenenliste, Statusauswahl, Notizbereich, fünf Review-Aktionen, Sidebar und Header bleiben sichtbar. Vertikales Scrollen bleibt ausschließlich für echten Inhaltsüberlauf verfügbar. Keine Browser-/Fallback-Aktion und kein CS2-Tick-Sprung wurden durch diesen Sichtcheck ausgelöst.

VERIFIED FOLLOW-UP: fokussierte Shell-Tests **29 passed**; erneuter vollständiger Portable-Build-Gate **189 passed**; `pip check`, `compileall` und `git diff --check` PASS. Der neue Portable samt Manifest/ZIP wurde nach den letzten Responsive-Korrekturen erzeugt.

STATUS / NEXT: `DONE — WAITING_FOR_TRISTAN`. Der nächste zulässige Schritt ist ausschließlich Tristans visuelle Abnahme des frischen Portable, besonders Analyse-Ergebnis und Embedded Review bei 1080×720. Keine weitere UI-, Produkt-, Analyzer-, Replay-, Optimizer-, Benchmark- oder Infrastrukturarbeit ohne neuen Auftrag.

## 2026-08-22 — UI Reference Pack verified / Optimizer + Shell alignment

STATUS: `WAITING_FOR_TRISTAN`

TASK: Die entpackte UI-Reference-Pack-Quelle zuerst verifizieren und danach ausschließlich den bereits freigegebenen Optimizer-/Shell-Abgleich fortsetzen. Keine weitere Produktseite, Regel, Evidence-/Sicherheitslogik oder Produktfunktion.

BRANCH: `dev/v1-foundation`

REFERENCE AUTHORITY: `docs/design/ui-reference/README_UI_REFERENCE.md` und `UI_REFERENCE_MANIFEST.json` wurden gelesen. Die manifestierten SHA-256-Werte der zwei Optimizer-`MASTER`-PNGs stimmen mit den lokalen Dateien überein. `optimizer_overview_MASTER.png` und `system_optimizer_detail_MASTER.png` sind die einzigen Screen-Ziele. `optimizer_legacy_from_concept_pdf_SUPERSEDED.png` bleibt ausgeschlossen; die PDF ist keine Ersatzreferenz. Variant 3 wurde nur für Shell, Branding, Header-/Chip-Übergang und Navigation verwendet. Das Manifest ist zusätzlich direkt im entpackten Ordner versioniert, weil es dort zunächst nur innerhalb der mitgelieferten ZIP lag.

CHANGED: Nur `src/improve_yourself/analyzer_shell.py`, `tests/test_analyzer_shell.py` und UI-Referenz-/Handoff-Dokumentation. Die Optimizer-Übersicht erhält eine MASTER-nahe Empfehlungen-/Statushierarchie mit wahrheitsgemäßem Vier-Bereiche-Ring, echten read-only Kennzahlen, 2×2-Domain-Karten und stabiler Detailsäule. Das Systemdetail erhält einen globalen Optimizer-Header, echte Rücknavigation, vier reale Kennzahlen, Suche/Statusfilter, eine gruppierte Ergebnisliste mit ausgewählter Zeile und eine lesbare rechte Erklärung. Rohwerte, Provenance und Evidence-Strukturen bleiben hinter dem vorhandenen bewussten `Technische Details`-Disclosure. Eine Rohstruktur im sichtbaren Evidenzabschnitt wurde abschließend durch den korrekten Status `Vorhandene Evidenzdaten · technische Details verfügbar.` ersetzt. Der globale Shell-Abgleich verkleinert die fixe Sidebar auf die MASTER-nahe Breite; Variant-3-Branding und der aktive, dunkle Cyan-State bleiben erhalten. Keine Regel, Entscheidung, Datenquelle, Hardwareerkennung, Apply-/Restore-Funktion oder andere Seite geändert.

RUNTIME EVIDENCE: Frischer Portable wurde geöffnet und beide verbindlichen Ansichten praktisch geprüft. Übersicht: dunkle Variant-3-Shell, aktueller Nav-State, Header-Hardwarechips, sichtbare System-Check-Aktion, Statusring, vier echte Bereichskarten und feste `DETAILS & ERKLÄRUNG`-Spalte. Systemdetail: Rücknavigation, Titel/Subtitel, vier Kennzahlen, Suche/Filter, dunkle gruppierte Tabelle, aktuelle Auswahl und Detailspalte. Keine helle/native Fremdfläche. Die letzte textliche Evidenzdarstellung ist nach dieser Prüfung erneut vollständig gebaut und getestet; die dargestellten Werte bleiben real/read-only.

CURRENT-vs-TARGET: **PASS im freigegebenen Optimizer-/Shell-Abgleich.** Die Runtime ist als Umsetzung der zwei MASTER-Screens erkennbar: Master-Hierarchie, Flächenaufteilung, Kartenraster, Detailspalte, Headerchips und aktive Navigation sind vorhanden. Keine pixelgenaue Bitmapkopie wird behauptet; reale Daten ersetzen die Mockupwerte. Der verbleibende Unterschied ist nur die unvermeidbare native Fensterchrome/Tk-Textmetriken und damit Final Polish, nicht mehr die frühere Developer-/Evidence-Wand.

VERIFIED: `python -m compileall -q src` PASS; vollständige Suite **188 passed**; `git diff --check` PASS. Frischer Portable-Build samt Manifest PASS. EXE SHA-256 `35844F7CD19A8581B04F27F80E10108905B164484968ADAC73295D4598906BF8`; ZIP SHA-256 `056F1FB031FE0772DB51E15DF76F533A89B352FCE0355CAF3242CB3ECDED4BF5`.

OPEN: Nur Tristans visueller Vergleich der zwei aktuellen Portable-Screens gegen die zwei MASTER-PNGs. Keine weitere UI-/Produktarbeit ohne neuen Auftrag.

NEXT: `WAITING_FOR_TRISTAN`.

MODEL_PROFILE: terra

MODEL_REASON: Begrenzter visueller Master-Abgleich mit realen read-only Daten, Native-Desktop-Shell und vollständiger Runtime-/Build-Prüfung ohne Architektur- oder Sicherheitsänderung.

COMPUTER_USE: yes

COMMIT/PR: pending current checkpoint on `dev/v1-foundation`.

## 2026-08-22 — UI Reference Pack authority update

STATUS: `WAITING_FOR_TRISTAN`

TASK: Die neue verbindliche Referenzhierarchie für künftige UI-Arbeit festhalten, ohne eine weitere Screen-Implementierung zu beginnen.

BRANCH: `dev/v1-foundation`

CHANGED: `docs/design/README.md`, `docs/design/MOCKUP_INDEX.md` und `docs/design/UI_SPEC.md` ordnen das UI Reference Pack v1.0.0 als Screen-Authority vor den älteren PDF-Kontext ein. `docs/UI_REFERENCE_PACK_POLICY.md` beschreibt den fail-closed Ablauf. Pack-`MASTER` ist verbindlich, `SUPERSEDED` ist ausgeschlossen. Für Optimizer sind ausschließlich `optimizer_overview_MASTER.png` und `system_optimizer_detail_MASTER.png` maßgeblich; die ältere PDF-Optimizeransicht ist kein Ziel mehr. Variant 3 bleibt für globale Shell, obere Übergänge/Header, Branding, linke Shell und Navigation bindend. Keine Produkt-, UI- oder Datenlogik geändert.

REFERENCE ACCESS: `/mnt/data/Improve_Yourself_UI_Reference_Pack_v1.0.0.zip` war in diesem Windows-Workspace weder als `/mnt/data` noch als `C:\\mnt\\data` oder `D:\\mnt\\data` erreichbar. README, Manifest und MASTER-Dateien konnten deshalb nicht gelesen oder gegen den aktuellen Portable geprüft werden. Entsprechend wurde nichts aus der PDF, Erinnerung oder dem zuletzt gepushten Optimizer-Stand rekonstruiert.

VERIFIED: Pfadverfügbarkeit explizit geprüft; Working Tree vor Dokumentation sauber. Für die Dokumentationsänderung folgt nur `git diff --check`; kein neuer Build/Test ist erforderlich, weil keine ausführbare Produktdatei geändert wird.

OPEN: Das UI Reference Pack muss dem Workspace zugänglich bereitgestellt oder erneut angehängt werden. Erst danach: README/Manifest lesen, MASTER/SUPERSEDED-Klassifikation belegen und einen neuen begrenzten Optimizer-/Shell-Abgleich gegen diese tatsächlichen Dateien freigeben.

NEXT: `WAITING_FOR_TRISTAN` — zugängliches ZIP oder die entpackten Referenzdateien bereitstellen. Keine UI-Änderung vorher.

MODEL_PROFILE: luna

MODEL_REASON: Eng begrenzte Referenz-/Handoff-Konsolidierung ohne Code-, Sicherheits- oder Produktentscheidung.

COMPUTER_USE: no

COMMIT/PR: `05d7b73 docs: lock UI reference pack authority`; `21674da docs: record UI reference pack handoff`; both pushed to `origin/dev/v1-foundation`.

## 2026-08-22 — Optimizer Visual Fidelity Pass

STATUS: `WAITING_FOR_TRISTAN`

TASK: Ausschließlich den angenommenen Optimizer-Piloten gegen die zwei verbindlichen visuellen Optimizer-Referenzen kalibrieren. Struktur, Navigation, Daten-, Evidence-, Matrix-Pack-, Rule-Pack- und read-only-Sicherheitslogik bleiben unverändert. Keine andere Produktseite bearbeiten.

BRANCH: `dev/v1-foundation`

CHANGED: Zentrale optimizer-exklusive Midnight-/Metallic-Tokens und eine kleine gemeinsame Komponentenfamilie ergänzen echte gerundete Oberflächen, Low-Fill-Actions, Hardware-Chips, metrische Statusflächen und Detail-/Tabellen-Chrome über den vorhandenen Tk-Inhalt. Übersicht und Systemdetail behalten ihre angenommene Struktur. Die vier Bereichskarten haben eine gemeinsame Mindesthöhe, damit auch die längere Network-Statuszeile ihre Aktion nicht abschneidet. Der primäre rechte Erklärungstext verdichtet nur vorhandene Contract-Werte zu lesbaren deutschen Darstellungslabels; die unveränderten Rohwerte bleiben ausschließlich hinter `Technische Details` zugänglich. Keine Produktregel, Bewertung, Hardwareerkennung, Datenquelle, Sicherheitsgrenze, Aktion oder andere Seite geändert.

RUNTIME EVIDENCE: Der frische finale Portable wurde nach dem letzten Packaging bei normaler Experimental-Größe (`1360x860`) geöffnet. Capture 1: Optimizer-Hauptübersicht mit dunklem Grund, Kompaktchips, abgerundeter Statusfläche, vier vollständigen 2x2-Karten, aktiver System-Karte und fester dunkler Detailspalte. Capture 2: System Optimizer mit Rücknavigation, dunklen Kennzahlenkarten, Such-/Filterzeile, Tabellenkopf/Zeilen/Selected-State, lesbarer rechter Erklärung und sekundärem `Technische Details`. Keine weiße oder helle native Fläche sichtbar. Die Portable verbleibt auf dem finalen System-Optimizer-Screen für Tristans Sichtcheck.

CURRENT-vs-TARGET: **PASS im Visual-Fidelity-Scope.** Farbwirkung folgt der Referenz: fast schwarzes Navy führt, tiefe Blau-Schwarz-Surfaces trennen die Ebenen, Cyan ist Kante/Fokus/aktive Führung statt dominierende Grundfläche. Cards, Chips, Actions, Tabelle und Detailspalte tragen nun dieselbe ruhige abgerundete Metallic-Formsprache; der frühere Tk-/Developer-Standardlook ist nicht mehr dominant. Keine pixelgenaue Bitmapkopie behauptet; reale read-only Daten und fehlende/unsichere Werte ersetzen die Mockupwerte wahrheitsgemäß.

VERIFIED: Vollständiger Build-Gate **187 passed**; `compileall` PASS; `git diff --check` PASS. Finales Manifest: `dist/experimental/experimental-build.json`; EXE SHA-256 `A721203F811CA56736132716F242552DF3B1D7B195B6903D17E3860B6FEF4D80`; ZIP SHA-256 `78661DB219DEDE2B6EC08CC6899F32AF2D8C942B2FDCC50387337F52BB2B3D62`.

OPEN: Ausschließlich Tristans visueller Vergleich der zwei finalen Runtime-Screens mit den bereitgestellten Optimizer-Referenzen.

NEXT: Keine weitere Arbeit. Bis zu einer neuen ausdrücklichen Freigabe: `WAITING_FOR_TRISTAN`.

MODEL_PROFILE: terra

MODEL_REASON: Eng begrenzte Runtime-Visualkalibrierung einer bestehenden native Desktopoberfläche ohne Logik-, Daten- oder Sicherheitsänderung.

COMPUTER_USE: yes

COMMIT/PR: `b244f73 feat: refine optimizer visual fidelity`; `b5dea12 docs: record optimizer visual fidelity handoff`; both pushed to `origin/dev/v1-foundation`.

## 2026-08-22 — Optimizer Reference-Locked Rebuild

STATUS: `WAITING_FOR_TRISTAN`

TASK: Ausschließlich die sichtbare Optimizer-Oberfläche anhand der zwei verbindlichen Optimizer-Referenzen neu strukturieren. Backend-, Evidence-, Matrix-Pack-, Rule-Pack- und read-only-Sicherheitslogik bleiben unverändert; keine andere Seite und keine weitere Produktarbeit.

BRANCH: `dev/v1-foundation`

CHANGED: Die bisherige lineare native Optimizer-Darstellung wurde als Layout nicht weiterverwendet. Die bestehende Tk-Desktopbasis bleibt erhalten (in diesem Checkout existiert kein PyWebView-/WebView2-Host). Die Übersicht besitzt jetzt Sidebar, Titel plus echte System-Check-Hardwarechips, große Empfehlungen-/Statusfläche mit denselben read-only-Zahlen, vier echte Domain-Karten im 2x2-Raster und eine feste rechte `DETAILS & ERKLÄRUNG`-Spalte. Das System-Detail hat Rücknavigation, Kennzahlen, Suche, Statusfilter und eine vier-spaltige echte Ergebnisliste; die Auswahl füllt die rechte Erklärung. Evidence/Provenance/Pack-/Rule-ID-Rohdaten erscheinen ausschließlich über `Technische Details`. Die neuen Helfer filtern und kürzen nur die vorhandenen Resultatprojektionen; vollständige unveränderte Werte bleiben im Detail sichtbar. Keine Regel, Hardwareaussage, Empfehlung, Apply-/Restore-Funktion, Engine oder Datenquelle ergänzt.

RUNTIME EVIDENCE: Nach dem finalen Packaging wurden exakt die zwei verlangten Runtime-Screens im frischen Portable geöffnet und erfasst: (1) Optimizer-Übersicht bei normaler Experimental-Auflösung mit Header-Chips, großer Statusfläche, 2x2-Kartenraster und fixer Detailspalte; (2) System Optimizer nach Öffnen der echten Karte mit Rücknavigation, Kennzahlen, Suche/Filter, Einstellung/Aktueller Zustand/Improve Empfehlung/Status und einer ausgewählten realen Zeile in der rechten Detailspalte. Der technische Detail-Button ist sichtbar, aber nicht standardmäßig geöffnet. Die frühere Developer-/Evidence-Wand ist in beiden Hauptansichten nicht sichtbar.

CURRENT-vs-TARGET: **PASS für die verbindliche sichtbare Struktur beider Referenzscreens.** Die Laufzeitansicht ist auf den ersten Blick als deren Produktumsetzung erkennbar: nicht mehr als umsortierte lineare Developer-UI. Die Native-Tk-Umsetzung ist bewusst keine pixelgenaue Bitmapkopie; das verbindliche Seitenraster, die Flächenhierarchie, aktive Karten, Detailspalte und Detail-Disclosure sind vorhanden. Reale Daten ersetzen nur Mockupwerte; fehlende Network-Qualität bleibt `PREVIEW`, unbekannte bzw. nicht empfohlene Sachverhalte bleiben fail-closed.

VERIFIED: `python -m compileall -q src` PASS; vollständige Suite **187 passed**; `git diff --check` PASS; finaler Portable-Build samt Manifest PASS. EXE SHA-256 `E48214C3F41D61A64E52EC1030733C9FEF4AC5532F3958FBF0AF272B14E7F7F4`; ZIP SHA-256 `CFEF0F406CDCF768A17ABCFCCBFEB88495937A7781CE3B5E0C341C805786A1BB`. Nach den beiden Screens keine weitere UI-Interaktion oder Produktänderung.

OPEN: Ausschließlich menschlicher Sichtcheck der zwei bereitgestellten Referenzen gegen den aktuellen Portable. Keine bekannte funktionale oder sicherheitsrelevante Abweichung innerhalb dieses Slices.

NEXT: Tristan prüft nur Optimizer-Übersicht und System Optimizer im neuen Portable gegen die Referenzbilder. Bis zu einer neuen, expliziten Freigabe: `WAITING_FOR_TRISTAN`.

MODEL_PROFILE: terra

MODEL_REASON: Bestehende native Desktopoberfläche mit eng begrenztem Strukturumbau, echten read-only Evidenzdaten und Runtime-Visualprüfung ohne Framework- oder Sicherheitswechsel.

COMPUTER_USE: yes

COMMIT/PR: `3d0004d feat: rebuild optimizer reference layout`; `547a314 docs: record optimizer reference handoff`; both pushed to `origin/dev/v1-foundation`.

## 2026-08-22 — UI Visual Source-of-Truth final Portable inspection

STATUS: `WAITING_FOR_TRISTAN`

TASK: Ausschließlich den vorhandenen finalen Portable-Build gegen die verbindlichen sichtbaren Masterseiten prüfen; fünf Runtime-Screens erfassen, den aktuellen Abgleich abschließen und keinen Produkt-, Optimizer-, Benchmark- oder Infrastruktur-Slice beginnen.

BRANCH: `dev/v1-foundation`

CHANGED: Vor der freigegebenen Sichtprüfung bereits im bestehenden UI-Source-of-Truth-Pass umgesetzt: Sidebar-Active-State als dunkle integrierte Fläche mit kurzer Cyan-Führung statt technischem Cut-out; Dashboard-`Zum Analyzer` über dieselbe bewusste Action-Komponente wie die Top-Module; System Optimizer als sichtbare Hauptansicht; vier gleich große echte Bereichskarten mit sichtbaren Aktionen; Evidence-Matrix/Pack-Details standardmäßig verborgen. Im finalen Prüfschritt nur Dokumentation/Handoff ergänzt, keine fachliche Logik geändert.

RUNTIME EVIDENCE: Frischer finaler Portable wurde direkt gestartet. Captures: (1) Dashboard/Home, (2) Analyzer / no-demo preflight, (3) Optimizer-Hauptübersicht, (4) System-Optimizer-Sicht, (5) Tactical-Replay-Empty-State. Dashboard und Analyzer zeigen die dunkle Shell sowie den gefüllten Sidebar-Active-State. Optimizer zeigt `SYSTEM OPTIMIZER` zuerst, danach vier klare selektierbare Karten und erst darunter den read-only System Check; technische Details sind nur hinter `Technische Evidenz & Pack-Details anzeigen`. Tactical Replay zeigt wahrheitsgemäß keine Szene und die drei echten Vorbereitungsschritte, ohne Replay-Daten zu erfinden.

CURRENT-vs-TARGET: Dashboard/Analyzer sind **FINAL POLISH**, nicht pixelgleich: Card-/Button-Material wirkt noch technischer als die Master-Flächentiefe; vor einem Demoimport bleiben CT/T-Flächen ehrlich leer. Optimizer-Hierarchie ist **PASS**: Hauptansicht → vier Karten → System Check, keine rohen Matrixdetails als Hauptoberfläche. System Optimizer insgesamt ist **ÄNDERN**, nicht global akzeptiert: Der Runtime-Viewport zeigte den obenliegenden Status/System-Check, aber trotz bereits geladenem Scan keinen separat sichtbaren `Dein System im Überblick`/per-setting Ergebnisbereich; der verwendete Scroll-Versuch bewegte die Ansicht nicht. Dieser Befund wird nicht durch einen behaupteten PASS verdeckt und ist für einen späteren explizit freigegebenen UI-Pass zu diagnostizieren. Tactical-Replay-Empty-State ist **PASS** für Wahrheit und Hierarchie; seine zusätzliche Leere ist bei fehlender Scene erwartbar.

VERIFIED: `compileall` PASS; vollständige Suite `185 passed`; `git diff --check` PASS. Frischer finaler Portable Build PASS: EXE SHA-256 `257110984B264B6A0C25F591893D8D324B9B3BEDC2AE2CBEE9354731AFCDE19F`, ZIP SHA-256 `D4A1F4E1CADCCB48F3446661F5A5D711B34F4C854CE8953872A68608B4B1FA14`; Manifest `dist/experimental/experimental-build.json`; kein Setup, da keine akzeptierte Installer-Toolchain vorhanden ist. Ein erster Packaging-Lauf enthielt einen lokalen `RoundedHomeAction.pack`-Runtimefehler; er wurde vor diesem finalen Artefakt korrigiert. Der finale Portable startete anschließend ohne Ausnahme.

DECISIONS: Keine neue Rule, keine Evidence-/Recommendation- oder Apply-/Write-Änderung. Unknown/Conditional/Insufficient-Evidence bleiben unverändert fail-closed. Die Details bleiben erreichbar, nur nicht als Standardoberfläche.

OPEN: Nur die spätere, explizit zu beauftragende Diagnose des System-Optimizer-Ergebnisviewport/Scrollpfads und die optischen Final-Polish-Punkte. Keine weitere Arbeit in diesem Handoff.

NEXT: Tristan prüft den gepushten finalen Portable gegen die hier festgehaltenen Screens und entscheidet, ob der sichtbare System-Optimizer-Ergebnisbereich als eigener UI-Korrekturpass beauftragt wird. Bis dahin: `WAITING_FOR_TRISTAN`.

MODEL_PROFILE: terra

MODEL_REASON: Bestehende native Windows-Oberfläche, echter Build-Runtime-Abgleich und fail-closed Produktgrenzen ohne Architekturwechsel.

COMPUTER_USE: yes

COMMIT/PR: `9bc525c feat: align shell structure to visual targets`; documentation checkpoint and push follow this line on `dev/v1-foundation`.

## 2026-08-21 — Embedded Analyzer Review product slice

STATUS: review
TASK: Den real abgenommenen Analyzer-/NetCon-Pfad als eingebetteten Review in die bestehende Midnight-/Metallic-Shell integrieren, ohne zweite Review-Engine oder neue Produktfunktion.
BRANCH: `dev/v1-foundation`
CHANGED: Neuer dünner `EmbeddedReviewSession` liest ausschließlich das fail-closed validierte `iy.analysis_flow/v1`, stellt Runde, exakten Tick, belegten Timecode, Kontext, Marker, Spielernamen, objektive Anker und Rule-IDs bereit und delegiert jeden CS2-Sprung unverändert an `Cs2ReviewCoordinator.open_scene(scene_id, tick)`. Der bestehende `iy.review_state/v1`-Vertrag akzeptiert nun kanonische explizite Scene-IDs; Status und Notiz bleiben source-/scene-bound, längenbegrenzt und atomar lokal gespeichert. `AnalyzerShellApp` zeigt Szenenliste und Detail innerhalb desselben Analyzer-/Review-Reiters; `Review anzeigen` öffnet keinen Browser. Der HTML-/Review-Server bleibt nur als ausdrücklich beschrifteter `HTML-Export im Browser (Fallback)`. Spezifikation: `docs/EMBEDDED_ANALYZER_REVIEW_V1.md`. Tests: `tests/test_embedded_review.py`. Keine Parser-, Indikator-, Rule-, Szenen-, Tick-, Benchmark-, Optimizer-, System-, Clip-, OBS- oder Videoänderung.
VERIFIED: Vor Änderung 125/125 Tests PASS. Danach gezieltes Embedded-/State-/Coordinator-/Shell-Gate 27/27 und vollständige Suite 129/129 PASS; `compileall`, Abhängigkeitsprüfung und `git diff --check` PASS. Reale UI mit bestehendem Ancient-Workflow: 54 Szenen innerhalb des Improve-Yourself-Fensters, keine neue Firefox-/Review-Ausgabe, Dark-/Variant-3-Oberfläche, Runde/Tick/Spieler/Regeln/Notiz/Status sichtbar. Drei verschiedene Szenen wurden aus dem Embedded Review über den unveränderten Coordinator erfolgreich an Tick 3654, 4362 und 12577 in `fut-vs-mouz-m2-ancient.dem` geöffnet. Bestehende automatisierte Fehlerabdeckung belegt CS2 offline, laufendes CS2 ohne NetCon/ungeeigneten Startmodus, NetCon ohne aktive Demo, falsche Demo und fremdes Scene-/Tick-Paar fail-closed. Frischer Portable-Build inklusive Tests PASS; EXE SHA-256 `9F8D10B9388690E4BFAD2B06DBB9BE29FDE7CB8DA930D0F4D6703C22CF19C15C`, ZIP SHA-256 `C811534090577B47600705CEC30535CF8A38AB7F8CBDCC602832EF16D2E64ECD`; gepackte EXE startet mit Branding/dunkler Shell.
DECISIONS: Native Präsentationsschicht statt neuer WebView-Abhängigkeit für diesen begrenzten Slice. Bestehender lokaler Review-Server und HTML bleiben kompatibler Export/Fallback, sind aber nicht mehr Hauptworkflow. Eine fehlende Tickrate bleibt `Zeit nicht belegt`; der exakte Tick wird angezeigt und kein 64-Hz-Timecode erfunden.
OPEN: Die reale Ancient-Quelle liefert keine belegte Tickrate, daher ist dort nur Tick, kein abgeleiteter Timecode verfügbar. Setup/Signing bleibt außerhalb dieses Slices unverändert offen. Der finale Portable-Embedded-Workflow benötigt noch Tristans eigener Produkt-Sichtcheck; Quellruntime und gebauter Start sind bereits geprüft.
NEXT: Tristan lädt denselben Ancient-Workflow im neuen Portable-Build, prüft Szenenliste/Notiz/Status und wiederholt einen Tick-Sprung; danach als nächsten getrennten Product Slice die gemeinsame 2D-Tactical-/Embedded-Review-Navigation spezifizieren, ohne neue Analyseautorität.
MODEL_PROFILE: terra
MODEL_REASON: Zusammenhängende native UI-, State-, Sicherheits- und Runtime-Integration auf bestehendem realem Analyzer-Pfad.
COMPUTER_USE: yes

## 2026-08-21 — Real NetCon multi-scene acceptance and connection guidance

STATUS: review
TASK: Tristans erfolgreichen praktischen Ancient-/NetCon-Nachtest übernehmen, den externen Review-Aufruf gegen die V1-UX-Vorgaben abgleichen und den belegten Normal-CS2-vs.-Workshop-Tools-Fehler verständlich unterscheiden.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/cs2_review_coordinator.py` erkennt beim fehlgeschlagenen NetCon-Aufbau read-only, ob `cs2.exe` bereits läuft. Die Meldung unterscheidet nun „CS2 läuft, NetCon fehlt“ mit konkretem Workshop-Tools-/Port-Hinweis von „CS2/NetCon nicht erreichbar“. `tests/test_cs2_review_coordinator.py` deckt beide Zustände ab. Dieser Handoff dokumentiert die Nutzerabnahme. Keine Parser-, Demo-, Regel-, Szenen-, Tick-, Benchmark-, Optimizer- oder Systemlogik geändert.
VERIFIED: Nutzerabnahme mit echter `fut-vs-mouz-m2-ancient.dem`: Demo geladen und verarbeitet, NetCon nach Start über Workshop Tools erreichbar, mindestens drei verschiedene Szenen/Ticks gewählt und jeder Tick zuverlässig in der laufenden Demo angesprungen. Screenshot-/Konsolenevidenz belegt `de_ancient`, `valve_demo_2` sowie 130.466 Playback-Ticks/-Frames. Prozessprobe erkannte den real laufenden `cs2.exe`; gezielte Coordinator-Tests 4/4 und vollständige Suite 125/125 PASS; `git diff --check` PASS.
DECISIONS: Der Browser-Review ist der aktuelle lokale V1-Adapter (`127.0.0.1`, Origin-/Scene-/Tick-geprüft), aber kein dokumentierter finaler UX-Vertrag. Die bindende UI-Spezifikation behandelt Analyzer/Review als Kernworkflow der gemeinsamen Anwendung; Empfehlung: Review im finalen UX-Flow in die Improve-Yourself-UI integrieren und Browser/HTML nur als lokalen Export-/Fallbackpfad behalten. Eine konkrete WebView-/native Rendererwahl bleibt eine freizugebende Implementierungsentscheidung.
OPEN: Finale Entscheidung über eingebetteten Review-Host und Browser-Fallback; `tasklist` kann bei nicht bestimmbarer Prozesslage bewusst nur die generische sichere Meldung liefern.
NEXT: Den aktuellen Portable-Build mit laufendem normalem CS2 gegen die neue falscher-Modus-Meldung und danach mit Workshop-Tools-NetCon gegen READY praktisch nachtesten; anschließend den eingebetteten Review als eigenen begrenzten UI-Slice spezifizieren.
MODEL_PROFILE: terra
MODEL_REASON: Begrenzte Runtime-Diagnose und sichere UX-Fehlerzustände mit Windows-Prozessgrenze.
COMPUTER_USE: no

## 2026-08-21 — Final Portable real-workflow acceptance

STATUS: review
TASK: Den gepushten finalen Portable-Build über den normalen Produktdialog mit dem frisch erzeugten echten Ancient-Workflow laden und die real freigeschalteten Zustände prüfen.
BRANCH: `dev/v1-foundation`
CHANGED: Nur dieser Handoff. Keine Produkt-, Workflow-, Ergebnis-, Packaging- oder Systemdatei geändert. Der ignorierte reale Workflow wurde ausschließlich gelesen.
VERIFIED: `Improve Yourself Experimental.exe` aus dem finalen Portable-Artefakt gestartet; `Vorhandene Analyse öffnen` und der native Dateidialog verwendet; `results/experimental-build-e2e/c183dd61fc6a/demo-workflow.json` nach vollständiger fail-closed Hashprüfung erfolgreich geladen. Sichtbar bestätigt: `de_ancient`, 54 Szenen, Review bereit, Quelle `fut-vs-mouz-m2-ancient.dem`, Hashpräfix `c183dd61fc6a`, Parser PASS, 18 Runden, 10 Spieler, 3.179 Grundevents sowie korrekte CT-/T-Line-ups. Reports zeigt 54 Szenen und aktivierte Report-/Timeline-Aktionen; Tactical Replay ist aktiv. Keine UI-Ausnahme oder helle Produktfremdfläche; Build anschließend sauber geschlossen.
DECISIONS: Keine. Der normale Restore-Pfad ist nun zusätzlich im tatsächlich verteilten EXE mit realen Daten belegt; dies ersetzt keine menschliche Inhaltsbewertung der Szenen und keine CS2-Live-Readiness-Prüfung.
OPEN: Tristan prüft weiterhin Szeneninhalte, Notizen/Review und CS2-Tick im eigenen Lauf. Setup bleibt `NEEDS_INSTALLER_SPEC`.
NEXT: Tristan verwendet denselben Portable-ZIP für den praktischen Review; Engineering ändert danach nur konkret gemeldete Laufzeit-/UI-Befunde.
MODEL_PROFILE: terra
MODEL_REASON: Reale Windows-Runtime-Abnahme an der verteilten EXE-/Workflow-Grenze.
COMPUTER_USE: yes
COMMIT/PR: pending documentation-only checkpoint on `dev/v1-foundation`.

## 2026-08-21 — Branded Portable Experimental integration

STATUS: review
TASK: Aktuellen Funktionsstand mit der verbindlichen UI-/Branding-Masterreferenz verbinden, vollständig regressionsprüfen und als praktisch testbaren Experimental-Build ausgeben.
BRANCH: `dev/v1-foundation`
CHANGED: Kanonische `Improve-Yourself-Logo-Variante-3-vollstaendig.png` bytegenau als `improve-yourself-logo-v3-full.png` integriert; deterministische kompakte PNG-/ICO-Exports ausschließlich aus dem genehmigten Balken-/Final-I-Bereich ergänzt. Shell verwendet die Marke als Fenster-/Taskleistenicon, konsistentere Card-/Button-Borders und ein eigenes vollständig dunkles Regeldetail-Unterfenster. Reproduzierbare PyInstaller-Portable-Pipeline, Build-Lock, Spec, ZIP und Buildmanifest ergänzt. Gepackter Standardausgabepfad nach realem Laufzeitbefund auf `%LOCALAPPDATA%\Improve Yourself\Experimental\results` korrigiert. Keine Parser-, Rule-, Szenen-, Replay-, Benchmark-, Optimizer- oder Systemänderungslogik geändert.
VERIFIED: Canonical source SHA-256 `3b33d2af88e97092506a1005012ba315e0484800585ef215b379f3f28390a25b`, 490x770; Brandingtests prüfen Quelle und PNG/ICO. Frischer echter E2E-Lauf aus `fut-vs-mouz-m2-ancient.dem`: Awpy PASS, `de_ancient`, 18 Runden, 10 benannte Spieler, 3.179 grundlegende Events, 235 Indikatoren/Regelresultate, 54 zusammengeführte Szenen und READY_FOR_REVIEW mit Review/Timeline/Tactical/Report/CS2-Ticks. Read-only System Check real: 6 OK, 2 REVIEW, 0 ACTION_REQUIRED. Portable EXE startete zweimal; Brand/Icon, dunkle Titelleiste, Analyzer, Dashboard, Rules, Reports, System Check, Settings und Tactical Replay öffneten crashfrei. Erster Packaged-Lauf deckte falschen cwd-abhängigen Profilpfad auf; Regressionstest und zweiter Lauf belegen den korrigierten LocalAppData-Pfad. Finaler Full-Gate-Build: 125/125 Tests, Buildabhängigkeiten, PyInstaller, ZIP, `compileall` und `git diff --check` PASS. EXE SHA-256 `d5c2fe8fbed6f7b18cc3ee20fd6f963b4b295313da9c77958d69d0304fbd0018`; Portable-ZIP SHA-256 `efae02edc21dfa58f347f46134dbf73ff1e524ef8a26e8066f95f94aa1115e98`.
DECISIONS: Portable ist die einzige behauptete Distribution. Kein Setup erzeugt, weil kein akzeptierter Installer-/Upgrade-/Uninstall-/Signingvertrag und keine unterstützte Installer-Toolchain bestehen. Kein `NEEDS_BRAND_ASSET`: Vollmarke ist vorhanden und hashgesichert. `System Check / Optimizer` bleibt `PARTIAL_REFERENCE`; Setup bleibt `NEEDS_INSTALLER_SPEC`, nicht `NEEDS_UI_REFERENCE`.
OPEN: Setup/Installer, Code Signing und menschliche Gesamtproduktabnahme bleiben offen. Native Windows-Dateiauswahldialoge folgen dem Betriebssystem; eigene Produktunterfenster bleiben dark. Der Portable-Build ist nicht signiert und Windows kann deshalb einen unbekannten Herausgeber anzeigen.
NEXT: Tristan entpackt den Portable-ZIP, startet `Improve Yourself Experimental.exe`, lädt die echte Ancient-Demo und prüft nacheinander Preflight/Line-ups, Full Demo und Player Select, Profile/Rules, 54 Szenen, Review/Tactical/Reports sowie den read-only System Check. Danach nur konkrete Laufzeit-/UI-Befunde priorisieren; Installer separat spezifizieren.
MODEL_PROFILE: terra
MODEL_REASON: Zusammenhängende UI-/Branding-/Packaging-Integration mit realem Demo- und Windows-Runtime-Gate.
COMPUTER_USE: yes
COMMIT/PR: pending final gate and push on `dev/v1-foundation`.

## 2026-08-21 — Improve Yourself Experimental consolidation

STATUS: waiting_for_tristan
TASK: Consolidate the existing real Analyzer/Review/Tactical Replay foundation into one early tester-facing Experimental workflow without restarting or pulling excluded V2/V3/benchmark/Optimizer/video work into scope.
BRANCH: `dev/v1-foundation`
CHANGED: Real demo import now ends at `READY_FOR_SELECTION` with an objective no-scene preflight exposing map, rounds, parser PASS, basic event count and named CT/T line-ups. Explicit analysis then applies Full Demo/Player Select and a local Review/Highlight/Coaching/Custom profile to the existing indicator->rule->profile->merged-scene engine. Added safe atomic `iy.analysis_profile/v1` local JSON storage and compact Custom rule toggles/details. Completed outputs now include neutral Review, Timeline, exact CS2 commands, a Tactical Replay projected from the same ReplayStore/selected scenes and `iy.analysis_report/v1`. Removed the visible Clip-worthy review choice in favor of neutral Follow-up while retaining legacy read compatibility. Consolidated Tk shell uses Improve Yourself / Make Up Your Mind. / Experimental, a native dark title bar, disclosed workflow/source/hash/profile path and disabled dependent controls before load. No 3D/POV, benchmark, Optimizer/System Check, OBS/video, ML or CS2 display-setting change.
VERIFIED: 119/119 tests, locked dependency check, eight CLI smokes, compile and diff check PASS. Visible Windows QA confirmed a single dark surface including native title bar, fixed branding/claim, pending preflight identity and disabled initial actions; the window closed cleanly. Existing real Ancient source truth `c183dd61…` reopened and reran through the new downstream path: 18 rounds, 10 players, 235 objective indicators/rule matches, 54 merged scenes, Timeline/Review, 28,335,824-byte Tactical Replay and 54-scene neutral report; first scene remains `r1-t3654-0` / tick 3654, already runtime-accepted in CS2. The original demo is absent at known direct paths, so no new parse is claimed; prior real Awpy/hash/runtime evidence plus current canonical-store rerun is the evidence chain. Release-hygiene search found no new personal paths, secrets, demos or generated results in tracked changes.
DECISIONS: Preflight is parse/replay evidence only and emits zero rule scenes. Profile filtering retains indicators and selects named objective rules; no profile is a suspect engine. Tactical Replay scenes are a derived projection over the same canonical frames and chosen analysis scenes, not a second demo interpretation. `clip-worthy` remains validation-only for old saved state and is absent from current UI. Local profile location is shown and user-controlled; no cloud/account layer.
OPEN: First complete product review, final packaging/installer and merge acceptance require Tristan. The known Hammer/VRAD SDK blocker remains unrelated and parked. Original Ancient `.dem` would be required only for a fresh parser rerun, not to validate the preserved hash-bound replay truth.
NEXT: None before review. Stop feature development and remain `WAITING_FOR_TRISTAN`.
MODEL_PROFILE: terra
MODEL_REASON: Cross-component workflow consolidation, state separation, local persistence, UI and real-evidence validation.
COMPUTER_USE: yes; the Experimental Windows shell was visually checked, the native light title-bar defect was found and corrected with dark DWM presentation, then rechecked and closed. No CS2/Steam/system setting interaction.

## 2026-08-21 — Shared Base full-status synchronization

STATUS: done
TASK: Consolidate the complete current Beast/project status into the shared Agent Base and push it without implicitly merging to `main`.
BRANCH: `dev/v1-foundation`
CHANGED: Expanded `docs/AGENT_BASE.md` with the synchronized branch/gate, real Ancient E2E evidence, shared replay truth, Analyzer-shell restore/relink/action-bound security, CS2 coordinator boundary, 2D and 3D/POV state, read-only System Check, local workflow, benchmark blocker, strict scope exclusions and the exact next engineering step. Updated the stale 33-test/five-CLI summary in `coordination/CURRENT.md` to the current 113-test/eight-CLI evidence. No product code, generated results, runtime files, benchmark assets or `main` change.
VERIFIED: Documentation cross-checked against current handoff, CURRENT cockpit, clean `dev/v1-foundation` at `4d4c161cf3dc10a6202253a7ee3ebf49fe31ecf3`, and the immediately preceding full 113/113 + dependency + eight-CLI + compile + diff PASS. This documentation-only synchronization receives an additional diff check before push.
DECISIONS: `docs/AGENT_BASE.md` is now the complete shared entry snapshot, while `coordination/CURRENT.md` remains the operative detail authority and this handoff retains chronological engineering evidence. `main` is not changed without explicit review/merge authorization.
OPEN: Merge/release acceptance remains Tristan's decision. Hammer multi-map compile remains parked on the documented Valve/SDK script-asset blocker.
NEXT: Continue only with the Base-listed Analyzer-shell usability slice: disable workflow-dependent controls until load and display manifest/source/hash identity; do not change validation/parser/review behavior.
MODEL_PROFILE: luna
MODEL_REASON: Repository-status reconciliation and documentation-only synchronization with no architecture or product-code change.
COMPUTER_USE: no; repository evidence was sufficient.
COMMIT/PR: this synchronization commit on `dev/v1-foundation`.

## 2026-08-21 — Action-bound workflow revalidation

STATUS: done
TASK: Revalidate the open workflow immediately before selection rerender and CS2 coordinator creation, failing closed without watchers, scans or a cached trust model.
BRANCH: `dev/v1-foundation`
CHANGED: `AnalyzerShellController.validate_current_workflow()` is now the single action-bound gate. Selection rerender invokes it before calling the injected rerenderer. CS2 coordinator creation invokes it before reading the flow/name and performs the potentially multi-second artifact/chunk validation on the existing worker thread. Preflight clears all prior connection/demo/filename indicators before starting and again on any integrity/runtime exception. No parser, rule, scene, timeline, CS2 command, file watcher, background scan, Optimizer/System Check or benchmark change.
VERIFIED: 113/113 tests, dependency check, eight CLI smokes, compile and diff check PASS. New tests mutate a previously accepted review/flow artifact and prove that rerender is never invoked and the review boundary rejects the changed source metadata. Existing 12/12 focused analyzer-shell tests pass.
DECISIONS: Trust is recomputed at each consequential action from the manifest and local artifacts; the shell does not retain a second trust cache. Full replay-chunk validation remains intentional evidence even though a real 18-round workflow takes several seconds, so it stays off the GUI thread.
OPEN: Workflow-dependent controls remain clickable before any workflow is loaded and communicate the missing prerequisite only after the action. Final styling/packaging remains deferred.
NEXT: Disable `Quelldemo zuordnen`, selection controls, `Analyse starten` and `CS2 prüfen` until a workflow result is loaded, then show the loaded manifest basename/source basename and abbreviated source hash as explicit local identity. Keep `Demo auswählen` and `Vorhandene Analyse öffnen` always available; do not alter validation, parsing or review behavior.
MODEL_PROFILE: terra
MODEL_REASON: Narrow trust-boundary closure and asynchronous UI failure semantics with deterministic regression coverage.
COMPUTER_USE: no; integrity behavior is controller/thread state and required no external application interaction.

## 2026-08-21 — Hash-bound source-demo relink

STATUS: done
TASK: Execute only the documented explicit source-demo relink for an already open workflow, with exact SHA-256 equality and no discovery/copy/reparse behavior.
BRANCH: `dev/v1-foundation`
CHANGED: Analyzer shell now exposes `Quelldemo zuordnen`. The user selects one existing `.dem`/`.dem.zst`; the controller first revalidates the open workflow, streams the source through SHA-256, rejects any mismatch without touching the manifest, and on equality atomically persists only `source_demo_name` as a basename. The UI resets stale readiness and immediately rechecks CS2 after success. No absolute source path, parser invocation, file copy/rename, folder scan, rule/scene/timeline, Optimizer/System Check or benchmark change.
VERIFIED: 111/111 tests, dependency check, eight CLI smokes, compile and diff check PASS. Tests prove matching-basename-only persistence, absence of the private parent path, mismatch byte preservation and temp-file cleanup. No original Ancient source was present at the three already known direct candidate paths, so no new real-source relink PASS is claimed; the prior real workflow restore remains valid.
DECISIONS: Hash equality is the only accepted identity bridge between an existing workflow and a user-selected source. Write happens only after full streaming digest completion and uses same-directory replace. Successful linking triggers fresh runtime evidence rather than carrying forward an old green readiness state.
OPEN: A manifest can still be externally altered after opening and before a later rerender/review action; those action boundaries should independently revalidate it. Final styling/packaging remains deferred.
NEXT: Revalidate the currently open `demo-workflow.json` and required artifacts immediately before selection rerender and CS2 coordinator creation, then fail closed and clear readiness if anything changed since open. Do not add watchers, background scans or a second cached trust model.
MODEL_PROFILE: terra
MODEL_REASON: Narrow local identity/write boundary with deterministic mismatch safety and UI refresh.
COMPUTER_USE: no; no new visual/runtime semantics beyond the labeled source action and automatic existing preflight.

## 2026-08-21 — Existing-analysis restore path

STATUS: done
TASK: Add only the explicit existing-workflow restore path documented by the prior handoff, without folder scanning, recent-result selection or Awpy reparse.
BRANCH: `dev/v1-foundation`
CHANGED: Analyzer shell now offers `Vorhandene Analyse öffnen` for an explicitly selected `demo-workflow.json`. The controller fail-closes on schema/status/policy/source-hash errors, missing/absolute/escaping required artifact paths, inconsistent analysis/replay/flow/timeline hashes, altered replay chunks, selection/count mismatches and empty review output. On PASS it restores the persisted roster, Full Demo/Player Select state, scenes and review directly. No parser, rule, scene, timeline, CS2 command, Optimizer/System Check or benchmark change.
VERIFIED: 109/109 tests, dependency check, eight CLI smokes, compile and diff check PASS. Focused tests prove valid no-runner restore and reject malformed hash, traversal, missing artifact and replay-source mismatch. The ignored real Ancient workflow reopened without Awpy in 6.3 s and restored `de_ancient`, 10 named players, Full Demo and 54 real scenes; its older manifest truthfully exposes no source filename, so CS2 exact-filename readiness remains unavailable rather than inferred.
DECISIONS: Explicit manifest selection is the only discovery mechanism. Every required artifact must remain under the selected workflow root. Reopening validates stored source metadata against every canonical replay chunk but does not claim the original `.dem` still exists because its private absolute path is not persisted. Legacy missing `source_demo_name` is not guessed from directories or unrelated files.
OPEN: Older valid workflows can reopen but cannot pass exact-filename CS2 readiness until a source identity is explicitly and hash-safely supplied. Final styling/packaging remains deferred.
NEXT: Add an explicit `Quelldemo zuordnen` action for an already open workflow: user selects one `.dem`/`.dem.zst`, the shell computes and requires exact SHA-256 equality before persisting only its basename as `source_demo_name`, then resets/rechecks readiness. Do not scan, infer, rename, copy or reparse the demo.
MODEL_PROFILE: terra
MODEL_REASON: Narrow security-bounded restore and desktop-state integration with real artifact validation.
COMPUTER_USE: no; controller/real-artifact behavior was validated directly, and no new runtime visual semantics were introduced beyond one labeled button.

## 2026-08-21 — Analyzer-shell CS2 readiness preflight

STATUS: done
TASK: Add the documented explanatory preflight to the desktop shell without launching/restarting CS2, editing Steam options or copying demos.
BRANCH: `dev/v1-foundation`
CHANGED: Added immutable `ReviewPreflight` and `Cs2ReviewCoordinator.preflight()` with separate netcon-reachable, demo-active and exact-filename states plus user-facing corrective messages. Analyzer shell now shows a CS2-Readiness panel and `CS2 prüfen`; Review remains disabled until all three checks pass. Review click repeats the probe asynchronously before opening, so stale green state cannot authorize a later launch. Import/selection changes reset readiness. No parser, rule, scene, timeline, CS2 launch or file-management change.
VERIFIED: 104/104 tests, dependency check, eight CLI smokes, compile and diff check PASS. Visible Windows smoke confirmed the three-state panel, explanatory message and disabled Review initial state. Live CS2 preflight returned PASS for reachable/[DEMO]/`iy_ancient.dem`, and correctly returned filename FAIL for expected `fut-vs-mouz-m2-ancient.dem` while `iy_ancient.dem` was active. Missing netcon and inactive-demo paths are deterministic tests.
DECISIONS: Readiness is evidence, not inference: reachable netcon alone is not demo-ready; demo mode without a disclosed filename is not identity-ready; renamed files are not assumed equivalent. Review is revalidated at action time and all checks run off the GUI thread.
OPEN: The shell currently imports/parses a demo per new session; it cannot explicitly reopen a previously generated workflow manifest. Final styling/packaging remains deferred. CS2/netcon preparation stays manual and instructional.
NEXT: Add an explicit “Vorhandene Analyse öffnen” path that validates an existing `iy.demo_workflow/v1` manifest, source hash metadata and required local artifacts, then restores roster/selection/review without Awpy reparse. Do not scan arbitrary folders, silently select recent data or weaken local-path validation.
MODEL_PROFILE: terra
MODEL_REASON: Narrow state/UI integration with fail-closed runtime checks and deterministic coverage.
COMPUTER_USE: yes; local shell layout/state was visually checked and closed cleanly; no CS2 input was issued.

## 2026-08-21 — Fail-closed scene-to-CS2 review coordinator

STATUS: done
TASK: Bind an existing generated review scene to a narrow local CS2 tick coordinator with demo-readiness, exact-demo and exact-scene validation; no broader CS2 process ownership.
BRANCH: `dev/v1-foundation`
CHANGED: Added `cs2_review_coordinator.py`: fixed-loopback netcon client, evidence-led `status` + `demo_info` readiness probe, exact expected demo filename check, immutable scene-ID/tick allowlist from `analysis-flow.json`, and origin-/size-limited loopback HTTP endpoint. Review scenes now expose “In CS2 öffnen” with visible sent/error status. Analyzer shell serves the existing review through the coordinator and closes the service with the window. Workflow manifests disclose only the source demo basename needed for identity comparison. No parser/rule/timeline/process-launch change.
VERIFIED: 103/103 tests, dependency check, eight CLI smokes, compile and diff check PASS. Tests reject altered tick, unknown scene, wrong demo, foreign Origin and oversized/invalid requests without sending a tick. Live installed-CS2 probe returned `Client: Connected [DEMO]`, `Demo contents for iy_ancient.dem`, and the real coordinator accepted only `r1-t3654-0`/`3654`, sent it, and visibly returned Ancient to about 0:57 in the first-round context.
DECISIONS: Fail closed unless CS2 is reachable on `127.0.0.1`, reports active `[DEMO]` playback, and `demo_info` matches the workflow's expected basename. Readiness commands are read-only; the sole state-changing command is the generated `demo_gototick`. The server binds only loopback, accepts same-origin POST only, and validates against canonical flow data rather than browser input.
OPEN: The coordinator does not launch/restart CS2, add `-netconport`, copy/rename demos or infer equivalent filenames. If the CS2 runtime copy was renamed, identity validation correctly rejects it until the expected workflow/demo filename and active filename match. Final product UX for preparing CS2/netcon remains separate.
NEXT: Add a narrow preflight panel to the desktop shell that explains and verifies the three prerequisites before opening review: local netcon reachable, active demo playback, exact filename match. It may display corrective instructions but must not launch/restart CS2, edit Steam options or copy demos automatically.
MODEL_PROFILE: terra
MODEL_REASON: Security-bounded local coordination and UI integration with real runtime evidence.
COMPUTER_USE: yes; read-only screenshot confirmed the real coordinator's generated tick landing in installed CS2; no CS2 UI input was issued in this slice.

## 2026-08-21 — Real-demo Analyzer desktop shell slice

STATUS: done
TASK: Integrate the proven `iy-demo-workflow` as the Analyzer's first local desktop import/selection/review slice without creating a second parser, roster, rule or scene authority.
BRANCH: `dev/v1-foundation`
CHANGED: Added `analyzer_shell.py` with a testable controller and thin Tk desktop adapter: `.dem`/`.dem.zst` selection, background import, named CT/T line-ups, distinct Full Demo and Player Select modes, deduplicated dropdown + Add Player, CT/T/Reset, analysis rerender and existing review launch. Refactored `demo_workflow.py` only to expose selection rerendering from its existing replay-v2 artifact; no reparse and no rule changes. Added `iy-analyzer-shell`, tests and its eighth setup smoke. Fixed the pre-existing PowerShell/Python quoting bug in Setup-V1's Python-version probe.
VERIFIED: 100/100 tests, dependency check, eight CLI smokes, compile and diff check PASS. Visible Windows smoke showed the local shell and all required controls; it closed cleanly. Real ignored Ancient ReplayStore selection reused the existing parse for player `steam:76561198063336407`, produced 22 real scenes in `player_select`, then successfully restored Full Demo. No fake result or second interpretation path was used.
DECISIONS: Shell is an adapter over `run_demo_workflow`/`rerender_demo_workflow`; canonical replay-v2 remains the single replay truth. Reset means empty Player Select and cannot silently analyze as Full Demo. An explicit Full Demo action is required to return to all-player analysis. Parsing/rerender work runs off the GUI thread.
OPEN: The shell is a functional engineering UI, not final branded product styling. It opens the existing self-contained review in the default browser; direct CS2 process/netcon lifecycle ownership is deliberately not added. Packaging/installer integration is still open.
NEXT: Bind a selected scene in the existing review output to a narrow local “Open in CS2” coordinator that validates demo readiness and sends only the scene's generated `demo_gototick`, with explicit status/error reporting. Do not add OBS/video, ML verdicts, a second timeline or broader CS2 process management.
MODEL_PROFILE: terra
MODEL_REASON: Standard multi-file controller/UI integration with real-data reuse and test coverage.
COMPUTER_USE: yes; startup layout/control presence and clean close were visually checked for the local desktop shell only.

## 2026-08-21 — Runtime-compatible Ancient end-to-end proof

STATUS: done
TASK: Close the remaining real Demo→Awpy→Selection→Rules→Merged Scenes→Timeline/JSON→CS2 tick-review criterion without changing the accepted analyzer rules.
BRANCH: `dev/v1-foundation`
CHANGED: No analyzer code or rule change. Ran the existing `iy-demo-workflow` unchanged on `fut-vs-mouz-m2-ancient.dem`; generated match artifacts remain ignored/local. Added only this completion evidence and the matching E2E evidence note.
VERIFIED: Source SHA-256 `c183dd61fc6a619f7af435d45eab374cd6f0097a7bd0da779971b15ef6746f7f`, 270,062,278 bytes. Awpy 2.0.2 completed: Ancient, 18 rounds, 10 named players, 235 objective indicators/rule matches merged into 54 scenes. Timeline/JSON/HTML/commands were produced. First scene is round 1 with generated `demo_gototick 3654`. The installed CS2 client loaded and normally played the same demo beyond the earlier incompatible-source failure point. After demo readiness, `demo_gototick 3654` was issued over localhost-only netcon and visibly returned to the first-round combat context; `demo_togglepause` then held the review at 0:58.3 with no parse error. Existing full gate remains 97/97 tests, dependency check, seven CLI smokes and diff check PASS.
DECISIONS: The earlier Mirage failure remains valid source-demo incompatibility evidence but is no longer the acceptance source. Ancient supplies the runtime-compatible proof. No rule threshold, scene window, parser interpretation or evidence requirement was weakened. Local netcon was used only to avoid startup-command timing and transmitted nothing externally.
OPEN: Product-shell wiring for choosing a `.dem`, displaying roster selection and opening generated review output is not implemented by this proof. The temporary CS2 game-directory copies `iy_review.dem` and `iy_ancient.dem` remain local; removal requires an explicit cleanup action. Toggle Console may still need manual restoration from temporary `F6` to the user's original `^` if not already restored.
NEXT: Integrate the proven `iy-demo-workflow` as the Analyzer shell's real local import action and bind its existing roster/Full Demo/Player Select/review output without duplicating parsing or rule state. Keep Optimizer/System Check, video/OBS/ML and V2/V3 scope out.
MODEL_PROFILE: terra
MODEL_REASON: Real parser and runtime acceptance proof completed with the existing implementation; no architecture escalation required.
COMPUTER_USE: yes; runtime-compatible Ancient playback and the generated tick-3654 review landing were visibly checked in installed CS2. Localhost netcon only, no external transmission.

## 2026-08-21 — Real neutral demo-to-review workflow

STATUS: blocked
TASK: Consolidate the existing Awpy/canonical replay pipeline into a real neutral Demo→Selection→Profile→Rules→Merged Scenes→Review workflow and prove it on a real CS2 demo, including a CS2 tick jump.
BRANCH: `dev/v1-foundation`
CHANGED: Added `analysis_flow.py` (roster/starting line-ups, Full Demo/player selection, neutral profile, objective indicators/rules, context merge, timeline/JSON and required selection UI), `demo_workflow.py` (hash-bound real `.dem` orchestration and local review artifacts), two public CLIs and tests. Replay-v2 kill normalization now preserves evidenced headshot/penetration/through-smoke/attacker-blind qualifiers. Setup smokes seven CLIs. Added locked product decision, evidence doc and updated CURRENT/handoff. No fake results, suspect verdict, OBS/video/ML, Optimizer, benchmark, asset or 3D change.
VERIFIED: 97/97 tests, dependency check, seven CLI smokes and diff check pass. Real 477-MB source hash `2d70058ba006…` completed through Awpy 2.0.2: Mirage, 30 rounds, 10 named players, observed 5 CT/5 T starting line-ups, 201 kills, 98 headshots, 30 entries, 21 smoke kills, 6 wallbangs, 19 bounded multi-kill combinations. 375 objective markers/rule matches merged into 97 scenes; explicit one-player selection produced 35 and deduplicated IDs. Timeline/JSON/HTML plus commands file generated; first scene is round 1/tick 6352 with `demo_gototick 6352`. Trade/info rules correctly remain disabled where timing/sound/context evidence is insufficient.
DECISIONS: Standard engine is neutral and objective-anchor-only; weak single information indicators cannot emit scenes. CT/T are starting-line-up quick selectors within Player Select, not a third mode. Context is 128 ticks before/256 after, merge gap 96; two same-attacker kills within 320 ticks form the V1 multi-kill combination. Missing tick rate prevents trade inference. Generated match data stays ignored/local.
OPEN: DONE is not claimed. With explicit user approval, the same hash-bound Mirage demo was copied unchanged to the local CS2 game directory as `game/csgo/iy_review.dem` because its original filename contains shell-sensitive characters. CS2 loaded it successfully and exposed the real ten-player line-up/events. Direct startup `demo_gototick 6352` was processed before demo readiness and stayed at the beginning. A controlled run using `demo_pauseatservertick 6352` disconnected with `Failed to parse message.` The user then manually replayed `iy_review` normally and confirmed the same `Failed to parse message` failure. This isolates the blocker to runtime compatibility of this demo with the installed CS2 client, not the generated tick command, analysis flow or scene rules. Therefore tick 6352 is not runtime-accepted evidence yet. During the automated attempt Toggle Console was temporarily rebound from `^` to `F6`; the user was asked to restore the original binding manually.
NEXT: Obtain another current real CS2 demo that plays through in the installed client, run the unchanged workflow on it, and validate its first generated scene tick in CS2. Do not mark DONE, alter scene rules or weaken evidence requirements to bypass this source-demo incompatibility. The existing Awpy/analysis proof remains valid but cannot satisfy the runtime-review criterion by itself.
MODEL_PROFILE: terra
MODEL_REASON: Multi-component parser/rule/scene/workflow integration with real-data validation; no Sol escalation needed.
COMPUTER_USE: yes; after renewed user approval, CS2 loaded and played the real Mirage demo, but the exact tick run ended in visible `Disconnected — Failed to parse message.`; stopped without dismissing the evidence dialog.

## 2026-08-21 — ReplayController-to-renderer session adapter

STATUS: done
TASK: Implement only the one-way ReplayController-to-renderer session adapter, preserving requested/resolved tick semantics, selection and FP/fixed-TP mapping without owning playback, parsing or UI.
BRANCH: `dev/v1-foundation`
CHANGED: Added `renderer_session.py` with immutable session state, committed-snapshot subscription, canonical frame restore, controller-view mapping, render readiness and lifecycle cleanup. Added focused tests and evidence documentation; updated CURRENT/handoff. No ReplayController behavior, timer, parser, product UI, sightline target policy, smoke/utility/event rendering, asset, benchmark, Optimizer/System Check or packaging change.
VERIFIED: 9/9 focused controller/session tests and 93/93 complete tests pass; full Setup-V1 and five CLI smokes pass. Tests preserve requested 14/resolved 12 and reject frame/resolved mismatches. Tactical 2D/no player does not render. Real Anubis ReplayStore/ReplayController round 1/tick 6401, player `steam:76561198009555616`, flowed through FP then analysis-TP with requested/resolved 6401/6401, renderer canonical tick 6401, two renders and clean dispose.
DECISIONS: ReplayController remains the sole mutable playback authority. Session only mirrors committed state and cannot seek, advance, parse or choose targets. It owns renderer subscription/disposal; Tactical 2D is explicitly outside 3D render readiness.
OPEN: Sightline evaluation/presentation exists but is not yet refreshed by the session; target choice is deliberately not inferred. No product UI exists.
NEXT: Connect the evaluated sightline pipeline to ReplayRendererSession only through an injected explicit-target coordinator: same frame, selected observer, caller-supplied target IDs, verified geometry and capability-gated smoke. Pass ready segments and clear them on Tactical 2D/no selection/tick change. Do not invent target-selection UI/policy or add utility/event rendering.
COMPUTER_USE: no UI action in this slice.

## 2026-08-21 — Canonical smoke evidence gate

STATUS: done
TASK: Implement only the SightlineResult smoke-evidence gate: full lifetime/position coverage before a fixed disclosed V1 approximation may return clear/blocked; partial/unavailable remains unknown; no smoke rendering.
BRANCH: `dev/v1-foundation`
CHANGED: Added `CanonicalSmokeEvidence` with explicit coverage gate, fixed disclosed 144-Source-Unit sphere approximation, segment/sphere intersection and fail-unknown validation of active lifetime evidence. Added synthetic boundary/integration tests and evidence documentation; updated CURRENT/handoff. No renderer, asset, benchmark, utility/event overlay, player model, replay schema/controller semantics, Optimizer/System Check or packaging change.
VERIFIED: 15/15 focused sightline/smoke tests and 91/91 complete tests pass; full Setup-V1 and five CLI smokes pass. Full-coverage synthetic cases prove outside clear, inside blocked and exact tangent blocked; partial/unavailable and malformed active full-coverage cases are unknown. Real Anubis reports `utility_lifetimes=partial`; at round 1/tick 6401 the geometry-clear nearby pair stays smoke unknown/final unknown despite zero listed active smokes, with evidence stating that the approximation was not applied.
DECISIONS: The 144-unit sphere is a disclosed V1 analytical approximation, not engine truth and not replay state. Clear is permitted only when full whole-replay lifetime/position coverage makes the current active-smoke set exhaustive. Absence under partial coverage is not evidence of clear.
OPEN: Real Anubis cannot produce smoke-clear/visible results from this dataset; no data is invented to close that limitation. Smoke/utility visualization remains unimplemented.
NEXT: Implement only the ReplayController-to-renderer session adapter: consume snapshots, restore the canonical typed frame, map existing FP/fixed-TP modes, and update selected player/frame without owning playback/parsing. Prove seek, selection and view switching preserve requested/resolved tick semantics. Do not add product UI, smoke rendering, utility/event overlays or another state authority.
COMPUTER_USE: no UI action in this slice.

## 2026-08-21 — Sightline renderer presentation boundary

STATUS: done
TASK: Add only the renderer presentation boundary for already evaluated SightlineResult values, fixed colors and eye-to-eye segments from the same canonical frame; prove FP/fixed-TP switching preserves tick/player/result without recomputing geometry or smoke.
BRANCH: `dev/v1-foundation`
CHANGED: Added immutable `SightlineSegment`, fixed V1 green/red/neutral palette and tick-matched presentation builder. Extended ReplayRenderer/NullRenderer/Panda candidate with `set_sightlines`; Panda draws only supplied coordinates/colors and replaces prior line nodes. Extended the local spike for exact round/tick/player/targets and controlled TP→FP→TP proof. Added tests/evidence doc and updated CURRENT/handoff. No evaluator rule, smoke approximation, utility/event overlay, asset, benchmark, model, freecam, ReplayController semantics, Optimizer/System Check or packaging change.
VERIFIED: 18/18 focused sightline/renderer tests and 84/84 complete tests pass. Native real-Anubis round 1/tick 6401 with observer `steam:76561198009555616` preserved the precomputed nearby unknown and map-blocked occluded results across `third_person -> first_person -> third_person`, resize `1100x700 -> 900x560`, and dispose. Ignored screenshot visibly confirms the red occluded line plus local wireframe; the nearby neutral line is not claimed as a fully isolated visual proof in this composition, while exact gray mapping/persistence are deterministic tests.
DECISIONS: Result color is presentation-only and fixed: visible green, occluded red, unknown neutral gray. Renderer accepts ready segments and never calls geometry/smoke providers. Missing endpoints produce no segment rather than an invented position; cross-tick results are rejected.
OPEN: Smoke remains unknown for the real clear-geometry pair because the real replay capability is partial and no accepted V1 volume approximation exists. No smoke or other utility visualization is present.
NEXT: Implement only the canonical smoke-evidence gate required by SightlineResult: require explicit full lifetime/position coverage before a fixed disclosed V1 smoke-volume approximation may return clear or blocked; partial/unavailable stays unknown. Validate synthetic boundaries and report real Anubis capability, without drawing smoke or other utility/event overlays.
COMPUTER_USE: Timed local native renderer/view-switch proof only; no external transmission or persistent setting change.

## 2026-08-21 — Canonical SightlineResult evaluator

STATUS: done
TASK: Implement only canonical sightline evaluation from one ReplayFrame and the verified VisibilityGeometry, with exact tick/player identity and visible/occluded/unknown evidence; do not draw an overlay or infer smoke.
BRANCH: `dev/v1-foundation`
CHANGED: Added `sightlines.py` with immutable `SightlineResult`, explicit decision table, separate smoke-evidence boundary and unknown-by-default implementation. Added the canonical `replay_frame_from_dict` restore path and removed the renderer spike's duplicate frame mapping. Added evaluator/round-trip tests and evidence documentation; updated CURRENT/handoff. No renderer drawing, asset, benchmark, smoke approximation, utility/event overlay, model, ReplayController semantics, Optimizer/System Check or packaging change.
VERIFIED: 17/17 focused sightline/visibility/renderer tests and 81/81 complete tests pass; full Setup-V1 and five CLI smokes pass. On real Anubis round 1/tick 6401, observer `steam:76561198009555616` to nearby `steam:76561198263389260` returns geometry clear + smoke unknown = final unknown, never visible. The same observer to `steam:76561198066871323` returns verified geometry blocked + smoke unknown = occluded. Exact tick and both identities remain in each immutable result/evidence.
DECISIONS: Geometry blocked is sufficient for occluded; geometry unknown remains unknown. Geometry clear becomes visible only with separately evidenced smoke clear. Default smoke coverage is unknown because this slice has no accepted V1 smoke-volume approximation. Evaluation stays outside the renderer and consumes shared replay truth.
OPEN: No overlay exists yet, and no real result can be called visible without complete relevant smoke evidence. Smoke approximation remains a later explicit Slice-F boundary rather than a shortcut here.
NEXT: Implement only a renderer presentation boundary for already evaluated SightlineResult values: fixed visible/occluded/unknown colors and eye-to-eye segments from the same canonical frame, without recomputing geometry or smoke. Prove FP/fixed-TP switching preserves tick/player/result. Do not add smoke approximation or other utility/event overlays.
COMPUTER_USE: no UI action in this slice.

## 2026-08-21 — Verified TP camera obstruction adjustment

STATUS: done
TASK: Execute only the documented next slice: verified visibility-mesh query boundary and fixed Third-Person camera-to-anchor obstruction adjustment, with clear/blocked/unknown behavior and no overlay or replay reinterpretation.
BRANCH: `dev/v1-foundation`
CHANGED: Added `visibility_mesh.py` with evidence-state/result protocol, unavailable implementation and read-only chunked `.tri` segment queries. Extended the fixed TP camera with verified last-intersection adjustment plus 8 Source Unit safety margin and diagnostics. Bound the existing disposable Panda spike to the same verified geometry and cached pose. Added focused tests and this evidence note; updated CURRENT/handoff. No replay schema/controller, benchmark, smoke, geometry, asset, Optimizer/System Check, overlay, model or packaging change.
VERIFIED: 12/12 focused renderer/visibility tests and 75/75 complete tests pass. The verified local Anubis controls reproduce `clear` for `(-259.6265,-1595.3811,52.0313)`→`(-508.1600,-1589.8218,66.0312)` and `blocked` with last fraction `0.9189757397145473` for the documented blocked endpoint `(-527.9521,2207.1423,89.0313)`. Native tick-4659 TP replay check returns `clear`, no adjustment, resize and dispose PASS. Synthetic multiple-wall proof selects the last hit; blocked movement is collinear and clear/unknown preserve the fixed pose.
DECISIONS: Unknown geometry remains unknown and does not masquerade as clear; only verified blocked evidence adjusts the camera. Adjustment cannot change target/angle or choose a cinematic alternative. Local derivatives and screenshots remain ignored. The query is chunked and correct for this slice; acceleration remains an adaptable renderer concern if playback profiling later requires it.
OPEN: Sightline evaluation/visualization and smoke evidence remain unimplemented. The real checked tick was clear, while controlled real and synthetic blocked cases prove the adjustment input path; no claim of broad runtime camera acceptance is made.
NEXT: Implement only canonical `SightlineResult` evaluation from one ReplayFrame and the same verified VisibilityGeometry, with exact tick/player identity and visible/occluded/unknown evidence. Keep smoke unknown unless canonical evidence proves the selected V1 approximation; do not render the overlay yet.
COMPUTER_USE: Timed local native renderer proof only; no external transmission or persistent setting change.

## 2026-08-21 — Slice D renderer protocol and native embed proof

STATUS: done
TASK: Continue only the documented Slice D: implement the minimal renderer boundary and prove local Anubis load, canonical camera updates, native embedding, resize and dispose without packaging assets or adding replay interpretation.
BRANCH: `dev/v1-foundation`
CHANGED: Added backend-neutral `renderer.py` with `ReplayRenderer`, deterministic FP/fixed-TP camera functions, explicit unavailable-state behavior and `NullRenderer`; added disposable `panda_renderer.py`, the local `Run-RendererEmbedSpike.py`, focused tests, exact optional spike dependencies and the Slice-D evidence note. Updated this handoff and `coordination/CURRENT.md`. No benchmark, smoke, geometry, Optimizer/System Check, replay schema/controller, tracked result or local-only asset changed.
VERIFIED: 8/8 focused renderer tests and 71/71 complete tests pass; Python compilation passes. With optional Panda3D 1.10.16 + panda3d-gltf 1.3.0, the verified ignored Anubis GLB loaded in a Panda viewport parented to a native Tk child window. Canonical tick 4659/player `steam:76561198009555616` drove the fixed TP camera; observed sizes were startup `1x1`, then `1100x700` and `900x560`; automatic dispose/close returned structured PASS. The ignored screenshot was visually inspected and contains local map geometry in the camera frustum. Materialless-physics warnings are expected and non-blocking for this wireframe proof.
DECISIONS: The renderer protocol and V1 camera semantics are stable; Panda3D remains only the first candidate behind the boundary. The optional dependency does not enter the default V1 install. Valve-derived geometry/replay/screenshot remain ignored and local-only. No freecam, overlays, events, player models, smoke interpretation, packaging or independent demo parsing was introduced.
OPEN: Production renderer/UI choice and distributable art remain undecided by design. Visibility-mesh obstruction correction is the next bounded implementation gap; the current TP spike does not yet adjust an obstructed camera.
NEXT: Implement only the verified visibility-mesh query boundary and the fixed Third-Person camera-to-anchor obstruction adjustment, including `camera_adjusted=true` plus clear/blocked/unknown tests. Do not add overlays, smoke interpretation, models, free camera, packaging or another replay truth.
COMPUTER_USE: Local native window was launched for a timed visual proof; no authentication, external transmission or persistent app/system setting change.

## 2026-08-22 — Module Integration Foundation V1

STATUS: done
TASK: Add the minimal, explicit integration boundary for future Analyzer-facing modules without adding Tactical, Review, Report or My Improvement feature logic.
BRANCH: `dev/v1-foundation`
CHANGED: Added `module_integration.py` with `ModuleDefinitionV1`, `ModuleRegistry`, `ModuleController`, `ModuleAdapterV1`, `ModuleStatus`, `ModuleContextV1`, and a versioned, deep-copying `AnalyzerDataHubV1`; added focused regression tests and `docs/MODULE_INTEGRATION_FOUNDATION_V1.md`. Analyzer Core, awpy adapter, parser, existing Analyzer/Review/Replay contracts and UI are unchanged.
VERIFIED: `tests/test_module_integration.py`: 7 passed; whole suite reached 30 passed before 10 environment failures when pytest could not create its pre-created scratch base directory. Source-only syntax compilation without bytecode writes passed; `git diff --check` passed. The normal setup script could not create a `.venv` in this worktree, and `compileall` could not create `__pycache__`; neither result is a product-test failure, so no full-suite/compileall PASS is claimed.
DECISIONS: Integration accepts only explicitly registered modules and exact `iy.module_adapter/v1`/projection identifiers. Missing or unregistered inputs are `UNAVAILABLE`; disabled modules are not prepared; adapter faults are `ERROR` and isolated. Hub and context data are defensively copied, and no module path imports awpy, initiates parsing, accesses raw parser data, or mutates shared hub data. `My Improvement` remains an independent future consumer, never Tactical-owned.
OPEN: No feature expansion follows from this foundation. Re-run the complete repository gate in a worktree where Python may create its isolated venv, pytest base temp directory and compile caches.
NEXT: WAITING_FOR_TRISTAN
COMMIT/PR: Pending final commit and push for this handoff.
MODEL_PROFILE: gpt-5.6-terra
MODEL_REASON: Narrow architecture and contract-boundary implementation with regression coverage.
COMPUTER_USE: no

## 2026-08-17 — Final `dev/v1-foundation` review toward `main`

STATUS: ready_for_review
TASK: Perform the final no-merge review of `dev/v1-foundation` against the current remote `main`, including scope, working tree, local artefacts, secrets, handoffs, tests and documented V1-foundation exit criteria.
BRANCH: `dev/v1-foundation` at `3a4ad8c` during validation; current remote `main` reviewed at `96e13771e33d9625f7e80d3790a464d8c557b6a9` (`Add Codex handoff channel`).
CHANGED: No product, benchmark, Kubus, Steam, SDK, VRAD, Hammer, system or generated-result data changed. Remote `main` was fetched read-only into `FETCH_HEAD` solely to establish the real merge comparison. This entry records the review result only; no merge was performed.
VERIFIED: `main` is the direct merge-base of the branch. The review range contains 57 intentional project files (3,826 additions / 22 deletions), including the consolidated V1 package, tests, locked dependencies, reproducible tools and versioned benchmark sources. `git diff --check FETCH_HEAD...HEAD` passes. The worktree has no untracked non-ignored files; ignored local content is limited to `.venv/`, `results/` and ordinary test/Python caches. No tracked generated/private result paths (demos, reports, HTML, logs, local configuration or secrets) are present. A tracked-text secret-indicator scan found no API token, private-key, password or API-key assignment pattern. `git fsck --no-reflogs` found only three classified unreachable historical checkpoint commits, not a ref or worktree inconsistency. `Setup-V1.ps1` passes on final HEAD: dependency consistency, 33/33 tests and help-smokes for all five shipped CLI entry points; Python `compileall` passes. The benchmark VMAP is the expected 401,300-byte versioned binary source and explicitly has `binary -diff -merge` attributes. The active source/tool legacy scan found only explanatory documentation/manifest wording, no imported or executed legacy-prototype runtime.
DECISIONS: All documented V1-foundation exit criteria are met: reviewed consolidation, coherent clean module structure, reproducible locked setup, runnable baseline and no active legacy-folder dependency. The real-demo `iy.pipeline/v1` PASS and Tristan's seven-scene Mirage 2D-radar PASS close the automated and bounded human proof. The still-parked Workshop Tools/VRAD asset-mount issue is separately documented as a benchmark compile/runtime blocker, not a Foundation merge blocker.
OPEN: No final-review blocker found. The broader V1 roadmap and the benchmark's external VRAD blocker remain separate from this Foundation merge decision.
NEXT: Recommendation to Tristan: merge `dev/v1-foundation` into the reviewed `main` base after a final remote-head recheck at merge time; do not combine that merge with a VRAD retry, benchmark source change or Kubus work.
MODEL_PROFILE: gpt-5.6-terra
MODEL_REASON: Repository-wide final review and merge-readiness assessment with source, test, artefact and secret boundaries.
COMPUTER_USE: no

## 2026-08-17 — Tristan 2D-radar acceptance and V1-foundation reassessment

STATUS: ready_for_review
TASK: Make the pre-existing local Mirage review available for Tristan, record the human 2D-radar acceptance, then reassess the documented V1-foundation exit condition without reopening the parked benchmark blocker.
BRANCH: `dev/v1-foundation`
CHANGED: No Analyzer, Replay, Radar, benchmark, Kubus, Steam, SDK, VRAD, Hammer, GPU, driver, registry, Adrenalin, smoke, geometry or controller data changed. The existing `results/workflow/b7532c82381b/` `READY_FOR_REVIEW` manifest and its pre-generated Viewer/Review artefacts were served unchanged through `iy-review-server` on loopback only. The service was then controlledly stopped; no listener remains on `127.0.0.1:8765`.
VERIFIED: The local Review page and review-state API each returned HTTP 200 while running, restricted to `127.0.0.1`, with seven scenes and `iy.review_state/v1`. Tristan completed the manual visual acceptance: all seven real Mirage scenes have plausible/correct player positions and view-direction lines; no obvious mirror, rotation, major translation or scale defect was observed; no scene was marked faulty. The prior automatic proof remains current: 33/33 tests, lockfile setup/dependency check, five public CLI help-smokes and a complete real-demo `iy.pipeline/v1` PASS.
DECISIONS: The bounded human 2D acceptance gate is closed PASS. The V1-foundation exit condition is now satisfied: coherent consolidated structure, reproducible setup and runnable baseline without active legacy-prototype-folder dependency, plus both automated and human 2D validation. Therefore `dev/v1-foundation` is READY_FOR_REVIEW toward `main`. This is not a merge, release or whole-V1-product declaration: Tristan retains the merge decision, and the broader V1 roadmap (including future Optimizer mutation/restore design) is separate.
OPEN: The only unchanged external runtime blocker is the parked Workshop Tools/VRAD preflight asset/mount failure, which prevents benchmark Full Compile and marker-synchronized camera acceptance but does not invalidate the V1 Analyzer/2D Foundation proof. Do not retry it without a new official SDK/Valve input, a changed build or explicit approval.
NEXT: Tristan reviews/decides the Foundation-to-`main` merge boundary. Independently, wait for material official SDK/Valve evidence before resuming the benchmark; no Kubus expansion.
MODEL_PROFILE: gpt-5.6-terra
MODEL_REASON: Human-acceptance handoff and evidence-based foundation completion assessment; no system or product behavior change.
COMPUTER_USE: no UI input; existing local loopback review service only.

## 2026-08-17 — Post-manual-control environment recheck

STATUS: waiting_for_tristan
TASK: Safely re-establish the actual Windows/Steam/Workshop-Tools state after Tristan's manual control, then resume only the already approved Improve Yourself proof work.
BRANCH: `dev/v1-foundation`
CHANGED: No product, benchmark, Steam, SDK, VRAD, Hammer, renderer, GPU, driver, registry, Adrenalin, Smoke, geometry or controller setting changed. No Workshop Tools, Hammer, VRAD preflight or Full Compile was launched. Kubus V0 remains frozen and was not touched.
VERIFIED: Read-only process inspection at 2026-08-17 04:53 UTC finds Steam running (fresh process start 04:38 UTC) but no `cs2.exe`, `hammer.exe`, `vrad3.exe` or relevant compiler process. The registered Steam root is `E:\Program Files (x86)\Steam`. CS2 App 730 manifest remains build `24701871`, `UpdateResult 0`, all Download/Stage byte counts `0`; SDK App 745 remains build/target `11399846` with the same zero-byte state. Their `LastPlayed` values and manifest write times changed consistently with the manual clean close, but build/depot state did not. No `check_raytracing_support.vrad3` loose asset exists, and no relevant VRAD/Hammer/script file has a modification time newer than the documented parked state. Improve Yourself is clean and synchronized at `f53457f`; `git diff --check` passes.
DIAGNOSIS: The environmental state is materially unchanged from the parked external SDK asset/mount blocker. The only newer facts are a cleanly ended Tool session and a fresh Steam process, neither of which supplies a new SDK build, readable preflight asset or supported remediation. Repeating the already failing VRAD preflight or Full Compile would add no evidence.
OPEN: WAITING_FOR_TRISTAN for the bounded real 2D-radar visual acceptance (local browser URL-policy boundary) and independently for an official CS2 Workshop Tools/SDK update, Valve support response, or explicit newly scoped remedy for the VRAD asset/mount blocker. The first item is the remaining V1 proof acceptance gate; the second blocks only the benchmark runtime compile/camera proof.
NEXT: Tristan can perform the bounded 2D visual review when available. For the benchmark, first compare a future official CS2/SDK build or support guidance against the recorded build IDs; only with material new evidence or explicit approval run the single VRAD preflight again, and only after preflight exit `0` run Full Compile.
MODEL_PROFILE: gpt-5.6-terra
MODEL_REASON: Read-only Windows/Steam state verification plus a narrow proof-handoff update; no product or system behavior change.
COMPUTER_USE: no UI input; process, manifest and file-state inspection only.

## 2026-08-17 — Kubus freeze and V1-foundation proof audit

STATUS: review
TASK: Reproducibly freeze the accepted Kubus V0 state, then close all locally executable V1-foundation proof checks without reopening the parked Workshop-Tools/VRAD diagnosis.
BRANCH: `dev/v1-foundation` (Improve Yourself); Kubus is separately committed at local Foundry commit `3c8c717`.
CHANGED: No product, benchmark, VRAD, Steam, driver, registry, Hammer, Smoke, geometry or controller source changed. Kubus V0 remains feature-frozen after its committed practical-use revalidation; its integrity audit remains reproducible. Project-status documentation now records the current proof evidence only. Local pipeline outputs and the real demo remain ignored.
VERIFIED: Kubus integrity audit at `2026-08-17T04:47:32` returned exit `0` (`24` jobs, `23` healthy, `1` prior warning, `0` errors); its pre-existing untracked `shared/input/improve-v1-inventory/` was preserved. Improve Yourself is clean at `a552c83`. `pytest -q` passes `33/33`. `Setup-V1.ps1` passes Python-3.13 lockfile installation, dependency consistency, all tests and help-smokes for `iy-analyze`, `iy-system-check`, `iy-workflow`, `iy-replay-viewer` and `iy-review-server`. The complete `Run-V1Pipeline.ps1` run is PASS in `results/pipeline/20260817T044946-446eec75822c/pipeline-evidence.json`: schema `iy.pipeline/v1`, clean commit `a552c83`, SHA-256 `446eec75822c0cae5ca020296ad900307e573302b81c8beb5b5daa98623058b6`, `de_anubis`, 307 kills, 22 round-wide multikills, valid analysis contract/invariants and a correctly disclosed limited result (missing `footsteps`, two warnings). It records no demo path, player name or detailed kill data.
DECISIONS: Kubus V0 is frozen for practical use: do not begin a Kubus/worker feature or worker-count extension. The narrow V1-foundation exit condition is met by coherent consolidated structure, reproducible setup and runnable baseline with no active legacy-folder dependency. The outstanding local human visual acceptance is not silently converted into an automated claim. The VRAD SDK asset/mount blocker remains parked; do not rerun its preflight or touch its configuration without a new official tools build, new evidence or Tristan's explicit approval.
OPEN: (a) No further automated V1-foundation proof gap was found after the successful full pipeline. The bounded 2D real-radar sight check remains WAITING_FOR_TRISTAN because browser navigation cannot cross the local URL-policy boundary. (b) The only external compile/runtime proof gap is the parked Workshop Tools/VRAD asset-mount blocker: `check_raytracing_support.vrad3` cannot be read although VRAD selected the RX 7900 XTX. It prevents Full Compile and the marker-synchronized Nuke/Ancient/Inferno acceptance, not the V1 Analyzer baseline.
NEXT: Commit/push this status-only proof checkpoint after final diff/test review. Then keep Improve Yourself priority on reviewable product gaps; resume the benchmark only after a material official SDK/Valve change or explicit new scope.
MODEL_PROFILE: gpt-5.6-terra
MODEL_REASON: Repository-level proof audit, local regression validation and narrow status handoff; no system or product-behavior change.
COMPUTER_USE: no

STATUS: partial
TASK: V1 consolidation: supported local launcher and startup validation
BRANCH: `dev/v1-foundation`
CHANGED: Added `tools/dev/Start-V1Review.ps1` as the supported Windows entry point. It validates demo/radar/numeric limits, prepares the locked Python 3.13 environment, runs `iy-workflow`, validates `iy.workflow/v1`, prints the exact review URL and starts `iy-review-server` visibly in the foreground. `-NoServe` supports deterministic artifact smoke tests; `-SkipSetup` is explicit. Setup now verifies every shipped CLI entry point. No browser is silently opened and no system/Optimizer change is performed.
VERIFIED: 28/28 tests pass. Locked setup and dependency consistency pass. Real Mirage `-NoServe` run returned a valid READY_FOR_REVIEW manifest and left no service. Normal launcher mode served `review.html` with HTTP 200 and `iy.review_state/v1` with seven scenes on `127.0.0.1:8877`, then stopped cleanly via Ctrl+C. Git diff check passes.
DECISIONS: Real demos and detailed results remain local and uncommitted. Regression evidence records source SHA-256 and aggregate map/tickrate/count/channel/quality facts, not player names or kill details. Missing `footsteps`/`player_sound` is a disclosed source-capability limitation, not a damaged-demo verdict. Do not commit a real binary fixture unless it is deliberately generated or licensed, non-sensitive, small, and provenance-documented.
OPEN: WAITING_FOR_TRISTAN: Open the generated local `results/replay/732855381761.viewer.html` in a browser and confirm that the six real Mirage scenes place players plausibly on the radar and that their direction lines align with expected sight directions. Windows Computer Use stopped at its browser URL-policy boundary, so Codex did not claim visual validation. Radar redistribution provenance remains unresolved; the binary stays local.
NEXT: Tristan performs the bounded real Mirage sight check when available. Independently, audit the branch against the documented V1-foundation exit condition and close only concrete gaps before preparing review toward `main`; Optimizer mutation/restore remains a separate, later safety boundary requiring explicit design and verification.
COMMIT/PR: Review persistence `e187175`; supported launcher is `659a5e6` on `dev/v1-foundation`.

## 2026-08-17 — Benchmark multi-map transition runtime check

STATUS: blocked
TASK: Implement and validate the locked Nuke -> Ancient -> Inferno transition sequence.
BRANCH: `dev/v1-foundation`
CHANGED: Controller V1.1 adds explicit transition metadata/markers, retains the controlled first Nuke smoke wall, removes the obsolete Ancient-end/Inferno-start smokes, adds the Red Room landmark marker and flash/white-fade handoff, and stages camera turns inside the occlusion windows. README, manifest and transition tests describe and enforce the source contract.
VERIFIED: Source/addon sync was hash-verified with backups before deployment. Automated suite passed 32/32 before the second Full Compile. The second Full Compile produced `game/csgo_addons/improve_yourself_benchmark/maps/improve_yourself_benchmark.vpk` at 2026-08-17 00:27:16. Real normal-viewer observation is FAIL: the white/occluded phase clears to empty sky and later effects render without surrounding geometry; a red-tinted empty view is not accepted as Red Room or Inferno validation.
DIAGNOSIS: A read-only DMX conversion of the versioned VMAP shows authored solids/entities centered near the origin (observed origins roughly -1760 through +1377, plus local mesh extents), while the controller sends Ancient to approximately x=+7850..8580 and Inferno to x=-8676..-7756. The transition timing can hide the teleport but cannot create the missing scene geometry. This explains the floating/isolated effects and empty-sky result.
OPEN: BLOCKED on map authoring, not on Steam/Workshop Tools. The locked product design still requires an actual Ancient B ramp/water/reflection scene, visibly red Red Room, and Inferno Apps/stairs. Do not mark the transition complete and do not continue blind camera-yaw tuning.
NEXT: Author or import project-owned graybox geometry for the two missing environments at deliberate coordinates (or rebase paths only after identifying real existing bounds), then re-run Full Compile and capture both occlusion exits. Preserve the first Nuke smoke wall until that comparison is complete.
COMMIT/PR: Pending an intentional checkpoint commit after final diff/test review; no successful runtime claim.

## 2026-08-17 — Transition graybox authoring and runtime recheck

STATUS: blocked
TASK: Establish real Ancient/Inferno destination geometry and valid camera coordinates, then Full Compile and runtime-test the locked transition sequence.
BRANCH: `dev/v1-foundation`
CHANGED: Added `tools/benchmark/author_transition_graybox.py`, which reproducibly clones project-owned cube meshes into an Ancient-style enclosed ramp/water/Red-Room corridor and an Inferno-style enclosed Apps/stair corridor, assigns unique DMX identifiers, extends the light/reflection probe bounds and refuses duplicate authoring. Re-authored controller paths/effects onto those in-map coordinates, retained the controlled first Nuke smoke wall, and kept the flash handoff. README, manifest and transition tests were updated.
VERIFIED: Manifest deploy completed with hash verification and backup `deploy-20260817-005153`. Final source hashes are VMAP `CA54A61FB837669E7E420CEBDB5E1F96B01C666E0531F35B20EBCDCD8E6CFBA8` and controller `8FD5218807B94BF02AFECFB44280C3A04133392FBDCCDC0488EF9D3D5720C53F`. Automated suite passes 32/32. Full Compile completed and loaded the rebuilt map in CS2. Normal-viewer observation remains FAIL: after load and during the moving camera pass the view continues to show the beige-gray origin test area and its orange/white guide lines; the enclosed Ancient corridor, reflective water, Red Room and Inferno stairs are not visible.
DIAGNOSIS: The earlier invalid +/-8,000-unit path error is removed at source and real destination meshes now exist in the VMAP, but source coordinates alone do not establish their compiled runtime placement. The remaining blocker is now narrowed to a mesh transform/instancing mismatch (or equivalent compile-time placement issue) between authored objects and controller camera coordinates, not Steam/Workshop Tools and not missing source geometry.
OPEN: BLOCKED on runtime placement evidence. Do not claim Ancient/Inferno visual acceptance. Do not add more smoke/fade/yaw tuning or more blind geometry before measuring the compiled mesh locations/transform semantics.
NEXT: Convert and inspect the newly authored object transforms together with their referenced mesh data, then derive one directly observable camera target from the compiled placement. Re-run Full Compile and capture Ancient water/Red Room and Inferno stairs only after that coordinate is proven.
COMMIT/PR: Pending checkpoint commit and push after final diff/test/sync verification.

## 2026-08-20 — 3D / POV V1 technical preflight

STATUS: blocked
TASK: Technical preflight A-F before any 3D/POV product implementation
BRANCH: `dev/v1-foundation`
CHANGED: Added `docs/3D_POV_V1_PREFLIGHT.md` and updated only the 3D workstream in `coordination/CURRENT.md`; no analyzer, replay, renderer, benchmark, map, utility, Steam, Hammer, or system state changed.
VERIFIED: Rebased the audit onto the current remote foundation before finalizing it. Inspected the active `iy.analysis/v1`, `iy.replay/v1`, workflow/viewer code and evidence, the legacy Tactical Replay parser and preserved real Mirage replay artifact, local Awpy 2.0.2 Anubis triangle data, and official Panda3D/Qt embedding/deployment documentation. The current branch already has a validated scene-only 2D contract and human Mirage radar PASS, but not full-match playback. Local `de_anubis.tri` contains 808,000 triangles with plausible bounds, while Awpy ties the resource set to build id 17595823 and supplies no accepted current-version/distribution proof. Current post-rebase repository regression suite passes: `33 passed in 1.60s`; `git diff --check` passes.
DECISIONS: Recommend Panda3D only as the first disposable integration spike behind `ReplayRenderer`; do not bind the product contract to it. PySide6/Qt Quick 3D remains the fallback if Qt is first accepted as the native app shell. Final preflight status is `3D_POV_V1_BLOCKED`.
OPEN: `iy.replay/v1` is sampled Multi-Kill scenes rather than full-match state; there is no central `ReplayController` or stable player-ID proof; current replay serialization does not contain the event/utility fields claimed by `docs/2D_VIEWER_FOUNDATION.md`; Anubis geometry currency/provenance/distribution is unresolved; and the accepted product surface is still HTML/loopback rather than a native desktop shell.
NEXT: Implement Phase A only: evolve the existing replay contract to full-match canonical state and regression-test field/event/utility availability, tick identity, and player identity against the existing real Anubis input. Do not start a renderer until the data and geometry gates pass.
MODEL_PROFILE: gpt-5.6-sol
MODEL_REASON: Architecture preflight with a 34-commit remote divergence, conflicting evidence between documentation and serialization code, and distribution/provenance gates.
COMPUTER_USE: no
COMMIT/PR: Preflight documentation commit on `dev/v1-foundation`; no merge authorized

## 2026-08-20 — 3D / POV V1 closed implementation specification

STATUS: done
TASK: Close the agreed 3D/POV Blueprint V1 into an implementation-ready specification without changing product code
BRANCH: `dev/v1-foundation`
CHANGED: Added `docs/3D_POV_V1_IMPLEMENTATION_SPEC.md`; recorded the locked 3D view/replay boundary in `docs/DECISIONS.md`; moved only the 3D workstream in `coordination/CURRENT.md` to `READY_FOR_IMPLEMENTATION`. No Analyzer, Replay, Viewer, Renderer, Benchmark, Optimizer, System Check, map asset, dependency, Steam/Hammer, or runtime code/state changed.
VERIFIED: The specification defines all five required blocks: asset specification, shared `iy.replay/v2` ReplayFrame model, V1 test matrix, slice handoff/strict COMPLETE criteria, and fixed/adaptable/deferred V1/V2 scope. Mandatory First Person POV, deterministic fixed Third-Person Analysis Camera and evidence-qualified sightlines all consume one ReplayController and one tick truth. Proposed modules, schemas, identity hierarchy, data flow, interpolation prohibitions, asset failure states, real-Anubis acceptance, packaging/performance guardrails, risks and first slice are explicit. Repository regression and specification-structure checks are run before commit.
DECISIONS: Settled product boundary is recorded, not reopened. `iy.replay/v2` is the incompatible canonical full-match contract; `iy.replay/v1` remains compatibility-only until 2D migration passes. Renderer choice remains behind `ReplayRenderer`; Slice A adds no renderer dependency. Freecam/orbit/cinematic camera and inferred data/geometry remain deferred.
OPEN: Implementation has not started. Anubis asset currency/distribution and the accepted native shell remain later gates; they do not block Slice A's contract/capability work.
NEXT: Implement Slice A only: immutable `iy.replay/v2` types, full-match builder/validator/store, stable identity and capability reporting, then run the private real-Anubis regression while keeping the entire current suite green.
MODEL_PROFILE: gpt-5.6-sol
MODEL_REASON: Closing cross-module replay, camera, asset, testing, packaging and scope contracts with long-lived compatibility consequences.
COMPUTER_USE: no
COMMIT/PR: Specification commit on `dev/v1-foundation`; no merge authorized

## 2026-08-20 — 3D / POV V1 Slice A canonical truth

STATUS: done
SLICE: A — canonical replay truth
BRANCH: `dev/v1-foundation`
CHANGED: Added immutable `iy.replay/v2` contracts, full-match Awpy builder, manifest/chunk validators, capability reporting, hash-verified read-only `ReplayStore`, 11 new tests, the reproducible `Run-ReplayV2Regression.ps1` path and `docs/3D_POV_V1_SLICE_A.md`. Existing `iy.replay/v1`, 2D viewer, Analyzer behavior, Benchmark, Optimizer, System Check, UI, dependencies and renderer state are unchanged.
DATA EVIDENCE: Private real `de_anubis` source SHA-256 `446eec75822c…`; 42 rounds, 252,401 frames, 2,524,000 player states, 10 Steam identities, 8,429 normalized events, 300,424 active utility states and 22 scene references. Zero unresolved real player snapshots. Generated 43-file store is approximately 56.9 MB and remains ignored/local.
ASSET EVIDENCE: n/a for Slice A. `map_geometry=unavailable`; no map asset or renderer dependency was added.
VERIFIED: `44 passed in 0.98s`; `compileall` passes. The public PowerShell regression path rebuilt the real match from the private compressed demo, validated the manifest and all 42 round-chunk hashes/invariants, emitted `iy.replay_regression/v1` with `status=PASS`, and preserved exact event ticks and evidenced utility lifetimes.
REGRESSIONS: Existing Analyzer, `iy.replay/v1`, viewer, workflow, review, system-check and benchmark-transition tests remain green within the 44-test suite.
RISKS: Real tick rate is absent (`null`) and must not be guessed before speed-based playback. Player/view/weapon/velocity and utility-lifetime capabilities are partial due real nulls/row absence. Alive state is only observed-row health-derived. Grenade source has 3,479,155 trajectory points but Slice A does not materialize them. Flash effect, sound and map geometry remain unavailable.
DECISIONS: Use compressed per-round chunks behind the unchanged logical `iy.replay/v2` contract to avoid a multi-gigabyte in-memory/full JSON artifact. Do not claim full capability where real rows are incomplete. Do not introduce a `64 Hz` default.
OPEN: Canonical tick-rate evidence is required before ReplayController speed semantics. Full dead/inactive-state reconstruction, trajectory materialization, flash evidence and asset geometry remain their explicitly scheduled later work.
NEXT: Begin Slice B with a bounded tick-rate evidence task, then implement the single ReplayController and migrate existing 2D state consumption to `iy.replay/v2`; no 3D renderer yet.
MODEL_PROFILE: gpt-5.6-sol
MODEL_REASON: New canonical persisted contract over 2.5 million real states with compatibility, memory, identity and evidence-quality consequences.
COMPUTER_USE: no
COMMIT/PR: Slice A implementation commit on `dev/v1-foundation`; no merge authorized

## 2026-08-20 — 3D / POV V1 Slice B1 shared controller

STATUS: done
SLICE: B1 — shared ReplayController; 2D migration remains next
BRANCH: `dev/v1-foundation`
CHANGED: Added `replay_controller.py`, seven focused controller tests, read-only round descriptor access on `ReplayStore`, `docs/3D_POV_V1_SLICE_B_CONTROLLER.md`, and current/handoff status. No renderer, camera implementation, sightline, map asset, Benchmark, Optimizer, System Check or legacy `iy.replay/v1` behavior changed.
DATA EVIDENCE: Direct `demoparser2.parse_header()` inspection of private real Anubis source `446eec75822c…` found format/version, patch, server, map and directory metadata, but no tick rate, playback duration or equivalent trusted timebase. Real manifest remains correctly `tick_rate=null`.
VERIFIED: 51/51 tests pass; full `Setup-V1.ps1` passes dependency consistency and five public CLI help smokes; `compileall` and `git diff --check` pass. Real ignored Anubis store smoke loaded 42 rounds/22 scenes, resolved a scene seek at its exact canonical tick and confirmed that time-based `play()` is explicitly blocked while deterministic navigation remains available.
REGRESSIONS: Existing Analyzer, `iy.replay/v1` viewer, workflow, review, System Check and benchmark tests remain green and unchanged.
RISKS: Automatic wall-clock playback cannot be truthfully enabled for the real reference until a trusted timebase exists. Listener callbacks are synchronous by design in this core and renderer/UI scheduling remains outside this slice.
DECISIONS: Do not infer FACEIT/CS2 64 Hz. Unknown timing is an explicit capability boundary: seek/scrub/event navigation work; play/advance raise `PlaybackTimingUnavailable`. Global demo-tick gaps between rounds remain canonical rather than being collapsed.
OPEN: Existing 2D Tactical Replay still consumes compatibility `iy.replay/v1`; therefore cross-view shared-consumption proof is not complete. First Person, fixed Third Person and sightlines remain mandatory later V1 slices, not implemented here.
NEXT: Migrate only the existing 2D tactical view's state/input path to `ReplayController` and `iy.replay/v2`; prove scene, player and requested/resolved tick synchronization and expose timing-unavailable state. Do not add a 3D renderer in that slice.
MODEL_PROFILE: gpt-5.6-terra
MODEL_REASON: Bounded controller implementation and deterministic timing/state tests on the established replay contract.
COMPUTER_USE: no
COMMIT/PR: Controller checkpoint on `dev/v1-foundation`; no merge authorized

## 2026-08-20 — 3D / POV V1 Slice B2 2D migration

STATUS: done
SLICE: B — shared control complete
BRANCH: `dev/v1-foundation`
CHANGED: Added `tactical_2d.py` as the renderer-only projection from validated `ReplayStore` frames and `ReplayController` contexts. `iy-replay-viewer` now accepts canonical `iy.replay/v2` manifests as well as compatibility `iy.replay/v1`, exposes scene/focus-player and requested/resolved tick state, and visibly disables automatic playback when timing is unavailable. Added migration/sampling/viewer tests and updated Slice-B/2D documentation. No 3D renderer, asset, camera, sightline, Benchmark, Optimizer or System Check change.
DATA EVIDENCE: Real private Anubis v2 store (source `446eec75822c…`) contains 42 rounds/22 scenes. Event-preserving uniform display sampling retains scene boundaries and every event-bearing frame while capping ordinary intermediate draws. Self-contained V2 viewer is 11,503,307 bytes (10.97 MiB) and generated in 5.93 seconds; ignored/local only.
ASSET EVIDENCE: n/a for Slice B. No Anubis geometry/radar asset was accepted or added.
VERIFIED: 55/55 tests pass before final setup; focused tests prove controller scene resolution, stable identity/focus, omission only of non-renderable state, boundary/event-preserving sampling, V1 compatibility, V2 viewer source/tick/timing markers and script-tag escaping. Real V2 viewer generation passes below the 10-second first-view target. Automated screenshot was unavailable because no Edge/Chrome/Firefox binary is installed; no new visual-acceptance claim is made, and the previously accepted canvas projection/drawing code is unchanged.
REGRESSIONS: `iy.replay/v1` input and all existing Analyzer/viewer/workflow/review/System Check/benchmark behavior remain supported and green in the repository suite.
RISKS: The self-contained V2 viewer intentionally embeds scene windows, not all 252,401 full-match frames. Full truth remains in the hash-verified store. Real wall-clock playback remains unavailable without evidenced timing. A new human visual check is still required if the preserved canvas rendering itself is changed later.
DECISIONS: Browser receives a renderer projection, not a second demo interpretation. Preserve all event-bearing frames even if that exceeds the nominal 256-frame display target. V1 compatibility remains until broader product migration is accepted.
OPEN: Slice B is complete. An accepted distributable Anubis map asset, transform and LOS proof do not yet exist; renderer work must not begin before that gate.
NEXT: Execute Slice C Asset Gate only: inventory candidate Anubis assets, establish provenance/distribution status, hashes, coordinate transform and known-point/LOS validation. Stop for Tristan if acceptance or licensing requires a product decision.
MODEL_PROFILE: gpt-5.6-terra
MODEL_REASON: Bounded cross-contract viewer migration with compatibility and real-artifact performance validation.
COMPUTER_USE: no; headless browser unavailable
COMMIT/PR: Slice B completion checkpoint on `dev/v1-foundation`; no merge authorized

## 2026-08-20 — 3D / POV V1 Slice C asset gate

STATUS: blocked
SLICE: C — Anubis asset gate
BRANCH: `dev/v1-foundation`
CHANGED: Added machine-enforced `iy.map_asset/v1` assessment (`map_assets.py`), six synthetic gate tests and `docs/3D_POV_V1_SLICE_C_ASSET_GATE.md`. No Valve/Awpy geometry was copied, extracted, converted or committed; no renderer/camera/sightline/Benchmark/System Check/Optimizer code changed.
DATA EVIDENCE: Real replay `446eec75822c…` has 2,523,998 observed player positions, all inside old Awpy triangle bounds. Replay bounds X `-1971.9473..1803.9713`, Y `-1759.9688..2771.7646`, Z `-191.9688..188.1563`. An Awpy BVH check at round 1/tick 6401 yields one visible and one blocked controlled pair in unchanged replay coordinates.
ASSET EVIDENCE: Local Awpy `de_anubis.tri`: build `17595823` (2025-03-04), 29,088,000 bytes, 808,000 triangles, SHA-256 `3DA37BBC33A9E9B2C469E9E39F1FF0A31A6EFE4212D10026516C803B708D9787`; technically compatible but stale/unapproved. Installed CS2 App 730 is build `24828357`; current `de_anubis.vpk` is 269,890,099 bytes, SHA-256 `BCA91CEE11592C65C2869C599769232F29335458376ED90431A013B58C938E07`; current but not extracted/converted/accepted. Awpy's MIT code license does not by itself establish rights for game-derived geometry; Valve terms do not justify an inferred product redistribution grant.
VERIFIED: Six focused map-asset tests pass: accepted synthetic local bundle, version mismatch, distribution block, wrong map, hash mismatch and path escape. Old geometry bounds and two-sided LOS behavior are reproducible. Full suite/setup pending final checkpoint run.
REGRESSIONS: No existing replay/viewer/analyzer/runtime behavior changed.
RISKS: Accepting the stale triangle soup would overclaim build parity. Extracting or distributing current Valve geometry without a chosen permitted route would overclaim authority. The current VPK also lacks an accepted derivative render/visibility mesh and known-point visual proof.
DECISIONS: None silently made. `map_geometry` remains `unavailable`; no placeholder geometry and no renderer start.
OPEN: Tristan must choose: (1) authorize current-build local-only extraction/derivative, never committed/distributed; (2) provide/approve a distributable controlled derivative with documented rights; or (3) retain Anubis 3D as unavailable.
NEXT: Wait for Tristan's asset-provenance route. If local-only is approved, extract/derive only into ignored local storage, bind it to build/hash, then perform transform, known-point and LOS acceptance before any Slice D work.
MODEL_PROFILE: gpt-5.6-terra
MODEL_REASON: Evidence-led asset integrity/provenance gate with product and distribution boundary.
COMPUTER_USE: no
COMMIT/PR: Slice C blocked-gate checkpoint on `dev/v1-foundation`; no merge authorized

## 2026-08-21 — 3D / POV V1 Slice C local-only completion

STATUS: done
SLICE: C — local-only Anubis asset gate complete
BRANCH: `dev/v1-foundation`
CHANGED: Added tested GLB-to-replay-space local derivative support and `Build-LocalAnubisAsset.py`; extended missing-asset coverage and updated the Slice-C/current handoff. Generated ValveResourceFormat tool, extracted physics GLB, render GLB, visibility TRI, manifests and validation PNGs remain below ignored `results/local-map-assets/`. No geometry or third-party binary is tracked/pushed.
DATA EVIDENCE: Real replay `446eec75822c…`; all 2,523,998 observed positions inside geometry bounds. Top-down overlay sampled 25,439 positions; perspective floor/height overlay sampled 10,289 positions. No mirror, quarter-turn or translation mismatch observed; player paths follow the physics corridors/floors.
ASSET EVIDENCE: Installed CS2 build `24828357`, VPK SHA `BCA91CEE…`. ValveResourceFormat CLI 19.2 Windows-x64 archive matched published SHA `53E7E8DA…`. Local bundle retains 27 normal world groups / 673,869 triangles and excludes clip/pass-bullets/water/sky groups. `render_mesh.glb` 77,560,564 bytes SHA `9AD0036D…`; `visibility_mesh.tri` 24,259,284 bytes SHA `D667D728…`; verified manifest SHA `D39B9BE7…`; identity transform; distribution `local_only`.
VERIFIED: Known visible pair remains true and known blocked pair false on current geometry. Real `assess_map_asset()` returns `available` in 0.141 s. Unit coverage includes world-only filtering, replay-space identity GLB, triangle output, schema/map/distribution/version/hash/path/missing gates. Full suite/setup pending final checkpoint run.
REGRESSIONS: No replay, 2D viewer, Analyzer, Benchmark, Optimizer or System Check behavior changed.
RISKS: Asset is valid only for this installed build/hash and must never be packaged or treated as distributable. Current collision mesh lacks authored materials and dynamic geometry. Any CS2 build/hash change invalidates the acceptance.
DECISIONS: Tristan's `next` accepted the explicitly recommended current-build local-only route. This is not approval for redistribution. For the matching local run `map_geometry=verified`; elsewhere it remains unavailable.
OPEN: No Slice-C technical blocker for this local run. Final product distribution still needs a separate rights-approved asset route.
NEXT: Begin Slice D only: minimal `ReplayRenderer` protocol and disposable native embed spike using the ignored local bundle; prove load, deterministic frame/camera updates, resize and dispose. Do not package geometry or add overlays/events yet.
MODEL_PROFILE: gpt-5.6-terra
MODEL_REASON: Current-build local asset derivation with coordinate, integrity, LOS and distribution-boundary validation.
COMPUTER_USE: no
COMMIT/PR: Slice C completion checkpoint on `dev/v1-foundation`; no merge authorized

## 2026-08-17 — Workshop Tools / Hammer startup recheck

STATUS: superseded
TASK: Resume marker-synchronized Inferno-camera validation after the `9ecd909` checkpoint.
BRANCH: `dev/v1-foundation`
CHANGED: No product, map, controller, smoke, geometry, Steam or SDK files changed.
VERIFIED: Steam is running. `cs2.exe -tools` starts Workshop Tools successfully and exposes the Asset Browser plus its Hammer tool entry. Starting Hammer from that entry reproduces `hammer.exe - Systemfehler`: `vstdlib.dll` is missing. Direct SDK-Hammer start reproduces the same error. This is an installed-tool runtime failure, not a repository build failure; the last verified repository state remains `9ecd909`, 33/33 tests and Full Compile `22 compiled, 0 failed, 1 skipped`.
OPEN: WAITING_FOR_TRISTAN. Repairing/verifying the Steam SDK installation can change installed third-party files and was not performed.
NEXT: Tristan repairs the Workshop Tools/CS2 SDK or explicitly approves Steam file verification. Then start Hammer through Workshop Tools, run Full Compile, log the automatic camera pose at Inferno `TRANSITION_EXIT`, compare it with static `0 3450 600 / 35 90 0`, and change only camera application/timing if needed.
COMMIT/PR: Superseded by the 2026-08-17 Steam repair and Hammer recheck below.

## 2026-08-17 — Steam repair, Hammer recovery and Full-Compile recheck

STATUS: waiting_for_tristan
TASK: Repair the documented Workshop Tools start failure, then resume the required Full Compile before the Inferno `TRANSITION_EXIT` camera comparison.
BRANCH: `dev/v1-foundation`
CHANGED: No repository source, map, smoke, geometry or controller changes. Steam was explicitly authorized to validate/repair installed third-party files. CS2 App 730 and the separately installed Counter-Strike: Global Offensive - SDK App 745 were both validated through Steam.
VERIFIED: Steam showed CS2 validation progressing from 8% to 88% and returning to `SPIELEN`; the SDK validation also returned installed/current. `cs2.exe -tools` again opened Asset Browser, and selecting `Hammer (Map Editor)` now started Hammer successfully (the earlier `vstdlib.dll` system error no longer occurred). `improve_yourself_benchmark.vmap` loads in Hammer. Full Compile was explicitly selected and started, but Hammer stopped before the actual compiler pipeline with `GPU Lightmap Baking`: `GPU ray tracing support required for GPU lightmap baking. If you're seeing this message despite having ray tracing-capable graphics hardware, try updating your graphics driver.`
DIAGNOSIS: The Steam/Workshop Tools startup blocker is resolved. The active blocker is now Hammer's required GPU-Raytracing Lightmap-Baking capability; this is an installed graphics/runtime prerequisite, not a repository test, camera, smoke, or geometry failure. No Full Compile result and no new runtime camera evidence exists from this recheck.
OPEN: WAITING_FOR_TRISTAN. A GPU driver update or another official baking/runtime configuration is a system-level decision and was not attempted. The measured static Inferno proof remains `setpos_exact 0 3450 600; setang_exact 35 90 0`; the automatic marker-synchronized comparison remains pending.
NEXT: Tristan supplies or approves the GPU-/driver or documented baking-setup remedy. Then run Full Compile, launch the rebuilt map, instrument/record the automatic Inferno `TRANSITION_EXIT` applied camera pose, compare it with the static validated pose, and change only camera application/timing if warranted. Do not change smoke or geometry before that comparison.
COMMIT/PR: Pending a status-only checkpoint after diff review; no source files changed.

## 2026-08-17 — Read-only GPU/DXR diagnosis for GPU Lightmap Baking

STATUS: waiting_for_tristan
TASK: Determine, without changing any driver, registry, AMD Adrenalin or Hammer setting, whether the actual adapter and DirectX raytracing prerequisites explain Hammer's GPU Lightmap Baking refusal.
BRANCH: `dev/v1-foundation`
CHANGED: No repository, Steam, driver, AMD Adrenalin, registry or Hammer-setting changes. DxDiag was opened locally with online WHQL signature checking declined.
VERIFIED: Windows reports one active display adapter: `AMD Radeon RX 7900 XTX` (PCI `VEN_1002&DEV_744C`), status `OK`, driver `32.0.31035.1003`, driver date 2026-07-24, 24,533 MB VRAM, 1920x1080 at 240 Hz. `cs2.exe -tools` is active on this single-adapter system. DxDiag reports DirectX 12, Direct3D DDI 12, feature levels through `12_2`, driver model `WDDM 3.2`, `DirectX 12 Ultimate: Aktiviert`, Direct3D acceleration enabled and `Es wurden keine Probleme gefunden`. Feature Level 12_2 requires DXR Tier 1.1; therefore the local adapter/runtime exposes the required DirectX raytracing capability.
DIAGNOSIS: The `GPU ray tracing support required` dialog is not explained by an absent RX 7900 XTX, by missing DX12/DXR support, or by a visibly failed display driver. It is now a Hammer/CS2 GPU-Lightmap-Baking detection or configuration-path issue that needs a narrower Hammer-side read-only diagnosis before treating a driver update as a remedy.
OPEN: WAITING_FOR_TRISTAN. No driver install/update, registry edit, Adrenalin change or compile-setting change was attempted.
NEXT: With a new explicit scope, inspect Hammer/CS2's relevant local configuration and compile logs read-only for the exact raytracing-device detection path; only then decide whether an official driver or baking-configuration remedy is warranted. Preserve the no-smoke/no-geometry constraint until Full Compile can run and the marker-synchronized camera comparison resumes.
COMMIT/PR: Pending status-only checkpoint after diff review; no source files changed.

## 2026-08-17 — Hammer/CS2 GPU-Lightmap-Baking detection-path diagnosis

STATUS: waiting_for_tristan
TASK: Identify, with local Hammer/CS2 inspection only, why GPU Lightmap Baking rejects the verified RX 7900 XTX/DXR stack.
BRANCH: `dev/v1-foundation`
CHANGED: No repository source, map, smoke, geometry, controller, Steam, driver, registry, AMD Adrenalin, Hammer or CS2 configuration was changed. The inspection was read-only.
VERIFIED: The only active Workshop Tools process is `cs2.exe -tools` (PID 17456); Steam's CS2 launch options are only `-novid -nojoy`. Its loaded renderer is `rendersystemdx11.dll`, not a DX12 renderer. This does not govern the baking preflight: the installed `hammer.dll` embeds and runs `vrad3.exe -script check_raytracing_support.vrad3 -vulkan -gpuraytracing`. The local Vulkan runtime is 1.4.341 and enumerates one discrete `AMD Radeon RX 7900 XTX` (vendor `0x1002`, device `0x744c`, AMD proprietary driver `26.7.1 (LLPC)`). It exposes `VK_KHR_acceleration_structure` rev. 13, `VK_KHR_ray_tracing_pipeline` rev. 1, `VK_KHR_ray_query` rev. 1, `VK_KHR_deferred_host_operations`, `VK_KHR_buffer_device_address`, `VK_KHR_spirv_1_4` and shader-float-controls extensions. The Tools video file records the same AMD vendor/device pair. Its `setting.knowndevice = 0` and Hammer's UI-only `3D Views/Hardware = false` were observed but are not used in the embedded VRAD preflight command; changing either would be unsupported guesswork. No recent Hammer/VRAD diagnostic log exists under the installed game tree, and the Hammer error dialog exposes no lower-level reason or error code.
DIAGNOSIS: The expected hardware/API condition is present for both relevant paths: Windows exposes DXR 1.1 (previous diagnosis) and the exact Vulkan RT extensions used by Hammer's `-vulkan -gpuraytracing` check are available on the actual RX 7900 XTX. The failure is therefore narrowed to the opaque `check_raytracing_support.vrad3`/VRAD preflight itself (its detection policy, invocation environment, or an internal compatibility defect), not to absent DXR, a wrong adapter, missing Vulkan RT extensions, Steam launch options, or a project setting. The observed Vulkan loader warning concerns missing layer-manifest registry entries, but Vulkan still initializes, enumerates the AMD device, and reports the required RT extensions; it is not sufficient evidence for a remedy.
OPEN: WAITING_FOR_TRISTAN. The smallest reproducible next diagnostic step would execute only Hammer's own fixed preflight command, `vrad3.exe -script check_raytracing_support.vrad3 -vulkan -gpuraytracing`, from the already installed Workshop Tools environment and capture its exit code/console output. This is an active executable run rather than a read-only inspection and can create transient shader/cache data, so it was not started under the current approval. No driver update or configuration change is justified by the evidence.
NEXT: On explicit approval, run that isolated preflight once, capture output, then close Workshop Tools without retaining configuration changes. If it reports a concrete unsupported capability, decide the smallest official remedy from that result; otherwise retain the evidence as an SDK/VRAD compatibility blocker for Valve/AMD. Only after GPU baking can start: Full Compile, then the marker-synchronized Inferno `TRANSITION_EXIT` camera comparison with the static validated pose `0 3450 600 / 35 90 0`.
COMMIT/PR: Pending status-only checkpoint after diff/test review; no product source files changed.

## 2026-08-17 — Steam-current check, restart recheck and parked SDK blocker

STATUS: waiting_for_tristan (parked)
TASK: Check only whether Steam offers a CS2/Workshop-Tools update or a fresh Steam session changes the installed tools state; otherwise preserve a complete SDK/Valve-support blocker.
BRANCH: `dev/v1-foundation`
CHANGED: No repository, map, smoke, geometry, controller, VRAD invocation, driver, registry, AMD Adrenalin, Hammer or CS2 configuration change. Steam was restarted under explicit approval after the active Tools session was cleanly ended; no Steam validation was repeated and no foreign file or manual script copy was made.
VERIFIED: Steam's own UI states `Ihr Steam-Client ist bereits aktuell`; its Library reports the SDK cloud status as `Aktuell`, and no update affordance was offered for Counter-Strike 2 or the SDK. Before the restart, CS2 App 730 and SDK App 745 had zero download/staging bytes. After the controlled restart, Steam is freshly running and `cs2.exe` is not. CS2 remains installed at build `24701871`, `UpdateResult 0`, `BytesToDownload 0`, `BytesDownloaded 0`, `BytesToStage 0`, `BytesStaged 0`; SDK 745 remains at build/target build `11399846` with the same zero-byte update state. `appmanifest_730.acf` changed only because Steam recorded the ended Tool-session `LastPlayed` time; SDK 745's manifest hash/time did not change. No updated SDK asset set was delivered.
DIAGNOSIS: The already reproduced `check_raytracing_support.vrad3` read failure remains unchanged after both Steam validation and a complete fresh Steam session. This is now a parked external SDK/Workshop-Tools asset-mount blocker. The available evidence does not support driver, registry, Adrenalin, Hammer/CS2 configuration, benchmark geometry, smoke, or controller work as a remedy.
OPEN: WAITING_FOR_TRISTAN. Do not resume Full Compile or alter the benchmark until an official CS2 Workshop Tools/SDK update, a targeted Valve support response, or an expressly approved official repair procedure supplies a materially different tools build or a supported script-mount remedy.
SUPPORT PACKAGE: Copy-ready report for Valve/Steam Support: `Counter-Strike 2 Workshop Tools / Hammer blocks every GPU Lightmap Baking Full Compile before the build pipeline. Steam App 730 and SDK App 745 were validated; Steam client is current; a full Steam restart produced no update (CS2 build 24701871, SDK build 11399846, all update/staging byte counts zero). On Windows 11 with AMD Radeon RX 7900 XTX, VRAD itself detects Vulkan Physical Device: AMD Radeon RX 7900 XTX and the Vulkan runtime exposes acceleration structure, ray-tracing pipeline and ray-query extensions. Running Hammer's fixed preflight from the valid CS2 game context, vrad3.exe -script check_raytracing_support.vrad3 -vulkan -gpuraytracing, exits 1 after GPU detection with: Failed to read .../game/csgo/check_raytracing_support.vrad3. The same name is not present as a loose installed file. Hammer surfaces only the misleading generic dialog GPU ray tracing support required for GPU lightmap baking. Please identify the supported location/mount path for check_raytracing_support.vrad3 or provide the Workshop Tools/SDK update that restores it.`
NEXT: Park the benchmark transition task. When Tristan has an official response or a newer Steam/SDK build, compare its build IDs first; only then re-run the single preflight and, on exit 0, Full Compile plus the marker-synchronized Inferno camera check.
COMMIT/PR: Pending status-only checkpoint after diff/test review; no product source files changed.

## 2026-08-17 — Executed VRAD GPU-raytracing preflight

STATUS: waiting_for_tristan
TASK: Run the explicitly approved one-shot VRAD `check_raytracing_support.vrad3` preflight and capture the complete output and exit status before deciding on Full Compile.
BRANCH: `dev/v1-foundation`
CHANGED: No repository source, map, smoke, geometry, controller, Steam, driver, registry, AMD Adrenalin, Hammer or CS2 configuration was changed. The permitted executable test refreshed only normal Tools thumbnail/resource-cache artefacts.
VERIFIED: A first direct invocation from `game/bin/win64` exited `1` before GPU initialization because it could not locate a gameinfo file. The same exact preflight command was then run from the installed CS2 game context (`game/csgo`): `vrad3.exe -script check_raytracing_support.vrad3 -vulkan -gpuraytracing`. Its complete console result was: `VRAD3 - Distributed Lighting Tool`; build `pc64 Aug 12 2026 14:24:12`; working directory `.../game/csgo`; `Vulkan Physical Device: AMD Radeon RX 7900 XTX`; one non-fatal capability note (`VK_EXT_extended_dynamic_state_2 does not support extendedDynamicState2PatchControlPoints, disabling.`); then `Failed to read .../game/csgo/check_raytracing_support.vrad3`; exit code `1`. The exact expected GPU is therefore detected by VRAD itself. The script is absent as a loose file from the verified CS2/SDK installation. Installed `pak01_dir.vpk` indexes were also inspected read-only and did not reveal the asset string; the shipped installation provides no `vpk.exe` lister.
DIAGNOSIS: This converts the generic Hammer dialog into a reproducible, non-GPU failure: the helper reaches Vulkan and selects the RX 7900 XTX, but cannot read the `check_raytracing_support.vrad3` asset needed to complete the bake-capability test. DXR, Vulkan RT extensions, adapter selection, Steam launch options, and the tools-viewer renderer are not the proximate blocker. The remaining cause is a missing/unmounted SDK preflight asset or an SDK/VRAD mounting-context defect. Since Steam has already validated App 730 and SDK App 745, repeating validation blindly is unlikely to create new evidence.
OPEN: WAITING_FOR_TRISTAN. Full Compile cannot proceed because Hammer will receive the same failed preflight status. No configuration or driver modification is justified.
NEXT: Preserve the captured output and request/approve a targeted official CS2 Workshop-Tools SDK update/repair or Valve support clarification specifically for `check_raytracing_support.vrad3` and VRAD's mounted-script context. After that asset is demonstrably readable, rerun the same preflight; only on exit `0` run Full Compile and the marker-synchronized Inferno `TRANSITION_EXIT` camera comparison.
COMMIT/PR: Pending status-only checkpoint after diff/test review; no product source files changed.

## 2026-08-17 — Fade recovery and Inferno camera measurement

STATUS: blocked
TASK: Remove the persistent Red-Room/flash occlusion and establish a valid view of the real Inferno stairs without smoke or geometry changes.
BRANCH: `dev/v1-foundation`
CHANGED: Corrected CS2 `fadeout`/`fadein` calls to supported time-plus-RGB syntax and routed the server-side cheat commands through `ServerCommand`. Raised the post-flash Inferno camera above the stair meshes. Smoke and VMAP geometry are unchanged. Controller hash is `45D2CF2C0EFB05454304B2F46630239D6B7998BC0F3172B8B71DD405DC07B4BD`.
VERIFIED: 33/33 tests pass. Hash-verified deploy backup is `deploy-20260817-014957`. Full Compile ended 2026-08-17 01:50:31 with `22 compiled, 0 failed, 1 skipped` and 25.066 s total elapsed. A fresh runtime pass no longer remains red after the flash handoff. With runtime frozen after the pass, `setpos_exact 0 3450 600; setang_exact 35 90 0` renders all five ascending white stair blocks clearly and proves valid geometry/camera coordinates.
DIAGNOSIS: The previous red full-screen blocker was invalid legacy fade syntax plus client-only dispatch. The remaining mismatch is narrower: at the automatic `TRANSITION_EXIT` marker, the interpolated camera still showed an empty enclosed floor/wall composition instead of the stair view produced by the same intended position/angle in the static check.
OPEN: BLOCKED only on proving why the automatic camera application/timing differs from the static validated view, then on the complete Ancient-water/Red-Room/flash/Inferno acceptance capture. Do not change smoke or geometry.
NEXT: Instrument or echo the applied camera position/angles at `TRANSITION_EXIT`, compare them with `0 3450 600 / 35 90 0`, correct only camera interpolation/application, Full Compile, then rerun the complete marker-synchronized sequence.
COMMIT/PR: Pending checkpoint commit and push after final diff/test/sync verification.

## 2026-08-17 — Compiled graybox transform correction

STATUS: blocked
TASK: Resolve the measured VMAP/runtime placement mismatch before further transition tuning.
BRANCH: `dev/v1-foundation`
CHANGED: `author_transition_graybox.py` now bakes each requested box dimension into the cloned mesh `position:0` vertices and emits unit object scale. The VMAP was reproducibly regenerated from the pre-graybox baseline; Nuke geometry, controller paths, smoke, flash and timing are unchanged. Manifest hash updated to `9D7BE49FD2FA9F720267E5FD155054F478F64416408AC681EF02B578274276CE`.
VERIFIED: 32/32 tests pass. Deployment was hash-verified with backup `deploy-20260817-011505`. After Reload From Disk, Full Compile reported `22 compiled, 0 failed, 1 skipped, 0m:26s`; end build was 2026-08-17 01:16:48 with 29.098 s total elapsed. A fresh normal-viewer run rendered the first transition smoke inside a closed corridor and subsequent frames inside the baked destination rooms, proving that compiled geometry now exists at the controller coordinates.
DIAGNOSIS: The earlier source transforms were arithmetically plausible but object scale was not a reliable compiled-size mechanism for the cloned flat mesh. Vertex baking fixes that placement/shape failure. Current frames are no longer empty sky, but landmark composition remains incomplete: reflective water, the intended Red Room read and the Inferno stair sequence were not all unambiguously visible in the sampled frames.
OPEN: BLOCKED only on marker-synchronized visual composition/acceptance, not Steam, Workshop Tools, missing geometry or runtime placement. Do not claim the full transition complete yet.
NEXT: Capture Ancient water, Red Room approach/flash and Inferno stair exit against their VConsole markers on this baked build. If a landmark misses the frame, adjust only the corresponding camera keyframe/target, then Full Compile and repeat the complete sequence.
COMMIT/PR: Pending checkpoint commit and push after final diff/test/sync verification.
# Handoff 2026-08-21 — Binding visual master integration

STATUS: review
TASK: Die nachgereichte neunseitige Concept-Preview als verbindliche visuelle Master-Referenz in den aktuellen Beast-Stand integrieren, ohne funktionale Wahrheit oder bestehende Arbeit zu verändern.
BRANCH: `dev/v1-foundation`
CHANGED: Exakte PDF unter `docs/design/Improve_Yourself_Concept_Preview_Discord_Q98.pdf` versioniert; `docs/design/README.md`, `UI_SPEC.md`, `BRANDING.md`, `MOCKUP_INDEX.md`, `docs/EXPERIMENTAL_V1.md`, `docs/AGENT_BASE.md`, `coordination/CURRENT.md` und dieser Handoff auf die Zwei-Wahrheiten-Regel und den tatsächlichen Sichtabgleich aktualisiert. Keine Produkt-, Parser-, Rule-, Replay-, Benchmark-, System-Check- oder Optimizer-Funktion geändert.
VERIFIED: Quell- und Repository-PDF sind SHA-256-identisch (`6CB861CCC49DD5D834975FE7474E5E2BE9A44208ADC18158561FAB0A6FF63606`); alle neun bildbasierten Seiten visuell geprüft und Repository-PDF mit neun lesbaren Seiten validiert. Konform: Variant-3-Marke, Midnight/Metallic-Grundsystem, dunkle Titelfläche, gemeinsame Sidebar, ruhige Karten-/Panelhierarchie, restrained cyan accents und keine weißen Fremdflächen. Restabweichungen: flachere Oberflächen, weniger metallische Tiefen-/Reflexionswirkung, sparsame Iconografie und geringere Paneldichte. `pytest` 122/122 PASS; `compileall` PASS; `git diff --check` PASS.
DECISIONS: PDF ist visuelle Wahrheit, aktueller Branch ist funktionale Wahrheit. PDF-Beispieldaten, Scores, langfristige Trends, automatische Apply-Aktionen und nicht vorhandene Module sind illustrativ und dürfen nicht als Funktion zurückkehren. Keine neue Designsprache und kein Redraw des Master-Logos.
OPEN: Menschliche Produktabnahme bleibt Tristan vorbehalten. Die dokumentierten visuellen Deltas sind nur nach konkreter Priorisierung umzusetzen; sie rechtfertigen keine freie Neugestaltung.
NEXT: Experimental-Build gegen die versionierte Master-PDF vollständig abnehmen und eine konkrete, priorisierte visuelle Abweichung zur Korrektur freigeben; bis dahin keine zusätzliche Funktion entwickeln.
MODEL_PROFILE: terra
MODEL_REASON: Verbindlicher Designabgleich und Repository-Konsolidierung ohne Architektur- oder Funktionsänderung.
COMPUTER_USE: no
COMMIT/PR: Master-Integration `7519690` plus nachfolgender `.pdf binary`-Schutzcommit auf `dev/v1-foundation`.

# Handoff 2026-08-21 — Experimental UI consolidation

STATUS: partial / review-ready within available UI evidence
TASK: Verbindliche Mockup-/UI-Zielrichtung mit dem realen Experimental-Demoablauf zusammenführen
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `src/improve_yourself/assets/improve-yourself-wordmark-v3.png`, `tests/test_analyzer_shell.py`, `docs/EXPERIMENTAL_V1.md`, `docs/AGENT_BASE.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`
VERIFIED: Exakte Variant-3-Wordmark-Quelle per identischem SHA-256 `9fcec0bf8d8b05340b038cf30feaead97463fbd35a2fde157b7d06a34f9cfd80` übernommen; finale native Windows-Sichtprüfung bei 1360x860 PASS (dunkle Titelleiste, vollständige Wortmarke, Sidebar, aktiver Reiter, keine weiße Fremdfläche); `pytest` 120/120 PASS; `compileall` PASS; `git diff --check` PASS.
DECISIONS: Keine neue Designsprache. Belegte Tokens/Typografie/Variant 3 sind verbindlich. `Dashboard`, `Reports` und `Settings` bleiben sichtbar `NEEDS_UI_REFERENCE`; `System Check / Optimizer` ist `PARTIAL_REFERENCE` und read-only. Keine Fake-Kennzahlen, Ersatzmasken oder Optimizer-Ausweitung.
OPEN: Die konkreten beschlossenen Detailmockups für Dashboard, Reports und Settings sind weder im aktuellen Repository noch im geprüften Variant-3-Referenzcheckout eindeutig verfügbar. Funktionale Real-Demo-Läufe wurden nicht verändert oder neu begonnen.
NEXT: Tristan ordnet die drei eindeutigen Detailreferenzen zu oder nimmt den konsolidierten Build ab; danach ausschließlich die belegten Reiterlayouts umsetzen.
MODEL_PROFILE: terra
MODEL_REASON: Zusammenhängende UI-/Funktionskonsolidierung mit Tests und visueller Runtime-Abnahme.
COMPUTER_USE: yes
COMMIT/PR: Implementierungsstand `4971b96` auf `origin/dev/v1-foundation`; dieser Handoff-Nachtrag dokumentiert die veröffentlichte Referenz.

## Handoff 2026-08-21 — Canonical design reference integration

STATUS: review
TASK: Die nachgereichten kanonischen Dateien unter `docs/design/` in den laufenden Experimental-UI-Auftrag integrieren.
BRANCH: `dev/v1-foundation`
CHANGED: Vier reine Designreferenz-Commits aus `origin/beast/analyzer-default-criteria-v1` nachvollziehbar übernommen; Dashboard mit realen Modul-Quick-Actions und lokalem Workflowstatus umgesetzt; Reports mit hash-/workflowgebundenem Zugriff auf echte Report-/Timeline-Artefakte; Settings auf das reale aktive Theme begrenzt; Tactical Replay öffnet nur das validierte lokale Artefakt; System Check ist direkt read-only ausführbar. Referenzmatrix, Tests, Experimental-Spezifikation, Shared Base und CURRENT entsprechend aktualisiert.
VERIFIED: 120/120 pytest PASS; compileall PASS; `git diff --check` PASS. Windows-Sichtprüfung bei 1360x860: gemeinsame dunkle Shell, vollständige Variant-3-Wortmarke, Analyzer, Dashboard-Modulkarten und Reports-Leerzustand PASS; eine unnötige Innenrahmenlinie im Reports-Aktionsbereich wurde dabei gefunden und entfernt.
DECISIONS: `docs/design/README.md`, `UI_SPEC.md`, `BRANDING.md` und `MOCKUP_INDEX.md` sind verbindlich. Fehlende Standalone-Rasterbilder blockieren Dashboard/Reports/Settings nicht mehr, weil `MOCKUP_INDEX.md` ausdrücklich die Ableitung aus globaler Shell und nächstem freigegebenem Modul vorgibt. Keine Fake-Werte, Fülloptionen oder Optimizer-Funktion ergänzt.
OPEN: System Check / Optimizer bleibt `PARTIAL_REFERENCE`, da Optimizer-Funktion weiterhin außerhalb dieses Replay-Strangs liegt. Produktabnahme und Merge bleiben Tristan vorbehalten.
NEXT: Vollständigen UI-/Produktfluss anhand des gepushten Experimental-Builds prüfen; nur konkrete Abweichungen gegen `docs/design/` korrigieren.
MODEL_PROFILE: terra
MODEL_REASON: Verbindliche Design-/Funktionsintegration mit lokalem Artefaktzugriff, Tests und GUI-Abnahme.
COMPUTER_USE: yes
COMMIT/PR: wird als abschließender kanonischer UI-Abgleich auf `dev/v1-foundation` committed und gepusht.

## Handoff 2026-08-21 — Real-workflow product review

STATUS: review
TASK: Den gepushten Experimental-Build vollständig mit dem bestehenden realen Ancient-Workflow gegen `docs/design/` prüfen und nur belegte Abweichungen korrigieren.
BRANCH: `dev/v1-foundation`
CHANGED: Optionalen `--workflow`-Start für exakt ein explizit benanntes, über dieselbe fail-closed Grenze validiertes Manifest ergänzt; kein Scan und kein Reparse. Read-only-/disabled-Combobox-Zustände vollständig in Midnight/Metallic überführt. Reproduzierbaren Start dokumentiert.
VERIFIED: Reale vorhandene Ancient-Wahrheit ohne Reparse geladen: de_ancient, 18 Runden, 10 benannte Spieler, 54 Szenen, Hashpräfix `c183dd61fc6a`. Analyzer/Review, Dashboard und Reports visuell bei 1360x860 geprüft; Dashboard und Reports zeigen ausschließlich diese echten Workflowdaten, Report-/Timeline-Aktionen sind nur im READY_FOR_REVIEW-Zustand aktiv. Helle Combobox-Systemfläche reproduziert, korrigiert und im selben Realzustand erneut mit PASS geprüft. 120/120 pytest, compileall und `git diff --check` PASS.
DECISIONS: Der Startparameter ist ein reproduzierbarer Test-/Power-User-Einstieg und kein zweiter Vertrauenspfad. Native Dateiauswahl bleibt erhalten. Keine Parser-, Regel-, Szenen-, Benchmark-, System- oder Optimizer-Änderung.
OPEN: CS2-Live-Readiness wurde nicht erneut ausgelöst; Tick 3654 bleibt die vorhandene Runtime-Evidenz. Merge und Gesamtproduktabnahme bleiben Tristan vorbehalten.
NEXT: Tristan führt den vollständigen Nutzerreview auf dem gepushten Build aus; Engineering korrigiert danach nur konkret gemeldete Design-/Funktionsabweichungen.
MODEL_PROFILE: terra
MODEL_REASON: Realer produktweiter UI-Zustandscheck mit kleiner sicherheitsrelevanter CLI-Erweiterung und Runtime-QA.
COMPUTER_USE: yes
COMMIT/PR: pending final gate and push on `dev/v1-foundation`.

## Handoff 2026-08-21 — Remaining-tab real-state review

STATUS: review
TASK: Rules, Tactical Replay, Settings und System Check/Optimizer im real geladenen Ancient-Zustand gegen die kanonische Designsprache prüfen.
BRANCH: `dev/v1-foundation`
CHANGED: TCheckbutton-Zustände vollständig an Midnight/Metallic angepasst; helle native Disabled-Flächen entfernt. Interne System-Check-Projektcopy (`PARTIAL_REFERENCE`, Replay-Konsolidierung) durch transparente Nutzertexte ersetzt. Ergebniszusammenfassung deutsch und verständlich formuliert; System-Check-Schema und Bewertung unverändert.
VERIFIED: Rules mit sieben real aktiven objektiven V1-Ankern, Tactical-Replay-Einstieg, restriktive Settings und System Check visuell geprüft. Read-only System Check real ausgeführt: 6 OK, 2 REVIEW/zu prüfen, 0 Handlungsbedarf, Policy weiterhin keine Änderungen angewendet. Checkbox-Fremdflächen reproduziert, korrigiert und im selben Workflow erneut visuell geprüft. Finale Nutzercopy ohne interne Projektbegriffe erneut visuell PASS. 120/120 pytest, compileall und `git diff --check` PASS.
DECISIONS: Interne Referenz-/Arbeitsstrangbegriffe gehören nicht in Nutzerflächen. Unknown/REVIEW bleibt unknown/zu prüfen und wird nicht zum negativen Befund. Keine Optimizer-, System- oder Replay-Funktion erweitert.
OPEN: Vollständiger Endnutzer-Abnahmelauf und Merge bleiben Tristan vorbehalten; CS2-Live-Readiness wurde nicht erneut ausgelöst.
NEXT: Gepushten Experimental-Build als zusammenhängenden Nutzerfluss abnehmen; danach nur konkrete Abweichungen korrigieren.
MODEL_PROFILE: terra
MODEL_REASON: Reale tabübergreifende Runtime-QA mit UI-Zustands- und Sicherheitscopy-Korrektur.
COMPUTER_USE: yes
COMMIT/PR: wird als verbleibender Tab-/System-Check-Review auf `dev/v1-foundation` committed und gepusht.

## Handoff 2026-08-21 — Supported Experimental tester start

STATUS: review
TASK: Den zusammenhängenden Endnutzer-Abnahmelauf über einen unterstützten lokalen Experimental-Start reproduzierbar machen.
BRANCH: `dev/v1-foundation`
CHANGED: `tools/dev/Start-Experimental.ps1` ergänzt. Ohne `-Workflow` öffnet er die normale Shell-Auswahl; mit `-Workflow` akzeptiert er nur eine vorhandene, ausdrücklich benannte `demo-workflow.json` und übergibt sie an die bestehende fail-closed Shell-Grenze. Locked Setup ist Standard, `-SkipSetup` nur explizit. README/Tools-Doku und zwei Windows-Launcher-Negativtests ergänzt. Keine Änderung am älteren `Start-V1Review.ps1`.
VERIFIED: Launcher real mit vorhandenem Ancient-Workflow und separatem OutputRoot gestartet; lokale Policy und exakt aufgelöster Manifestpfad sichtbar, Shell öffnete erfolgreich. Fehlender Pfad und vorhandene Nicht-Manifestdatei enden vor Shellstart mit verständlichem Fehler. 122/122 pytest, compileall, PowerShell-Help-Smoke und `git diff --check` PASS.
DECISIONS: Experimental erhält einen eigenen unterstützten Testerstart; der ältere integrierte V1-Review-Launcher bleibt unverändert. Kein Ordnerscan, Recent-Autoselect, Reparse, Upload oder automatischer System-/Optimizer-Apply.
OPEN: Menschliche Gesamtproduktabnahme und Merge bleiben Tristan vorbehalten. Kein Installer/EXE-Paket in diesem Slice; der Launcher verwendet bewusst die gesperrte Projektumgebung.
NEXT: Tristan startet `.\tools\dev\Start-Experimental.ps1 -SkipSetup -Workflow '.\results\demo-workflow-ancient\c183dd61fc6a\demo-workflow.json'` für die Endnutzerabnahme; danach nur konkrete Befunde korrigieren.
MODEL_PROFILE: terra
MODEL_REASON: Unterstützter lokaler Produkteinstieg mit Fail-closed-Grenze, Windows-Tests und Realstart.
COMPUTER_USE: yes
COMMIT/PR: pending commit/push on `dev/v1-foundation`.
# Handoff 2026-08-21 — Master-layout Analyzer Review <-> Tactical Replay slice

STATUS: WAITING_FOR_TRISTAN
TASK: Binding layout-master integration plus one-scene-context Analyzer Review <-> Tactical Replay product slice.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py` now presents the Analyzer entry as master-aligned Demo/source, CT/T line-up, selection/profile and Analysis/CS2-readiness panels; Dashboard uses the canonical full Variant-3 wordmark; Embedded Review stays a native scene-rail/detail presentation; Tactical Replay is a native scene rail + dominant replay canvas + frame timeline + bottom action strip. Added `src/improve_yourself/embedded_tactical.py` as a validation/presentation adapter over the existing ReplayStore, ReplayController and `build_tactical_2d_projection`; no parser, analysis, scene, review or NetCon authority was duplicated. Added focused tests and `docs/ANALYZER_TACTICAL_CONTEXT_V1.md`; synchronized Shared Base and CURRENT.
UI_MASTER_CHECK: Dashboard: canonical full wordmark, restrained module-card row and real current-workflow panel; no illustrative counters. Analyzer entry: long flat form replaced by grouped multi-column panels matching the Demo Analyzer composition while preserving current player/profile flow. Embedded Review: scene rail left, canonical scene detail/status/note/actions right. Tactical Replay: scene rail left, dominant central positional canvas, nearby frame timeline/context and bottom controls, matching the page-06 hierarchy. Shared compact sidebar, active module state, dark title/chrome, Midnight panels and restrained blue contours remain consistent. Structural residuals are evidence-bound: no map radar asset, utility/event timeline, team score/economy or match clock exists in the current replay truth, so those illustrative master elements were not fabricated. System Check/Optimizer remains read-only and was not expanded.
BRANDING: Canonical Variant 3 unchanged. Sidebar uses the approved wordmark crop; Dashboard uses the full wordmark; EXE/window/taskbar retain the derived compact icon. `NEEDS_BRAND_ASSET` does not apply.
CONTEXT_PRESERVATION: Review and Tactical use the same canonical analysis `scene_id`; presented context includes map, round, tick, timecode/explicit unknown, players/focus where present, profile, selection mode, review state and note. Tactical scene stepping updates the Review selection; returning selects and scrolls to that exact scene. An initially observed Tk list-selection race that reverted `Next scene` was reproduced and fixed by suppressing only the queued programmatic selection event.
PORTABLE_SIGHTCHECK: Fresh Portable started with the existing validated `c183dd61fc6a` Ancient workflow. Branding, grouped Analyzer composition, 54-scene Embedded Review and native Tactical page rendered without a foreign white surface. Final package flow: Review scene Tick 3654 -> Tactical Tick 3654 -> Next scene Tick 4362 -> return to Review Tick 4362. Zoom changed the positional scale; reset/pan bindings remain the existing tested implementation. No normal-flow browser window opened.
NETCON: From the synchronized Review scene, the existing fail-closed coordinator reported `In CS2 geöffnet: fut-vs-mouz-m2-ancient.dem · Tick 4362`. This revalidates the unchanged loopback/active-demo/allowed-scene boundary in the new navigation flow. Prior practical ticks 3654/4362/12577 remain historical evidence; this slice actively repeated 4362.
VERIFIED: `pytest` 131/131 PASS (also executed inside the final build); Python `compileall` PASS; `git diff --check` PASS. Final Portable build PASS with dependency check clean. EXE SHA-256 `1A52B7C92E9F92EA590DE19A2A8D0687FF87700A77034756F09BCAEC1A43C562`; ZIP SHA-256 `9151726293DE516BFEE8DFB68E83BCECCDD9551ED8D883306401F7C9F69B36E6`. Setup/signing is still not generated because no supported installer/signing contract is defined.
DECISIONS: Current branch remains functional truth; the nine-page PDF remains visual/structural truth. Current functions are fitted into the master hierarchy; obsolete illustrative data is not restored. Browser HTML stays explicit export/fallback. No new analyzer rules, clip/OBS/video, 3D/POV, benchmark, optimizer or replay-engine work was started.
OPEN: Human visual/product acceptance and merge decision remain Tristan's. The master's actual radar background and richer utility/event/score panels require separately proven source data/assets before implementation. True tick rate remains unavailable in this demo evidence, so timecode correctly remains `Zeit nicht belegt`. Window minimum remains 1080x720; the verified primary view was 1360x890. No functional blocker remains for this slice.
NEXT: Tristan reviews the pushed Portable build and either accepts this slice or reports a concrete screen-specific master deviation; do not start another Product Slice or merge to `main` without that decision.
MODEL_PROFILE: terra
MODEL_REASON: Cross-cutting desktop layout, shared-state integration, packaging and real CS2 runtime validation.
COMPUTER_USE: yes
COMMIT/PR: This handoff is part of the final pushed `dev/v1-foundation` checkpoint; exact HEAD is recorded in the final task report.

# Handoff 2026-08-21 — Visual Master Conformance correction pass

STATUS: WAITING_FOR_TRISTAN
TASK: Den bestehenden Experimental-Slice grafisch an die verbindliche neunseitige Master-PDF angleichen, ohne Architektur, Funktionen oder Replay-Wahrheit zu erweitern.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `docs/AGENT_BASE.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`. Die bestehende Tk-/Desktop-Shell erhielt ein tieferes Midnight-/Metallic-Farbsystem, moderne flache Button-/Dropdown-/Scale-/Rule-Zustände, klarere Panel- und Border-Hierarchie, kompakte Sidebar-Symbole und einen Variant-3-Dashboard-Hero. Analyzer-Aktionen und Auswahlzeilen wurden für kleinere Breiten neu angeordnet; der Analyzer-Inhalt ist bei 1080x720 scrollbar. Der Tactical-HTML-Fallback liegt in einer eigenen responsiven Sekundärzeile.

| Screen | Structural Master Match | Visual Master Match | Remaining Deviation |
| --- | --- | --- | --- |
| Application Shell / Hauptfenster | PASS | PASS | Native Windows-Titelleiste bleibt als erlaubter Desktop-Host sichtbar, ist aber dunkel und erzeugt keine weiße Fremdfläche. |
| Home / Dashboard | PASS | PASS | Bewusst geringere Informationsdichte; keine illustrativen Master-Kennzahlen ohne reale Daten. |
| Analyzer | PASS | PASS | Bei 1080x720 vertikal scrollbar; keine Demo-Bibliothek erfunden. |
| Embedded Analyzer Review | PASS | PASS | Keine Szenen-Thumbnails oder Radarbilder, weil dafür keine freigegebenen Assets/Daten vorliegen. |
| Tactical Replay | PASS | PASS | Positionsgrid statt Master-Radar; Utility-/Score-/Economy-Leisten bleiben mangels belegter Replay-Daten aus. |
| Rules / Profile | PASS | PASS | V1 zeigt die vorhandenen neutralen Anker/Profile, keine neue Regelbearbeitung. |
| Optimizer / System Check | PASS für aktuellen read-only Umfang | PASS | Bewusst sparsamer als das illustrative Masterbild; keine Optimizer-Funktion in diesem Slice. |
| Settings / Reports | PASS für vorhandenen Realumfang | PASS | Restriktive echte Aktionen statt illustrativer Optionen oder Fake-Werte. |

BRANDING: Kanonische Logo-Variante 3 unverändert. Vollmarke auf dem Dashboard, freigegebener Wordmark-Crop in der Sidebar und bestehende Compact-Mark für EXE/Fenster/Taskleiste. Kein `NEEDS_BRAND_ASSET`.
DECISIONS: Die bestehende Desktop-/Tk-Architektur bleibt. Der Pass verändert ausschließlich Darstellung und responsive Anordnung. Keine Analyzer-Kriterien, Rules, Replay-/3D-/POV-, Optimizer-, Benchmark-, Clip- oder Video-Funktion begonnen. HTML bleibt expliziter Export/Fallback, nicht normaler Review-Hauptweg.
VERIFIED: Gezielte GUI-Prüfung mit real vorhandenem Ancient-Workflow bei 1080x720: Dashboard-Hero ohne Überlagerung; Analyzer horizontal vollständig und vertikal scrollbar; Rules als einheitliche Metallic-Zeilen; Tactical-Szenenrail, Grid und Primäraktionen vollständig sichtbar, Browser-Fallback separat erreichbar. Frischer Portable-Build bei 1360x860 praktisch geöffnet: Analyzer -> Embedded Review (54 reale Szenen, Tick 3654) -> Tactical; Szenen 3654, 4362 und 5860 sichtbar gewechselt; Rückkehr zum synchronisierten Review-Pfad ohne Browseröffnung. Vollständiger `pytest`: 131/131 PASS; Build führte dieselben 131 Tests erneut mit PASS aus; `compileall` PASS; `git diff --check` PASS. EXE SHA-256 `63FB16E72B355B2694A218F24E7229CB98D833480AB43B78818B65E9749E0E1B`; Portable-ZIP SHA-256 `364AF963EF5AE9FA9BB4DA7BB5F409B9F766E28D49593CF9CE06351C3EF5B906`. Setup/Signing weiterhin nicht erzeugt, da kein unterstützter Installer-/Signing-Vertrag definiert ist.
OPEN: Master-Radarbild, echte Utility-/Eventtimeline, Score/Economy und Szenen-Thumbnails benötigen separat belegte Daten/Assets und wurden nicht simuliert. Die äußere native dunkle Windows-Titelleiste bleibt die einzige sichtbare Host-Konvention. Menschliche visuelle Produktabnahme und Mergeentscheidung bleiben Tristan vorbehalten.
NEXT: Tristan prüft ausschließlich den neu gepushten Portable-Build gegen die Masterbilder und meldet Abnahme oder konkrete screenbezogene Restabweichung. Bis dahin kein weiterer Product Slice und kein Merge nach `main`.
MODEL_PROFILE: terra
MODEL_REASON: Zusammenhängender visueller Desktop-Conformance-Pass mit responsiver Runtime-QA, vollständigem Gate und Packaging.
COMPUTER_USE: yes
COMMIT/PR: Dieser Handoff wird mit dem Visual-Conformance-Checkpoint auf `dev/v1-foundation` committed und gepusht; exakter HEAD im Abschlussbericht.

# Handoff 2026-08-21 — Direct Home master implementation

STATUS: WAITING_FOR_TRISTAN
TASK: Page 03 der verbindlichen Concept Preview als direkte Home-/Command-Center-Komposition umsetzen, statt nur deren Designprinzipien zu interpretieren.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `docs/design/UI_SPEC.md`, `docs/design/MOCKUP_INDEX.md`, `docs/AGENT_BASE.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`. Home enthält nun den Master-Header mit Begrüßung und vier echten Statuskarten, sechs Moduleinstiegskarten, die mittlere Dreiteilung Fortschritt/letzte Analyse/Schnellzugriff sowie die unteren Idee-/Community-Flächen. Bei Standardbreite bleibt die 6x1-Modulzeile; unter 1000 Pixel Inhaltsbreite reflowt sie auf 3x2. Home ist wie Analyzer vertikal scrollbar.
DATA_TRUTH: Statuskarten, Fortschritts-/Pipelinebereich und letzte Analyse konsumieren ausschließlich den bereits geöffneten realen Workflow (`map_id`, Parserstatus, Runden, Spieler, Szenen, Auswahlmodus, Reviewstatus, Quellname und Hashpräfix). Nicht implementierte Benchmark-/Community-Funktionen zeigen ehrliche inaktive beziehungsweise erklärende Zustände. Keine illustrativen Scores, Streaks, Datumswerte oder Analysehistorie erfunden.
MASTER_MATCH: Sidebar PASS; Header/Begrüßung PASS; obere Statuskarten PASS; sechs Moduleinstiege PASS; Fortschrittsübersicht PASS mit realem Pipelinezustand statt Fake-Score; letzte Analysen PASS mit genau dem belegten lokalen Workflow statt erfundener Historie; Schnellzugriff PASS; untere Informations-/Community-Struktur PASS. Direkte Desktop-Sichtprüfung bei 1360x860 und maximierter Breite zeigt die 6x1-Masterhierarchie; 1080x720 zeigt vollständigen 3x2-Reflow ohne horizontales Clipping und mit vertikal erreichbaren Folgeflächen.
SCOPE: Keine neue Funktion, Analyzerregel, Replay-/3D-/POV-, Optimizer-, Benchmark-, Clip- oder Videofunktion. Bestehende Navigation und Zielseiten werden nur als Home-Einstiege wiederverwendet. Logo-Variante 3 und Shell-Branding unverändert.
VERIFIED: Gezielte Analyzer-Shell-Tests 15/15 PASS. Vollständiger `pytest` 131/131 PASS; derselbe vollständige Lauf im finalen Build erneut 131/131 PASS; `compileall` und `git diff --check` PASS. Frische Portable-EXE mit dem vorhandenen echten Ancient-Workflow gestartet und Home praktisch geöffnet: 18 Runden, 10 Spieler, 54 Szenen, Parser PASS und Review bereit erscheinen aus der realen Workflow-Wahrheit; alle Masterblöcke sichtbar, keine Browseröffnung. EXE SHA-256 `F63E6D83F8618C302C592D4F8B4D224C9DA7F596C37DEF76DE464ACC49ED3E6A`; Portable-ZIP SHA-256 `F84D4D1ED7AFA1211FD0BD317791A2D930806763CA717E65717FB774DCE044CD`.
OPEN: My-Improvement-Langzeitmetriken, echte Analysehistorie, Benchmarkausführung und Community-Einreichung bleiben mangels aktuellem Produktumfang bewusst ohne erfundene Funktion. Nutzerabnahme bleibt Tristan vorbehalten.
NEXT: Tristan vergleicht den neuen Portable-Home-Screen direkt mit Seite 03 und meldet Abnahme oder eine konkrete verbleibende Home-Abweichung. Kein neuer Product Slice und kein Merge nach `main`.
MODEL_PROFILE: terra
MODEL_REASON: Direkter, responsiver Screen-Master-Abgleich innerhalb der bestehenden Desktop-Shell.
COMPUTER_USE: yes
COMMIT/PR: Dieser Handoff wird mit dem direkten Home-Master-Checkpoint auf `dev/v1-foundation` committed und gepusht; exakter HEAD im Abschlussbericht.

# Handoff 2026-08-21 — Home visual master correction pass

STATUS: WAITING_FOR_TRISTAN
TASK: Ausschließlich die noch nicht angenommene grafische Umsetzung des direkt strukturell akzeptierten Page-03-Home-Masters korrigieren; keinen neuen Product Slice starten und keine Home-Struktur neu entwerfen.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `docs/AGENT_BASE.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`. Home behält Header, vier reale Statuskarten, sechs Moduleinstiege, Fortschritt, letzte Analyse, Schnellzugriff und die unteren Informationsflächen in identischer Reihenfolge und Datenbindung. Es nutzt jetzt eine eigene Home-Komponentenfamilie: abgestufte Midnight-/Metallic-Panels, akzentcodierte feine Oberkanten, instrumentierte Modulicons, eine zurückhaltende technische Headerlinie, Flow-Anzeige sowie eigene moderne Button-Zustände. Die generischen flachen Tk-Karten bleiben auf Home nicht mehr sichtbar.
DATA_TRUTH: Keine Master-Beispielwerte übernommen. Status-, Pipeline-, letzte-Analyse- und Reviewwerte konsumieren weiterhin ausschließlich den aktuell geladenen lokalen Workflow; bei fehlender Demo bleiben die expliziten Nicht-verfügbar-Zustände sichtbar. Analyzer-, Replay-, NetCon-, System-Check- und Optimizer-Autorität sind unverändert.
MASTER_MATCH: Struktur Page 03 weiterhin PASS (bereits akzeptiert). Grafische Anpassung: Midnight-/Metallic-Gesamteindruck PASS; Panel-/Card-Hierarchie PASS; feine blaue bzw. modulbezogene Akzentlinien PASS; moderne Aktions- und Statusflächen PASS; technisches Linien-/Instrumentdetail PASS; Variant-3-Sidebar-Branding unverändert PASS. Der native dunkle Fensterrand bleibt bewusst die einzige Host-Konvention.
VERIFIED: `compileall` PASS; `git diff --check` PASS. Gezielte Analyzer-Shell-Tests 15/15 PASS. Vollständiger `pytest` 131/131 PASS, im frischen Build erneut 131/131 PASS; Abhängigkeitstest `pip check` PASS. Direkte Quell-Sichtprüfung und anschließende Sichtprüfung der frischen Portable-EXE bei 1360x860: Home zeigt die vollständige sechsmodulige Command-Center-Hierarchie, keine weißen/fremden Flächen und die neuen akzentuierten Panels/Controls. Die bestehende responsive 3x2-Reflow-Logik unter 1000 Pixeln wurde nicht verändert; sie bleibt über die vorhandenen Shell-Tests abgesichert. EXE SHA-256 `1D7A9921B9EC121ED6B25F08B2205414E2057E31C28A72706441DE8C5E32A17A`; Portable-ZIP SHA-256 `0D98DB956C1EF94630D54106E6268690459D3C08E685F5A0299736A038C2E5A7`.
BUILD: `dist/experimental/Improve Yourself Experimental/Improve Yourself Experimental.exe`, `dist/experimental/Improve-Yourself-Experimental-Portable.zip` und `dist/experimental/experimental-build.json` sind frisch erzeugt. Kein Setup/Installer und kein Signing, da hierfür weiterhin kein akzeptierter Vertrag vorliegt.
OPEN: Menschliche Page-03-Home-Abnahme durch Tristan. Nicht Teil dieses Passes: neue Funktionsflächen, neue Analyzer-/Rules-/Replay-/3D-/POV-/Optimizer-/Benchmark-/Clip-Funktionen, alternative Branding-Varianten oder ein Merge nach `main`.
NEXT: Tristan öffnet ausschließlich den frischen Portable-Build, vergleicht Home direkt mit Page 03 und meldet Abnahme oder eine konkrete verbleibende grafische Abweichung. Bis dahin keine weitere Produktarbeit.
MODEL_PROFILE: terra
MODEL_REASON: Eng begrenzter visueller Korrekturpass innerhalb der vorhandenen nativen Shell mit Paket-Runtime-QA.
COMPUTER_USE: yes
COMMIT/PR: Diesen Handoff mit dem Home-Visual-Checkpoint auf `dev/v1-foundation` committen und pushen; exakten HEAD anschließend berichten.

# Handoff 2026-08-21 — Home final typography and responsive correction pass

STATUS: WAITING_FOR_TRISTAN
TASK: Ausschließlich die verbleibenden Home-Abweichungen Typografie sowie Responsive-/Viewport-/Scroll-Verhalten korrigieren. Die bereits angenommene Struktur und Visual Direction bleiben unverändert; kein neuer Product Slice.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `src/improve_yourself/assets/fonts/Inter-Variable.ttf`, `src/improve_yourself/assets/fonts/Orbitron-Variable.ttf`, zugehörige `OFL`-Lizenzen, `packaging/improve-yourself-experimental.spec`, `docs/design/UI_SPEC.md`, `docs/AGENT_BASE.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`, `tests/test_analyzer_shell.py`.
TYPOGRAPHY: Gemeinsame Theme-Grundlage setzt Inter für normale UI-/Leseschrift ein. Orbitron wird ausschließlich für Home-Displaytitel, Modulnamen und bewusst wenige technische Labels verwendet; Buttons, Navigation, Status, Beschreibungen und Werte bleiben Inter. Beide offiziellen OFL-Fonts liegen im Paket und werden unter Windows via `AddFontResourceExW(..., FR_PRIVATE, ...)` nur im Prozess registriert. Es gibt keine globale Installation oder Runtime-Netzwerkabhängigkeit.
RESPONSIVE_LAYOUT: Die Ursache der bisherigen unnötigen vertikalen Scrollbar war der stets erzeugte und gepackte `ttk.Scrollbar` für den Dashboard-Canvas. Sie ist jetzt bedarfsabhängig: Nur wenn die echte Canvas-Scrollregion höher als der Canvas-Viewport ist, wird sie gezeigt; ansonsten bleibt der Inhalt oben bei `y=0`. Home-Zeilen erhalten begrenzte, viewportabhängige Grid-Mindesthöhen und Abstände über `dashboard_layout_metrics`, statt globale Schrift-/Icon-/Button-Skalierung. Breite unter 1000 Content-Pixeln nutzt weiterhin den akzeptierten 3x2-Modulreflow; große Breiten bleiben 6x1.
CAUSES: Die oberhalb beobachtete Leerfläche war keine Daten-/Funktionsfläche, sondern die Verbindung aus persistentem Canvas-Scrollcontainer und nicht an die verfügbare Höhe gebundener natürlicher Frame-Höhe. Das Layout synchronisiert nun Scrollregion, Canvasbreite und tatsächliche Overflow-Sichtbarkeit nach Configure-Ereignissen; Home wird beim Seitenwechsel wieder auf den Ursprung gesetzt.
VERIFIED: Zusätzlicher Responsive-Unit-Test ergänzt. Gezielte Shell-Tests 16/16 PASS; vollständiger `pytest` 132/132 PASS und im Build erneut 132/132 PASS. `compileall`, `pip check` und `git diff --check` PASS. Praktisch geprüft: (A) maximiertes Quellfenster — Home startet oben, verteilt die vorhandene Höhe, kein Home-Scrollbar; (B) normales großes Quellfenster 1360x860 — alle Page-03-Blöcke auf einer Ansicht, kein Home-Scrollbar; (C/D) echte Quell-Shell auf exakt 1080x720 — Module reflowen sichtbar 3x2, Scrollbar erscheint erst wegen echten Overflows; der Scrolltest erreicht Fortschritt, letzte Analyse, Schnellzugriff und beide unteren Bereiche ohne Clipping oder Überlagerung. Frische Portable-EXE geöffnet: Fonts werden sichtbar gerendert, Home bleibt scrollbar-frei solange der Inhalt passt, Navigation zu Home funktioniert. Die verpackte `_internal/improve_yourself/assets/fonts/`-Struktur enthält Inter, Orbitron und beide OFL-Dateien. EXE SHA-256 `6BAD23E1914A96360E527E6335479C1B5F83994542A00D6BF48B98F47BCEF891`; Portable-ZIP SHA-256 `969D9B2A152A31AE0379DC3D7C7C04AAFD6C19223695C4D46BAA78C9C45CFAD0`.
BUILD: Frisch erzeugt: `dist/experimental/Improve Yourself Experimental/Improve Yourself Experimental.exe`, `dist/experimental/Improve-Yourself-Experimental-Portable.zip`, `dist/experimental/experimental-build.json`. Installer/Signing bleiben bewusst aus, weil hierfür kein freigegebener Vertrag existiert.
OPEN: Ausschließlich menschliche Home-Abnahme durch Tristan. Keine bekannte funktionale Regression; keine weiteren Produktfunktionen, Layout-Neuerfindung, Analyzer-/Rules-/Replay-/3D-/POV-/Optimizer-/Benchmark-/Clip-Arbeit oder Merge nach `main` Teil dieses Passes.
NEXT: Tristan öffnet den frischen Portable-Build und prüft Home bei großem/maximiertem sowie kleinerem Fenster gegen Page 03. Bis zu Abnahme oder einer konkret belegten Restabweichung keine weitere Produktarbeit.
MODEL_PROFILE: terra
MODEL_REASON: Eng abgegrenzter nativer Desktop-Theme-/Viewport-Pass mit Runtime- und Paketprüfung.
COMPUTER_USE: yes
COMMIT/PR: Diesen Handoff mit dem finalen Home-Korrekturcheckpoint auf `dev/v1-foundation` committen und pushen; exakten HEAD anschließend berichten.

# Handoff 2026-08-21 — Home module action alignment correction

STATUS: WAITING_FOR_TRISTAN
TASK: Ausschließlich die gemeinsame vertikale Ausrichtung der sechs oberen Home-Modulaktionen korrigieren, ohne die angenommene Page-03-Struktur, Typografie, Datenbindung oder sonstige Home-Visuals zu verändern.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `docs/AGENT_BASE.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`.
IMPLEMENTATION: Alle Modul-Cards verwenden nun denselben fünfzeiligen Grid-Aufbau: Akzentkante, Icon/Titel, Beschreibung, flexibler Spacer und Action. Die Card-Grid-Zeile des Spacers trägt das verbleibende Höhenwachstum; die Action liegt stets in der gemeinsamen letzten Zeile. Dadurch können Beschreibungen unterschiedlich lang bleiben, ohne die Button-Höhe zu verändern. Es gibt keine individuellen Offsets oder Card-Sonderregeln.
SCOPE: Keine sonstige Home-Struktur oder -Typografie geändert. Keine Analyzer-, Review-, Tactical-, Rules-, Optimizer-, Benchmark-, 3D/POV-, Clip- oder Videofunktion begonnen. Kein Merge nach `main`.
VERIFIED: `compileall` PASS; `git diff --check` PASS; gezielte Analyzer-Shell-Tests 16/16 PASS; vollständiger `pytest` 132/132 PASS. Direkte Quell-Sichtprüfung: (A) breite 6x1-Modulzeile mit allen sechs Actions auf derselben Grundlinie; (B) 1080x720 mit responsivem 3x2-Reflow und je Reihe weiterhin gleicher Action-Grundlinie. Bestehende große/kleine Card-Breiten und volle Buttonbreite bleiben erhalten.
BUILD: Frisch erzeugt und praktisch geöffnet: `dist/experimental/Improve Yourself Experimental/Improve Yourself Experimental.exe`, `dist/experimental/Improve-Yourself-Experimental-Portable.zip`, `dist/experimental/experimental-build.json`. Die Portable zeigt den Alignment-Fix selbst im normalen 6x1-Home. EXE SHA-256 `A8141463760CBB74C1CDE0C17BF16C8449F47F2C812577F4F5BB737BCAED3ED7`; Portable-ZIP SHA-256 `483AA6C91699679192375D1ACE5CAE145FA671209B0001F4B958A8194AA0062A`. Kein Installer/Signing, weil kein freigegebener Vertrag vorliegt.
OPEN: Ausschließlich menschliche Home-Endabnahme durch Tristan.
NEXT: Tristan prüft die frische Portable ausschließlich auf gleich hohe Modul-Cards, ausgerichtete Actions und den bekannten Responsive-Reflow; anschließend Abnahme oder konkrete Restabweichung. Bis dahin keine weitere Produktarbeit.
MODEL_PROFILE: terra
MODEL_REASON: Eng begrenzter, bereits spezifizierter Desktop-Layout-Korrekturpass mit Runtime- und Paketprüfung.
COMPUTER_USE: yes
COMMIT/PR: Dieser Handoff ist Teil des gepushten `dev/v1-foundation`-Checkpoints; exakter HEAD steht im Abschlussbericht.

# Handoff 2026-08-22 — Active System Check Contract Alignment Pass

STATUS: DONE — WAITING_FOR_TRISTAN
TASK: Den aktiven read-only System Check mit dem bereits versionierten zwölf-Check-Pack-01-Vertrag abgleichen, alle bestehenden Projektionen konsistent machen und den Real-System-Evidence-Pass wiederholen. Keine Regel-, Hardware-, Apply-/Write-, Registry-, BIOS-, Treiber-, Network- oder Benchmark-Erweiterung.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/system_check.py`, `tests/test_system_check.py`, `src/improve_yourself/optimizer_evidence.py`, `src/improve_yourself/analyzer_shell.py`, `tests/test_optimizer_evidence.py`, `tests/test_analyzer_shell.py`, `docs/ACTIVE_SYSTEM_CHECK_CONTRACT_ALIGNMENT.md`, `coordination/agents/codex.md`.
CAUSE / FIX: Der aktive Branch enthielt eine ältere Acht-Check-Projektion. Ausschließlich die bereits versionierte read-only Collector-/Test-Implementierung aus `origin/main@2cd358c` wurde übernommen; keine unverbundenen Main-Änderungen wurden gemergt. Der aktive Output enthält jetzt 12/12 Pack-01-Basen: `windows`, `cpu`, `memory`, `motherboard`, `gpu`, `gpu_driver`, `chipset_driver`, `graphics_settings_profile`, `display`, `monitor`, `secure_boot`, `tpm`.
PROJECTION: Home und Optimizer konsumieren die aktuelle Vertragsform `display.active_displays` und die separat erhobene `monitor.monitors`-Evidenz. Der frühere `refresh_rates_hz`-Pfad bleibt ausschließlich für bereits gespeicherte v1-Scans lesekompatibel. Es wird kein Monitor, Treiber-, CS2- oder Setting-Zustand erschlossen. Unknown, Conditional und Insufficient Evidence bleiben fail-closed.
REAL EVIDENCE: Wiederholung auf dem einzigen derzeit lokal verfügbaren expliziten Tester, ohne Rohprofil- oder Pfadspeicherung. Gültiges `iy.system_check/v1`, policy `read_only: true`, `changes_applied: false`; 12 Check-Basen, Status 10 OK / 1 REVIEW / 1 ACTION_REQUIRED. Pack 01: 11 NO_CHANGE / 1 CONDITIONAL / 0 positive Recommendations, `apply_available: false`. Kein Registry-, BIOS-, Treiber-, Netzwerk- oder Benchmark-Write. Kein weiterer realer Tester war im aktuellen Arbeitsbereich verfügbar; er wurde nicht als getestet behauptet.
VERIFIED: Vertrags-/System-Check-/Pack-/Shell-Teilmenge **42/42 PASS**; vollständiger `pytest` **182/182 PASS**; `compileall` PASS; `git diff --check` PASS. Vollständiger Portable-Build bis zum frischen Manifest PASS, einschließlich `pip check`, PyInstaller und Portable-ZIP. EXE SHA-256 `C26A29FB39E47D3E2A5D674C4108DB8EBECD8F6CEF5105AB4282A8F2E7721896` (19,845,032 Bytes); ZIP SHA-256 `619FF0B01CE737B177733318F22926739BC740AF933AA76C2856BCCA44D3D5CF` (168,833,907 Bytes); beide stimmen mit dem Manifest überein. Pack 01 ist im Portable-Laufzeitpfad vorhanden.
EVIDENCE LIMITS: Die vorhandenen drei exakten Herstellerquellen bleiben absichtlich eng und live, nicht release-fixiert. Fehlende Monitor-/Security-/Treiber-/Chipset-Evidenz bleibt sachlich Unknown, Conditional oder Insufficient; ein lokaler Tester ist kein Hardware-Golden-Master und keine Performance-Aussage.
NEXT: Genau ein zulässiger Folgeblock nach Freigabe: denselben read-only Evidence Pass auf weiteren explizit bereitgestellten Testsystemen wiederholen und Unknown/Conditional/Exclusion klassifizieren. Keine Hardware-Unterstützung oder Regel ohne neuen fachlichen Auftrag verbreitern.
MODEL_PROFILE: terra
MODEL_REASON: Enger Vertrag-/Evidenzabgleich mit fail-closed Sicherheitsgrenze und realer Read-only-Gegenprobe.
COMPUTER_USE: no
COMMIT/PR: `19bb881 fix: align active system check contract` plus `e0eeceb docs: record active contract alignment handoff`; gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — UI Target Alignment & Consolidation Pass V1.1

STATUS: DONE — WAITING_FOR_TRISTAN
TASK: Die funktionale Experimental-Shell anhand der verbindlichen UI-Zielentscheidungen konsolidieren; CURRENT → TARGET → GAP → IMPLEMENTATION dokumentieren und ausschließlich bestehende Funktionen/Evidenzgrenzen erhalten.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `tests/test_analyzer_shell.py`, `docs/UI_TARGET_ALIGNMENT_V1_1.md`, `coordination/agents/codex.md`.
CURRENT VS TARGET: Der vollständige kompakte Abgleich für Dashboard, Sidebar, Analyzer, Embedded Review, Optimizer-Hauptseite, vier Optimizer-Domains, System Optimizer, Statussemantik, Tactical Replay und gemeinsame Shell steht in `docs/UI_TARGET_ALIGNMENT_V1_1.md`. Der aktuelle Branch bleibt funktionale Wahrheit; PDF/UI_SPEC/BRANDING/MOCKUP_INDEX bleiben visuelle Wahrheit. Keine Mockup-Beispielwerte/Funktionen wurden übernommen.
IMPLEMENTATION: Optimizer ist wieder als erkennbare Hauptübersicht sichtbar: System, Graphics, Network und BIOS Optimizer. System Check ist korrekt als `1 · SYSTEM CHECK — LOKALE FAKTEN` innerhalb des System Optimizer abgegrenzt; `2 · OPTIMIZER ASSESSMENT — EINORDNUNG` folgt erst nach Fakten. Ohne vorhandene Domain-Fakten bleiben Graphics/Network/BIOS ehrlich Preview. Das System-Check-/Optimizer-Page ist bei kleinerer Höhe scrollbar, ohne die Datenlogik umzubauen.
ANALYZER FIX: `analysis_profile_criteria_view()` ist der stabile semantische Hook für den Profilblock; keine positionsabhängige Zuordnung. Es zeigt den tatsächlichen bestehenden Regelumfang (`review_v1` 7/7; `highlight_v1` 5/7), statt für eine geforderte Optik Regeln zu erfinden oder zu reduzieren. Die Badge wird beim Start, beim Profilwechsel und bei Custom-Änderungen aktualisiert.
STATUS / REPLAY: Bestehende Status werden nur lesbar übersetzt (`READY / OK`, `EVIDENCE / NO CHANGE`, `CONDITIONAL`, `UNKNOWN / NOT AVAILABLE`, `WARNING / ACTION REQUIRED`); die Bewertung selbst bleibt unverändert und fail-closed. Tactical Replay startet mit einem echten dreistufigen Empty State (Analyse → Review-Szene → Tactical), zeigt Runtime-Controls erst nach Übergabe einer validierten Szene und baut keine zweite Replay-Wahrheit.
VISUAL REVIEW: Live in der laufenden Shell geprüft: Dashboard, Analyzer, Optimizer und Tactical Replay. Sichtbar bestätigt: persistente dunkle Sidebar mit Variant-3-Branding, keine weiße Fremdfläche, Page-03-Dashboardstruktur erhalten, Kriterienbadge im Profilblock, vier Optimizer-Kacheln, Fakten-vor-Bewertung-Hierarchie, klarer No-Apply-Hinweis und Tactical-Empty-State. Home wurde ausdrücklich nicht neu umgebaut; sein globaler Final-Polish bleibt getrennt/deferred.
VERIFIED: Gezielte Shell-/System-Check-/Pack-Tests **37/37 PASS**; vollständiger `pytest` **185/185 PASS**; `compileall` PASS; `git diff --check` PASS. Vollständiger Portable-Build bis zum frischen Manifest PASS, einschließlich `pip check`, PyInstaller und Portable-ZIP. EXE SHA-256 `8BBC007E92AD3957FBDC453593B97A9875479903151A9B08FD7A3952F2AA4153`; ZIP SHA-256 `8FE78AE16C3215D03C874B5DB7F692B9C3592617411AFABEC97DA14180A2E0E3`; beide stimmen mit dem Manifest überein. Matrix Pack 01 ist im Portable-Laufzeitpfad enthalten.
BOUNDARIES: Keine neuen Optimizer-Regeln/Hardware-Mappings, keine Apply-/Write-/Registry-/BIOS-/Treiber-/Netzwerkänderung, keine Benchmark-Arbeit, kein Framework-Wechsel, keine neue Review-Engine. Graphics/Network/BIOS werden nicht als funktionsfähig vorgetäuscht; die dargestellten Fakten kommen nur aus der bestehenden read-only Pipeline.
NEXT: Tristan prüft den frischen Portable-Build gegen die dokumentierte Zielstruktur, besonders Optimizer-Übersicht, Analyzer-Kriterienbadge, Statusverständlichkeit und Tactical-Empty-State. Keine weitere UI- oder Produktarbeit ohne neuen Auftrag.
MODEL_PROFILE: terra
MODEL_REASON: Zusammenhängender UI-/Informationsarchitektur-Pass mit funktionaler Regression und sichtbarer Desktop-Prüfung.
COMPUTER_USE: yes
COMMIT/PR: `5d13891 feat: align experimental UI to target structure`; finaler Branch-HEAD wird im Abschlussbericht nach dem Push bestätigt.

# Handoff 2026-08-21 — Improve Yourself UI completion pass

STATUS: WAITING_FOR_TRISTAN
TASK: Den akzeptierten Home-Dark-V1-Kandidaten unverändert lassen und ausschließlich die bestehende native Shell über die gemeinsamen Dark-V1-Controls auf die vorhandenen Kernrouten übertragen. Kein neuer Product Slice, keine neue Engine und keine Produktlogik.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `docs/AGENT_BASE.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`.
UI WORK: Der gemeinsame Card-, Formular-, Button-, Check-, Slider-, Status-Badge- und Seitenüberschrifts-Layer verwendet Dark V1: App `#020A12`, Sidebar `#03101C`, Panel `#071725`, raised/Card `#0A1C2D`, Hover `#0D2236`, dezente Borders (`#0A2132`/`#071A27`), Akzente `#0B79C9`/`#13A7E8` und Text `#E4E8ED`/`#A0ABB8`/`#687789`. Display-Überschriften und Abschnittskicker nutzen die bereits paketierte Display-Schrift; Lesetext bleibt Inter. Dadurch wirken vorhandene Routen wie eine Anwendung, ohne ihren Ablauf oder ihre Datenautorität zu verändern.
HOME STATUS: `HOME DARK V1 – READY FOR FINAL VISUAL ACCEPTANCE`. Home wurde nicht strukturell geändert: sechs Modul-Cards, die Action-Grundlinie, responsive Geometrie, Sidebar, untere Bereiche sowie die feste Reihenfolge **Letzter Systemscan → Dein Fortschritt – Überblick → Letzte Analysen** bleiben erhalten. Dieser Status bedeutet nicht `ACCEPTED`; nur Tristan kann die finale visuelle Home-Abnahme erteilen.
CORE SCREEN COVERAGE:
| Bestehender Screen | Dark-V1-Abgleich | Praktische Prüfung | Restabweichung |
| --- | --- | --- | --- |
| Home / Dashboard | vollständige bestehende Master-Implementierung bleibt aktiv | Quelle auf 1362×892 geöffnet | finale menschliche Abnahme gegen Page 03 offen |
| Analyzer / Review | PageTitle, Status-Badge sowie gemeinsame Cards/Buttons/Formulare | zuvor auf Quelle geöffnet; aktuelle Demo- und Analysefunktionen unverändert | Embedded-Detailansicht braucht für einen visuellen Datentest eine reale geladene Analyse; kein zweiter Review-Pfad angelegt |
| Tactical Replay | PageTitle, gemeinsame Karten, Status-Badge, Timeline-/Control-Flächen | Quelle auf 1362×892 geöffnet | ohne aktive Review-Szene korrekt neutraler Zustand; Datenszene nicht künstlich erzeugt |
| System Check / Optimizer | PageTitle, dunkle Card-/Button-/Lesetext-Hierarchie | Quelle auf 1362×892 geöffnet | nur bestehender read-only System Check; keine Optimizer-Autorität ergänzt |
| Rules / Reports / Settings | PageTitle, Display-Abschnittskicker und gemeinsame Controls | über gemeinsame Shell-Styles abgedeckt | keine separaten Masterbilder vorhanden; daher Dark-V1-Konsistenz statt freier Neugestaltung |
SCOPE: Parser, Demoimport, Rule Engine, Szenen, eingebetteter Review, Tactical-Replay-Truth, CS2/NetCon, System Check, Optimizer, Datenbindung, Routenfolge und Branding Variant 3 wurden nicht verändert. Es gibt keine neue Remote-Schnittstelle, keine erfundenen Analyse-/Fortschrittswerte und keinen neuen Screen.
VERIFIED: Gezielte Analyzer-Shell-Tests **18/18 PASS**; vollständiger `pytest` **134/134 PASS**; `compileall` PASS; `git diff --check` PASS. Der kontrollierte Build-Gate wiederholte `pytest` **134/134 PASS** und `pip check` PASS. Quellen-Sichtprüfung bestätigte Home, Tactical Replay und System Check jeweils auf 1362×892 mit gemeinsamer Midnight-/Metallic-Oberfläche. Die frische Portable wurde praktisch auf Analyzer und anschließend Home geöffnet; Navigation, aktive Route, Variant-3-Wortmarke sowie die neutralen leeren Datenzustände arbeiten ohne Regression. Eine aktive Embedded-Review-Szene wurde nicht künstlich erzeugt.
BUILD: Frisch bereit unter `dist/experimental/Improve Yourself Experimental/Improve Yourself Experimental.exe`, `dist/experimental/Improve-Yourself-Experimental-Portable.zip` und `dist/experimental/experimental-build.json`. EXE SHA-256 `6A23599B16949CC332A66BD1EBCFC78168375E9E95B8FC51EC2E6F3F4230F4CC` (19,788,451 Bytes); Portable-ZIP SHA-256 `A82D305B8E874BBCBBC71C9BEDACEC096026FB5E348FEAC59708032EA099B6C7` (168,771,697 Bytes). Der offizielle Build-Gate erzeugte die EXE und schloss seinen eigenen Archive-/Manifest-Schritt anschließend regulär ab. Paketprüfung bestätigt Inter, Orbitron und die Variant-3-Wortmarke in den erwarteten mitgelieferten Asset-Pfaden.
WORKTREE: Vor dem Abschluss nur die vier oben genannten versionierten Dateien; Test- und Paketartefakte bleiben ignoriert.
OPEN: 1. Tristans finaler visueller Home-Vergleich gegen Page 03. 2. Optionaler Echt-Daten-Sichttest des eingebetteten Review, sobald Tristan eine vorhandene Demo/Analyse im frischen Build öffnet; keinerlei Fake-Szene zur Demonstration verwenden.
NEXT: Tristan prüft die neue Portable auf Home und die Dark-V1-Konsistenz der vorhandenen Kernrouten. Bis zu dessen Entscheidung keine weitere Produktarbeit, kein neuer Slice und kein Merge nach `main`.
MODEL_PROFILE: terra
MODEL_REASON: Begrenzter bestehender Desktop-UI-Completion-Pass mit gemeinsamer Komponentenbasis und Runtime-/Paket-QA.
COMPUTER_USE: yes
COMMIT/PR: Dieser versionierte Handoff gehört zum Checkpoint `ui: extend dark v1 styling across core screens`; der exakte finale HEAD wird nach dem Push im Abschlussbericht ausgewiesen.

# Handoff 2026-08-21 — Home final visual pass / last run

STATUS: WAITING_FOR_TRISTAN
TASK: Ausschließlich die bereits angenommene Home-Oberfläche ein letztes Mal an das kanonische Home-Master-Farbgewicht und die Modulbutton-Formsprache angleichen. Keine Informationsarchitektur, Reihenfolge, Funktionen, Datenanbindung, Typografie, responsive Geometrie oder Sidebar-Grundstruktur ändern.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `docs/AGENT_BASE.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`.
IMPLEMENTATION: Große Home-Status- und Modulkarten verwenden die bereits verbindliche dunkle Panelstufe `#071725` statt der helleren raised-Stufe. Für ausschließlich die sechs oberen Module ersetzt `RoundedHomeAction` die kantigen, vollfarbigen nativen Buttons: eine gemeinsame 37px-Action mit 7px-Radius, dunkler Innenfläche `#0A1C2D`, feiner jeweiliger Modul-Kontur, zurückhaltendem Hover, gleicher Grid-Zeile, gleicher Breite und unverändertem Command-/Disabled-/Tastaturverhalten. Modulfarben bleiben nur Akzent, nicht Button- oder Card-Grundfläche. Keine andere Home-Action und keine andere Produktseite wurde im Rahmen dieses Auftrags neu gestaltet.
HOME STATUS: `HOME VISUAL TEMPLATE LOCKED – READY FOR FINAL VISUAL ACCEPTANCE`. Der Lock bedeutet: Die aktuelle Home-Implementierung ist der kanonische Template-Stand für diesen freigegebenen Master, bis Tristan eine konkrete neue Abweichung oder einen neuen UI-Auftrag gibt. Er bedeutet weder einen Merge nach `main` noch eine implizite flächige Übertragung der Home-Komponenten auf weitere Seiten.
VISUAL CHECK: Quell-Shell auf 1362×892 geöffnet. App-Hintergrund bleibt nahezu schwarz; große Module und mittlere/untere Panels heben sich nur über dunkle Navy-Stufen ab. Alle sechs oberen Actions stehen auf einer Linie und sind erkennbar abgerundet, dunkel und fein nach ihrer Modulfarbe konturiert. Direkter Klick auf `Übersicht öffnen` navigierte unverändert nach Reports; keine Daten oder Analyse wurde erzeugt. Der kompakte Responsive-Grid-/Action-Mechanismus blieb unverändert, weil nur die Action-Chrome innerhalb derselben Grid-Zeile ersetzt wurde.
VERIFIED: Gezielte Analyzer-Shell-Tests **18/18 PASS**; `compileall` PASS; vollständiger `pytest` **134/134 PASS** im Wiederholungslauf; `git diff --check` PASS. Der erste vollständige Lauf brach einmalig im bestehenden Loopback-Origin-Test mit Windows `WinError 10053` ab, bevor eine erwartete HTTP-Antwort gelesen wurde; derselbe unveränderte Lauf war unmittelbar danach vollständig grün, daher kein reproduzierbarer UI-/Produktfehler. Der offizielle Build-Gate wiederholte `pytest` **134/134 PASS** und `pip check` PASS. Frische Portable auf Analyzer und Home geöffnet; Home zeigt die dunklen Card-Flächen und sechs abgerundete Modulactions wie geprüft.
BUILD: Frisch bereit: `dist/experimental/Improve Yourself Experimental/Improve Yourself Experimental.exe`, `dist/experimental/Improve-Yourself-Experimental-Portable.zip`, `dist/experimental/experimental-build.json`. EXE SHA-256 `43CC5CDF15FAF2C5A6862E451D3BD525CB98D5EAE4E18DB1DEF21F876DFCBCB7` (19,790,195 Bytes); Portable-ZIP SHA-256 `F60E32E02BE961360A9BC1F5313EDE2DC82EB2B3410CFD2DAB7A62C75BBB8A8D` (172,978,916 Bytes). Der PyInstaller-Lauf erzeugte die EXE korrekt; weil der lokale Wrapper in dieser Umgebung seinen letzten Archivschritt nicht abwartbar zurückgab, wurde der unveränderte vorhandene Kopier-/ZIP-/Manifest-Schritt danach mit der frischen EXE ausgeführt, nachdem die offene Portable geschlossen war.
WORKTREE: Vor Abschluss die vier genannten versionierten Dateien; Test-/Build-Ergebnisse bleiben ignoriert.
OPEN: Ausschließlich Tristans finaler visueller Vergleich von Home mit dem kanonischen Master. Keine weitere UI-Arbeit ohne neuen Auftrag.
NEXT: Tristan prüft den frischen Portable-Build direkt auf Gesamtdunkelheit der Card-Flächen und die sechs subtilen abgerundeten Modulbuttons. Bei Zustimmung Home-Abnahme dokumentieren; andernfalls nur eine konkrete, begrenzte visuelle Abweichung benennen.
MODEL_PROFILE: terra
MODEL_REASON: Letzter eng begrenzter Home-Surface-/Action-Chrome-Pass ohne Produktfunktionsausweitung.
COMPUTER_USE: yes
COMMIT/PR: Wird nach dem finalen Commit-/Push-Checkpoint ergänzt.

# Handoff 2026-08-21 — Product decision: Home accepted / System Check next

STATUS: IN_PROGRESS
TASK: Die Produktentscheidung dokumentieren und den autorisierten nächsten Funktionsstrang System Check / Optimizer zunächst gegen den vorhandenen realen read-only Ergebnisfluss abgleichen.
DECISION: **HOME STATUS: FUNCTIONALLY ACCEPTED / VISUAL FINALIZATION DEFERRED.** Home wird nicht als visuell final abgenommen. Navigation, Modulaufteilung, Systemscan-Projektion, Fortschritt, letzte Analysen und Informationsbereiche bleiben die akzeptierte funktionale Basis. Keine weitere isolierte Home-Korrektur und keine ungeprüfte globale Vererbung des aktuellen Stils. Ein späterer bewusst freigegebener Final-Polish entscheidet erst über globale Surface-, Card-, Button-, Border-, Radius- und Akzent-Tokens.
NEXT SCOPE: System Check / Optimizer, ausschließlich read-only: vorhandenes `iy.system_check/v1` mit echten lokalen Ergebnissen erfassen, bestehende Ergebnisdarstellung auf Fakten/Bewertung/Hinweise/Unbekannt prüfen und nur nach diesem Abgleich eine eng begrenzte Ergebnisdarstellung ergänzen. Keine Firmware-, Treiber-, Registry-, Windows- oder sonstige Systemänderung; kein neuer Analyzer-/Replay-/Benchmark-/UI-Polish-Slice.
INITIAL INVENTORY: `system_check.py` erfasst bereits Windows, CPU, RAM, Mainboard/BIOS, GPU/Treiber, Anzeige, Secure Boot und TPM read-only; die aktuelle Desktop-Route zeigt bislang primär Ausführen-Action plus kompakten Status, während Home sechs Datenpunkte projiziert. Reale Erfassung und Sichtprüfung stehen als nächster Schritt an.
BRANCH: `dev/v1-foundation`
CHANGED: `docs/AGENT_BASE.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`.
VERIFIED: Dokumentationsabgleich erfolgt; Quellinventar ohne Funktionsänderung gelesen. Reale System-Check-Ausführung folgt.
OPEN: Ergebnisdarstellung der bestehenden System-Check-Route ist noch nicht anhand eines frisch erfassten lokalen `iy.system_check/v1`-Datensatzes verifiziert.
NEXT: Read-only System Check real ausführen, Schema und sichtbare Route gegen dieselben Ergebnisse prüfen; erst dann über die kleinste notwendige Ergebnisdarstellung entscheiden.

# Handoff 2026-08-21 — System Check real result presentation

STATUS: WAITING_FOR_TRISTAN
TASK: Den bestehenden System Check / Optimizer anhand echter lokaler read-only Evidenz fertig prüfen und die minimal notwendige Ergebnisdarstellung innerhalb der vorhandenen Route ergänzen.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `tests/test_analyzer_shell.py`, `docs/AGENT_BASE.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`.
IMPLEMENTATION: `system_check_result_view()` konsumiert ausschließlich ein vorhandenes `iy.system_check/v1`-Payload und trennt Datum, gespeicherte Zählung, Ausführungsrichtlinie, Check-Status, Zusammenfassung und Evidenz. Es bewertet nicht neu und leitet aus unbekannten Werten keine Maßnahmen ab. Die bestehende System-Check-Route zeigt nach Laden oder Run acht echte Checks in einem responsiven 4×2-Raster; jedes Element enthält Label, Status, Aussage und `Evidenz:`. Die View erscheint nur für ein bestätigtes Schema. `UI_REFERENCE_STATUS` für System Check / Optimizer ist deshalb `IMPLEMENTED`; das bedeutet Ergebnisdarstellung, nicht eine Optimizer-Autorität.
REAL RESULT: Read-only-Probe und anschließender UI-Run auf diesem Rechner: **6 OK · 2 REVIEW · 0 ACTION_REQUIRED**. Windows, CPU, RAM, Mainboard/BIOS, GPU/Treiber und Anzeige wurden als Evidenz angezeigt. Secure Boot und TPM blieben `REVIEW` mit `enabled: nicht sicher ermittelt`; keine Behauptung „aus“, keine Empfehlung und keine Änderung. Das Payload bestätigt `read_only: true`, `changes_applied: false`, `elevation_requested: false`.
VISUAL / RUNTIME CHECK: Quelle auf 1362×892 mit gespeichertem echten Datensatz und nach anschließendem echten Button-Run geöffnet. Ursprünglich war das 2×4-Resultatraster in dieser Höhe zu lang; das ausschließlich darstellungsseitig verdichtete 4×2-Raster zeigt alle acht Checks gleichzeitig. Der echte Lauf aktualisierte Zeitstempel und Zusammenfassung. Home wurde nicht verändert.
VERIFIED: Gezielte System-Check-/Shell-Tests **22/22 PASS**; vollständiger `pytest` **135/135 PASS**; `compileall` PASS; `git diff --check` PASS. Build-Gate: `pytest` **135/135 PASS**, `pip check` PASS. Neue Testdeckung sichert Schema-Validierung, Read-only-Richtlinie, Evidenzformatierung und die Darstellung eines unbekannten Sicherheitswertes.
BUILD: Frisch bereit: `dist/experimental/Improve Yourself Experimental/Improve Yourself Experimental.exe`, `dist/experimental/Improve-Yourself-Experimental-Portable.zip`, `dist/experimental/experimental-build.json`. EXE SHA-256 `17D060548F8E38AC1AF14866383E0E8BB0F1EFAB9C638B1D6A486147F0A649B1` (19,793,433 Bytes); Portable-ZIP SHA-256 `01B7A573DFAF9D3E8F0661B2CFB3BDC9448411AA218EFCE9121CA673785A1D8E` (172,982,237 Bytes). Der Build-Gate erzeugte die EXE; in dieser Desktop-Umgebung wurde der unveränderte Archiv-/Manifest-Schritt danach mit der frischen EXE abgeschlossen, nachdem die offene Portable geschlossen war.
HOME DECISION: **FUNCTIONALLY ACCEPTED / VISUAL FINALIZATION DEFERRED.** Keine weitere isolierte Home-Korrektur und keine ungeprüfte Übertragung des aktuellen Stils.
OPEN: Der Name Optimizer bleibt als bestehender Navigationstext; es gibt bewusst keine Optimizer-Empfehlung oder Ausführungsfunktion, weil keine reale sichere Aktion autorisiert ist. Eine spätere Erweiterung braucht einen getrennten Produktauftrag samt Safety-/Evidenz-Kriterien.
NEXT: Tristan legt den nächsten begrenzten Produktbereich fest. Bis dahin kein neuer UI-Polish, keine Optimizer-Automatik, keine Systemänderung und kein Merge nach `main`.
MODEL_PROFILE: terra
MODEL_REASON: Read-only System-Evidence-Slice mit realem Desktop- und Paketnachweis.
COMPUTER_USE: yes
COMMIT/PR: Wird nach dem Abschlusscommit/-push ergänzt.

# Handoff 2026-08-21 — Optimizer Evidence Matrix + Synthetic System Validation

STATUS: REVIEW
TASK: Eine nachvollziehbare, lokale und ausschließlich read-only Optimizer-Evidenzschicht über dem bestehenden System Check etablieren. Keine Tweaks, keine automatische Konfigurationsänderung, kein Benchmark-Map-Arbeitspaket und keine künstlichen Messwerte.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/optimizer_evidence.py`, `src/improve_yourself/analyzer_shell.py`, `tests/test_optimizer_evidence.py`, `tests/test_analyzer_shell.py`, `pyproject.toml`, `docs/OPTIMIZER_EVIDENCE_MATRIX_V1.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`.
IMPLEMENTATION: Die neue deklarative Matrix `iy.optimizer_evidence_matrix/v1` trägt pro Regel ID, Name, Kategorie, aktuelle/angestrebte Zustandsreferenz, Support-/Ausschlussbedingungen, erwartete Wirkung, Nebenwirkungen, Reversibilität, Backup-/Restore-Anforderung, Evidenzklasse, Confidence, Quellenbegründung, Messmetriken und Validierungsstatus. Die Klassen **VERIFIED_STABLE**, **CONDITIONAL** und **EXPERIMENTAL** sind getrennt. Der Matcher nutzt ausschließlich bestätigte `iy.system_check/v1`-Werte; CS2-, Driver-Option-, Gaming- und Limitation-Fakten werden nicht erfunden, sondern als fehlend ausgewiesen. Die bestehende System-Check-/Optimizer-Route zeigt nach einem gültigen Scan die verständliche Evidence-Matrix mit Systembasis, Kandidatenklasse, Wirkung, Risiko, Rücknahme und fehlenden Eingaben. Es gibt keinen Apply-Button und keinen Schreibpfad.
SYNTHETIC VALIDATION: `iy.optimizer_synthetic_matrix/v1` erzeugt exakt **150** deterministische Profile über AMD/Intel (X3D/non-X3D), AMD/NVIDIA GPU-Klassen, 8/16/32/64 GB RAM, RAM-Speed, Windows-Builds, 60–360 Hz, CPU/GPU-Limitierung und Performance-/Quality-Ziel. Jede Probe und das Ergebnis sind ausdrücklich `SYNTHETIC / EXPECTED / NOT MEASURED`. Der Runner `iy.optimizer_runner_report/v1` erfasst Auswahl, Ausschlüsse, fehlende Eingaben, Konflikte, Backup-/Restore-Anforderungen und die vollständige Matrix. Der aktuelle Lauf: 150 Systeme; 25 stable, 120 conditional, 62 experimental Selektionsresultate, 543 nachvollziehbare Ausschlüsse, 10 ohne Kandidat; kein Messwert und keine reale FPS-Behauptung.
CONFLICT / AB: Auswahlreihenfolge ist verbindlich **safety → compatibility → evidence → stability → performance**, nicht maximale FPS. Der spätere echte Validierungsvertrag ist `A_BASELINE → B_OPTIMIZED → A_REPEAT → B_REPEAT`, mit Durchschnitts-FPS, 1%-Lows, Frametime-Perzentilen/Stabilität, Stutter, CPU/GPU-Limitierung, reproduzierbarer Differenz und Latenz wenn messbar. Ein späterer Apply-Slice darf erst nach vollständiger READ→SNAPSHOT→APPLY→VERIFY→RESTORE-Implementierung und ausdrücklicher Freigabe entstehen.
VERIFIED: Neue Matrix-/Runner-/Konflikt-/A/B-/Missing-data-Tests plus Shell-Test **27/27 PASS**. Vollständiger `pytest` **143/143 PASS**; `compileall` PASS; `pip check` PASS; `git diff --check` PASS. Der CLI-Lauf schrieb lokal `results/optimizer-synthetic-report.json` mit Schema `iy.optimizer_runner_report/v1`, Systemzahl 150 und Label `SYNTHETIC / EXPECTED / NOT MEASURED`; das Resultat bleibt ignoriert.
BUILD: Frisch bereit: `dist/experimental/Improve Yourself Experimental/Improve Yourself Experimental.exe`, `dist/experimental/Improve-Yourself-Experimental-Portable.zip`, `dist/experimental/experimental-build.json`. Das Build-Gate lief mit **143/143 PASS** und `pip check` PASS. EXE SHA-256 `9561AD24E0B3464AD25DF454A4AA0308BD9A5B6031617E2B628C8E8B0C1FA6E7` (19,807,368 Bytes); Portable-ZIP SHA-256 `524567D3AE59228634A0E7E11F33757F02CF39BE107996D1F88D737D00524A61` (168,792,626 Bytes). Der PyInstaller-Lauf lieferte die frische EXE; der lokale Runner schnitt seine Konsolenausgabe beim letzten Archivschritt zeitlich ab, daher wurde der vom Skript definierte Hash-/Manifest-Schritt danach rein mechanisch mit genau dieser EXE und dem vollständigen ZIP fertiggestellt. Beide finalen Hashes wurden erneut geprüft.
OPEN: Der aktuelle System Check hat keinen sicheren, bestätigten Leser für RAM-Speed, bestätigte CS2-Konfiguration, GPU-Treiberoptionen, Gaming-Modus oder momentane CPU/GPU-Limitierung. Diese Inputs werden absichtlich als fehlend angezeigt. Die synthetische Matrix ist Testevidenz, keine Hardware-/FPS-Evidenz.
NEXT: Tristan prüft den frischen Portable-Build auf die sichtbare, rein informative Optimizer-Evidence-Matrix und entscheidet anschließend über einen getrennten, weiterhin read-only Collector- oder A/B-Recorder-Slice. Bis dahin keine Optimizer-Apply-Funktion und keine weitere Produkt-/Benchmark-Arbeit.
MODEL_PROFILE: terra
MODEL_REASON: Mehrteiliger, sicherheitsrelevanter System-Evidence-Slice mit Schema-, UI-, Test- und Packaging-Gate.
COMPUTER_USE: no
COMMIT/PR: `3d621a0 feat: add optimizer evidence matrix validation`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Optimizer Evidence Foundation V1

STATUS: REVIEW
TASK: Die bestehende Optimizer-Evidence-Matrix zur kanonischen, weiterhin strikt read-only Domain-/Recommendation-Grundlage erweitern. Kein Apply-Pfad, keine riskante Systemänderung und keine Performance-Simulation.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/optimizer_foundation.py`, `src/improve_yourself/system_check.py`, `pyproject.toml`, `tests/test_optimizer_foundation.py`, `docs/OPTIMIZER_EVIDENCE_FOUNDATION_V1.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`.
REUSED: Der neue Collector nutzt den vorhandenen Windows-System-Check-Collector (`collect_windows_facts`) und normalisiert dessen read-only Fakten zu `iy.system_profile/v1`. Die bestehende 150-System-Matrix (`synthetic_system_matrix`) bleibt die einzige synthetische Profilbasis; der neue Harness legt keine zweite Performance-/Benchmark-Simulation an.
IMPLEMENTATION: `optimizer_foundation.py` ist die gemeinsame Infrastructure für **System Optimizer**, **Graphics Optimizer**, **Network Optimizer** und **BIOS Optimizer**. Das versionierte Datenmodell enthält `SYSTEM_PROFILE`, `OPTIMIZATION_RULE`, `RULE_COMPATIBILITY`, `EVIDENCE_RECORD`, `RECOMMENDATION_RESULT` und die später reservierte `VALIDATION_RESULT`-Struktur. Recommendation-Zustände: RECOMMENDED, ALREADY_RECOMMENDED, CONDITIONAL, NO_CHANGE, INSUFFICIENT_EVIDENCE. Interne Reifegrade: VERIFIED, CONDITIONAL_VERIFIED, EXPERIMENTAL, REJECTED, NO_BENEFIT; nicht-reife Regeln werden nicht empfohlen. `recommendation_detail_view_model()` liefert den gemeinsamen Informationspanel-Vertrag, ausdrücklich ohne Apply-Aktion.
COLLECTOR: Der reale lokale `iy-system-profile`-Lauf war read-only (`changes_applied: false`). Sicher erfasst werden CPU-Name/Hersteller/Architektur/Familie, GPU-Name/Vendor/Treiber, RAM-Kapazität, Mainboard-Hersteller/Produkt/Version, BIOS-Version/Datum/Hersteller, Windows-Edition/Version/Build, Adapter-Displayauflösung/Refresh sowie physische Netzwerkadapter (Name/Hersteller/Treiber/Link-Speed/MAC als lokale Inventarevidenz). RAM-Speed, MTU, erweiterte Adapterfeatures, aktive Spiele-Route, CS2-Konfiguration, GPU-Driver-Optionen und CPU/GPU-Limitierung bleiben korrekt unknown/not_available.
FIXTURES / BIOS: Fünf ausdrücklich fixture-only, SYNTHETIC/TEST_ONLY-Regeln decken System, Graphics, Network, BIOS und Conditional/Exclusion ab. BIOS bleibt in derselben Engine, aber die Fixture ist nicht changeable, HIGH risk, manual-action-required und trägt Guidance-/spätere Screenshot-Verifikationsmetadaten. Es wurde kein BIOS-Workflow dupliziert.
HARNESS: 150 vorhandene synthetische Profile wurden durch dieselbe Recommendation-Engine geführt. Ergebnis ausschließlich für Entscheidungslogik: **314 RECOMMENDED, 98 CONDITIONAL, 38 NO_CHANGE, 300 INSUFFICIENT_EVIDENCE, 0 Performancewerte**. Label: `SYNTHETIC / DECISION LOGIC ONLY / NOT MEASURED`.
VERIFIED: Foundation-Tests plus bestehende Optimizer-/System-Check-Tests **15/15 PASS**; vollständiger `pytest` **148/148 PASS**; `compileall` PASS; `pip check` PASS; `git diff --check` PASS. CLI-Smokes erzeugten lokal `results/system-profile.json` und `results/optimizer-foundation-fixtures.json`; beide sind ignorierte lokale Evidenz, nicht eingecheckt.
OPEN: Die fünf Regeln sind absichtlich nur technische Fixtures und keine kuratierten echten Optimizer-Regeln. Es existiert keine automatisierte Aktion. Keine echte A/B-/Performance-Evidenz wurde erzeugt.
NEXT: Tristan entscheidet über den nächsten separaten, weiterhin read-only Schritt: entweder kuratierte reale Evidence Records für wenige freigegebene Regeln oder ein eng begrenzter Collector für noch sicher erfassbare MTU/Adapterfeatures/CS2-Lesedaten. Erst deutlich später: Snapshot/Restore/Verify und ein explizit freigegebener Apply-Slice.
MODEL_PROFILE: terra
MODEL_REASON: Sicherheitsrelevanter Datenmodell-/Collector-Slice mit echter lokaler Read-only-Prüfung und deterministischem Harness.
COMPUTER_USE: no
COMMIT/PR: `54c1943 feat: add optimizer evidence foundation`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Optimizer Foundation V1 final architecture alignment

STATUS: WAITING_FOR_TRISTAN
TASK: Die verbindliche V1-Architektur ohne Apply-/Write-Pfad abschließen und die Foundation nur dort erweitern, wo Datenmodell, Network-/BIOS-Sonderfälle, Zustandsprovenance oder Tests fehlten.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/optimizer_foundation.py`, `src/improve_yourself/system_check.py`, `tests/test_optimizer_foundation.py`, `docs/OPTIMIZER_EVIDENCE_FOUNDATION_V1.md`, `coordination/agents/codex.md`.
FINAL ALIGNMENT: Die gemeinsame Engine bleibt die einzige Basis für System/Graphics/Network/BIOS. `RULE_COMPATIBILITY` trägt nun auch Rule-Konflikte; `EVIDENCE_RECORD` kann Evidenzversion und Beobachtungszeit speichern. Die verbindlichen Maturity-Werte heißen `RELEASE_VERIFIED`, `CONDITIONAL_VERIFIED`, `EXPERIMENTAL`, `REJECTED_NO_BENEFIT`. Recommendation-Ergebnisse enthalten zusätzlich den deterministischen ALREADY_RECOMMENDED-Weg. Nicht qualifizierte Regeln werden nicht empfohlen.
NETWORK: Der read-only Windows-Collector erfasst pro physischem Adapter nun Interface-Index, Link-Speed, IPv4-MTU, Connection-State und RSS, sofern Windows dies zuverlässig zurückgibt. EEE, Interrupt Moderation, Offloads, Energieverwaltung und Duplex/Link Mode bleiben explizit `NOT_RELIABLY_DETECTABLE`; keine Einstellung wird verändert. Der reale lokale Collector zeigte eine erkannte MTU und keine RSS-Behauptung, wenn Windows keine sichere Antwort lieferte.
PROVENANCE: `SYSTEM_PROFILE` unterscheidet nun per `field_observation` mindestens DETECTED, NOT_AVAILABLE und NOT_RELIABLY_DETECTABLE (INFERRED ist als zulässiger Status reserviert, wird aktuell nicht als Fakt ausgegeben). CS2-Konfiguration, GPU-Treiberoptionen sowie CPU/GPU-Limitierung bleiben korrekt unbekannt.
VERIFIED: Vollständiger `pytest` **149/149 PASS**; `compileall` PASS; `pip check` PASS; `git diff --check` PASS. Echter lokaler `iy-system-profile`-Collector erneut read-only ausgeführt; 150-System-Fixture-Harness bleibt ausschließlich `SYNTHETIC / DECISION LOGIC ONLY / NOT MEASURED`.
KNOWN LIMITS: Die Fixture-Regeln bleiben Testdaten und liefern keine reale Performance-Evidenz. Kein Ping/Jitter/Packet-Loss-Reader und kein aktiver-Gamesocket-/Routenbeleg wurde eingeführt; diese Werte würden sonst eine neue Mess- bzw. Netzwerkdiagnoseautorität benötigen.
NEXT: Genau ein möglicher Folge-Slice nach neuer Freigabe: einen lokalen, read-only Network Quality Collector für klar deklarierte Ping/Jitter/Packet-Loss-Proben mit Datenschutz-/Zielhost-Entscheidung spezifizieren. Kein Apply-/Snapshot-/Restore-Slice ohne getrennte Autorisierung.
MODEL_PROFILE: terra
MODEL_REASON: Finaler sicherheitsrelevanter Architektur-/Collector-Abgleich ohne systemverändernde Autorität.
COMPUTER_USE: no
COMMIT/PR: `18244ae feat: finalize optimizer foundation architecture`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Network Quality Collector V1

STATUS: WAITING_FOR_TRISTAN
TASK: Einen lokalen, deklarierte-Ziele-only Network Quality Collector als Observed-Network-Quality-Evidenz in die gemeinsame Optimizer Foundation einfügen, ohne Recommendation- oder Apply-Pfad.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/network_quality.py`, `tests/test_network_quality.py`, `pyproject.toml`, `docs/NETWORK_QUALITY_COLLECTOR_V1.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`.
METHOD: `iy.network_quality_measurement/v1` misst ICMP Echo einzeln pro Probe. Ergebnis enthält versioniertes/deklariertes Ziel samt Zweck und TargetClass, Methode, Anzahl, Intervall, Timeout, Messzeitpunkt, Measurement-Session-ID, alle Proben, erfolgreiche/fehlgeschlagene Proben, RTT Min/Max/Mean/Verteilung, klar definierte Jitter-Metrik (Mittel der absoluten Differenzen aufeinanderfolgender erfolgreicher RTTs) und Packet-Loss-Formel (fehlende angeforderte Proben / angeforderte Proben). Eine einzelne Probe ist `TOO_FEW_SAMPLES`.
TARGETS / PRIVACY: Klassen sind LOCAL_GATEWAY, CONTROLLED_PUBLIC_TARGET und GAME_RELEVANT_TARGET. Es gibt keinen Default- oder versteckten externen Host; Ziel-ID, Host und Zweck sind Pflichtparameter. Lokale Speicherung nur in der vom Aufrufer gewählten Datei; `external_transfer: false`, `public_ip_persisted: false`. MAC-Adressen werden aus dem Adapterkontext entfernt.
FAILURE STATES: Bei Null-Erfolg wird TARGET_UNREACHABLE, TIMEOUT oder BLOCKED_OR_FILTERED statt Packet Loss des Nutzeranschlusses ausgegeben. Teilverlust mit mindestens einer Antwort ist eine gültige Beobachtung; unter drei Erfolgen bleibt der Zustand TOO_FEW_SAMPLES. Adapter ohne Kontext ist ADAPTER_UNAVAILABLE. Allgemeine Probe-Fehler bleiben als Probe-Fehler sichtbar.
FOUNDATION INTEGRATION: `network_quality_evidence()` erzeugt einen vorhandenen `EVIDENCE_RECORD` mit SourceType OBSERVED_NETWORK_QUALITY, klarer TargetClass und Provenance „Korrelation ist keine Konfigurationskausalität“. Der Collector erzeugt selbst keine Recommendation. `measurement_session_id` bereitet spätere BEFORE/AFTER-Vergleiche vor, ohne Änderungspfad.
VERIFIED: Netzwerktests **4/4 PASS** (RTT/Jitter, Teilverlust, Timeout/unreachable, Zielklassen, lokale Speicherung/Adapter-Privacy, Evidence ohne Recommendation); zusammen mit Foundation-Tests **10/10 PASS**. Vollständige Suite und Diff-/Compile-Gate folgen vor Commit.
KNOWN LIMITS: Kein Ping/Jitter/Packet-Loss-Live-Run gegen einen externen Host wurde ohne explizit vom Nutzer gewähltes Ziel ausgeführt. ICMP kann vom Ziel gefiltert werden und repräsentiert keine CS2-/FACEIT-Qualität. Kein TCP/UDP-Spieltraffic, kein Routing-, Firewall- oder Adapterwrite.
NEXT: Tristan entscheidet über genau einen Folge-Slice: einen expliziten, privacy-reviewed Katalog von kontrollierten Testzielen/Target-Packs oder kuratierte reale Network-Evidence-Records. Keine Apply-Arbeit ohne neue Freigabe.
MODEL_PROFILE: terra
MODEL_REASON: Netzwerk- und datenschutzsensibler, aber strikt read-only Daten-/Test-Slice.
COMPUTER_USE: no
COMMIT/PR: `b5c9754 feat: add network quality collector`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Optimizer Evidence Integration Proof V1

STATUS: WAITING_FOR_TRISTAN
TASK: Den vollständigen gemeinsamen, read-only Optimizer-Evidence-Pfad nachweisen, ohne Target-Pack, neue Engine, Apply-Pfad oder reale Regeln.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/optimizer_foundation.py`, `tests/test_optimizer_integration_proof.py`, `tests/test_optimizer_foundation.py`, `docs/OPTIMIZER_EVIDENCE_INTEGRATION_PROOF_V1.md`, `coordination/agents/codex.md`.
PIPELINE: `integration_proof()` orchestriert ausschließlich die vorhandene Foundation: **COLLECT → SYSTEM_PROFILE → RULE_COMPATIBILITY → EVIDENCE → RECOMMENDATION_RESULT → UI_VIEWMODEL**. Jedes Result hält Rule-ID, Domain, State, Rationale, Missing Data, vollständige Required-/Exclusion-Trace, Konflikte und berücksichtigte Evidence Records. Das Result ist read-only.
FOUR DOMAINS / RESULTS: Sechs als FIXTURE/TEST markierte Regeln beweisen System, Graphics, Network, BIOS, Conditional/Exclusion und SECURITY_PERFORMANCE_TRADEOFF. Tests weisen RECOMMENDED, ALREADY_RECOMMENDED, CONDITIONAL, NO_CHANGE, INSUFFICIENT_EVIDENCE sowie eine explizit gematchte Exclusion nach. Fehlende Daten ergeben nie ein positives Result. Der Trade-off-Typ ist zwingend NO_CHANGE und kann nicht automatisch empfohlen oder angewendet werden.
NETWORK: `OBSERVED_NETWORK_QUALITY` aus Network Quality Collector V1 wird als eigener Evidence-Pfad neben Configuration Evidence übergeben. Die Provenance stellt klar: Korrelation ist keine Konfigurationskausalität. Beobachtetes RTT/Jitter/Packet-Loss kann daher keine Adapterursache oder automatische Empfehlung erzeugen.
UI CONTRACT: Das gemeinsame Detail-ViewModel liefert Optimizer/Improve-Empfehlungsgruppe, Domain, Titel, Zustand, Status, Erklärung, systemspezifische Begründung, Wirkung, Evidence/Gültigkeit, Risiko, Restore-Information, BIOS Guidance und Explainability. Fixtures werden explizit als `FIXTURE_ONLY — <state>` gekennzeichnet; `apply_available: false` ist fest.
SYNTHETIC: Der bestehende 150-System-Harness bleibt unverändert die einzige synthetische Decision-Logic-Matrix und enthält keine reale Performance-/Latency-Evidenz oder VALIDATION_RESULT.
VERIFIED: Vollständiger `pytest` **155/155 PASS**; `compileall` PASS; `pip check` PASS; `git diff --check` PASS.
KNOWN LIMITS: Es gibt keine reale Release-Regel, keine echte Optimizer-Recommendation, keinen Target-Pack, keine UI-Neugestaltung und keinen Apply-/Write-Pfad. Network Quality bleibt reine Beobachtung.
NEXT: Genau ein empfohlener Folge-Slice nach neuer Freigabe: privacy-reviewed, versionierte controlled Target Packs für die bereits vorhandene Network-Quality-Messung. Keine weitere Arbeit ohne Auftrag.
MODEL_PROFILE: terra
MODEL_REASON: Integrations-/Explainability-Nachweis über sicherheitsrelevante Datenpfade ohne Systemänderung.
COMPUTER_USE: no
COMMIT/PR: `6186a5c feat: prove optimizer evidence integration`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Controlled Network Target Pack V1

STATUS: WAITING_FOR_TRISTAN
TASK: Einen kleinen privacy-reviewed und versionierten Katalog kontrollierter Ziele für den bestehenden Network Quality Collector implementieren, ohne versteckten Kontakt, Recommendation oder Netzwerkänderung.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/network_target_pack.py`, `src/improve_yourself/network_quality.py`, `tests/test_network_target_pack.py`, `docs/CONTROLLED_NETWORK_TARGET_PACK_V1.md`, `coordination/agents/codex.md`.
SCHEMA: `iy.network_target_pack/v1` enthält Pack-ID/-Version und Targets mit stabiler ID, Anzeigename, Klasse, Host/Template, Protokoll, Zweck, Owner, Privacy Notice, erwarteter Offenlegung, Interpretationsscope, Target-Version, valid_from/until, ACTIVE/DEPRECATED/TEMPORARILY_DISABLED sowie technischen Voraussetzungen.
V1 CATALOG: Aufgenommen wurde ausschließlich `local-gateway-template` (ACTIVE, LOCAL_GATEWAY, Version 1.0.0). Das Ziel enthält keinen eingebetteten Host: Nutzer bestätigt die lokale Gateway-Adresse vor jeder Messung. Das Ergebnis gilt nur für die lokale Verbindung, nicht für Internet-/CS2-/FACEIT-Latenz. **Verworfen / nicht aufgenommen:** öffentliche und game-relevante Hosts, weil für sie kein separat geprüfter Betreiber-/Zweck-/Stabilitäts-/Disclosure-/Game-Relevance-Vertrag vorliegt. Kein generischer öffentlicher Pinghost wurde erfunden.
CONSENT / PRIVACY: `select_target()` akzeptiert nur bekanntes, ACTIVE, gültiges Pack-Target mit explizitem resolved_host und `user_confirmed=True`; es startet keine Messung. `selection_view_model()` stellt vor einem späteren UI-Start Ziel, Zweck, Klasse, Protokoll, Datenschutzhinweis und Offenlegung bereit. Pack-Laden verursacht keinen Kontakt. Messergebnisse bleiben lokal; der bestehende Collector persistiert keine öffentliche IP oder MAC.
VERSIONING / COLLECTOR: Der ausgewählte NetworkTarget übergibt `target_pack_version` an jede Measurement Session, zusätzlich zu target_id, TargetClass und Target-Version. Deprecated/Disabled Targets bleiben für historische Resultate interpretierbar, starten aber keine neue Messung. Der Collector bleibt die einzige Messengine.
VERIFIED: Target-Pack-Tests **5/5 PASS**: Schema, stabile ID, Version, Active/Deprecated/Expired, unbekanntes/ungültiges Target, zwingender Host/Consent, historische Pack-Version, Collector-Integration ohne Livekontakt, Timeout ohne falschen Packet-Loss-Schluss, Selection-View. Vollständiger `pytest` **160/160 PASS** (ein erster fremder Loopback-Origin-Guard-Test lieferte einmalig WinError 10053 statt HTTPError; unveränderter Wiederholungslauf vollständig grün); `compileall` PASS; `pip check` PASS; `git diff --check` PASS.
KNOWN LIMITS: Es ist absichtlich kein externer V1-Host verfügbar. Gateway-Discovery wird nicht automatisch vorgenommen; der Host muss konkret bestätigt übergeben werden. Network-Collector-Unterbau gilt danach für V1 als ausreichend; keine weitere Vertiefung ohne Auftrag.
NEXT: Genau ein empfohlener Folge-Slice nach neuer Freigabe: Integration eines kleinen kuratierten realen Optimizer-Regelkatalogs über die bestehende Evidence-/Recommendation-Foundation. Kein weiterer Network-Unterbau.
MODEL_PROFILE: terra
MODEL_REASON: Datenschutz- und Netzwerkkontakt-Governance mit versionierter historischer Nachvollziehbarkeit.
COMPUTER_USE: no
COMMIT/PR: `75d9350 feat: add controlled network target pack`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Synthetic Matrix Validation V1

STATUS: WAITING_FOR_TRISTAN
TASK: Die vorhandene 150-System-Synthetic-Matrix als finale, kanonische und wiederverwendbare Validierungsstrecke für kommende kuratierte Rule Packs absichern — ohne Performance-Simulation oder neue Infrastruktur.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/optimizer_evidence.py`, `src/improve_yourself/optimizer_foundation.py`, `tests/test_synthetic_matrix_validation.py`, `docs/SYNTHETIC_MATRIX_VALIDATION_V1.md`, `coordination/agents/codex.md`.
PROFILES: Exakt 150 Profile, jetzt jeweils `iy.system_profile/v1`, `SYNTHETIC_VALIDATION`, `SYNTHETIC / EXPECTED / NOT MEASURED` und `real_evidence_allowed: false`. Abdeckung: AMD/Intel CPUs, AMD/NVIDIA GPUs und Treiberzustände, 8/16/32/64 GB, Windows-Builds, 60/120/144/165/240/360 Hz, Mainboard/BIOS-Varianten, NICs mit 100/1000/2500 Mbps, MTU/RSS/Unknown-Feature-Zuständen, bereits empfohlenem Zustand, fehlender Treiberversion, fehlendem Mainboard/BIOS und fehlendem Adapter.
HARNESS: `validate_synthetic_rule_pack(rule_pack)` verwendet dieselbe gemeinsame Foundation und nimmt später kuratierte `OptimizationRule`-Packs ohne Umbau der Profile oder des Tests entgegen. Es erzeugt deterministische Profile→Compatibility→Evidence Sufficiency→Recommendation Result-Traces inklusive State- und Domain-Zählern. Kennzeichnung: `SYNTHETIC / DECISION LOGIC ONLY / NOT REAL EVIDENCE`; `real_validation_result_created: false`, `confidence_changed: false`.
ABDECKUNG: Tests zeigen alle vier Domains sowie RECOMMENDED, ALREADY_RECOMMENDED, CONDITIONAL, NO_CHANGE, INSUFFICIENT_EVIDENCE, gematchte Exclusion und SECURITY_PERFORMANCE_TRADEOFF. Missing/Unknown bleibt Missing/Unknown; keine positive Empfehlung durch Annahme. Keine FPS-/Frametime-/Ping-/Jitter-Verbesserung und keine reale Evidence/Validation Result wird erzeugt.
REAL TESTER PREP: Synthetische und spätere echte Profile folgen demselben `iy.system_profile/v1`-Schema. Ein späterer read-only Shadow-Recommendation-Tester kann daher lokal erfassen, auswerten und protokollieren, ohne Systemdaten automatisch zu übertragen. Dieser Slice implementiert keine Übertragung.
VERIFIED: Neue Matrix-Tests **3/3 PASS**; vollständiger `pytest` **163/163 PASS**; `compileall` PASS; `pip check` PASS; `git diff --check` PASS.
COVERAGE LIMITS: Keine Hardwarekatalog-Vollständigkeit, kein echter A/B-Nachweis und keine reale Confidence-Erhöhung. Die erwarteten Resultate sind deterministische Rule-Pack-Entscheidungen, keine Performanceprognosen.
NEXT: Genau ein empfohlener Folge-Slice nach neuer Freigabe: den separat gelieferten kuratierten realen V1-Matrix-/Rule-Pack mit stabilen Rule-IDs einspielen und gegen diese Matrix prüfen. Keine weitere Optimizer-Infrastruktur eigenständig vertiefen.
MODEL_PROFILE: terra
MODEL_REASON: Finaler deterministischer Validierungs-/Safety-Pass vor dem realen kuratierten Regelkatalog.
COMPUTER_USE: no
COMMIT/PR: `4754ac6 feat: finalize synthetic matrix validation`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Optimizer UI Integration V1

STATUS: WAITING_FOR_TRISTAN
TASK: Die bestehende read-only Optimizer Foundation als echten Produktfluss in der vorhandenen Improve-Shell darstellen, ohne neue Engine, reale Regeln, Apply oder visuellen Gesamt-Neubau.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `tests/test_analyzer_shell.py`, `docs/OPTIMIZER_UI_INTEGRATION_V1.md`, `coordination/agents/codex.md`.
FLOW: Nach einem bestätigten read-only System-Check zeigt die bestehende System Check / Optimizer-Route nun Improve Empfehlungen: Zusammenfassung geprüfter, technischer Fixture-Treffer, bereits passender, Conditional-, Insufficient-Evidence- und manueller/BIOS-Fälle. Darunter liegen vier gleichwertige Buttons/Unteransichten für System, Graphics, Network und BIOS. Sie filtern dieselben datengesteuerten Resultate, nicht vier separate Engines.
CARDS / DETAILS: Jede Setting-Card zeigt Name, aktuellen Zustand, Fixture-markierte Improve-Empfehlung, Status, Evidenzkontext und ggf. manuellen BIOS-Hinweis. Details anzeigen öffnet das eine gemeinsame Detailpanel mit Was ist das, Zustand, Empfehlung, systemspezifischer Begründung, möglicher Wirkung, Evidence/Gültigkeit, Risiko/Trade-off, Restore-Information, BIOS Guidance sowie Compatibility-/Missing-Explainability. Es gibt ausdrücklich keinen Apply-Button oder Write-Pfad.
NETWORK / BIOS: Observed Network Quality bleibt im Foundation-Vertrag von Configuration Evidence getrennt; fehlende Messung wird nicht als 0 dargestellt. BIOS bleibt manuell mit Guidance-/Screenshot-Vorbereitung und keinem Apply. Fixtures werden immer als `FIXTURE_ONLY — <state>` gerendert und nie wie echte Improve-Empfehlungen behandelt.
SYNTHETIC TEST: `optimizer_product_view(synthetic_profile, internal_test=True)` erlaubt den begrenzten internen Weg für ein ausgewähltes kanonisches Matrixprofil (u.a. #037), ohne ihn als normalen Nutzerzustand oder Debug-Schalter auszustellen. Künftige kuratierte Rule Packs fließen über Foundation → ViewModel → bestehende UI ohne neue Rule-spezifische UI.
VERIFIED: UI-/ViewModel-/Synthetic-Profile-Tests **23/23 PASS**; vollständiger `pytest` **164/164 PASS**; `compileall` PASS; `pip check` PASS; `git diff --check` PASS.
KNOWN LIMITS: Keine kuratierten realen Regeln, keine echte Network-Messanzeige ohne lokale gültige Messung, kein visueller Endpolish und kein Apply. Der Detailtext zeigt strukturierte Evidenz transparent; die spätere finale Komponenten-/Spacing-Abnahme bleibt getrennt.
NEXT: Genau ein empfohlener Folge-Slice nach neuer Freigabe: den separat gelieferten kuratierten realen V1-Matrix-/Rule-Pack einspielen und gegen die 150-System-Matrix sowie diese UI testen. Keine weitere Infrastruktur ohne Auftrag.
MODEL_PROFILE: terra
MODEL_REASON: Produktintegration einer bestehenden sicherheitskritischen Read-only-Datenkette mit UI-/ViewModel-Regressionen.
COMPUTER_USE: no
COMMIT/PR: `e19ddff feat: integrate optimizer foundation into UI`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Optimizer Real Rule Pack Readiness V1

STATUS: WAITING_FOR_TRISTAN
TASK: Den datengetriebenen, fail-closed Rule-Pack-Import samt Synthetic-Regression und bestehender UI-Anbindung für den separat gelieferten kuratierten Matrix Pack 01 vorbereiten, ohne eigene reale Regeln oder weitere Infrastruktur.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/rule_pack.py`, `src/improve_yourself/optimizer_foundation.py`, `src/improve_yourself/analyzer_shell.py`, `tests/test_rule_pack.py`, `docs/OPTIMIZER_REAL_RULE_PACK_READINESS_V1.md`, `coordination/agents/codex.md`.
SCHEMA: `iy.improve_rule_pack/v1` finalisiert stabile Rule-ID, Domain, Setting, Beschreibung, Current-State-Pfad, Candidate-State, Compatibility/Exclusions, Dependencies/Conflicts, Evidence, Klassen-/Maturity-Metadaten, Risk, Restart, Read/Apply/Restore-Capabilities, Erklärung, Version und Provenance. Unterstützte Pack-Klassen: RELEASE_CANDIDATE, CONDITIONAL, EXPERIMENTAL, NO_CHANGE, SECURITY_PERFORMANCE_TRADEOFF, REJECTED. Apply ist nur Metadatum, nicht implementiert.
VALIDATION GATE: `import_rule_pack()` ist fail-closed für Schema, doppelte IDs, ungültige Domain/Risk/Class, fehlende State-/Explanation-/Provenance-Metadaten, fehlende/ungültige Evidence, invalide Compatibility und widersprüchliche Required/Exclusion-Conditions. Ungültige Regeln werden nicht still aktiviert. `validate_rule_pack()` importiert nur nach bestandenem Gate und startet danach die bestehende 150-System-Synthetic-Regression.
SYNTHETIC / REAL: Der Regression-Report liefert deterministisch pro Rule/Systemklasse matched/excluded/recommended/already/conditional/no-change/insufficient/conflict über den bestehenden Harness. Er kann kein reales VALIDATION_RESULT erzeugen, Confidence nicht erhöhen und keine Performancebehauptung ableiten.
UI: Importierte `OptimizationRule`-Objekte fließen direkt in `optimizer_product_view(..., rules=rules)` → Improve Empfehlungen → richtige Domain → gemeinsame Setting Cards → gemeinsames Detailpanel. Test beweist diesen Weg für den Fixture-Pack ohne Rule-spezifischen UI-Code; alle Fixtures bleiben sichtbar `FIXTURE_ONLY`, Apply bleibt false.
SCHEMA LIMITS: Kein echter Matrix Pack 01 wurde erfunden oder recherchiert. Das Fixture-Pack ist nur ein syntaktisches/semantisches Formatbeispiel. Eine spätere reale Pack-Signatur, Content-Pack-Lieferkette oder Release-Freigabe ist nicht Gegenstand dieses Slices.
VERIFIED: Rule-Pack-Import-/Gate-/Regression-/UI-Tests **12/12 PASS**; vollständiger `pytest` **171/171 PASS**; `compileall` PASS; `pip check` PASS; `git diff --check` PASS.
NEXT: Erwarteter nächster Input ist ausschließlich der separat kuratierte Improve Matrix Pack 01. Nach dessen Lieferung: Pack importieren, fail-closed validieren, über 150 Profile regressieren und in UI prüfen. Keine weitere Infrastruktur oder eigenen realen Optimizer-Regeln beginnen.
MODEL_PROFILE: terra
MODEL_REASON: Finaler Import-/Safety-Gate vor kuratiertem Inhalt, mit deterministischer Regression und UI-Durchstich.
COMPUTER_USE: no
COMMIT/PR: `243287a feat: prepare optimizer rule pack readiness`, gepusht nach `origin/dev/v1-foundation`.

# Hold 2026-08-22 — WAITING_FOR_MATRIX_PACK_01

STATUS: WAITING_FOR_MATRIX_PACK_01
TASK: Ausschließlich Readiness prüfen; keine neue Optimizer-Infrastruktur, keine eigenen realen Regeln und keine Network-/BIOS-/Apply-Arbeit.
BRANCH: `dev/v1-foundation`
HEAD: `f2e59db docs: record matrix pack hold status`.
HOLD CHECK: Arbeitsbaum sauber. Relevante Optimizer-/Evidence-/Rule-Pack-/Synthetic-/UI-Tests **33/33 PASS**. Der fail-closed Fixture-Pack-Import validiert, anschließend läuft die sofort ausführbare 150-System-Regression mit `valid: true`, `system_count: 150`, `real_validation_result_created: false`, `confidence_changed: false`. `git diff --check` PASS.
SAFETY: EXPERIMENTAL, REJECTED, INSUFFICIENT_EVIDENCE und SECURITY_PERFORMANCE_TRADEOFF bleiben über die bestehende Foundation keine normale positive Improve-Empfehlung. Importierte Regeln benötigen keinen Rule-spezifischen UI-Code; der gemeinsame UI-/Detailvertrag bleibt read-only und `apply_available: false`.
BLOCKER: Keiner. Der einzige erwartete fachliche Input ist der separat kuratierte Improve Matrix Pack 01.
NEXT: Nach Lieferung Matrix Pack 01 exakt fail-closed importieren, Schema/IDs/Evidence/Compatibility/Exclusions validieren, vollständig gegen 150 Profile regressieren, Resultate pro Rule/Systemklasse dokumentieren und in Optimizer-UI/Detailpanel prüfen — ohne Systemänderung.
COMMIT/PR: `f2e59db docs: record matrix pack hold status`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Matrix Pack 01 integration attempt

STATUS: BLOCKED — WAITING_FOR_MATRIX_PACK_01
TASK: Den freigegebenen festen Ablauf IMPORT → VALIDATE → 150-SYSTEM REGRESSION → UI REVIEW für das kuratierte reale Improve Matrix Pack 01 ausführen, ausschließlich read-only innerhalb der bestehenden Foundation.
BRANCH: `dev/v1-foundation`
CHANGED: Nur dieser Handoff; keine Produktcode-, Regel-, Infrastruktur-, Apply-/Write-, Network-/BIOS- oder Benchmark-Änderung.
INPUT CHECK: Weder der aktuelle Checkout noch `origin/dev/v1-foundation` enthält ein tatsächliches kuratiertes Matrix-Pack-01-Artefakt. Auffindbar sind nur `src/improve_yourself/rule_pack.py`, `tests/test_rule_pack.py` und die Readiness-Dokumentation. Der einzig importierbare Inhalt ist `fixture-rule-pack`; alle Regeln sind als `fixture_only: true` gekennzeichnet und dürfen nicht als reale Improve-Regeln ausgegeben werden.
VERIFIED: Projekt-venv (Python 3.13) — relevante Rule-Pack-/Synthetic-/Integration-/UI-Tests **33/33 PASS**. Der bestehende fail-closed Fixture-Import liefert `valid: true`, `fixture_rules: true`, `system_count: 150`, `real_validation_result_created: false`, `confidence_changed: false`. `git diff --check` PASS; Arbeitsbaum vor diesem Handoff sauber. Ein erster Aufruf über den globalen Python-3.14-Interpreter schlug lediglich wegen fehlendem `pytest` fehl; die verbindliche Projektumgebung läuft danach grün.
UI REVIEW: Für den Fixture-Pack ist der bestehende generische UI-Pfad getestet: Domainzuordnung und gemeinsames Detailmodell werden ohne Rule-spezifischen UI-Code dargestellt, alle Modelle sind sichtbar `FIXTURE_ONLY`, `apply_available: false`. Dies ist ausdrücklich kein UI-Review eines realen Matrix Pack 01, weil dessen Daten nicht vorliegen.
RISKS / UNKNOWN: Reale Rule-IDs, Provenance, Evidence, Compatibility, Exclusions, Konflikte und Unknown-/Conditional-Verteilung sind ohne das kuratierte Artefakt nicht prüfbar. Eine Ersetzung durch Fixture- oder selbst recherchierte Regeln wäre fachlich falsch und außerhalb des freigegebenen Scopes.
NEXT: Tristan liefert das versionierte kuratierte Improve Matrix Pack 01 als Repository-Datei oder eindeutig referenziertes Artefakt. Danach genau einmal den vorgesehenen read-only Ablauf ausführen: fail-closed Import, vollständige Validation, 150-System-Report pro Rule/Systemklasse, Konflikt-/Unknown-/Exclusion-Auswertung und generischen UI-/Detailpanel-Review.
MODEL_PROFILE: terra
MODEL_REASON: Bestehende sicherheitskritische Read-only-Regelstrecke geprüft; vollständige Integration ist ausschließlich durch den fehlenden kuratierten Eingabeinhalt blockiert.
COMPUTER_USE: no
COMMIT/PR: `c9b8703 docs: record matrix pack input blocker`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Improve Matrix Pack 01 integrated

STATUS: DONE — WAITING_FOR_TRISTAN
TASK: Improve Matrix Pack 01 als versionierte, maschinenlesbare Read-only-System-Check-Basis importieren, fail-closed validieren, über die bestehende 150-System-Matrix regressieren und im vorhandenen Optimizer-UI-/Detailvertrag prüfen.
BRANCH: `dev/v1-foundation`
CHANGED: `config/rule-packs/improve-matrix-pack-01.json`, `src/improve_yourself/rule_pack.py`, `src/improve_yourself/optimizer_foundation.py`, `src/improve_yourself/analyzer_shell.py`, `packaging/improve-yourself-experimental.spec`, `tests/test_matrix_pack_01.py`, `docs/IMPROVE_MATRIX_PACK_01.md`, `coordination/agents/codex.md`.
PACK: `iy.improve_rule_pack/v1`, `improve-matrix-pack-01`, Version `1.0.0`, `READ_ONLY_SYSTEM_CHECK_BASIS`. Es enthält ausschließlich die vorhandenen 12 System-Check-Basen `windows`, `cpu`, `memory`, `motherboard`, `gpu`, `gpu_driver`, `chipset_driver`, `graphics_settings_profile`, `display`, `monitor`, `secure_boot`, `tpm` sowie die separaten vorhandenen Setting-IDs `latency`, `upscaling`, `frame_pacing`, `sync`, `sharpening`, `quality_overrides`, `game_tuning`. Alle 12 Regeln sind read-only, Apply/Restore false; kein neuer Tweaksatz.
PROVENANCE: Exakter bestehender Source-Contract `origin/main@2cd358c`, `src/improve_yourself/system_check.py`; drei Quellen AMD RX 7900 XTX, Gigabyte X870 GAMING X WIFI7 und AMD X870 sind enthalten. Ihre live beobachteten Werte sind ausdrücklich nicht release-fixiert. Nicht gemappte Hardware, nicht auslesbare Profilwerte und fehlende Live-Vergleiche bleiben Unknown/Unsupported/Review.
IMPORT / VALIDATE: `load_rule_pack_document()` liest das JSON, dann bleibt `import_rule_pack()` der einzige bestehende fail-closed Gate. Format, Regeln, Evidence und UI laufen über dieselbe Foundation; kein zweiter Importer und keine Rule-spezifische UI.
REGRESSION: Vollständige deterministische 150-System-Auswertung: 1.800 Rule-System-Ergebnisse = RECOMMENDED 0, ALREADY_RECOMMENDED 0, NO_CHANGE 1.159, CONDITIONAL 172, INSUFFICIENT_EVIDENCE 469. 90 AMD-only Profilexclusions, 143 bedingte statt geratene Chipsatzzuordnungen. Mainboard-/Treiber-/Monitor-Missing sowie alle 300 fehlenden Secure-Boot-/TPM-Evidenzen bleiben INSUFFICIENT_EVIDENCE. Es gibt keine fachlich vorhandenen Pack-01-Konflikte; der bestehende Fixture-Contract beweist weiterhin die allgemeine deterministische Konfliktbehandlung, ohne eine reale Regel zu erfinden. Synthetic erzeugt keine reale VALIDATION_RESULT und ändert keine Confidence.
FIX: Trade-off-Schutz überschrieb vorher auch fehlende Secure-Boot-/TPM-Evidenz mit NO_CHANGE. Er unterdrückt nun ausschließlich positive RECOMMENDED/ALREADY_RECOMMENDED-Zustände; Unknown bleibt korrekt INSUFFICIENT_EVIDENCE.
UI REVIEW: Der bestehende generische Detailvertrag zeigt für Pack-Regeln nachvollziehbar `READ-ONLY FACTS AVAILABLE`, `CONDITIONAL / NOT CONFIRMED`, `UNSUPPORTED / EXCLUDED` oder `UNKNOWN / NOT AVAILABLE`, einschließlich Compatibility-Trace, Missing-Pfade, Evidence und Risiko. Die normale Desktop-System-Check-/Optimizer-Route lädt das gebündelte Pack 01 über denselben fail-closed Importer; bei ungültigem Pack leert sie die Bewertung und fällt nicht auf Fixtures zurück. Jede Pack-Karte meldet `NO AUTOMATIC IMPROVE RECOMMENDATION — <state>` und `apply_available: false`. Keine neue Ansicht, keine Remote-Schnittstelle, kein Apply.
VERIFIED: Neue Matrix-Pack-Tests plus vollständiger `pytest` **175/175 PASS**; `compileall` PASS; pack-native Import/Validate/150-Regressions-Smoke PASS; `git diff --check` PASS. Der Packaging-Check bestätigt das JSON im Portable-Laufzeitpfad `_internal/config/rule-packs/improve-matrix-pack-01.json`. Die neue Teststrecke prüft Version/JSON, 12+7 Contract-IDs, drei nicht release-fixierte Quellen, fail-closed Import, deterministische 150-System-Verteilung, no-positive-recommendation, no-apply sowie Unknown/Conditional-Darstellung.
RISKS / LIMITS: Kein Anspruch auf reale 150-Hardware-Golden-Master, keine reale Performance- oder Confidence-Aussage. Pack 01 enthält bewusst nur die vorhandenen exakten AMD-/Gigabyte-/AMD-Mappings; alles andere bleibt offen. Es existiert keine Pack-01-Konfliktregel, weil der bestehende System-Check-Vertrag keine definiert. Der Packaging-Gate erzeugte die frische EXE und das Pack liegt darin korrekt vor; die nach einer zeitlich unterbrochenen ZIP-Archivierung lokal reparierte Portable-ZIP hat einen anderen Hash als das ignorierte, ältere `experimental-build.json`. Das Manifest ist daher kein aktueller Release-Nachweis und vor einer Distribution einmal vollständig über den etablierten Build-Gate neu zu erzeugen.
NEXT: Tristan prüft den gepushten Pack-01-Checkpoint und entscheidet über die nächste explizite, weiterhin read-only fachliche Erweiterung oder reale Tester-Evidenz. Keine Apply-/Write-, Registry-, BIOS-, Network-, Benchmark- oder weitere Optimizer-Infrastruktur ohne Auftrag.
MODEL_PROFILE: terra
MODEL_REASON: Sicherheitskritische, bestehende Read-only-Semantik in ein versioniertes Pack integriert und bis UI-Vertrag/150-Profil-Regression nachgewiesen.
COMPUTER_USE: no
COMMIT/PR: `776b28c feat: integrate improve matrix pack 01`, `7fd1df7 docs: finalize matrix pack 01 handoff` und `830f13f docs: record matrix pack packaging caveat`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Real-System Evidence Pass 01

STATUS: DONE — WAITING_FOR_TRISTAN
TASK: Pack 01 gegen das lokal verfügbare reale, read-only System-Check-Ergebnis prüfen, Unknown/Conditional/Exclusion/Insufficient-Evidence klassifizieren, die reale UI-Projektion kontrollieren und den vollständigen Portable-Build bis Manifest nachweisen.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/optimizer_evidence.py`, `tests/test_optimizer_evidence.py`, `tools/dev/Build-Experimental.ps1`, `docs/REAL_SYSTEM_EVIDENCE_PASS_01.md`, `coordination/agents/codex.md`.
REAL EVIDENCE: Ein verfügbarer lokaler Tester, ohne Speicherung von Rohprofil oder absolutem Pfad. `iy.system_check/v1` war gültig und policy-bestätigt read-only (`changes_applied: false`, `elevation_requested: false`); 8 aktuelle Checks, Summary 6 OK / 2 REVIEW / 0 ACTION_REQUIRED. Kein Apply, Registry-, BIOS-, Treiber-, Network- oder Benchmark-Write.
PACK RESULT: 12 Pack-Karten, 8 NO_CHANGE, 1 CONDITIONAL (`Grafiktreiber-Aktualität`), 3 INSUFFICIENT_EVIDENCE (`Monitorerkennung`, `Secure Boot`, `TPM 2.0`), 0 RECOMMENDED, 0 ALREADY_RECOMMENDED, 0 Exclusions. Jeder ViewModel-Eintrag `apply_available: false`; `fixture_only: false`. Conditional und Unknown werden über die gemeinsame UI als `CONDITIONAL / NOT CONFIRMED` bzw. `UNKNOWN / NOT AVAILABLE` erklärt, mit Missing-Evidence-Pfaden.
FIX: Die vorhandene Mainboard-/BIOS-Evidenz des System Check wurde in `profile_from_system_check()` bisher nicht in das gemeinsame Optimizerprofil projiziert. Die verlustfreie Read-only-Projektion von Hersteller/Produkt/Version und BIOS-Version/-Datum ist ergänzt und im zweiten Realpass bestätigt. Keine Erkennung, Regel oder Bewertung wurde erweitert.
SYNTHETIC VS REAL: Die 150-System-Matrix bleibt Logikcoverage, nicht reale Erwartungsverteilung und nicht Performanceevidenz. Sie deckt explizite Exclusions und Fixture-Conflict-Logik ab; im einen realen Tester trat keine Exclusion/kein Conflict auf. Real bestätigt die Safety-Grenze: fehlende/unpassende Daten werden weder geraten noch positiv empfohlen.
KNOWN LIMIT: Aktiver `dev/v1-foundation`-System Check liefert derzeit acht statt der zwölf Pack-01-Basen. Daher bleiben Driver-/Chipset-Currentness, Graphics-Profile und Monitor-Identity auf diesem Tester conditional oder insufficient, soweit sie nicht aus tatsächlich gelieferter Evidenz bestätigt werden. Das ist dokumentierte fehlende Evidenz, kein negativer Hardwarebefund.
BUILD: Vollständiger etablierter Portable-Build PASS, einschließlich frischem Manifest. Build-Gate: `pytest` 175/175 PASS, `pip check` PASS, PyInstaller PASS, Portable-ZIP PASS. Die eingebundene Pack-Datei ist im Portable-Laufzeitpfad bestätigt. EXE SHA-256 `1A1075DCBB4230DC41412C199D944E0FFE610696DAEDDCFAD02E77AC2D638558` (19.834.027 Bytes), Portable-ZIP SHA-256 `AF12377B612B785536C2CE2618EA1A10C4228B0EE8B568C5F17C29BFBD2B8AB4` (168.822.622 Bytes); beide Werte stimmen exakt mit `dist/experimental/experimental-build.json` überein. Der Build-Skript-Hashpfad verwendet nun .NET-SHA-256 statt des im Hintergrundlauf nicht verfügbaren Cmdlets `Get-FileHash`.
NEXT: Tristan entscheidet ausschließlich über den vorgeschlagenen nächsten fachlichen Slice: read-only Abgleich des aktiven 8-Check-System-Check-Vertrags mit dem bereits versionierten 12-Check-Vertrag, danach weitere ausdrücklich bereitgestellte reale Tester. Keine Apply-/Write-/Rule-Research-/Benchmark-Arbeit ohne Auftrag.
MODEL_PROFILE: terra
MODEL_REASON: Realer, privacy-bewusster read-only Evidence-Abgleich mit gezielter Datenpfadkorrektur und Release-Gate.
COMPUTER_USE: no
COMMIT/PR: `da9cd34 feat: validate matrix pack against real system evidence`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-21 — Home final color / surface conformance pass

STATUS: WAITING_FOR_TRISTAN
TASK: Ausschließlich die angenommene Home-Struktur gegen das festgelegte Farbgewicht und die Oberflächentiefe des Improve-Home-Masters kalibrieren. Keine Route, Datenbindung, Geometrie, Typografie, Funktion oder Produkt-Scope erweitert.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `docs/AGENT_BASE.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`.
THEME: Die zentrale Oberfläche verwendet nun App `#020A12`, Sidebar `#03101C`, Panel `#071725`, raised/Card `#0A1C2D`, Hover `#0D2236`, Border `#0A2132`, Border-soft `#071A27`, Active-Border `#1174AD`, Blau `#0B79C9`, Cyan `#13A7E8`, Text `#E4E8ED`, Secondary `#A0ABB8`, Muted `#687789`. Die Canvas-Surfaces, Home-ttk-Styles, Metrikzellen, Sidebar-Statusfläche, Navigation-Hover/Active, Icons, Gauge und Tech-Linie verwenden die zentrale Skala statt der bisherigen hellen stahlblauen Flächen oder permanenter leuchtender Konturen.
SCOPE: Die verbindliche Reihe Letzter Systemscan → Dein Fortschritt – Überblick → Letzte Analysen, alle sechs Modulkarten, Sidebar-Routen, gerundete Ecken, Action-Grundlinie, Fonts, Systemscan-Projektion, echte/neutral leere Datenzustände und Responsive-Verhalten blieben unverändert. Modulidentitäten bleiben an Linie/Icon/Button vorhanden, bilden aber keine Card-Grundfläche mehr. Keine Analyzer-, Embedded-Review-, Tactical-, Rules-, System-Check- oder NetCon-Logik geändert.
VISUAL_CHECK: Quell-Shell und anschließend die frisch paketierte Portable-EXE praktisch auf Home geöffnet. Gesamtfläche und Sidebar sind sehr dunkel; die Topmodule, mittleren drei Panels und unteren Informationsflächen unterscheiden sich nur über geringe Navy-Stufen und subtile Borders. Aktive Navigation bleibt als abgerundeter blauer Fokus lesbar, ohne dass die Sidebar oder alle Cards zum HUD werden. Text bleibt auf den dunkleren Flächen lesbar; die Portable zeigt erwartungsgemäß einen neutralen Systemscan, wenn ihr eigener lokaler Datenordner noch keinen Scan enthält.
VERIFIED: Gezielte Analyzer-Shell-Tests **18/18 PASS**; vollständiger `pytest` **134/134 PASS**; `compileall` PASS; `git diff --check` PASS. Der Build-Gate führte erneut `pytest` **134/134 PASS** sowie `pip check` PASS aus. PyInstaller erzeugte die neue EXE; weil der lokale Wrapper-Prozess in dieser Umgebung vor seinem letzten Kopier-/ZIP-Schritt beendet wurde, wurde exakt dieser mechanische, im bestehenden Skript definierte Schritt anschließend mit der frisch erzeugten EXE ausgeführt, nachdem die vorher geöffnete Portable sauber geschlossen war.
BUILD: Frisch geprüft und bereit: `dist/experimental/Improve Yourself Experimental/Improve Yourself Experimental.exe`, `dist/experimental/Improve-Yourself-Experimental-Portable.zip`, `dist/experimental/experimental-build.json`. EXE SHA-256 `87DD29463FCC11087E6E8830CE079D18F3D5947F29000AFA67DBDDF79A66997F`; Portable-ZIP SHA-256 `8077FBB2D59BAFDF2411CE479F3841803D0DA44A17FAEB65FD05CE4AF1852D9D`.
WORKTREE: Vor Commit nur die vier oben genannten versionierten Dateien geändert; temporäre Testartefakte wurden entfernt, lokale Ergebnisdaten bleiben ignoriert.
OPEN: Ausschließlich Tristans visueller Abgleich dieser neuen Portable gegen den Home-Master. Kein Merge nach `main` und kein neuer Product Slice.
NEXT: Tristan prüft die neue Portable nur auf Home-Farbgewicht, Surface-Kontrast, Sidebar, aktive Navigation, Akzentdisziplin, Border-/Radius-Ruhe und Textkontrast. Bei Zustimmung `HOME: ACCEPTED / UI MASTER LOCKED`; ansonsten genau eine weitere begrenzte visuelle Abweichung melden.
MODEL_PROFILE: terra
MODEL_REASON: Eng begrenzter visueller Token-/Surface-Pass ohne Funktionsänderung.
COMPUTER_USE: yes
COMMIT/PR: Diesen Handoff mit dem Farb-/Surface-Checkpoint auf `dev/v1-foundation` committen und pushen; exakter HEAD folgt im Abschlussbericht.

# Handoff 2026-08-21 — Final Home master pass

STATUS: WAITING_FOR_TRISTAN
TASK: Den bestehenden Home-Slice vollständig gegen die verbindliche Page-03-Masterreferenz abschließen, ohne einen neuen Product Slice oder strukturellen Neubau zu beginnen.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `tests/test_analyzer_shell.py`, `docs/AGENT_BASE.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`.
IMPLEMENTATION: Die feste mittlere Reihe lautet links nach rechts **LETZTER SYSTEMSCAN → DEIN FORTSCHRITT – ÜBERBLICK → LETZTE ANALYSEN**. `SCHNELLZUGRIFF` ist vollständig entfernt. Der Systemscan besitzt das geforderte 2×3-Raster für CPU, GPU, RAM, Windows, Treiber und Monitor, Zeitpunkt, Gesamtstatus, echte Hinweise sowie genau die Aktion `Systemdetails anzeigen` auf die bestehende System-Check-/Optimizer-Route. `system_scan_home_view()` akzeptiert nur das vorhandene lokale Schema `iy.system_check/v1`, projektiert daraus nachweisbare Evidenz und lässt nicht vorhandene Daten neutral. Ein gespeicherter lokaler Scan wird beim Home-Start gelesen, ein neu gestarteter vorhandener read-only Systemscan aktualisiert dieselbe Anzeige. Fortschritt hat Gesamtstatus sowie AIM, DUELS, UTILITY, GAME SENSE / POSITIONING und PERFORMANCE vorbereitet; ohne echte Datengrundlage bleiben alle Werte sauber als nicht verfügbar sichtbar.
THEME: Verbindlich konsolidiert: App `#010D19`, Panel `#182D4F`, Panel-soft `#30485A`, Accent `#075C94`, Accent-bright `#0A9AE7`, Accent-strong `#0065DA`, Text `#D0D1D3`, Secondary `#8F97A4`, Muted `#627188`. Gemeinsame Modul- und Unterflächen verwenden nun dieselben dunklen Konturen und 8px-Rundungen; Sidebar-Active/Hover bleibt eine ruhige integrierte blaue Fläche. Akzentfarben bleiben Kennzeichnung, keine dominierende Grundfläche. Variant-3-Branding, Orbitron für markante Displaytexte, Inter für reguläre UI und die gemeinsame Action-Grundlinie sind unverändert.
DATA_TRUTH: Ein lokaler read-only `iy.system_check/v1`-Lauf wurde erzeugt und die Projektion erfolgreich mit dem tatsächlich gespeicherten Schema geprüft. Keine Hardwarewerte, Scores, Analysehistorie oder Hinweise aus Mockups übernommen. Die Laufzeitdaten verbleiben in ignoriertem lokalem `results/`.
VERIFIED: `compileall` PASS; gezielte Shell-Tests **18/18 PASS**; vollständiger `pytest` **134/134 PASS**; `git diff --check` PASS. Quell-Shell wurde im kleinen 1080×720-Viewport gestartet: responsiver 3×2-Modulreflow und vertikales Scrolling nur für echten Overflow bleiben verfügbar. Die große Home-Ansicht bleibt ohne unnötigen Scrollbar. Vor dem Packaging läuft zusätzlich der vollständige Build-Gate.
SCREEN | STRUCTURAL MASTER MATCH | VISUAL MASTER MATCH | REMAINING DEVIATION: Home / Dashboard | PASS – Header, vier Statuskarten, sechs Module, feste Mittelreihe, untere Idee-/Community-Flächen | PASS – dunkle ruhige Midnight-Surfaces, subtile Konturen, gerundete Sidebar-Active-Fläche, Orbitron/Inter | ausschließlich menschliche Endabnahme gegen das Masterbild. Analyzer / Embedded Review / Tactical Replay / Rules / Optimizer / Settings / Reports | bestehender Stand, nicht verändert | nicht Gegenstand dieses Home-Passes | getrennte spätere Screen-Abnahme.
BUILD: Frisch erzeugt und praktisch geöffnet: `dist/experimental/Improve Yourself Experimental/Improve Yourself Experimental.exe`, `dist/experimental/Improve-Yourself-Experimental-Portable.zip`, `dist/experimental/experimental-build.json`. Das Build-Gate führte die vollständigen **134/134** Tests aus; `pip check` PASS. EXE SHA-256 `4A153BAF6F614EA8A3FF297F3B12FF8632C96AF19684C2529F42352420F8E235`; Portable-ZIP SHA-256 `D289C3C06192BFB2ECE7F3C4AA79AA7E11054D13327F15C88504F9FCF897BFB8`.
WORKTREE: Vor Commit nur die oben genannten Quell-, Test- und Koordinationsdateien geändert; lokale Scan-/Testartefakte sind ignoriert.
OPEN: Ausschließlich Tristans visueller Endvergleich des neuen Portable-Builds mit Page 03. Erst danach darf `HOME: ACCEPTED / UI MASTER LOCKED` festgehalten werden. Keine Produktarbeit, kein Merge nach `main` vorher.
NEXT: Tristan öffnet den frischen Portable-Build, prüft Home maximiert, groß, klein und bei sinnvoller Mindestgröße. Bei Zustimmung die Master-Lock-Entscheidung zurückmelden; bei Abweichung genau eine begrenzte visuelle Korrektur nennen.
MODEL_PROFILE: terra
MODEL_REASON: Eng begrenzter finaler Home-Conformance-/Runtime-Pass ohne Produktfunktionsausweitung.
COMPUTER_USE: yes
COMMIT/PR: Commit und Push dieses Handovers auf `dev/v1-foundation` nach erfolgreichem finalem Build-Gate.

# Handoff 2026-08-21 — Home final sidebar and surface master-conformance pass

STATUS: WAITING_FOR_TRISTAN
TASK: Ausschließlich die letzten visuellen Abweichungen zur verbindlichen Page-03-Home-Referenz korrigieren: Sidebar/Navigation/Statusfläche sowie die gemeinsame Card-/Panel-Tonalität. Bereits angenommene Struktur, Typografie, Action-Ausrichtung und Responsive-/Viewport-Verhalten bleiben unverändert.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `docs/AGENT_BASE.md`, `coordination/CURRENT.md`, `coordination/agents/codex.md`.
IMPLEMENTATION: Zentralisierte Midnight-Surface-Tokens (`night`, `deep`, `panel`, `card`, `sidebar`, Linien-/Metallwerte) senken die Helligkeit der gemeinsamen Card-/Panel-Familie und halten Konturen subtil. `RoundedHomeSurface` zeichnet den gemeinsamen Home-Card-/Panel-Perimeter mit echten dezenten Rundungen, während sein unveränderter innerer `ttk`-Body die vorhandenen Labels, Buttons und Grid-Regeln trägt. Die Sidebar verwendet nicht länger native `ttk`-Auswahlbuttons: `SidebarNavItem` zeichnet für jede bestehende Route denselben großzügigen, gerundeten Icon-/Text-Eintrag mit ruhigem Hover sowie einer integrierten blauen Aktivfläche und leichtem Außen-Glow. `SidebarStatusPanel` nutzt die gleiche gerundete, lokale Statussprache. Es gibt keine page-spezifischen Pixelkorrekturen.
SCOPE: Keine Änderung an Seitenreihenfolge, Navigation-Zielen, Datenbindung, Analyzer-/Review-/Tactical-/NetCon-Autorität, Card-Action-Grid, Fonts, Buttonlogik, Scroll-/Viewport-Verhalten oder Produktumfang. Keine neue Funktion, kein neuer Slice und kein Merge nach `main`.
VISUAL_CHECK: Direkte Quell-Sichtprüfung auf der realen Home-Seite: Sidebar ist dunkler integriert; aktive Route zeigt keine klassische rechteckige Windows-Selection mehr, sondern eine abgerundete blaue Flächenhierarchie mit funktionalem Icon-/Text-Abstand. Der lokale/private Statusblock nutzt dieselbe Tonalität. Die sechs Modul-Cards sowie mittleren/unteren Panels zeigen echte dezente Außenrundungen, bleiben vollständig sichtbar und gleich ausgerichtet; die Statuskarten sind als vier kompakte Flächen vollständig sichtbar. Die Akzentlinien und die dunkle Midnight-Trennung zum Hintergrund bleiben erhalten.
VERIFIED: `compileall` PASS; gezielte Analyzer-Shell-Tests 16/16 PASS; vollständiger `pytest` 132/132 PASS; `git diff --check` PASS. Der Build führte die vollständigen 132 Tests erneut mit PASS aus; Abhängigkeitsprüfung (`pip check`) PASS. Frische Portable-EXE praktisch geöffnet: Analyzer-Route, aktive gerundete Sidebar-Navigation und Home-Dashboard mit sechs ausgerichteten Modulactions, mittleren und unteren Panels sichtbar; keine weiße/klassische Auswahlfläche.
BUILD: Frisch erzeugt: `dist/experimental/Improve Yourself Experimental/Improve Yourself Experimental.exe`, `dist/experimental/Improve-Yourself-Experimental-Portable.zip`, `dist/experimental/experimental-build.json`. EXE SHA-256 `29206ECF536ABCD7E0E6A134222E3241260D9D82D77DA35E14679E202613FDB9`; Portable-ZIP SHA-256 `7AAF3F73B760126BE7D36E68CED74ACBD855B9551E131AA0A14123F8E9BD8479`. Kein Installer/Signing, weil kein freigegebener Vertrag vorliegt.
OPEN: Ausschließlich menschlicher finaler Page-03-Sichtcheck durch Tristan.
NEXT: Tristan prüft den frischen Portable-Build gegen den Home-Master auf Sidebar/Status-Komponente und ruhige Midnight-Surfaces; danach `Home: ACCEPTED` oder eine konkrete, begrenzte Restabweichung. Bis dahin keine weitere Produktarbeit.
MODEL_PROFILE: terra
MODEL_REASON: Eng begrenzter visueller Desktop-Conformance-Pass mit gemeinsamer Komponentenbasis und Runtime-/Paket-QA.
COMPUTER_USE: yes
COMMIT/PR: Dieser Handoff ist Teil des gepushten `dev/v1-foundation`-Checkpoints; exakter HEAD steht im Abschlussbericht.
# Handoff 2026-08-22 — External Test Candidate V1 blocker correction

STATUS: WAITING_FOR_TRISTAN
TASK: Den im manuellen Portable-Test gefundenen Release-Blocker im bestehenden Unified-Analyzer-Workflow beheben sowie ausschließlich den Optimizer-Detail-Scroll und das My-Improvement-Text-Clipping korrigieren.
BRANCH: `dev/v1-foundation`
CHANGED: `src/improve_yourself/analyzer_shell.py`, `tests/test_analyzer_shell.py`, `coordination/agents/codex.md`.
ANALYZER FIX: Ein expliziter neuer Demoimport ruft jetzt vor dem Parserlauf `begin_import()` auf und entfernt damit den zuvor aktiven Workflow fail-closed. Übersicht und Analyse zeigen sofort die konkrete ausgewählte Datei, den laufenden lokalen Parse sowie die begründete Sperre von Analyse/Review/Tick-Sprung. Nach bestätigtem Parse werden Demo, Map, Runden, Line-ups, Basisereignisse und Analysebereitschaft aus dem vorhandenen Workflow gezeigt; bei Fehler bleibt die UI eindeutig gesperrt und erklärt den nächsten zulässigen Schritt. Es gibt keine neue Parser-, Rule- oder Replay-Logik.
ANALYZER COMPOSITION: `Analyse starten` und die bestehende CS2-/Review-Aktion stehen jetzt direkt nach Spielerwahl und Profil vor dem Regelblock. Nicht verfügbare Review-Aktionen sind zunächst tatsächlich deaktiviert, statt funktionslos zu wirken; der sichtbare Text erklärt jeweils Import, Parse, Analyse oder Review als aktuellen Zustand.
REAL PORTABLE E2E: Mit der echten lokalen `fut-vs-mouz-m2-ancient.dem` in einer frischen Portable geprüft: Auswahl sichtbar → lokaler Parse sichtbar → **PASS**, `de_ancient`, 18 Runden, 10 Spieler, 3.179 Basisereignisse → Full-Demo-/Profilkonfiguration freigegeben → explizite Analyse gestartet → **54** reale zusammengeführte Szenen → eingebetteter Review mit realen Runden, Ticks und Markern (erste Szene Runde 1, Tick 3654; entry/headshot/kill) → dieselbe Szene erfolgreich an den vorhandenen 2D Tactical Viewer übergeben. Kein Fake-Ergebnis und kein Browser-Hauptworkflow.
OPTIMIZER FIX: Die rechte Detailspalte der gemeinsamen Optimizer-Unteransichten besitzt nun eine eigene sichtbare Scrollbar; untere Bereiche wie `EVIDENZ & GÜLTIGKEIT`, `ÄNDERUNG & WIEDERHERSTELLUNG` und `Technische Details` werden nicht mehr im festen Rounded-Card-Viewport abgeschnitten. System und Graphics wurden praktisch geprüft; Graphics ließ die komplette Detailfläche über den neuen Scrollweg erreichen. Alle Domains verwenden dieselbe Detailkomponente, ohne Rule-/Evidence-Änderung.
MY IMPROVEMENT FIX: Die Vergleichsmetriken verwenden ein gemeinsames Zwei-Spalten-Grid mit reduziertem Innenabstand. Unterhalb enger Breite wechselt die obere Kartenfamilie responsiv von 5 auf 3+2 Karten; dadurch bleiben `AKTUELL` und `VERGLEICH` vollständig lesbar. Im frischen Portable bei Wide-Größe praktisch geprüft.
TESTS: gezielte Shell-Regression **30/30 PASS**; vollständiger `pytest` **190/190 PASS**; `compileall` PASS; `git diff --check` PASS. Der finale Build-Gate führte ebenfalls **190 passed** und `pip check` PASS aus.
BUILD: Frisch erzeugt: `dist/experimental/Improve Yourself/Improve Yourself.exe` (19.884.893 Bytes, SHA-256 `E7CBA731AC9B5AFDE94118B4E6E995DA3495D50D4D170512254E8DAC8643B885`) und `dist/experimental/Improve-Yourself-Experimental-Portable.zip` (168.802.222 Bytes, SHA-256 `FE3FA61CB492FD35D87FDFA85579786096FBD4D33358EDAF87F7975DEB0D9B0D`). Portable enthält die vollständige Runtime; kein Installer wurde hinzugefügt.
KNOWN LIMITS: Der manuelle NetCon-/CS2-Tick-Sprung war nicht Teil dieses erneuten Korrekturtests, weil er zuvor bereits praktisch bestätigt war und keine NetCon-/CS2-Logik verändert wurde. Die vorhandene 2D-Übergabe wurde erneut ausgeführt. Keine neue Funktion, keine Produktregel, kein Optimizer-Apply und keine Benchmark-Arbeit.
NEXT: Tristan führt die erneute funktionale Kandidatenabnahme mit derselben echten Demo durch. Bei bestandenem manuellen CS2-Tick-Sprung kann dieser Build als External Test Candidate freigegeben werden; bei einem reproduzierbaren neuen Kernfehler den konkreten Schritt und die sichtbare Meldung zurückgeben. Bis dahin keine zusätzliche Produkt- oder Polish-Arbeit beginnen.
COMPUTER_USE: yes — frische Portable-Instanzen, echter Demoimport, Analyse, Review, 2D-Übergabe und UI-Checks.
COMMIT/PR: `8309c12 fix: restore portable analyzer workflow`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Final Candidate Recovery

STATUS: WAITING_FOR_TRISTAN
TASK: Aus dem aktuellen `dev/v1-foundation`-HEAD genau einen frischen, extern testbaren Portable Candidate erzeugen und praktisch gegen eine echte lokale CS2-Demo prüfen. Keine neue Produktlogik außerhalb des bestätigten Parser-Status, der finalen Sidebar und der kleinen normalen Seiten-Historie.
BRANCH: `dev/v1-foundation`
SOURCE: Ausgangspunkt war der aktuelle gepushte HEAD `356b90d` plus der Candidate-Fast-Audit; die vorherige `dist/experimental`-Ausgabe wurde nicht als Test- oder Übergabepfad verwendet.
CHANGED:
- `src/improve_yourself/analyzer_shell.py`: finale Sidebar-Reihenfolge **Dashboard → Analyzer → Tactical Replay → My Improvement → Optimizer → Benchmark**; Reports und Settings liegen sekundär unten. Der sichtbare Eintrag lautet nur noch `Optimizer`, der bestehende interne read-only-System-Check/Optimizer-Routenkey bleibt unverändert. Eine kleine `← Zurück`-Historie deckt normale Seitenwechsel ab; Tactical→Review und Optimizer-Detail→Übersicht behalten ihre eigenen Rückwege.
- `src/improve_yourself/analyzer_shell.py`: bestätigter langer lokaler Demo-Parse zeigt nun ehrlich `Datei ausgewählt → Parser läuft → <verstrichene Sekunden>` in Shell-Status und Import-Karte. Der Timer endet sowohl bei Parser-PASS als auch bei Fehler. Keine Prozentwerte, keine Parser-/Rule-/Replay-Änderung.
- `tools/dev/Build-Experimental.ps1`: derselbe bestehende Portable-Pfad akzeptiert optionalen Output-, Archive-, Manifest- und Channel-Namen. Der Standard bleibt unverändert; der externe Candidate erhält einen getrennten Ordner, eindeutige ZIP und ein frisches Manifest.
- `packaging/EXTERNAL_TEST_CANDIDATE_README.txt`: nennt neutral das direkt danebenliegende Build-Manifest statt eines alten Experimental-Dateinamens.
- `tests/test_analyzer_shell.py`: erwartet die freigegebene finale Sidebar-Reihenfolge.
REAL PORTABLE E2E: Im tatsächlich frischen Candidate mit `fut-vs-mouz-m2-ancient.dem` geprüft: Datei sichtbar ausgewählt → laufender Timer sichtbar → Import PASS mit `de_ancient`, 18 Runden, 10 Spielern und 3.179 Basisereignissen → Full Demo / `review_v1` verfügbar → explizite Analyse gestartet und nach beobachteten 19,5 s **54** reale zusammengeführte Szenen → eingebetteter Review, erste reale Situation **Runde 1 · Tick 3654 · 3 Marker** (`entry`, `headshot`, `kill`) → Übergabe derselben Szene an 2D Tactical Replay mit gemeinsamen Tick/Frame → `← Zurück zum Review` zeigt wieder denselben eingebetteten Review. Kein Fake-Ergebnis, kein Browser-Hauptworkflow.
PARSE MEASUREMENT: Der finale Candidate zeigte den Parser-Timer bei 3 s sichtbar; der bestätigte Ergebniszustand wurde nach beobachteten **66,3 s** erreicht. Das ist die gemessene Obergrenze des manuellen Smoke-Intervalls, keine erfundene Leistungskennzahl.
RUNTIME / LAYOUT: Der praktische Candidate-Check lief in einer 1362×892-Runtime und erfüllt damit die angeforderte Mindestbreite/-höhe von 1080×720. Analyzer/Review waren vollständig erreichbar. Graphics Optimizer: die rechte Detailfläche scrollt bis `EVIDENZ & GÜLTIGKEIT` sowie `ÄNDERUNG & WIEDERHERSTELLUNG`; kein abgeschnittener Endbereich. My Improvement: alle fünf oberen Vergleichskarten zeigen `AKTUELL` und `VERGLEICH` vollständig; `POSITIONING / GAME SENSE` wird lesbar umgebrochen. Allgemeines `← Zurück` führte von My Improvement zum letzten Optimizer-Stand; der spezielle Optimizer-Rückweg führte weiterhin korrekt zur Übersicht.
TESTS: gezielte Shell-Regression **30/30 PASS**; vollständige Suite separat **190/190 PASS**; finaler Portable-Build-Gate erneut **190/190 PASS**, `pip check` PASS, `compileall` PASS, `git diff --check` PASS. Ein erster Wiederholungsbuild brach reproduzierbar vor Packaging mit einem einzelnen Windows-Loopback-Socket-Abbruch (`WinError 10053`, 189/190) ab; der isolierte Vollsuite- und der finale Build-Gate liefen danach vollständig grün. Kein Produktfehler wurde daraus abgeleitet oder kaschiert.
BUILD / INTEGRITY: Der einzige Übergabepfad ist `dist/candidates/Improve-Yourself-External-Test-Candidate-V1/Improve-Yourself-External-Test-Candidate-V1.zip`. Das zugehörige `candidate-build.json` meldet Channel `external-test-candidate-v1`; EXE, README und alle Runtime-Dateien sind im ZIP. EXE SHA-256 `3C010663148246577DA21BDC9D0868BDE67C5B0D7781B3AE92C300EAB7899B93` (19.886.361 Bytes); ZIP SHA-256 `DD15490055D9360C8C950CA7AC806216D121DEBC3D4D5F3A17C05D4123A2A8D8` (168.806.253 Bytes). Beide Werte wurden unabhängig erneut gegen das Manifest verifiziert.
KNOWN LIMITS: Kein Installer, Signing oder Update-System. Keine CS2-/NetCon-Tick-Sprung-Wiederholung in diesem Candidate-Recovery-Lauf; der funktionierende lokale Pfad wurde nicht verändert, die geforderte Analyzer→Review→Tactical→Review-Kette dagegen real erneut geprüft. Der Candidate bleibt lokal/read-only.
NEXT: Tristan verteilt oder prüft ausschließlich diesen einen ZIP-Candidate nach `EXTERNAL_TEST_CANDIDATE_README.txt`. Bei einem reproduzierbaren Tester-Kernfehler dessen exakten Schritt, sichtbaren Text und Candidate-Hash zurückgeben; ohne neuen Auftrag keine Produkt-/Polish-/Benchmark-Arbeit beginnen.
MODEL_PROFILE: terra
MODEL_REASON: Eng begrenzte Candidate-Recovery mit lokalem Runtime- und Packaging-Nachweis.
COMPUTER_USE: yes — nur für den realen Portable-Demo-/Review-/Tactical-/Layout-Smoketest.
COMMIT/PR: `5d30047 feat: establish analyzer core foundation`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Demo Pipeline Consolidation & Performance V1

STATUS: WAITING_FOR_TRISTAN
TASK: Den vorhandenen lokalen Demo-Datenpfad auf eine kanonische, hashgebundene Verarbeitung konsolidieren: **Demo → einmal SHA-256 → einmal vollständiger Awpy-Parse → iy.analysis/v1 + iy.replay/v2 → Analyzer / Review / Tactical / Reports**. Keine neue Datenbank, keine zweite Engine und keine Änderung an Analyse-, Szenen- oder Replay-Semantik.
BRANCH / BASE: `dev/v1-foundation`, Ausgangs-HEAD `58fb133e01c52e3baedf161f7acc6ed2a98b1f2c`, Arbeitsbaum vor der Änderung sauber.
REFERENCE DEMO: `fut-vs-mouz-m2-ancient.dem`, 270.062.278 Bytes, vollständiger SHA-256 `c183dd61fc6a619f7af435d45eab374cd6f0097a7bd0da779971b15ef6746f7f`. Dieselbe lokale Referenzdemo wurde für IST-, NACHHER- und Runtime-Prüfung verwendet; sie wird nicht versioniert.
CHANGED:
- `src/improve_yourself/awpy_adapter.py`: `AwpyAdapter.parse_demo()` führt den vollständigen, Replay-kompatiblen Awpy-Parse einmal aus. `adapt()` leitet die bisherige Basisanalyse daraus ab; `parse()` bleibt als selbstständiger Kompatibilitätseinstieg erhalten.
- `src/improve_yourself/service.py` und `src/improve_yourself/replay_builder.py`: akzeptieren optional den bereits gestreamten Quellhash und denselben bereits geparsten Awpy-Context. Eigenständige CLI-/Service-Aufrufe behalten den bisherigen vollständigen lokalen Hash-/Parsepfad.
- `src/improve_yourself/demo_workflow.py`: Quellhash ist gestreamt (kein `read_bytes()` der großen Demo mehr). Der Erstimport validiert Typ/Größe, hasht exakt einmal und leitet `iy.analysis/v1` sowie `iy.replay/v2` aus exakt einem Awpy-Parse ab. Reale monotone Messpunkte `T0…T7` liegen transparent im lokalen Workflow-Manifest (`iy.demo_timing/v1`); keine Prozentwerte, Restzeitschätzungen oder Telemetrie.
- `src/improve_yourself/demo_workflow.py`: Hashgebundener Reuse akzeptiert ausschließlich ein vollständig local-validiertes `iy.demo_workflow/v1` mit gleichem vollständigem Quellhash, passender Awpy-/Replay-/Workflow-Version, gültiger Analyse, erforderlichen Artefakten und sämtlichen Replay-Chunk-Hashes. Jede Abweichung fällt fail-closed auf den normalen Neuimport zurück.
- `src/improve_yourself/demo_workflow.py` und `src/improve_yourself/analyzer_shell.py`: Der native Tactical-Pfad bleibt direkt `analysis-flow.json + iy.replay/v2`. `tactical-replay.html` wird nicht mehr synchron bei jeder Analyse erzeugt; der bestehende Browser-Fallback erzeugt ihn erst bei einem expliziten Review-/Tactical-HTML-Export aus demselben kanonischen Datensatz.
- `tests/test_demo_workflow.py`: deckt einmaligen Quellhash/Parse, die realen Timing-Phasen, validierten Reuse-fall und fail-closed Invalid-/Missing-Manifest sowie Lazy-Tactical-Export ab.
REAL MEASUREMENT (T0 → T6, identische Demo):
- IST vor der Konsolidierung: **56,024982 s**. Quellhash statisch dreifach im Workflowpfad (Workflow, Basisanalyse, Replay) und Awpy-Parse zweimal (Basisanalyse + Replay).
- NACHHER final: **52,698433 s**, genau **1** vollständiger Quellhash und genau **1** Awpy-Parse. Die gespeicherten realen Phasen: T1 0,000162 s, T2 0,161776 s, T3 0,162488 s, T4 2,970903 s, T5 51,899651 s, T6 51,899652 s.
- Explizite Analyse T6 → T7: **6,612436 s**; Ergebnis `READY_FOR_REVIEW`, **54** reale zusammengeführte Szenen. Bewusster HTML-Tactical-Export (nur Fallback): **6,596054 s**. Derselbe validierte Workflow wurde danach in **5,816716 s** wiederverwendet, ohne erneuten Parse.
- Aussagegrenze: Die moderate T0→T6-Verbesserung wird nicht als pauschale Performancebehauptung ausgegeben. Der messbare Rest liegt in sicherer Erzeugung, Komprimierung und Validierung der 18 Replay-Chunks; diese Integritätsarbeit wurde bewusst nicht abgeschaltet.
DATA / E2E PROOF: Der finale lokale Neuimport ergab unverändert `de_ancient`, 18 Runden, 10 Spieler, 3.179 grundlegende Events und anschließend 54 Szenen. In der praktisch geöffneten lokalen Shell: Auswahl → sichtbarer Importstatus `Datei ausgewählt · Parser läuft · <verstrichene Sekunden>` → Parser-PASS/Analysebereitschaft → Full Demo / `review_v1` → Analyse → eingebetteter Review → reale erste Szene **Runde 1 · Tick 3654 · 3 Marker** (`entry`, `headshot`, `kill`) → 2D Tactical derselben Szene / desselben Ticks → `← Zurück zum Review`. Der Browser war nicht Hauptworkflow. Keine CS2-/NetCon-Logik wurde verändert oder in diesem Pass erneut ausgelöst.
VERIFIED: neue gezielte Pipeline-/Shell-/Replay-/Embedded-Tests **64/64 PASS**; vollständige Suite **194/194 PASS**; `compileall` PASS; `git diff --check` PASS. Lokale Runtime-Prüfung mit Computer Use nur für Import/Analyse/Review/Tactical; keine System- oder Netzwerkautorität.
FAIL-CLOSED / LIMITS: Manipulierte bzw. unvollständige Reuse-Artefakte werden nicht geöffnet, sondern normal neu verarbeitet; fehlende/unklare Hardware oder Analyzerdaten werden nicht ergänzt. Komprimierte `.dem.zst`/`.dem.bz2` verwenden im neuen Erstimport ebenfalls nur eine Materialisierung, weil Parse/Analyse/Replay denselben Context teilen; die vorhandene Fixture-/Importer-Regression bleibt grün. Kein neuer Rule-/Score-/Coaching-/Replay-/Map-/Optimizer-/Benchmark-Slice, keine Datenbank und keine Telemetrie.
NEXT: Tristan prüft diesen gepushten Konsolidierungs-Checkpoint anhand des neuen Handoffs. Als **einziger** zulässiger Folgepunkt ohne neue Produktsemantik bleibt bei Bedarf ein gezielter, gemessener Replay-Chunk-I/O-Optimierungsauftrag; keine weitere automatische Optimierung.
MODEL_PROFILE: terra
MODEL_REASON: Bestehenden Datenvertrag und fail-closed Integritätsgrenzen konsolidieren, real messen und ohne semantische Änderung regressionsprüfen.
COMPUTER_USE: yes — ausschließlich für den lokalen echten Analyzer→Review→Tactical→Review-Runtime-Nachweis.
COMMIT/PR: `a9b833a perf: consolidate demo pipeline`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Improve Analyzer Core Foundation V1

STATUS: WAITING_FOR_TRISTAN
TASK: Den bestehenden, einmalig geparsten lokalen Demo-Pfad unter den verbindlichen Core-Vertrag ziehen: **Analyzer → AnalysisRequestV1 → AnalyzerCore → AwpyAdapter → Raw Parser Result → Validator/Normalizer → ImproveMatchDataV1 → AnalyzerDataHub**. Die bestehende objektive Analyse-, Szenen-, Review- und Replay-Semantik bleibt unverändert.
BRANCH / BASE: `dev/v1-foundation`, Ausgangs-HEAD `cceb6f9`.
CHANGED:
- `docs/ANALYZER_CORE_FOUNDATION_V1.md`: verbindlicher, implementierter V1-Vertrag mit Grenzen, Schemas, technischen Gates und Hub-Projektionen.
- `src/improve_yourself/analyzer_core.py`: `AnalysisRequestV1` (`iy.analysis_request/v1`), expliziter `METRICS_V1`-Vertrag (`iy.metrics/v1`), `ValidationReportV1`, `ImproveMatchNormalizer`, `ImproveMatchDataV1` (`iy.improve_match_data/v1`) und der einzige Produktpfad, der einen `AwpyAdapter` für einen Request koordiniert.
- `src/improve_yourself/analyzer_data_hub.py`: rein lesender, fail-closed Hub mit den klaren Projektionen `overview`, `analysis` und `replay`; kein Parser und keine Raw-Awpy-Exposition.
- `src/improve_yourself/demo_workflow.py`: persistiert `improve-match-data-v1.json` und `validation-report-v1.json`, bindet Request/Hash/Replay zusammen und akzeptiert Reuse nur mit beiden validierten Core-Artefakten.
- `src/improve_yourself/analyzer_shell.py`: öffnet Workflows erst nach bestehender Integritätsprüfung **und** validiertem Match Data; der Controller hält den Hub als Analyzer-Dateneingang. Keine UI-/Regeländerung.
- `src/improve_yourself/service.py`, `replay_builder.py`, `replay.py`: keine Produktmodule importieren Awpy direkt mehr. Standalone-Pfade gehen über den Core; der Adapter bleibt die alleinige Awpy-Importgrenze.
- `tests/test_analyzer_core.py`, `tests/test_demo_workflow.py`, `tests/test_analyzer_shell.py`: Request-/Schema-/Hub-Projektionen, Unknown/fail-closed-Verhalten, neue zwingende Workflow-Artefakte und Shell-Validierung regressionsgesichert.
CORE CONTRACT: `METRICS_V1` deklariert Match-/Map-/Teams-/Spieler-/Runden-Fakten, Tick-/Zeit-/State-/Positions-/Blickwinkel-Klassen, Kills/Deaths/Assists/Damage/Shots/Weapons/Utility/Grenades/Smokes/Infernos/Bomb/Footsteps sowie Economy. Es behauptet keine Verfügbarkeit: der Parser meldet vorhandene und nicht vorhandene Kanäle explizit. Neue Metriken benötigen eine explizite Contract-Erweiterung oder V2.
VALIDATION: Unlesbarer Header, fehlende referenzierbare Runden, ungültige Tickrate und das Fehlen sämtlicher referenzierbarer Kills blockieren fail-closed. Warm-up-/unzugeordnete Ereignisse werden als `unknown_records` gezählt und ohne Deutung verworfen; sie werden weder erraten noch zu Szenen gemacht. Doppelte Events werden gezählt und verworfen. Die bestehende Chunk-/Hashvalidierung von `iy.replay/v2` bleibt unverändert aktiv.
REAL E2E: Mit `fut-vs-mouz-m2-ancient.dem` (SHA-256 `c183dd61fc6a619f7af435d45eab374cd6f0097a7bd0da779971b15ef6746f7f`) in einem frischen lokalen Lauf geprüft: `READY_FOR_REVIEW`; `iy.analysis_request/v1`, `iy.metrics/v1`, `iy.improve_match_data/v1` und `iy.validation_report/v1` PASS vorhanden; `de_ancient`, **18** Runden, **10** Spieler, **124** referenzierbare Kill-Datensätze, **4** unbekannte/unzugeordnete Ereignisse verworfen, **0** Duplikate, anschließend die unveränderte Analyse mit **54** realen zusammengeführten Szenen. Ein anschließend geöffneter existierender Workflow lieferte über `AnalyzerDataHub` wieder `de_ancient` und dieselben 10 Spieler. Kein Fake-Resultat, keine neue Parser- oder Replay-Engine.
VERIFIED: gezielte Core-/Workflow-/Shell-Regression **37/37 PASS**; vollständige Suite **197/197 PASS**; `compileall` PASS; `git diff --check` PASS. Der reale Lauf wurde getrennt von Fixtures nach geschriebenem `demo-workflow.json` und validiertem Hub geprüft.
KNOWN LIMITS: Die Core-Validierung ist eine technische Datenqualitätsgrenze, keine Gameplay-Bewertung. `iy.replay/v2` bleibt die bestehende kanonische Replay-Wahrheit; Match Data verweist/projiziert sie, statt einen zweiten Replay-State zu erzeugen. Es wurde keine Tactical-/Review-/3D-/POV-/Report-/Optimizer-/Benchmark-Funktion begonnen.
NEXT: Tristan prüft den Core-Contract-Checkpoint. Ein möglicher nächster fachlicher Schritt benötigt eine explizite Freigabe zur Erweiterung von Metrics V1 oder zu einem klar getrennten Consumer-Slice; ohne Freigabe keine weitere Analyse-/Replay-/Benchmark-Arbeit.
MODEL_PROFILE: terra
MODEL_REASON: Versionierter, fail-closed Core-Schnitt und reale E2E-Validierung über einen bestehenden großen Demo-Pfad.
COMPUTER_USE: no
COMMIT/PR: `5d30047 feat: establish analyzer core foundation`, gepusht nach `origin/dev/v1-foundation`.

# Handoff 2026-08-22 — Analyzer Core Foundation V1 Clarification Pass

STATUS: WAITING_FOR_TRISTAN
TASK: Ausschließlich drei unscharfe Stellen des bestehenden Core-Vertrags präzisieren: tatsächliche Metrics-V1-Datenoberfläche, consumer-neutrale technische Validation und minimale versionierte Consumer-Projektionen. Kein neuer Parser, keine neue Analyse-/Replay-Semantik und keine neue Produktfunktion.
BRANCH / BASE: `dev/v1-foundation`, Ausgangs-HEAD `e510c1d`.
DECISION: Variante B ist jetzt explizit umgesetzt. Kleine, produktrelevante Facts liegen in `iy.metrics/v1` inline; große Tick-/State-/Positions-/Blickwinkel-/Utility-Daten bleiben genau einmal im bestehenden, hash-validierten `iy.replay/v2` und erscheinen in Metrics V1 nur als eindeutige versionierte `replay_reference`. Metrics V1 ist damit Datenort- und Availability-Vertrag, keine Wunschliste möglicher Awpy-Spalten.
CHANGED:
- `src/improve_yourself/analyzer_core.py`: `METRICS_V1_FIELDS` benennt jetzt konkrete Inline-Projektionen (`iy.metrics.match/v1`, `iy.metrics.rounds/v1`, `iy.metrics.events/v1`) und die kanonische `iy.replay/v2`-Referenz. `channel_availability` führt `available`, `unavailable` und `unknown` ehrlich; der Validation Report führt zusätzlich technische Capabilities.
- `src/improve_yourself/analyzer_core.py`: Fehlende optionale Gameplay-Kanäle, einschließlich eines killfreien aber strukturell gültigen Matches, führen nicht mehr zu einem Core-FAIL. Referenzierbare Runden, lesbarer Header, nicht widersprüchliche Tickgrenzen, valide Quell-/Replay-Bindung und der Aufbau normalisierter Daten bleiben die fail-closed Core-Grenze. Warm-up/unzugeordnete Events bleiben `unknown_records` und werden ohne Deutung verworfen.
- `src/improve_yourself/analyzer_data_hub.py`: zusätzlich zu den technischen Kompatibilitätsprojektionen `overview`/`analysis`/`replay` existieren minimale, versionierte Projektionen: `iy.analyzer_projection/v1`, `iy.tactical_projection/v1`, `iy.review_projection/v1`, `iy.report_projection/v1`. Tactical erhält Identität/Runden-Kontext plus die ausdrückliche Replay-V2-State-Referenz, nicht Raw-Awpy oder eine doppelte Tickkopie. Jede Abfrage liefert eine mutationsisolierte Kopie.
- `docs/ANALYZER_CORE_FOUNDATION_V1.md`: Contracts, Datenorte, PASS/FAIL-Grenze, Consumer-Verteilung und Scope entsprechend präzisiert.
- `tests/test_analyzer_core.py`: regressionssichert den tatsächlichen Metrics-Vertrag, `kills: unavailable` bei Core-PASS, strukturell unbrauchbare Runden als FAIL, alle vier Consumer-Schemas, Mutationsisolation, Hub fail-closed und den statischen Guard, dass nur `awpy_adapter.py` Awpy importiert.
REAL E2E: Frischer Lauf mit `fut-vs-mouz-m2-ancient.dem` (SHA-256 `c183dd61fc6a619f7af435d45eab374cd6f0097a7bd0da779971b15ef6746f7f`) erreichte `READY_FOR_REVIEW`: `iy.improve_match_data/v1`/`iy.metrics/v1`/Validation PASS, `de_ancient`, 18 Runden, `kills: available`, `footsteps: available`, explizite `iy.replay/v2`-Referenz, 4 unbekannte Records ohne Interpretation und die unveränderten 54 realen Szenen. Dieselben Match Data erzeugten danach die vier versionierten Hub-Projektionen ohne erneuten Parserlauf.
VERIFIED: gezielte Core/Workflow/Shell/Replay-Regression **47/47 PASS**; vollständige Suite **199/199 PASS**; `compileall` PASS; `git diff --check` PASS. Arbeitsbaum vor Handoff enthielt ausschließlich die vier oben genannten Clarification-Dateien.
KNOWN LIMITS: Availability ist kein Gameplay-Urteil. `via_replay_v2` bedeutet ausschließliche Datenlage im bestehenden kanonischen Replay, nicht stillschweigend verfügbare State-Daten. Noch keine Consumer-UI, Tactical-/Review-/Report-Erweiterung, neue Regel, Parser-, NetCon-, Optimizer- oder Benchmark-Arbeit.
NEXT: Tristan prüft den präzisierten Core-Vertrag. Eine spätere neue Consumer-Funktion muss ausschließlich eine der versionierten Hub-Projektionen verwenden oder vorab einen expliziten Projection-Contract erhalten; ohne Freigabe keine Folgearbeit.
MODEL_PROFILE: terra
MODEL_REASON: Enger Contract-/Fail-closed-Pass mit realem Demo-E2E-Nachweis und ohne Produktsemantik-Ausweitung.
COMPUTER_USE: no
COMMIT/PR: `acb885b refactor: clarify analyzer core contracts`, gepusht nach `origin/dev/v1-foundation`.
