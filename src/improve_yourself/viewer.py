from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import math
from pathlib import Path
from typing import Any

from .replay import REPLAY_SCHEMA
from .replay_contract import REPLAY_V2_SCHEMA
from .replay_controller import ReplayController
from .replay_store import ReplayStore
from .tactical_2d import TACTICAL_2D_PROJECTION_SCHEMA, build_tactical_2d_projection


_MAP_OVERVIEW_SCHEMA = "iy.map_overview_metadata/v1"
_MAP_OVERVIEW_ROOT = Path(__file__).resolve().parents[2] / "resources" / "map_overviews" / "maps"


def world_to_radar(x: float, y: float, pos_x: float, pos_y: float, scale: float) -> tuple[float, float]:
    """Project CS2 world coordinates into Source radar-image pixels."""
    if scale <= 0:
        raise ValueError("radar scale must be positive")
    return ((x - pos_x) / scale, (pos_y - y) / scale)


def _validate_replay(payload: dict[str, Any]) -> None:
    if payload.get("schema") not in (REPLAY_SCHEMA, TACTICAL_2D_PROJECTION_SCHEMA):
        raise ValueError(f"expected {REPLAY_SCHEMA} or {REPLAY_V2_SCHEMA} replay payload")
    if payload.get("coordinate_space") != "cs2_world":
        raise ValueError("viewer requires cs2_world coordinates")
    if not isinstance(payload.get("scenes"), list):
        raise ValueError("replay scenes must be a list")


def _radar_data_uri(path: Path | None) -> str:
    if path is None:
        return ""
    data = path.read_bytes()
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _verified_radar_transform(map_id: str) -> tuple[float, float, float]:
    """Load the only approved V2 radar transform for a canonical map identifier.

    Overview metadata deliberately does not contain a Valve radar texture. A caller
    may supply a locally authorised image, but its projection must come from this
    static map-overview contract rather than CLI guesses.
    """
    path = _MAP_OVERVIEW_ROOT / f"{map_id}.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"no verified map overview metadata for {map_id}") from error

    transform = document.get("transform")
    origin = transform.get("origin_world") if isinstance(transform, dict) else None
    if (
        document.get("schema") != _MAP_OVERVIEW_SCHEMA
        or document.get("map_id") != map_id
        or not isinstance(origin, dict)
        or transform.get("verification_status") != "VERIFIED"
        or transform.get("world_x_to_canvas") != "positive_x"
        or transform.get("world_y_to_canvas") != "negative_y"
        or transform.get("rotation_deg_clockwise") != 0
    ):
        raise ValueError(f"map overview metadata is not a verified V2 transform for {map_id}")

    values = (origin.get("x"), origin.get("y"), transform.get("world_units_per_pixel"))
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in values):
        raise ValueError(f"map overview metadata has incomplete transform values for {map_id}")
    pos_x, pos_y, scale = (float(value) for value in values)
    if scale <= 0:
        raise ValueError(f"map overview metadata has an invalid transform scale for {map_id}")
    return pos_x, pos_y, scale


