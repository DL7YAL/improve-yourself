from __future__ import annotations

import argparse
import json
import shutil
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Any

from .preflight import PREFLIGHT_SCHEMA, preflight_demo
from .branding import ASSET_ROOT, brand_markup
from .optimizer_input import build_optimizer_input
from .system_check import run_system_check
from .workflow import run_workflow


def _text(value: object) -> str:
    import html
    return html.escape(str(value))


def render_preflight(preflight_path: Path, output_path: Path) -> Path:
    data = json.loads(preflight_path.read_text(encoding="utf-8"))
    if data.get("schema") != PREFLIGHT_SCHEMA:
        raise ValueError("expected iy.analyzer_preflight/v1")
    return _render_preflight_v1(data, output_path)


def _render_preflight_v1(data: dict[str, Any], output_path: Path) -> Path:
    """Single local Preview shell; Analyzer remains the only analysis entrypoint."""
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
    document = f'''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="/assets/improve-yourself-mark.svg"><title>Improve Yourself · Preview V1</title><style>:root{{color-scheme:dark;font-family:system-ui;background:#07111e;color:#edf7ff}}*{{box-sizing:border-box}}body{{margin:0}}.app{{max-width:1240px;margin:auto;padding:18px}}.top{{display:flex;align-items:center;gap:24px;border-bottom:1px solid #264766;padding-bottom:12px}}.brand img{{width:278px;height:70px}}.nav{{display:flex;gap:7px;flex-wrap:wrap}}button,.nav button{{background:#19334d;color:#dcefff;border:1px solid #386384;border-radius:8px;padding:9px 12px;font-weight:700;cursor:pointer}}button.primary{{background:#8edbff;color:#06101a;border:0}}button[disabled]{{opacity:.45;cursor:not-allowed}}.nav button.active{{background:#8edbff;color:#06101a}}main{{max-width:1120px;margin:20px auto}}.card{{background:#102033;border:1px solid #264766;border-radius:13px;padding:18px;margin-top:16px;box-shadow:0 8px 28px #0004}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}}h1,h2,h3{{margin-top:0}}.muted,small{{color:#a9c7dc}}.warn{{border-color:#8c6e31;background:#211d14}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;text-align:left;border-bottom:1px solid #264766}}select,input{{background:#0b1727;color:#edf7ff;border:1px solid #386384;border-radius:7px;padding:8px}}.criterion{{font-weight:800}}.assessable{{color:#76ddb0}}.not_assessable{{color:#ffd171}}.not_implemented,.disabled{{color:#a9c7dc}}.hidden{{display:none}}.mode{{display:flex;gap:8px}}.recommendation{{border-left:3px solid #8edbff;padding:10px;background:#0b1727;margin:8px 0}}dialog{{background:#102033;color:#edf7ff;border:1px solid #386384;border-radius:12px}}</style><div class="app"><header class="top">{brand_markup()}<nav class="nav"><button class="active" data-tab="analyzer">Analyzer</button><button data-tab="replay" disabled>Tactical Replay</button><button data-tab="system">System Check</button><button data-tab="optimizer">Optimizer</button><button disabled title="In Entwicklung">My Improvement · In Entwicklung</button><button disabled title="In Entwicklung">Benchmark · In Entwicklung</button><button data-tab="settings">Einstellungen</button></nav></header><main><section id="analyzer"><div class="card"><h1>Analyzer</h1><p class="muted">1 Analyseprofil → 2 Demo laden → 3 Preflight → 4 Analyse → Match Review</p></div><section class="card"><h2>1. Analyseprofil</h2><label>Aktives Profil <select id="profile"><option value="default">{_text(profile['label'])}</option></select></label> <button id="new-profile">Eigenes Profil</button><p><strong>Version:</strong> {_text(profile['version'])}</p><p class="muted">{_text(profile['disclaimer'])}</p><ul>{criteria}</ul></section><section class="card"><h2>2. Demo-Preflight</h2><p><strong>Map:</strong> {_text(match['map_name'])} · <strong>Reguläre Runden:</strong> {match['regular_rounds']} · <strong>Endstand:</strong> {scores}</p><div class="grid">{scoreboard}</div></section><section class="card warn"><h2>Datenqualität</h2><p><strong>Nicht verfügbar:</strong> {missing}</p><p>Fehlende Daten werden nicht geschätzt und nicht als negativer Befund gewertet.</p></section><section class="card"><h2>3. Analyse starten</h2><p>Es werden nur vorhandene, aktiv bewertbare Kriterien verwendet. Rohdaten und Fakten bleiben unverändert.</p><button id="start" class="primary">Analyse starten</button> <span id="status" class="muted"></span></section></section><section id="system" class="hidden"><div class="card"><h1>System Check</h1><p class="muted">Read-only Diagnose. Es werden keine Einstellungen verändert.</p><button id="run-system" class="primary">System Check ausführen</button><div id="system-result"></div></div></section><section id="optimizer" class="hidden"><div class="card"><h1>Optimizer · Preview</h1><p class="muted">Ist-Zustand → Bewertung → Empfehlung. Kein Apply, Restore oder Tuning in Preview V1.</p><div class="mode"><button data-mode="Performance" class="primary">Performance</button><button data-mode="Quality">Quality</button></div><div id="optimizer-result" class="muted">Zuerst den System Check ausführen.</div></div></section><section id="settings" class="hidden"><div class="card"><h1>Einstellungen</h1><p><strong>Theme:</strong> Metallic / Mitternachtsblau (aktiv)</p><p class="muted">Babyblau / Hell-Metallic ist als spätere Theme-Variante vorbereitet; Preview V1 verwendet bewusst das dunkle Standardtheme.</p></div></section></main></div><dialog id="profile-dialog"><form method="dialog"><h2>Eigenes Analyseprofil</h2><label>Name <input id="custom-name" maxlength="60" required></label><p>Verfügbare Kriterien (maximal 5):</p><label><input type="checkbox" value="round_multikill" checked> Rundenweiter Multi-Kill</label><p class="muted">Nicht implementierte Kriterien werden nicht als funktionierende Auswahl angeboten.</p><button value="cancel">Abbrechen</button><button id="save-profile" value="default">Profil speichern</button></form></dialog><script>const tabs=['analyzer','system','optimizer','settings'],store='iy.custom_analysis_profiles/v1';let system=null;function show(tab){{tabs.forEach(id=>document.querySelector('#'+id).classList.toggle('hidden',id!==tab));document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x.dataset.tab===tab))}}document.querySelectorAll('[data-tab]').forEach(x=>x.onclick=()=>show(x.dataset.tab));const profile=document.querySelector('#profile'),dialog=document.querySelector('#profile-dialog');function profiles(){{try{{return JSON.parse(localStorage.getItem(store)||'[]')}}catch{{return[]}}}}function refresh(){{profile.innerHTML='<option value="default">Improve Default V1</option>';profiles().forEach((p,i)=>profile.add(new Option(p.name,'custom:'+i)));}}refresh();document.querySelector('#new-profile').onclick=()=>dialog.showModal();document.querySelector('#save-profile').onclick=()=>{{const name=document.querySelector('#custom-name').value.trim(),selected=[...dialog.querySelectorAll('input[type=checkbox]:checked')].map(x=>x.value);if(!name||selected.length>5)return;const all=profiles();all.push({{name,criteria:selected}});localStorage.setItem(store,JSON.stringify(all));refresh();profile.value='custom:'+(all.length-1)}};async function jsonResponse(r){{const text=await r.text();if(!(r.headers.get('content-type')||'').includes('application/json'))throw Error(`Serverantwort ist kein JSON (HTTP ${{r.status}}).`);const data=JSON.parse(text);if(!r.ok)throw Error(data.error||`HTTP ${{r.status}}`);return data}}document.querySelector('#start').onclick=async()=>{{const b=document.querySelector('#start'),s=document.querySelector('#status');b.disabled=true;s.textContent='Analysiert lokal …';try{{const data=await jsonResponse(await fetch('/api/start-analysis',{{method:'POST'}}));location.href=data.review_url}}catch(error){{s.textContent='Analyse fehlgeschlagen: '+error.message;b.disabled=false}}}};function renderSystem(data){{const checks=data.checks||[];document.querySelector('#system-result').innerHTML=checks.map(c=>`<article class="recommendation"><strong>${{c.label}}</strong><br>${{c.summary||'Nicht prüfbar / unbekannt'}}<br><small>${{c.user_view?.action||'Keine automatische Änderung.'}}</small></article>`).join('');const mode=document.querySelector('#optimizer-result');mode.innerHTML=`<h2>Mein System</h2>${{checks.map(c=>`<div class="recommendation"><strong>${{c.label}}</strong> · ${{c.user_view?.status||'Nicht prüfbar / unbekannt'}}<br><small>${{c.user_view?.action||'Noch nicht bewertet / in Entwicklung'}}</small></div>`).join('')}}<p class="muted">CS2 · Grafiktreiber · Windows/System · Display · Treiber · später BIOS/UEFI: nur vorhandene, belastbare Informationen werden gezeigt.</p>`}}document.querySelector('#run-system').onclick=async()=>{{const button=document.querySelector('#run-system');button.disabled=true;try{{system=await jsonResponse(await fetch('/api/system-check',{{method:'POST'}}));renderSystem(system)}}catch(error){{document.querySelector('#system-result').textContent='System Check fehlgeschlagen: '+error.message}}finally{{button.disabled=false}}}};document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{{document.querySelectorAll('[data-mode]').forEach(x=>x.classList.remove('primary'));b.classList.add('primary');if(system)renderSystem(system)}});</script>'''
    enhancements = '''
const replayNav=document.querySelector('[data-tab="replay"]');replayNav.disabled=false;
const replaySection=document.createElement('section');replaySection.id='replay';replaySection.className='hidden';replaySection.innerHTML='<div class="card"><h1>2D Tactical Replay</h1><p class="muted">Noch keine Review-Szene ausgewählt. Analysiere zuerst diese Demo oder öffne später eine Szene aus dem Match Review.</p></div>';document.querySelector('#system').before(replaySection);
const chooseDemo=document.createElement('button');chooseDemo.id='choose-demo';chooseDemo.textContent='Andere Demo auswählen';chooseDemo.title='Lokale .dem, .dem.zst oder .dem.bz2 auswählen';document.querySelector('#analyzer > .card').append(document.createTextNode(' '),chooseDemo);chooseDemo.onclick=async()=>{if(!window.pywebview?.api){document.querySelector('#status').textContent='Diese Funktion ist in Improve Yourself.exe verfügbar.';return}try{const result=await window.pywebview.api.choose_demo();if(result?.ok)location.href='/analyzer.html';else document.querySelector('#status').textContent=result?.error||'Keine Demo ausgewählt.'}catch(error){document.querySelector('#status').textContent='Demoauswahl fehlgeschlagen: '+error.message}};
const settings=document.querySelector('#settings .card');settings.insertAdjacentHTML('beforeend','<hr><h2>Lokales Nutzerprofil</h2><label>Name <input id="local-profile-name" maxlength="60" autocomplete="name"></label> <button id="save-local-profile">Lokal speichern</button><p id="local-profile-status" class="muted">Wird ausschließlich in diesem Desktopfenster lokal gespeichert.</p>');const localProfileKey='iy.local_profile/v1',localProfileInput=document.querySelector('#local-profile-name'),localProfileStatus=document.querySelector('#local-profile-status');try{const saved=JSON.parse(localStorage.getItem(localProfileKey)||'{}');localProfileInput.value=saved.name||''}catch{}document.querySelector('#save-local-profile').onclick=()=>{const name=localProfileInput.value.trim();localStorage.setItem(localProfileKey,JSON.stringify({name}));localProfileStatus.textContent=name?'Lokales Profil gespeichert.':'Lokales Profil ohne Namen gespeichert.'};
'''
    document = document.replace('data-tab="replay" disabled', 'data-tab="replay"')
    document = document.replace("const tabs=['analyzer','system','optimizer','settings']", "const tabs=['analyzer','replay','system','optimizer','settings']")
    document = document.replace("</script>", enhancements + "</script>")
    wide_styles = '''<style>
.app{width:100%;max-width:none;margin:0;padding:clamp(14px,2vw,34px)}.top{width:100%;justify-content:space-between;gap:18px}.top .brand{flex:0 0 auto}.nav{justify-content:flex-end}.nav button{white-space:nowrap}main{max-width:none;width:100%;margin:22px 0}.card{padding:clamp(18px,2vw,30px)}#analyzer .grid{grid-template-columns:repeat(2,minmax(320px,1fr));align-items:start}#analyzer .grid h3{margin-top:0}#system-result{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:14px}.optimizer-grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(320px,.85fr);gap:18px;margin-top:18px}.optimizer-panel{background:#0b1727;border:1px solid #264766;border-radius:11px;padding:18px}.optimizer-panel h2{margin-bottom:14px}.optimizer-panel .recommendation{margin:8px 0}.optimizer-status{display:inline-block;background:#19334d;border-radius:999px;padding:4px 8px;margin:0 0 10px;color:#dcefff;font-size:.9rem}@media(max-width:900px){.app{padding:14px}.top{align-items:flex-start}.nav{justify-content:flex-start}.optimizer-grid,#analyzer .grid{grid-template-columns:1fr}}@media(max-width:620px){.top{flex-direction:column}.nav{width:100%}.nav button{flex:1 1 145px}.card{padding:16px}}
</style>'''
    wide_script = '''
renderSystem=function(data){const checks=data.checks||[];const cards=checks.map(c=>`<article class="recommendation"><strong>${c.label}</strong><br>${c.summary||'Nicht prüfbar / unbekannt'}<br><small>${c.user_view?.action||'Keine automatische Änderung.'}</small></article>`).join('');document.querySelector('#system-result').innerHTML=cards;const statusCards=checks.map(c=>`<article class="recommendation"><strong>${c.label}</strong><br><small>${c.user_view?.status||'Nicht prüfbar / unbekannt'}</small></article>`).join('');const recommendationCards=checks.map(c=>`<article class="recommendation"><strong>${c.label}</strong><br><small>${c.user_view?.action||'Noch nicht bewertet / für Preview V1 noch nicht definiert.'}</small></article>`).join('');document.querySelector('#optimizer-result').innerHTML=`<div class="optimizer-grid"><section class="optimizer-panel"><h2>Mein System</h2>${statusCards}</section><section class="optimizer-panel"><h2>Empfehlungen / Bewertung</h2><span class="optimizer-status">Read-only Preview</span>${recommendationCards}<p class="muted">Performance und Quality unterscheiden nur vorhandene, belastbare Bewertungen. Es wird keine Einstellung angewendet.</p></section></div>`};
'''
    document = document.replace("</style>", wide_styles + "</style>")
    document = document.replace("</script>", wide_script + "</script>")
    output_path.write_text(document, encoding="utf-8")
    return output_path


class AnalyzerServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], demo: Path | None, output_root: Path, preflight_path: Path | None, workflow_args: dict[str, Any]):
        self.directory = output_root
        self.demo, self.output_root, self.preflight_path, self.workflow_args = demo, output_root, preflight_path, workflow_args
        self.lock = Lock(); self.analysis_started = False; self.review_url: str | None = None
        super().__init__(address, AnalyzerHandler)

    def select_demo(self, demo: Path) -> None:
        """Switch the local session to a new demo without leaving the desktop app."""
        demo = demo.resolve()
        if demo.suffix.lower() not in {".dem", ".zst", ".bz2"} or not demo.is_file():
            raise ValueError("Bitte eine lokale .dem-, .dem.zst- oder .dem.bz2-Datei auswählen.")
        with self.lock:
            preflight = preflight_demo(demo, self.output_root / "preflight", self.workflow_args["max_bytes"])
            render_preflight(preflight, self.output_root / "analyzer.html")
            data = json.loads(preflight.read_text(encoding="utf-8"))
            radar, pos_x, pos_y, scale = _resolve_radar(data, self.workflow_args)
            self.demo, self.preflight_path = demo, preflight
            self.workflow_args.update({"radar_path": radar, "pos_x": pos_x, "pos_y": pos_y, "scale": scale})
            self.analysis_started = False; self.review_url = None


