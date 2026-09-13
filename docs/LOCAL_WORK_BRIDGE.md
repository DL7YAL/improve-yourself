# Gemeinsamer lokaler Arbeitsstand und GitHub

## Verbindlicher Ablauf

Beide Zugänge öffnen denselben explizit festgelegten Windows-Checkout.
Die gleiche Maschine oder Installation allein stellt das nicht sicher.
BRIX1 ist der vom Benutzer benannte gemeinsame Arbeitsbereich; BRIX2 bezeichnet
den zweiten Zugang, nicht automatisch einen zweiten identischen Dateibestand.
Die Brücke wird zuerst getestet und danach im Windows-Checkout aktiviert.

Ein schreibender Auftrag pro gemeinsamem Git-Repository einschließlich seiner
Worktrees. Die kooperative Sperre gilt für Teilnehmer, die diese Brücke benutzen;
sie verhindert keine manuellen Editoränderungen oder Git-Befehle anderer Prozesse.
Einzelprojekte dürfen eigene Repositories und lokale Sicherungsordner verwenden.
Ihre Ergebnisse kommen erst nach einer geprüften Integration im Hauptstand an.
Alte Checkouts werden nicht automatisch zusammengeführt oder entfernt.

Mindestens die letzten **20 % des verfügbaren Nutzungslimits** bleiben für
Kontrolle, Tests, lokale Sicherung, Commit, Push und Handoff reserviert.
Keine neue Featurearbeit in dieser Reserve. Ein Merge erfolgt nur bei gesonderter
Freigabe. Das Werkzeug misst keine Kontingente und fängt kein Chat-Ende ab.
Bei unbekanntem Kontingent häufig kleine Zwischenstände erstellen; jeder
Auftragswechsel braucht einen dokumentierten Abschluss oder offenen Blocker.

## Windows-Aufruf (Python 3.10+ und Git)

Im autoritativen Checkout auf einem freigegebenen `codex/`-Arbeitsbranch:

```powershell
python .\tools\dev\work_bridge.py start --owner Brix1 --backup-root 'D:\ProjectBackups\ImproveYourself'
python .\tools\dev\work_bridge.py status
python .\tools\dev\work_bridge.py checkpoint --session <SESSION-ID>
```

Alternativ: `Work-Bridge.ps1 -Action status -Repo <Checkout> -PythonExe <python.exe>`.
Für Start zusätzlich `-Owner` und `-BackupRoot`, für Übergabe `-Session` verwenden.
Beide Zugänge verwenden dieselbe Installation, Checkout-Adresse und dieselbe
Sitzungs-ID nur nach ausdrücklicher Übergabe. Die ID ist ein Koordinationsmerkmal,
keine Authentifizierung. Eine offene Sitzung verhindert einen zweiten Start.

Start sichert vor dem Fetch. Bei lokalen Änderungen oder abweichendem Remote-HEAD
stoppt er; kein automatischer Pull, Reset oder Konfliktentscheid. Die Sitzung
bleibt zur Sicherung/Übergabe offen. Nach Konfliktklärung kann in dieser Sitzung
weitergearbeitet werden, sobald ein erneuter manueller Vergleich sauber ist.

Vor Abschluss: Änderungen und neue Dateien prüfen, passende Tests ausführen,
Handoff im Repository schreiben und nur einzeln freigegebene Pfade committen.
Kein blindes `git add .`. Danach:

```powershell
$reviewed = git rev-parse HEAD
python .\tools\dev\work_bridge.py finish --session <SESSION-ID> --reviewed-head $reviewed --validation 'Tests: Ergebnis und Einschränkungen' --handoff 'docs/<auftragsbericht>.md'
```

Die Prüfung verlangt einen sauberen Checkout und den exakt freigegebenen Commit.
Sie pusht nur den Arbeitsbranch ohne Force und liest den Remote-Hash zurück.
Validierungsangabe und Handoff sind Angaben des Bearbeiters; die Brücke führt
keine projektspezifischen Tests aus und ersetzt keinen Secret-Review.
Wenn Push/Prüfung scheitert, bleibt die Sitzung offen und die lokale Sicherung
erhalten. Erst `SYNCED` bestätigt den GitHub-Abgleich. Kein automatischer Merge.

## Sicherung und Wiederherstellung

