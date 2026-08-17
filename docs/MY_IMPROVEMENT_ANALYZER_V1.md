# My Improvement — Analyzer-Zielbild und lokale Grundlage

## Zugehörigkeit und Grenze

My Improvement ist ein Teil des **Demo Analyzers**, nicht des System Checks oder
Optimizers. Beide Auswertungen verwenden künftig dieselben neutralen,
versionierten Analyzer-Fakten:

```text
Demo -> neutrale Fakten -> Match Review
                        -> My Improvement (eigener Spieler)
```

Der aktuelle V1-Analyzer erzeugt noch keine ungesicherten Aim-, Sichtbarkeits-
oder Input-Scores. Ein einzelner Wert oder Hinweis ist niemals ein Cheat- oder
Hack-Nachweis.

## Versionierte lokale Datenbasis

Die nächste nicht-invasive Ausbaustufe verwendet ausschließlich reduzierte,
lokale Datensätze:

- `iy.improvement_match/v1`: Source-Hash zur Duplikaterkennung, Datum soweit
  zuverlässig vorhanden, Map, stabile eigene Spielerkennung, eigene
  Matchfakten, verfügbare Metriken, Datenqualität, Analyzer-/Metrikversion und
  optionale Referenzen auf Review-Szenen.
- `iy.improvement_history/v1`: lokales Profil und höchstens 60 dieser
  reduzierten Matchdatensätze. Bei Match 61 rotiert nur der älteste
  **reduzierte** Datensatz; Rohdemos gehören nicht in die Historie oder ein
  Backup.

Eine lokale Profilbezeichnung ist frei wählbar. Die Spielerzuordnung erfolgt
später entweder freiwillig über einen Steam-Profil-Link ohne Login oder über
eine einmalige Auswahl aus einer geeigneten Demo. Ein Nickname allein ist kein
dauerhafter Schlüssel.

## Metrikplan und Evidenzgrenzen

| Bereich | V1-Fakten / späteres Ziel | Grenze |
| --- | --- | --- |
| Aim | Crosshair Placement, Time to Damage, Spray Control | Erst nach belastbarer Sichtbarkeits-, Geometrie- und Input-Definition; keine erfundenen Schwellen. |
| Duels | Opening Duel, First Damage/Exchange, Trade, Traded, Duel Outcome | Nur aus eindeutig zuordenbaren Ereignissen. |
| Utility | Flash-/HE-/Feuer-Fakten und Nutzung; Smoke als Nutzung/Position | Keine Smoke-Qualitätswertung ohne belastbare Sichtlinien-/Timing-Methode. |
| Kontext | K/D, ADR, HS-% und weitere vorhandene Matchwerte | Kontext, kein alleiniger Aim- oder Qualitätsnachweis. |

Geplante Vergleiche: aktuelles Match, persönliche Basis bis 30 Matches,
Trend bis 60 Matches und nur bei belegter Quelle eine FACEIT-Level-10-Referenz.
Bei fehlender Datenbasis wird z. B. `8/30 Matches — eingeschränkte Trendbasis`
angezeigt; eine Level-10-Referenz wird niemals erfunden.

## Nutzerziel

My Improvement soll wenige nachvollziehbare Aussagen liefern: Was lief gut,
was entwickelt sich, was sollte überprüft/trainiert werden und welche echten
Szenen belegen den Hinweis. Cloud-Sync, vollständige Demoablage, 3D/POV und
generische Coaching-Sätze sind nicht Bestandteil dieser Grundlage.
