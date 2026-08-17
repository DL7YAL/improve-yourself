import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const [analysisArg, outputArg] = process.argv.slice(2);
if (!analysisArg || !outputArg) {
  throw new Error("Usage: node Build-AnalyzerExcelReport.mjs <analysis.json> <report.xlsx>");
}

const analysis = JSON.parse(await fs.readFile(analysisArg, "utf8"));
if (analysis.schema !== "iy.analysis/v1") throw new Error("expected iy.analysis/v1");
if (!Array.isArray(analysis.kills) || !Array.isArray(analysis.multikills)) throw new Error("analysis lacks kills or multikills");

const nonMatchKills = analysis.kills.filter((kill) => !Number.isInteger(kill.round_number) || kill.round_number < 1);
const nonMatchScenes = analysis.multikills.filter((scene) => !Number.isInteger(scene.round_number) || scene.round_number < 1);
const kills = analysis.kills.filter((kill) => Number.isInteger(kill.round_number) && kill.round_number >= 1).sort((a, b) => a.round_number - b.round_number || a.tick - b.tick);
const scenes = analysis.multikills.filter((scene) => Number.isInteger(scene.round_number) && scene.round_number >= 1).sort((a, b) => a.round_number - b.round_number || a.first_tick - b.first_tick);
const players = [...new Set(kills.flatMap((kill) => [kill.attacker, kill.victim]).filter(Boolean))].sort((a, b) => a.localeCompare(b, "de"));
const rounds = [...new Set(kills.map((kill) => kill.round_number))].sort((a, b) => a - b);
const generatedAt = new Date().toISOString().replace("T", " ").replace("Z", " UTC");
const sourceId = String(analysis.source_sha256 || "").slice(0, 12);
const userView = analysis.user_view || {};
const readableWarnings = [
  ...(analysis.data_quality?.warnings || userView?.limitations || []),
  ...(nonMatchKills.length || nonMatchScenes.length ? [`${nonMatchKills.length + nonMatchScenes.length} Ereignis(se) ohne reguläre Matchrundenzuordnung wurden nicht als Matchrunde dargestellt.`] : []),
]
  .filter((warning) => !/(KeyError|Traceback|Exception)/i.test(String(warning)));

const workbook = Workbook.create();
const overview = workbook.worksheets.add("Übersicht");
const roundSheet = workbook.worksheets.add("Runden");
const playerSheet = workbook.worksheets.add("Spieler");
const killSheet = workbook.worksheets.add("Kills");
const sceneSheet = workbook.worksheets.add("Multi-Kills & Szenen");
const qualitySheet = workbook.worksheets.add("Datenqualität");
const infoSheet = workbook.worksheets.add("Info");
for (const sheet of [overview, roundSheet, playerSheet, killSheet, sceneSheet, qualitySheet, infoSheet]) sheet.showGridLines = false;

const palette = { navy: "#102A43", blue: "#1F5A94", sky: "#DCEEFF", pale: "#F5F9FD", border: "#C9D7E6", amber: "#FFF2CC", red: "#FCE4D6", green: "#E2F0D9", text: "#172B4D", white: "#FFFFFF" };
const title = (sheet, text, range) => {
  sheet.getRange(range).merge();
  sheet.getRange(range.split(":")[0]).values = [[text]];
  sheet.getRange(range).format = { fill: palette.navy, font: { bold: true, color: palette.white, size: 18 }, horizontalAlignment: "left", verticalAlignment: "center" };
  sheet.getRange(range).format.rowHeight = 30;
};
const section = (sheet, text, range) => {
  sheet.getRange(range).merge();
  sheet.getRange(range.split(":")[0]).values = [[text]];
  sheet.getRange(range).format = { fill: palette.blue, font: { bold: true, color: palette.white }, verticalAlignment: "center" };
};
const header = (sheet, range) => { sheet.getRange(range).format = { fill: palette.sky, font: { bold: true, color: palette.text }, borders: { preset: "outside", style: "thin", color: palette.border }, wrapText: true, verticalAlignment: "center" }; };
const body = (sheet, range) => { sheet.getRange(range).format = { borders: { preset: "insideHorizontal", style: "thin", color: palette.border }, verticalAlignment: "top" }; };

