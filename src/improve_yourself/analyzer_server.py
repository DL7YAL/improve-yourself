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
    quality = "".join(f"<li><strong>{_text(item['label'])}:</strong> {_text(item['status'])} — {_text(item['message'])}</li>" for item in data["criteria"])
    available = ", ".join(map(_text, data["data_quality"]["available_channels"])) or "Keine"
    missing = ", ".join(map(_text, data["data_quality"]["missing_channels"])) or "Keine"
    scores = " · ".join(f"{_text(team['label'])} {team['rounds_won']}" for team in match["teams"])
    document = f'''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Improve Yourself – Analyse-Preflight</title><style>:root{{color-scheme:dark;font-family:system-ui;background:#08111e;color:#edf3fb}}body{{margin:0;padding:24px}}main{{max-width:1100px;margin:auto}}.card{{background:#111f32;border:1px solid #273a54;border-radius:12px;padding:16px;margin-top:16px}}table{{width:100%;border-collapse:collapse;margin-bottom:16px}}td,th{{padding:8px;text-align:left;border-bottom:1px solid #273a54}}button{{background:#58a6ff;color:#07111e;border:0;border-radius:9px;padding:12px 16px;font-weight:800;cursor:pointer}}.muted{{color:#aebfd3}}.warn{{background:#211c12;border-color:#8b6b2d}}</style><main><header><h1>Improve Yourself · Analyzer V1</h1><p class="muted">1 Profil → 2 Demo-Preflight → 3 Analyse → 4 Review</p></header><section class="card"><h2>1. Aktives Analyseprofil</h2><p><strong>{_text(profile['label'])}</strong> · Version {_text(profile['version'])}</p><p class="muted">{_text(profile['disclaimer'])}</p></section><section class="card"><h2>2. Demo geladen · technischer Preflight</h2><p><strong>Map:</strong> {_text(match['map_name'])} · <strong>Reguläre Runden:</strong> {match['regular_rounds']} · <strong>Endstand:</strong> {scores}</p><h2>Overall-Scoreboard</h2>{scoreboard}</section><section class="card warn"><h2>Datenqualität und Kriterien vor der Analyse</h2><p><strong>Einschränkung:</strong> {missing}</p><ul>{quality}</ul><p>Fehlende Daten sind kein negativer Befund und werden nicht geschätzt. Technische Details verbleiben im lokalen Analyseartefakt.</p></section><section class="card"><h2>3. Analyse</h2><p>Die Analyse verwendet ausschließlich die oben als bewertbar ausgewiesenen Profilkriterien. Rohdaten und Fakten werden nicht verändert.</p><button id="start">Analyse starten</button> <span id="status" class="muted"></span></section></main><script>document.querySelector('#start').onclick=async()=>{{const b=document.querySelector('#start'),s=document.querySelector('#status');b.disabled=true;s.textContent='Analysiert lokal …';try{{const r=await fetch('/api/start-analysis',{{method:'POST'}}),d=await r.json();if(!r.ok)throw Error(d.error);location.href=d.review_url;}}catch(e){{s.textContent='Analyse fehlgeschlagen: '+e.message;b.disabled=false;}}}};</script></html>'''
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
        server = AnalyzerServer(("127.0.0.1", args.port), args.demo.resolve(), root, preflight, {"max_bytes": args.max_mib * 1024 * 1024, "max_frames": args.max_frames, "radar_path": args.radar, "pos_x": args.pos_x, "pos_y": args.pos_y, "scale": args.scale})
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as error: parser.error(str(error))
    print(f"Analyzer preflight: http://127.0.0.1:{server.server_port}/analyzer.html")
    print("Only this local machine can connect. Press Ctrl+C to stop.")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
    return 0


if __name__ == "__main__": raise SystemExit(main())