class AnalyzerHandler(SimpleHTTPRequestHandler):
    server: AnalyzerServer
    def __init__(self, *args: Any, **kwargs: Any): super().__init__(*args, directory=str(args[2].directory), **kwargs)
    def log_message(self, format: str, *args: Any) -> None: return
    def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_POST(self) -> None:
        if self.path == "/api/select-demo":
            try:
                value = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0")) or "0").decode("utf-8"))
                self.server.select_demo(Path(str(value.get("path", ""))))
                self._json(HTTPStatus.OK, {"preflight_url": "/analyzer.html"})
            except (OSError, ValueError, json.JSONDecodeError) as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return
        if self.path == "/api/system-check":
            try:
                system_path = run_system_check(self.server.output_root / "system-check.json")
                payload = json.loads(system_path.read_text(encoding="utf-8"))
                optimizer_path = self.server.output_root / "optimizer-input.json"
                optimizer_path.write_text(json.dumps(build_optimizer_input(payload), ensure_ascii=False, indent=2), encoding="utf-8")
                self._json(HTTPStatus.OK, payload)
            except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return
        if self.path != "/api/start-analysis": self._json(HTTPStatus.NOT_FOUND, {"error": "Endpoint nicht gefunden."}); return
        with self.server.lock:
            if self.server.demo is None or self.server.preflight_path is None:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "Bitte zuerst eine lokale Demo auswählen."}); return
            if self.server.review_url: self._json(HTTPStatus.OK, {"review_url": self.server.review_url, "reused": True}); return
            if self.server.analysis_started: self._json(HTTPStatus.CONFLICT, {"error": "Analyse läuft bereits lokal. Bitte kurz warten."}); return
            self.server.analysis_started = True
            try:
                manifest = run_workflow(self.server.demo, self.server.output_root, preflight_path=self.server.preflight_path, **self.server.workflow_args)
                run = manifest.parent.name
                self.server.review_url = f"/{run}/review.html"
                self._json(HTTPStatus.OK, {"review_url": self.server.review_url})
            except Exception as error:
                self.server.analysis_started = False
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})