def visible_players_at_frame(players: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Hide only players explicitly reported dead by the canonical replay state."""
    return [player for player in players if player.get("alive") is not False]


def render_viewer(
    replay_path: Path,
    output_path: Path,
    *,
    radar_path: Path | None = None,
    pos_x: float = 0,
    pos_y: float = 0,
    scale: float = 1,
    scenes: list[dict[str, Any]] | None = None,
    store: ReplayStore | None = None,
    controller: ReplayController | None = None,
) -> Path:
    payload = json.loads(replay_path.read_text(encoding="utf-8"))
    is_v2 = payload.get("schema") == REPLAY_V2_SCHEMA
    if is_v2:
        if (store is None) != (controller is None):
            raise ValueError("V2 viewer requires both store and controller when either is supplied")
        if store is None:
            store = ReplayStore(replay_path)
            controller = ReplayController(store)
        projection_scenes = None
        if scenes is not None:
            projection_scenes = [
                {"scene_id": item["scene_id"], "round_number": item["round_number"],
                 "tick": item["review_tick"], "end_tick": item["end_tick"],
                 "focus_player_id": item.get("focus_player_id")}
                for item in scenes
            ]
        payload = build_tactical_2d_projection(store, controller, source_scenes=projection_scenes)
    _validate_replay(payload)
    if radar_path is not None and scale <= 0:
        raise ValueError("radar scale must be positive")
    if is_v2 and radar_path is not None:
        if (pos_x, pos_y, scale) != (0, 0, 1):
            raise ValueError("V2 radar transforms are derived from verified map overview metadata")
        map_id = payload.get("map_name")
        if not isinstance(map_id, str) or not map_id:
            raise ValueError("V2 viewer requires a canonical replay map_id for a radar image")
        pos_x, pos_y, scale = _verified_radar_transform(map_id)

    model = {
        "replay": payload,
        "radar": {
            "data_uri": _radar_data_uri(radar_path),
            "pos_x": pos_x,
            "pos_y": pos_y,
            "scale": scale,
        },
    }
    # Escaping '<' prevents an embedded player name from closing the script tag.
    model_json = json.dumps(model, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    html = _HTML.replace("__IY_VIEWER_MODEL__", model_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a self-contained iy.replay/v1 or iy.replay/v2 2D viewer")
    parser.add_argument("replay", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/replay/viewer.html"))
    parser.add_argument("--radar", type=Path)
    parser.add_argument("--pos-x", type=float, default=0)
    parser.add_argument("--pos-y", type=float, default=0)
    parser.add_argument("--scale", type=float, default=1)
    args = parser.parse_args()
    try:
        result = render_viewer(
            args.replay, args.output, radar_path=args.radar,
            pos_x=args.pos_x, pos_y=args.pos_y, scale=args.scale,
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(result)
    return 0


_HTML = r'''<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Improve Yourself – 2D Replay</title>
<style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#09111d;color:#e9f0fa}*{box-sizing:border-box}
body{margin:0;padding:20px}.shell{max-width:1180px;margin:auto}.bar,.meta{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
h1{font-size:20px;margin:0 auto 0 0}.card{background:#111e30;border:1px solid #263851;border-radius:12px;padding:14px;margin-top:14px}
button,select,input{accent-color:#62a8ff;background:#17283d;color:#fff;border:1px solid #3a506d;border-radius:7px;padding:7px}
input[type=range]{flex:1;min-width:180px}.stage{position:relative;aspect-ratio:1;max-height:72vh;margin:auto}
canvas{width:100%;height:100%;background:#07101a;border-radius:8px}.pill{color:#a9bed7;font-size:13px}.warn{color:#ffc56e}
</style></head><body><main class="shell">
<div class="bar"><h1>Improve Yourself · 2D Replay</h1><span id="map" class="pill"></span><span id="quality" class="pill"></span></div>
<section class="card bar"><label>Szene <select id="scene"></select></label><button id="previous-scene">‹ Szene</button><button id="next-scene">Szene ›</button><button id="previous-frame">‹ Frame</button><button id="play">▶ Abspielen</button><button id="next-frame">Frame ›</button><label>Tempo <select id="speed"><option value="0.5">0,5×</option><option value="1" selected>1×</option><option value="2">2×</option></select></label><label id="player-wrap" hidden>Spieler <select id="player"></select></label><input id="frame" type="range" min="0" value="0"><span id="tick" class="pill"></span></section>
<section class="card stage"><canvas id="canvas" width="1024" height="1024"></canvas></section>
<section class="card meta"><span class="pill">T = orange · CT = blau · Linie = Blickrichtung</span><span class="pill">Spieler verschwinden nur bei explizit belegtem Todeszustand.</span><span id="notice" class="pill warn"></span></section><section class="card"><strong id="scene-info"></strong><div id="event-info" class="pill"></div></section>
</main><script>const MODEL=__IY_VIEWER_MODEL__;
const replay=MODEL.replay,radar=MODEL.radar,canvas=document.querySelector('#canvas'),ctx=canvas.getContext('2d');
const sceneEl=document.querySelector('#scene'),frameEl=document.querySelector('#frame'),playEl=document.querySelector('#play'),speedEl=document.querySelector('#speed'),playerEl=document.querySelector('#player'),eventEl=document.querySelector('#event-info'),sceneInfoEl=document.querySelector('#scene-info');let playing=false,timer=null,img=null;
const isV2=replay.source_schema==='iy.replay/v2',timingAvailable=!isV2||replay.controller.timing_available;
document.querySelector('#map').textContent=replay.map_name;document.querySelector('#quality').textContent=isV2?`${replay.scenes.length} Szenen · gemeinsame Replay-Wahrheit v2`:`${replay.scenes.length} Szenen · ${replay.data_quality.omitted_incomplete_player_snapshots} ausgelassene Snapshots`;
replay.scenes.forEach((s,i)=>sceneEl.add(new Option(`Runde ${s.round_number} · ${s.marker_player}`,i)));
if(isV2){document.querySelector('#player-wrap').hidden=false;playerEl.add(new Option('Kein Spieler gewählt',''));replay.players.forEach(p=>playerEl.add(new Option(p.display_name,p.player_id)));if(!timingAvailable){playEl.disabled=true;playEl.textContent='▶ Zeitbasis nicht verfügbar';document.querySelector('#notice').textContent='Navigation ist exakt; automatische Wiedergabe ist ohne belegte Tickrate deaktiviert.'}}
if(radar.data_uri){img=new Image();img.onload=draw;img.src=radar.data_uri}else document.querySelector('#notice').textContent='Kein Radar eingebettet – relative Weltansicht.';
function scene(){return replay.scenes[Number(sceneEl.value)||0]}function frame(){return scene()?.frames[Number(frameEl.value)||0]}
function project(p,players){if(img)return[(p.x-radar.pos_x)/radar.scale*canvas.width/img.naturalWidth,(radar.pos_y-p.y)/radar.scale*canvas.height/img.naturalHeight];
 const xs=players.map(q=>q.x),ys=players.map(q=>q.y),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),span=Math.max(maxX-minX,maxY-minY,1);return[100+(p.x-minX)/span*824,924-(p.y-minY)/span*824]}
function draw(){ctx.clearRect(0,0,1024,1024);if(img)ctx.drawImage(img,0,0,1024,1024);else{ctx.strokeStyle='#1c3046';for(let n=0;n<=1024;n+=128){ctx.beginPath();ctx.moveTo(n,0);ctx.lineTo(n,1024);ctx.stroke();ctx.beginPath();ctx.moveTo(0,n);ctx.lineTo(1024,n);ctx.stroke()}}
 const f=frame(),s=scene();if(!f){document.querySelector('#tick').textContent='Kein renderbarer Snapshot';sceneInfoEl.textContent=`Runde ${s?.round_number??'—'} · ${s?.marker_player??'Kein Fokusspieler'}`;eventEl.textContent='Für diese Szene liegen keine renderbaren Positions- und Blickrichtungsdaten vor.';return}const frameIndex=Number(frameEl.value),requested=frameIndex===0?(s.requested_tick??f.tick):f.tick,resolved=f.tick,timestamp=typeof f.timestamp_seconds==='number'?` · ${f.timestamp_seconds.toFixed(3)} s`:'';document.querySelector('#tick').textContent=isV2?`Tick ${resolved} · angefordert ${requested}${timestamp} · Frame ${frameIndex+1}/${s.frames.length}`:`Tick ${f.tick} · Frame ${frameIndex+1}/${s.frames.length}`;sceneInfoEl.textContent=`Runde ${s.round_number} · ${s.marker_player}`;eventEl.textContent=typeof f.event_count==='number'?`${f.event_count} belegte Ereignisse am Snapshot.`:'Keine Ereignisdaten am Snapshot.';
 const visiblePlayers=f.players.filter(p=>p.alive!==false);for(const p of visiblePlayers){const [x,y]=project(p,visiblePlayers),color=p.side.toUpperCase()==='CT'?'#55aaff':'#ff9f43',a=p.yaw*Math.PI/180,selected=!playerEl.value||playerEl.value===p.player_id;ctx.globalAlpha=selected?1:.35;ctx.strokeStyle=color;ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+Math.cos(a)*34,y-Math.sin(a)*34);ctx.stroke();ctx.fillStyle=color;ctx.beginPath();ctx.arc(x,y,10,0,Math.PI*2);ctx.fill();ctx.font='16px system-ui';ctx.fillStyle='#fff';ctx.fillText(p.name,x+14,y-12)}ctx.globalAlpha=1}
function step(delta){const max=Number(frameEl.max);frameEl.value=Math.min(max,Math.max(0,Number(frameEl.value)+delta));draw()}
function reset(){playing=false;clearInterval(timer);playEl.textContent='▶ Abspielen';const s=scene(),hasFrames=(s?.frames.length||0)>0;frameEl.max=Math.max(0,(s?.frames.length||1)-1);frameEl.value=0;for(const control of [frameEl,document.querySelector('#previous-frame'),document.querySelector('#next-frame'),playEl])control.disabled=!hasFrames||(!timingAvailable&&control===playEl);if(!hasFrames)document.querySelector('#notice').textContent='Keine renderbaren Snapshots für diese Szene.';else if(!radar.data_uri)document.querySelector('#notice').textContent='Kein Radar eingebettet – relative Weltansicht.';draw()}
sceneEl.onchange=()=>{const s=scene();if(isV2)playerEl.value=s.focus_player_id||'';reset()};playerEl.onchange=draw;frameEl.oninput=draw;document.querySelector('#previous-frame').onclick=()=>step(-1);document.querySelector('#next-frame').onclick=()=>step(1);document.querySelector('#previous-scene').onclick=()=>{sceneEl.value=Math.max(0,Number(sceneEl.value)-1);sceneEl.onchange()};document.querySelector('#next-scene').onclick=()=>{sceneEl.value=Math.min(replay.scenes.length-1,Number(sceneEl.value)+1);sceneEl.onchange()};playEl.onclick=()=>{if(!timingAvailable)return;playing=!playing;playEl.textContent=playing?'⏸ Pause':'▶ Abspielen';clearInterval(timer);if(playing)timer=setInterval(()=>{const max=Number(frameEl.max);frameEl.value=Number(frameEl.value)>=max?0:Number(frameEl.value)+1;draw()},100/Number(speedEl.value))};speedEl.onchange=()=>{if(playing){playEl.onclick();playEl.onclick()}};if(isV2)playerEl.value=scene()?.focus_player_id||'';reset();</script></body></html>'''


if __name__ == "__main__":
    raise SystemExit(main())