title(overview, "Improve Yourself · Analyzer Report", "A1:H1");
overview.getRange("A2:H2").merge();
overview.getRange("A2").values = [["Lokaler Match- und Szenenbericht. Automatische Hinweise sind keine Cheat-Nachweise."]];
overview.getRange("A2:H2").format = { fill: palette.pale, font: { italic: true, color: palette.text }, wrapText: true };
section(overview, "Match-Überblick", "A4:D4");
overview.getRange("A5:A10").values = [["Map"], ["Analysierte Runden"], ["Erkannte Kills"], ["Review-Szenen"], ["Beteiligte Spieler"], ["Headshots"]];
overview.getRange("B5").values = [[analysis.map_name || "Unbekannte Map"]];
overview.getRange("B6:B10").formulas = [[`=COUNTA(Runden!A3:A${rounds.length + 2})`], [`=COUNTA(Kills!A3:A${kills.length + 2})`], [`=COUNTA('Multi-Kills & Szenen'!A3:A${scenes.length + 2})`], [`=COUNTA(Spieler!A3:A${players.length + 2})`], [`=COUNTIF(Kills!F3:F${kills.length + 2},"Ja")`]];
overview.getRange("A5:B10").format = { fill: palette.white, borders: { preset: "all", style: "thin", color: palette.border } };
overview.getRange("A5:A10").format.font = { bold: true, color: palette.text };
overview.getRange("B6:B10").format.numberFormat = "#,##0";
section(overview, "Kurz zusammengefasst", "F4:H4");
overview.getRange("F5:H8").merge();
overview.getRange("F5").values = [[(userView.facts || []).join(" ") || "Die vorhandenen Analyzer-Daten wurden in diesem Bericht zusammengefasst."]];
overview.getRange("F5:H8").format = { fill: palette.pale, wrapText: true, verticalAlignment: "top", borders: { preset: "outside", style: "thin", color: palette.border } };
section(overview, "Was ist interessant?", "A12:H12");
overview.getRange("A13:H15").merge();
overview.getRange("A13").values = [["Die Multi-Kill-/Szenen-Tabelle zeigt ausschließlich vorhandene, rundenweite Analyzer-Marker. Sie hilft beim gezielten Nachschauen; sie ist keine Aussage über Absicht, Information oder Cheating."]];
overview.getRange("A13:H15").format = { fill: palette.amber, wrapText: true, verticalAlignment: "top", borders: { preset: "outside", style: "thin", color: palette.border } };
section(overview, "Datenqualität", "A17:H17");
overview.getRange("A18:H20").merge();
overview.getRange("A18").values = [[userView.assessment?.message || "Datenqualität siehe separates Tabellenblatt."]];
overview.getRange("A18:H20").format = { fill: analysis.data_quality?.status === "ok" ? palette.green : palette.amber, wrapText: true, verticalAlignment: "top", borders: { preset: "outside", style: "thin", color: palette.border } };
overview.getRange("A22:H22").merge();
overview.getRange("A22").values = [["Tipp: Filtere Kills nach Runde oder Spieler und nutze die Szenenliste als Review-Einstieg."]];
overview.getRange("A22:H22").format = { font: { italic: true, color: palette.text } };
overview.getRange("A:A").format.columnWidth = 23; overview.getRange("B:B").format.columnWidth = 16; overview.getRange("C:E").format.columnWidth = 13; overview.getRange("F:H").format.columnWidth = 20;

title(roundSheet, "Runden · vorhandene Ereignisübersicht", "A1:C1");
roundSheet.getRange("A2:C2").values = [["Runde", "Erkannte Kills", "Multi-Kill-Szenen"]];
roundSheet.getRange(`A3:A${rounds.length + 2}`).values = rounds.map((round) => [round]);
for (let row = 3; row <= rounds.length + 2; row += 1) {
  roundSheet.getRange(`B${row}:C${row}`).formulas = [[
    `=COUNTIF(Kills!$A$3:$A$${kills.length + 2},A${row})`,
    `=COUNTIF('Multi-Kills & Szenen'!$A$3:$A$${scenes.length + 2},A${row})`,
  ]];
}
header(roundSheet, "A2:C2"); body(roundSheet, `A3:C${rounds.length + 2}`); roundSheet.getRange(`A3:C${rounds.length + 2}`).format.numberFormat = "#,##0";
roundSheet.tables.add(`A2:C${rounds.length + 2}`, true, "RoundsTable"); roundSheet.freezePanes.freezeRows(2);
roundSheet.getRange("A:C").format.columnWidth = 20;