def _resolve_radar(data: dict[str, Any], workflow_args: dict[str, Any]) -> tuple[Path | None, float, float, float]:
    radar = workflow_args.get("radar_path"); pos_x = float(workflow_args.get("pos_x", 0)); pos_y = float(workflow_args.get("pos_y", 0)); scale = float(workflow_args.get("scale", 1))
    if radar is None:
        packaged = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "resources" / "maps"
        for maps in (packaged, Path.home() / ".awpy" / "maps"):
            overview = maps / f"{data['match']['map_name']}.png"; metadata = maps / "map-data.json"
            if overview.is_file() and metadata.is_file():
                transform = json.loads(metadata.read_text(encoding="utf-8")).get(data["match"]["map_name"], {})
                return overview, float(transform.get("pos_x", pos_x)), float(transform.get("pos_y", pos_y)), float(transform.get("scale", scale))
    return radar, pos_x, pos_y, scale


def create_server(output_root: Path, port: int, *, max_mib: int = 2048, max_frames: int = 256, radar_path: Path | None = None, pos_x: float = 0, pos_y: float = 0, scale: float = 1) -> AnalyzerServer:
    output_root = output_root.resolve(); output_root.mkdir(parents=True, exist_ok=True)
    assets = output_root / "assets"; assets.mkdir(exist_ok=True)
    shutil.copyfile(ASSET_ROOT / "improve-yourself-mark.svg", assets / "improve-yourself-mark.svg")
    workflow_args = {"max_bytes": max_mib * 1024 * 1024, "max_frames": max_frames, "radar_path": radar_path, "pos_x": pos_x, "pos_y": pos_y, "scale": scale}
    server = AnalyzerServer(("127.0.0.1", port), None, output_root, None, workflow_args)
    _write_empty_analyzer(output_root / "analyzer.html")
    return server


