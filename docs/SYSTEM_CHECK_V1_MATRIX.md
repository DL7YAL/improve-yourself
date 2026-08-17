# System Check / Optimizer Input V1 — Soll-/Ist-Matrix

Stand: 2026-08-17. Die Klassifikation ist Teil des System-Check-Vertrags und
wird zusätzlich an `iy.optimizer_input/v1` weitergegeben. „Erkannt“ ist nicht
gleichbedeutend mit „bewertet“.

| V1-Punkt | Aktueller Vertrag | Klassifikation | Bewertungsgrenze |
| --- | --- | --- | --- |
| CPU | Name und logische Prozessoren aus Windows | zuverlässig automatisch geprüft | Keine Benchmark- oder OC-Empfehlung. |
| RAM | installierte Gesamtkapazität, 16-GB-V1-Schwelle | zuverlässig bewertet | Kapazität, nicht Takt/Timings. |
| Mainboard | Hersteller und Produkt | zuverlässig automatisch geprüft | Keine geratene Chipsatzzuordnung. |
| BIOS | Version und Datum | zuverlässig automatisch geprüft | Kein Online-BIOS-Vergleich. |
| Windows | Produkt, Version und Build | zuverlässig automatisch geprüft | Keine Windows-Tweak-Bewertung. |
| GPU | Adapter und installierter Treiberversionswert | zuverlässig automatisch geprüft | Herstellerneutraler Inventarpfad. |
| GPU-Treiber-Aktualität | AMD RX 7900 XTX gegen feste offizielle AMD-Seite | zuverlässig bewertet, sonst unbekannt | Nur exakt zugeordnete Produktseite; kein Download/Install. |
| Globale GPU-/Treiberoptionen | Latenz, Upscaling, Frame-Pacing, Sync, Schärfung, Qualitäts-Overrides | technisch untersucht, nicht belastbar auslesbar | Keine lokale, dokumentierte read-only Wertquelle in dieser V1. |
| CS2-Spielprofil | AMD-CS2-Beobachtungsartefakt und mögliche Profilwerte | Anwendung beobachtet; Profilwert technisch untersucht, nicht belastbar auslesbar | Beobachtung beweist kein Profil und kein Override. |
| Effektiver GPU-Wert | globaler Wert plus CS2-Override | technisch untersucht, nicht belastbar auslesbar | Keine Heuristik aus UMD, Registry oder Binärdateien. |
| Chipsatz | exakt Gigabyte X870 Gaming X WiFi7 → AMD X870 | zuverlässig automatisch geprüft, sonst unbekannt | Mapping ausschließlich mit Herstellerbeleg. |
| Chipsatztreiber | installierte AMD-Chipsatzsoftware gegen offizielle AMD-X870-Seite | zuverlässig bewertet, wenn Chipsatz exakt zugeordnet | Ohne Zuordnung oder offizielle Version unbekannt. |
| Aktive Auflösung | aktive Anzeige aus Windows | zuverlässig automatisch geprüft | Keine Skalierungs-/Renderauflösungsannahme. |
| Aktive Bildwiederholrate | aktive Anzeige aus Windows | zuverlässig bewertet | Unter 120 Hz erhält verständlichen Prüfhinweis. |
| Monitorerkennung | WMI-Benutzerfreundlicher Monitorname | zuverlässig automatisch geprüft, sonst unbekannt | Fehlender Name bedeutet nicht fehlender Monitor. |
| Secure Boot | `Confirm-SecureBootUEFI`, sicherer Registry-Fallback | zuverlässig automatisch geprüft, sonst unbekannt | Unbekannt wird niemals als deaktiviert ausgegeben. |
| TPM / TPM 2.0 | `Get-Tpm`, sicherer `tpmtool`-Fallback | zuverlässig automatisch geprüft, sonst unbekannt | Vorhanden und bereit nur bei positiver Evidenz. |
| Anti-Cheat-Readiness | Aggregat aus Secure Boot und TPM 2.0 | zuverlässig bewertet für genau diese Kriterien | Kein pauschales „Anti-Cheat Ready“. |
| NVIDIA-Profilerfassung | gemeinsame provider-neutrale Matrix/Optimizer-Felder | noch nicht implementiert auf diesem AMD-System | Keine erfundenen NVIDIA-Werte oder Simulation. |

## AMD-Adrenalin: nachgewiesene Quellen und Grenze

AMD dokumentiert globale Grafikoptionen und Anwendungsprofile; ein
spielbezogener Override soll den globalen Wert übersteuern. Die relevanten
Kategorien werden deshalb im provider-neutralen `setting_matrix` jeweils als
`global_value`, `cs2_override` und `effective_value` geführt.

Die lokale read-only Untersuchung hat folgende Quellen voneinander getrennt:

| Quelle | Befund | Als Ist-Wert verwendbar? |
| --- | --- | --- |
| AMD Display-Driver-UMD-/Registry-Konfiguration | Werte liegen teils binär bzw. ohne dokumentierte Zuordnung vor | Nein |
| `AMD CN GameReport/cs2.exe/gpa.bin` | CS2 wurde von AMD beobachtet | Nur Anwendung beobachtet; kein Profilwert |
| `AMD CN steamdata/730.json` | Steam-Store-Metadaten für App 730 | Nein, kein Treiberprofil |
| lokale AMD-Installationsdateien | GameConfig ist ein Katalog unterstützter Spiele-/Spieldateien | Nein, kein wirksamer Nutzerwert |
| AMD ADLX | AMD dokumentiert eine native SDK-Schnittstelle; diese V1 bringt keine getestete native Read-only-Bindung mit | Nein |
| AMD Software „Snap Settings“ | AMD dokumentiert manuellen Export eines Einstellungs-Snapshots als ZIP | Potenzieller, ausdrücklich bereitgestellter Folgeinput; in V1 noch kein dokumentierter Parservertrag |

Damit bleibt der korrekte V1-Status für jede aufgeführte AMD-Option
`technically_investigated_not_reliably_readable`. Das verhindert eine falsche
Optimizer-Bewertung. Ein späterer, enger Folgeauftrag kann einen AMD-
Snapshot-Parser nur anhand einer dokumentierten Datei-/Feldspezifikation und
eines vom Nutzer bewusst exportierten Beispiels einführen. Der Workflow wäre
dann: Nutzer exportiert read-only einen Snapshot → Improve liest die übergebene
Kopie lokal → Improve vergleicht und zeigt Ergebnis. Improve importiert den
Snapshot nicht zurück in AMD Software und ändert keine AMD-Einstellung.

## Optimizer-Eingabe

`iy.optimizer_input/v1` enthält für jeden Check ein `planning_item` mit:

- Ist-Zustand (`observed_state`), technischem Status und Klassifikation;
- Nutzerbewertung, Priorität, Relevanz und konkreter Empfehlung;
- begrenzter Evidenz/Quelle;
- Read-only-/No-Apply-Policy.

Es enthält keine Demo-, Replay- oder Analyzer-Daten. `input_complete` bedeutet
nur, dass der explizite System-Check vertragsgerecht übertragen wurde — nicht,
dass jeder Hardware- oder Profilwert automatisch auslesbar ist.