title(playerSheet, "Spieler · verlässliche Kill-Ereignis-Übersicht", "A1:F1");
playerSheet.getRange("A2:F2").values = [["Spieler", "Kills", "Tode", "Headshots", "Headshot-Rate", "Multi-Kill-Szenen"]];
playerSheet.getRange(`A3:A${players.length + 2}`).values = players.map((name) => [name]);
for (let row = 3; row <= players.length + 2; row += 1) {
  playerSheet.getRange(`B${row}:F${row}`).formulas = [[
    `=COUNTIF(Kills!$C$3:$C$${kills.length + 2},A${row})`,
    `=COUNTIF(Kills!$D$3:$D$${kills.length + 2},A${row})`,
    `=COUNTIFS(Kills!$C$3:$C$${kills.length + 2},A${row},Kills!$F$3:$F$${kills.length + 2},"Ja")`,
    `=IF(B${row}=0,0,D${row}/B${row})`,
    `=COUNTIF('Multi-Kills & Szenen'!$B$3:$B$${scenes.length + 2},A${row})`,
  ]];
}
header(playerSheet, "A2:F2"); body(playerSheet, `A3:F${players.length + 2}`); playerSheet.getRange(`E3:E${players.length + 2}`).format.numberFormat = "0.0%";
playerSheet.tables.add(`A2:F${players.length + 2}`, true, "PlayersTable"); playerSheet.freezePanes.freezeRows(2);
for (const col of ["A", "B", "C", "D", "E", "F"]) playerSheet.getRange(`${col}:${col}`).format.columnWidth = col === "A" ? 24 : 16;

title(killSheet, "Kills · vorhandene Ereignisdaten", "A1:F1");
killSheet.getRange("A2:F2").values = [["Runde", "Tick", "Killer", "Opfer", "Waffe", "Headshot"]];
killSheet.getRange(`A3:F${kills.length + 2}`).values = kills.map((kill) => [kill.round_number, kill.tick, kill.attacker, kill.victim, kill.weapon || "Unbekannt", kill.headshot ? "Ja" : "Nein"]);
header(killSheet, "A2:F2"); body(killSheet, `A3:F${kills.length + 2}`); killSheet.getRange(`A3:B${kills.length + 2}`).format.numberFormat = "#,##0";
killSheet.tables.add(`A2:F${kills.length + 2}`, true, "KillsTable"); killSheet.freezePanes.freezeRows(2);
killSheet.getRange("A:B").format.columnWidth = 14; killSheet.getRange("C:D").format.columnWidth = 22; killSheet.getRange("E:E").format.columnWidth = 18; killSheet.getRange("F:F").format.columnWidth = 13;

title(sceneSheet, "Multi-Kills & Szenen · Review-Einstieg", "A1:G1");
sceneSheet.getRange("A2:G2").values = [["Runde", "Spieler", "Kills", "Erster Tick", "Letzter Tick", "Beteiligte Opfer", "Review-Hinweis"]];
sceneSheet.getRange(`A3:G${scenes.length + 2}`).values = scenes.map((scene) => [scene.round_number, scene.player, scene.kill_count, scene.first_tick, scene.last_tick, scene.victims.join(", "), "Vorhandener Multi-Kill-Marker; im Spielkontext prüfen."]);
header(sceneSheet, "A2:G2"); body(sceneSheet, `A3:G${scenes.length + 2}`); sceneSheet.getRange(`A3:E${scenes.length + 2}`).format.numberFormat = "#,##0";
sceneSheet.tables.add(`A2:G${scenes.length + 2}`, true, "ScenesTable"); sceneSheet.freezePanes.freezeRows(2);
sceneSheet.getRange("A:A").format.columnWidth = 12; sceneSheet.getRange("B:B").format.columnWidth = 22; sceneSheet.getRange("C:E").format.columnWidth = 14; sceneSheet.getRange("F:F").format.columnWidth = 42; sceneSheet.getRange("G:G").format.columnWidth = 42; sceneSheet.getRange(`F3:G${scenes.length + 2}`).format.wrapText = true;