def _write_empty_analyzer(output_path: Path) -> None:
    output_path.write_text(f'''<!doctype html><meta charset="utf-8"><link rel="icon" href="/assets/improve-yourself-mark.svg"><title>Improve Yourself · Preview V1</title><style>:root{{color-scheme:dark;font-family:system-ui;background:#07111e;color:#edf7ff}}body{{margin:0}}main{{max-width:1420px;margin:auto;padding:24px}}.top{{display:flex;gap:28px;align-items:center;border-bottom:1px solid #264766;padding-bottom:14px}}.brand img{{width:290px}}.card{{background:#102033;border:1px solid #264766;border-radius:14px;padding:24px;margin-top:24px;box-shadow:0 8px 28px #0004}}button{{background:#8edbff;color:#06101a;border:0;border-radius:8px;padding:12px 16px;font-weight:800;cursor:pointer}}.muted{{color:#a9c7dc}}</style><main><header class="top">{brand_markup()}<strong>Analyzer · Tactical Replay · System Check · Optimizer Preview</strong></header><section class="card"><h1>Demo auswählen</h1><p class="muted">Wähle eine lokale .dem, .dem.zst oder .dem.bz2-Datei. Es gibt keinen Upload und keine Cloud-Verbindung.</p><button id="choose">Demo öffnen</button><p id="status" class="muted"></p></section><section class="card"><h2>Tactical Replay</h2><p class="muted">Noch keine Review-Szene ausgewählt. Analysiere zuerst eine Demo oder öffne eine Szene aus dem Match Review.</p></section></main><script>document.querySelector('#choose').onclick=async()=>{{const s=document.querySelector('#status');if(!window.pywebview?.api){{s.textContent='Diese Preview wird über Improve Yourself.exe geöffnet.';return}};s.textContent='Öffnet lokale Dateiauswahl …';try{{const r=await window.pywebview.api.choose_demo();if(r?.ok)location.href='/analyzer.html';else s.textContent=r?.error||'Keine Demo ausgewählt.'}}catch(e){{s.textContent='Demoauswahl fehlgeschlagen: '+e.message}}}};</script>''', encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the local Analyzer V1 profile and demo preflight before analysis")
    parser.add_argument("demo", type=Path); parser.add_argument("--output", type=Path, default=Path("results/analyzer")); parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--max-mib", type=int, default=2048); parser.add_argument("--max-frames", type=int, default=256); parser.add_argument("--radar", type=Path); parser.add_argument("--pos-x", type=float, default=0); parser.add_argument("--pos-y", type=float, default=0); parser.add_argument("--scale", type=float, default=1)
    args = parser.parse_args()
    try:
        server = create_server(args.output, args.port, max_mib=args.max_mib, max_frames=args.max_frames, radar_path=args.radar, pos_x=args.pos_x, pos_y=args.pos_y, scale=args.scale)
        server.select_demo(args.demo)
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as error: parser.error(str(error))
    print(f"Analyzer preflight: http://127.0.0.1:{server.server_port}/analyzer.html")
    print("Only this local machine can connect. Press Ctrl+C to stop.")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
    return 0


if __name__ == "__main__": raise SystemExit(main())