Jeder Start, Zwischenstand und Abschluss erzeugt einen neuen Ordner außerhalb
des Checkouts mit `history.bundle`, `working.zip` und bei Erfolg `manifest.json`.
Das Bundle enthält Git-Referenzen und Historie; das ZIP enthält die gespeicherten
versionierten und nicht ignorierten neuen Dateien. Gelöschte Pfade und SHA-256
werden im Manifest erfasst. Änderungen während der Sicherung führen zum Abbruch.
Unvollständige Sicherungen ohne Manifest gelten nicht als geprüft.

Ignorierte Dateien, externe Assets und ungespeicherte Editorpuffer sind ausgeschlossen.
Große Blender-/CS2-Daten benötigen zusätzlich eine eigene lokale Assetsicherung;
ab 512 MiB Dateisumme stoppt diese erste Werkzeugversion. Keine automatische
Backup-Löschung. Sicherungsordner lokal zugriffsbeschränken und für Ausfallschutz
zusätzlich auf ein anderes Laufwerk sichern. Die Backups können private Daten
aus der Git-Historie enthalten und dürfen nicht nach GitHub hochgeladen werden.

Zur Wiederherstellung in einen **neuen leeren Ordner** aus dem Bundle klonen,
auf den Manifest-Commit wechseln und dort die gesicherten Arbeitsdateien
wiederherstellen. Gelöschte Pfade anhand des Manifests prüfen. Erst nach Vergleich
den wiederhergestellten Ordner übernehmen; nie den aktiven Checkout blind resetten.
Das ZIP speichert Inhalte, keine exakte Git-Staging-Aufteilung oder Dateirechte.

Nach Absturz: Sperre prüfen und Beteiligte kontaktieren. Nicht automatisch stehlen.
Ein Operator kann bei nachweislich beendeter Arbeit die Sperrdatei im Git-Verzeichnis
unter einem Archivnamen umbenennen. Backups und Verlauf bleiben erhalten.

## Einführungsstand

Windows-Kerntest des Commits `1717316`: vom Benutzer am 2026-09-13 ausgeführt,
Git 2.55.0.windows.5 und Python 3.13.15, alle drei Integrationstests PASS.
Die JSON-Ergebnisdatei wurde lokal zurückgelesen. Dies prüft weder Windows-
Aufgabenplanung noch GitHub-SSH. Der erweiterte Linux-Test umfasst vier Tests.

### 30-Minuten-Sicherung

`Install-WorkBridgeSchedule.ps1 -Repo <gemeinsamer Checkout> -PythonExe <python.exe>`
registriert eine Windows-Aufgabe für den angemeldeten Benutzer. Sie ruft alle
30 Minuten `auto-checkpoint` auf und wird einmal sofort gestartet. Ohne aktive
Brückensitzung meldet sie IDLE; sie erzeugt dann keine Sicherung. Nach `start`
sichert sie dieselbe Sitzung einschließlich uncommitteter, nicht ignorierter
Dateien. Sie führt keine Commits, Pushes oder Merges aus.

Die geprüfte Runtime wird unter LocalAppData in einen eindeutigen Ordner kopiert.
`latest-result.json` enthält das jüngste Resultat, `failures.log` die Fehler.
Keine automatische Benachrichtigung ist eingerichtet. Der Operator muss Fehler
prüfen. Eine belegte Sperre oder sich gleichzeitig ändernde Datei kann einen
Lauf abbrechen; die vorherige Sicherung bleibt erhalten. Nach einem harten
Prozessabbruch kann eine manuell zu prüfende Sperre verbleiben.
Die Aufgabe läuft nur während der Benutzer angemeldet ist; Schlafzustand und
ausgeschalteter Rechner erlauben keine garantierten 30-Minuten-Sicherungen.
Ein vorhandener gleichnamiger Zeitplan wird nicht überschrieben.
Pause: `Disable-ScheduledTask -TaskName ImproveYourself-WorkBridge-30min`.

Windows-Zeitplaninstallation und tatsächliche Ausführung bleiben bis zum
Einrichtungstest UNVERIFIED. Vor produktiver Nutzung beide Zugänge explizit
auf denselben Windows-Checkout richten und dort `start` erfolgreich ausführen.

Unter Linux meldet BRIX1 viele Änderungen, deren getrackter Diff mit
`--ignore-space-at-eol` leer ist. Zeilenenden mit Git for Windows prüfen,
bevor daraus Commits erzeugt werden. Weitere ältere Checkouts existieren.
Diese Einführung verändert keine dieser Arbeitskopien und vereinheitlicht
deren Dateien nicht automatisch. Windows-Ausführung und beide Zugänge müssen
vor produktiver Nutzung am selben Pfad nachgewiesen werden.