title(qualitySheet, "Datenqualität · was verfügbar ist und was fehlt", "A1:D1");
section(qualitySheet, "Bewertung", "A3:D3");
qualitySheet.getRange("A4:B6").values = [["Status", analysis.data_quality?.status || "unbekannt"], ["Einordnung", userView.assessment?.status || "Nicht prüfbar / unbekannt"], ["Empfehlung", userView.assessment?.action || "Keine automatische Interpretation."]];
qualitySheet.getRange("A4:B6").format = { borders: { preset: "all", style: "thin", color: palette.border }, wrapText: true, verticalAlignment: "top" };
qualitySheet.getRange("A4:A6").format.font = { bold: true }; qualitySheet.getRange("B4").format.fill = analysis.data_quality?.status === "ok" ? palette.green : palette.amber;
section(qualitySheet, "Vorhandene Datenkanäle", "A8:B8");
const availableChannels = analysis.available_channels || [];
const availableRows = availableChannels.length ? availableChannels : ["Keine verfügbare Quelle gemeldet."];
qualitySheet.getRange(`A9:A${availableRows.length + 8}`).values = availableRows.map((channel) => [channel]);
header(qualitySheet, "A8:B8"); qualitySheet.getRange("A8").values = [["Datenkanal"]]; qualitySheet.getRange("B8").values = [["Bedeutung"]];
qualitySheet.getRange(`B9:B${availableRows.length + 8}`).values = availableRows.map(() => [availableChannels.length ? "Vom Analyzer geliefert" : "Keine Verfügbarkeit gemeldet"]);
body(qualitySheet, `A9:B${availableRows.length + 8}`);
const missingStart = 11 + availableRows.length;
section(qualitySheet, "Fehlende Datenquellen und Grenzen", `A${missingStart}:D${missingStart}`);
header(qualitySheet, `A${missingStart + 1}:B${missingStart + 1}`); qualitySheet.getRange(`A${missingStart + 1}`).values = [["Fehlende Quelle"]]; qualitySheet.getRange(`B${missingStart + 1}`).values = [["Folge"]];
const missingChannels = analysis.data_quality?.missing_channels || [];
const missingRows = missingChannels.length ? missingChannels : ["Keine fehlende Quelle gemeldet."];
const missingEnd = missingStart + missingRows.length + 1;
qualitySheet.getRange(`A${missingStart + 2}:B${missingEnd}`).values = missingRows.map((channel) => [channel, missingChannels.length ? "Nicht als negativer Befund interpretieren" : "Keine fehlende Quelle gemeldet"]);
body(qualitySheet, `A${missingStart + 2}:B${missingEnd}`);
const warningStart = missingEnd + 3;
section(qualitySheet, "Konkrete Hinweise", `A${warningStart}:D${warningStart}`);
const warnings = readableWarnings.length ? readableWarnings : ["Keine zusätzliche Warnung gemeldet."];
const warningEnd = warningStart + Math.max(1, warnings.length);
qualitySheet.getRange(`A${warningStart + 1}:D${warningEnd}`).merge(true);
qualitySheet.getRange(`A${warningStart + 1}:A${warningEnd}`).values = warnings.map((warning) => [warning]);
qualitySheet.getRange(`A${warningStart + 1}:D${warningEnd}`).format = { fill: palette.amber, wrapText: true, borders: { preset: "outside", style: "thin", color: palette.border } };
qualitySheet.getRange("A:A").format.columnWidth = 26; qualitySheet.getRange("B:B").format.columnWidth = 48; qualitySheet.getRange("C:D").format.columnWidth = 18;

title(infoSheet, "Info · Bericht und Interpretation", "A1:F1");
infoSheet.getRange("A3:B8").values = [["Analyzer-Schema", analysis.schema], ["Report-Version", "iy.analyzer_excel_report/v1"], ["Erstellt", generatedAt], ["Map", analysis.map_name || "Unbekannt"], ["Quell-ID", sourceId ? `${sourceId}…` : "Nicht verfügbar"], ["Originaldemo", "Nicht eingebettet; kein lokaler Pfad enthalten"]];
infoSheet.getRange("A3:B8").format = { borders: { preset: "all", style: "thin", color: palette.border }, wrapText: true, verticalAlignment: "top" }; infoSheet.getRange("A3:A8").format.font = { bold: true };
section(infoSheet, "Interpretationshinweise", "A10:F10");
infoSheet.getRange("A11:F15").merge();
infoSheet.getRange("A11").values = [["Dieser Bericht fasst vorhandene Analyzer-Ereignisse zusammen. Multi-Kill-Szenen und andere Hinweise dienen als Einstieg für eine menschliche Prüfung. Sie sind kein Cheat-Nachweis. Fehlende Datenquellen werden offen ausgewiesen und dürfen nicht als negativer Befund ausgelegt werden."]];
infoSheet.getRange("A11:F15").format = { fill: palette.amber, wrapText: true, verticalAlignment: "top", borders: { preset: "outside", style: "thin", color: palette.border } };
infoSheet.getRange("A:A").format.columnWidth = 25; infoSheet.getRange("B:B").format.columnWidth = 55; infoSheet.getRange("C:F").format.columnWidth = 14;

const outputPath = path.resolve(outputArg);
await fs.mkdir(path.dirname(outputPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
const keyCheck = await workbook.inspect({ kind: "table", range: "Übersicht!A1:H22", include: "values,formulas", tableMaxRows: 24, tableMaxCols: 8 });
const formulaErrors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 50 }, summary: "Analyzer report formula error scan" });
const previewDir = path.join(path.dirname(outputPath), "previews");
await fs.mkdir(previewDir, { recursive: true });
for (const sheetName of ["Übersicht", "Runden", "Spieler", "Kills", "Multi-Kills & Szenen", "Datenqualität", "Info"]) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(previewDir, `${sheetName.replaceAll(" ", "-").replaceAll("&", "and")}.png`), new Uint8Array(await preview.arrayBuffer()));
}
console.log(JSON.stringify({ outputPath, map: analysis.map_name, kills: kills.length, scenes: scenes.length, players: players.length, keyCheck: keyCheck.ndjson, formulaErrors: formulaErrors.ndjson }));
