from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Any

from .preflight import PREFLIGHT_SCHEMA, preflight_demo
from .workflow import run_workflow


def _text(value: object) -> str:
    import html
    return html.escape(str(value))


def render_preflight(preflight_path: Path, output_path: Path) -> Path:
    data = json.loads(preflight_path.read_text(encoding="utf-8"))
    if data.get("schema") != PREFLIGHT_SCHEMA:
        raise ValueError("expected iy.analyzer_preflight/v1")
    match = data["match"]; profile = data["profile"]
    scoreboard = ""
    for side, title in (("T", "TERRORISTS"), ("CT", "COUNTER-TERRORISTS")):
        rows = [p for p in match["players"] if p["side"] == side]
        cells = "".join(f"<tr><td>{_text(p['name'])}</td><td>{p['kills']}</td><td>{p['deaths']}</td><td>{p['headshots']}</td></tr>" for p in rows) or "<tr><td colspan=4>Nicht zuverlässig zuordenbar</td></tr>"
        scoreboard += f"<h3>{title}</h3><table><thead><tr><th>Spieler</th><th>Kills</th><th>Tode</th><th>Headshots</th></tr></thead><tbody>{cells}</tbody></table>"
    status_label = {"assessable": "aktiv und bewertbar", "not_assessable": "für diese Demo nicht bewertbar", "not_implemented": "noch nicht implementiert", "disabled": "deaktiviert"}
    criteria = "".join(f"<li><strong>{_text(item['label'])}:</strong> <span class=\"criterion {item['status']}\">{_text(status_label.get(item['status'], item['status']))}</span><br><small>{_text(item['message'])}</small></li>" for item in data["criteria"])
    available = ", ".join(map(_text, data["data_quality"]["available_channels"])) or "Keine"
    missing = ", ".join(map(_text, data["data_quality"]["missing_channels"])) or "Keine"
    scores = " · ".join(f"{_text(team['label'])} {team['rounds_won']}" for team in match["teams"])
    document = f'''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Improve Yourself – Analyse-Preflight</title><style>:root{{color-scheme:dark;font-family:system-ui;background:#08111e;color:#edf3fb}}body{{margin:0;padding:24px}}main{{max-width:1100px;margin:auto}}.card{{background:#111f32;border:1px solid #273a54;border-radius:12px;padding:16px;margin-top:16px}}table{{width:100%;border-collapse:collapse;margin-bottom:16px}}td,th{{padding:8px;text-align:left;border-bottom:1px solid #273a54}}button,select{{background:#58a6ff;color:#07111e;border:0;border-radius:9px;padding:12px 16px;font-weight:800}}.muted,small{{color:#aebfd3}}.warn{{background:#211c12;border-color:#8b6b2d}}.criterion{{font-weight:800}}.assessable{{color:#69d596}}.not_assessable{{color:#ffca62}}.not_implemented,.disabled{{color:#aebfd3}}dialog{{background:#111f32;color:#edf3fb;border:1px solid #273a54;border-radius:12px;max-width:560px}}dialog label{{display:block;margin:10px 0}}</style><main><header><h1>Improve Yourself · Analyzer V1</h1><p class="muted">1 Profil auswählen → 2 Demo laden → 3 Analyse → 4 Review</p></header><section class="card"><h2>1. Analyseprofil auswählen</h2><label for="profile"><strong>Aktives Profil</strong></label><br><select id="profile" aria-label="Analyseprofil"><option value="default">{_text(profile['label'])}</option></select> <button id="new-profile" type="button">Eigenes Profil erstellen</button><p><strong>Version:</strong> {_text(profile['version'])}</p><p class="muted">{_text(profile['disclaimer'])}</p><h3>Enthaltene Kriterienfamilien</h3><ul>{criteria}</ul><small>Eigene Profile wählen nur aus von Improve implementierten Kriterien; sie enthalten keine frei definierten Schwellen oder Operatoren.</small></section><dialog id="profile-dialog"><form method="dialog"><h2>Eigenes Analyseprofil</h2><label>Name <input id="custom-name" maxlength="60" required></label><p>Verfügbare Kriterien (maximal 5):</p><label><input type="checkbox" value="round_multikill" checked> Rundenweiter Multi-Kill</label><p class="muted">Weitere Kriterien werden erst auswählbar, sobald Improve sie belastbar implementiert hat. Nicht implementierte Kriterien können nicht aktiviert werden.</p><button value="cancel">Abbrechen</button><button id="save-profile" value="default">Profil speichern</button></form></dialog><section class="card"><h2>2. Demo geladen · technischer Preflight</h2><p><strong>Map:</strong> {_text(match['map_name'])} · <strong>Reguläre Runden:</strong> {match['regular_rounds']} · <strong>Endstand:</strong> {scores}</p><h2>Overall-Scoreboard</h2>{scoreboard}</section><section class="card warn"><h2>Datenqualität und Kriterienstatus</h2><p><strong>Einschränkung:</strong> {missing}</p><p>Die Kriterienübersicht oben wurde für diese Demo aktualisiert. Fehlende Daten sind kein negativer Befund und werden nicht geschätzt.</p></section><section class="card"><h2>3. Analyse</h2><p>Die Analyse verwendet ausschließlich die oben als aktiv und bewertbar ausgewiesenen Profilkriterien. Rohdaten und Fakten werden nicht verändert.</p><button id="start">Analyse starten</button> <span id="status" class="muted"></span></section></main><script>const profile=document.querySelector('#profile'),dialog=document.querySelector('#profile-dialog'),store='iy.custom_analysis_profiles/v1';function profiles(){{try{{return JSON.parse(localStorage.getItem(store)||'[]')}}catch{{return[]}}}}function refresh(){{profile.innerHTML='<option value="default">Improve Default V1</option>';profiles().forEach((p,i)=>profile.add(new Option(p.name,'custom:'+i)));}}refresh();document.querySelector('#new-profile').onclick=()=>dialog.showModal();document.querySelector('#save-profile').onclick=()=>{{const name=document.querySelector('#custom-name').value.trim();const selected=[...dialog.querySelectorAll('input[type=checkbox]:checked')].map(x=>x.value);if(!name||selected.length>5)return;const all=profiles();all.push({{name,criteria:selected}});localStorage.setItem(store,JSON.stringify(all));refresh();profile.value='custom:'+(all.length-1);}};document.querySelector('#start').onclick=async()=>{{const b=document.querySelector('#start'),s=document.querySelector('#status');b.disabled=true;s.textContent='Analysiert lokal …';try{{const r=await fetch('/api/start-analysis',{{method:'POST'}}),d=await r.json();if(!r.ok)throw Error(d.error);location.href=d.review_url;}}catch(e){{s.textContent='Analyse fehlgeschlagen: '+e.message;b.disabled=false;}}}};</script></html>'''
    output_path.write_text(document, encoding="utf-8")
    return output_path


class AnalyzerServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], demo: Path, output_root: Path, preflight_path: Path, workflow_args: dict[str, Any]):
        self.directory = output_root
        self.demo, self.output_root, self.preflight_path, self.workflow_args = demo, output_root, preflight_path, workflow_args
        self.lock = Lock(); self.analysis_started = False
        super().__init__(address, AnalyzerHandler)


class AnalyzerHandler(SimpleHTTPRequestHandler):
    server: AnalyzerServer
    def __init__(self, *args: Any, **kwargs: Any): super().__init__(*args, directory=str(args[2].directory), **kwargs)
    def log_message(self, format: str, *args: Any) -> None: return
    def do_POST(self) -> None:
        if self.path != "/api/start-analysis": self.send_error(HTTPStatus.NOT_FOUND); return
        with self.server.lock:
            if self.server.analysis_started: self.send_error(HTTPStatus.CONFLICT, "analysis already started"); return
            self.server.analysis_started = True
            try:
                manifest = run_workflow(self.server.demo, self.server.output_root, preflight_path=self.server.preflight_path, **self.server.workflow_args)
                run = manifest.parent.name
                body = json.dumps({"review_url": f"/{run}/review.html"}).encode("utf-8")
                self.send_response(HTTPStatus.OK); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
            except Exception as error:
                self.server.analysis_started = False
                body = json.dumps({"error": str(error)}).encode("utf-8")
                self.send_response(HTTPStatus.BAD_REQUEST); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the local Analyzer V1 profile and demo preflight before analysis")
    parser.add_argument("demo", type=Path); parser.add_argument("--output", type=Path, default=Path("results/analyzer")); parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--max-mib", type=int, default=2048); parser.add_argument("--max-frames", type=int, default=256); parser.add_argument("--radar", type=Path); parser.add_argument("--pos-x", type=float, default=0); parser.add_argument("--pos-y", type=float, default=0); parser.add_argument("--scale", type=float, default=1)
    args = parser.parse_args()
    try:
        root = args.output.resolve(); root.mkdir(parents=True, exist_ok=True)
        preflight = preflight_demo(args.demo, root / "preflight", args.max_mib * 1024 * 1024)
        render_preflight(preflight, root / "analyzer.html")
        data = json.loads(preflight.read_text(encoding="utf-8")); radar = args.radar
        if radar is None:
            maps = Path.home() / ".awpy" / "maps"; overview = maps / f"{data['match']['map_name']}.png"; metadata = maps / "map-data.json"
            if overview.is_file() and metadata.is_file():
                transform = json.loads(metadata.read_text(encoding="utf-8")).get(data["match"]["map_name"], {})
                radar = overview; args.pos_x = transform.get("pos_x", args.pos_x); args.pos_y = transform.get("pos_y", args.pos_y); args.scale = transform.get("scale", args.scale)
        server = AnalyzerServer(("127.0.0.1", args.port), args.demo.resolve(), root, preflight, {"max_bytes": args.max_mib * 1024 * 1024, "max_frames": args.max_frames, "radar_path": radar, "pos_x": args.pos_x, "pos_y": args.pos_y, "scale": args.scale})
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as error: parser.error(str(error))
    print(f"Analyzer preflight: http://127.0.0.1:{server.server_port}/analyzer.html")
    print("Only this local machine can connect. Press Ctrl+C to stop.")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
    return 0


if __name__ == "__main__": raise SystemExit(main())
