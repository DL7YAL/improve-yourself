from __future__ import annotations

import argparse
import base64
import copy
import json
import mimetypes
from pathlib import Path
from typing import Any

from .replay import REPLAY_SCHEMA


def world_to_radar(x: float, y: float, pos_x: float, pos_y: float, scale: float) -> tuple[float, float]:
    """Project CS2 world coordinates into Source radar-image pixels."""
    if scale <= 0:
        raise ValueError("radar scale must be positive")
    return ((x - pos_x) / scale, (pos_y - y) / scale)


def _validate_replay(payload: dict[str, Any]) -> None:
    if payload.get("schema") != REPLAY_SCHEMA:
        raise ValueError(f"expected {REPLAY_SCHEMA} replay payload")
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


def active_players_at_tick(
    players: list[dict[str, Any]], events: list[dict[str, Any]], tick: int
) -> list[dict[str, Any]]:
    """Keep a player visible until, and only until, documented kill evidence says otherwise."""
    known_dead = {
        event["victim"]
        for event in events
        if isinstance(event, dict)
        and isinstance(event.get("victim"), str)
        and event["victim"]
        and isinstance(event.get("tick"), int)
        and event["tick"] <= tick
    }
    return [player for player in players if str(player.get("name", "")) not in known_dead]


def _viewer_replay(payload: dict[str, Any]) -> dict[str, Any]:
    """Add viewer-only active-player state without changing the replay payload contract."""
    viewer_payload = copy.deepcopy(payload)
    for scene in viewer_payload["scenes"]:
        events = scene.get("events") if isinstance(scene.get("events"), list) else []
        for frame in scene.get("frames", []):
            players = frame.get("players") if isinstance(frame.get("players"), list) else []
            frame["active_players"] = active_players_at_tick(players, events, int(frame["tick"]))
    return viewer_payload


def render_viewer(
    replay_path: Path,
    output_path: Path,
    *,
    radar_path: Path | None = None,
    pos_x: float = 0,
    pos_y: float = 0,
    scale: float = 1,
) -> Path:
    payload = json.loads(replay_path.read_text(encoding="utf-8"))
    _validate_replay(payload)
    if radar_path is not None and scale <= 0:
        raise ValueError("radar scale must be positive")

    model = {
        "replay": _viewer_replay(payload),
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
    parser = argparse.ArgumentParser(description="Create a self-contained iy.replay/v1 2D viewer")
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
<section class="card bar"><label>Szene <select id="scene"></select></label><button id="previous-scene">‹ Szene</button><button id="next-scene">Szene ›</button><button id="previous-frame">‹ Frame</button><button id="play">▶ Abspielen</button><button id="next-frame">Frame ›</button><label>Tempo <select id="speed"><option value="0.5">0,5×</option><option value="1" selected>1×</option><option value="2">2×</option></select></label><input id="frame" type="range" min="0" value="0"><span id="tick" class="pill"></span></section>
<section class="card stage"><canvas id="canvas" width="1024" height="1024"></canvas></section>
<section class="card meta"><span class="pill">T = orange · CT = blau · Linie = Blickrichtung</span><span class="pill">Tote verschwinden nur ab einem dokumentierten Kill-Tick.</span><span id="notice" class="pill warn"></span></section><section class="card"><strong id="scene-info"></strong><div id="event-info" class="pill"></div></section>
</main><script>const MODEL=__IY_VIEWER_MODEL__;
const replay=MODEL.replay,radar=MODEL.radar,canvas=document.querySelector('#canvas'),ctx=canvas.getContext('2d');
const sceneEl=document.querySelector('#scene'),frameEl=document.querySelector('#frame'),playEl=document.querySelector('#play'),speedEl=document.querySelector('#speed'),eventEl=document.querySelector('#event-info'),sceneInfoEl=document.querySelector('#scene-info');let playing=false,timer=null,img=null;
document.querySelector('#map').textContent=replay.map_name;document.querySelector('#quality').textContent=`${replay.scenes.length} Szenen · ${replay.data_quality.omitted_incomplete_player_snapshots} ausgelassene Snapshots`;
replay.scenes.forEach((s,i)=>sceneEl.add(new Option(`Runde ${s.round_number} · ${s.marker_player} · ${s.events?.length||0} Kills`,i)));
if(radar.data_uri){img=new Image();img.onload=draw;img.src=radar.data_uri}else document.querySelector('#notice').textContent='Kein Radar eingebettet – relative Weltansicht.';
function scene(){return replay.scenes[Number(sceneEl.value)||0]}function frame(){return scene()?.frames[Number(frameEl.value)||0]}
function project(p,players){if(img)return[(p.x-radar.pos_x)/radar.scale*canvas.width/img.naturalWidth,(radar.pos_y-p.y)/radar.scale*canvas.height/img.naturalHeight];
 const xs=players.map(q=>q.x),ys=players.map(q=>q.y),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),span=Math.max(maxX-minX,maxY-minY,1);return[100+(p.x-minX)/span*824,924-(p.y-minY)/span*824]}
function draw(){ctx.clearRect(0,0,1024,1024);if(img)ctx.drawImage(img,0,0,1024,1024);else{ctx.strokeStyle='#1c3046';for(let n=0;n<=1024;n+=128){ctx.beginPath();ctx.moveTo(n,0);ctx.lineTo(n,1024);ctx.stroke();ctx.beginPath();ctx.moveTo(0,n);ctx.lineTo(1024,n);ctx.stroke()}}
 const f=frame();if(!f)return;const s=scene(),index=Number(frameEl.value);document.querySelector('#tick').textContent=`Tick ${f.tick} · Frame ${index+1}/${s.frames.length}`;sceneInfoEl.textContent=`Runde ${s.round_number} · Multi-Kill: ${s.marker_player}`;const nearby=(s.events||[]).filter(e=>Math.abs(e.tick-f.tick)<=Math.max(1,(s.end_tick-s.start_tick)/s.frames.length));eventEl.textContent=nearby.length?nearby.map(e=>`Kill: ${e.attacker} → ${e.victim} (${e.weapon})${e.marker_multikill?' · Multi-Kill':''}`).join(' | '):'Kein Kill am aktuellen Snapshot.';
 const activePlayers=f.active_players||f.players;for(const p of activePlayers){const [x,y]=project(p,activePlayers),color=p.side.toUpperCase()==='CT'?'#55aaff':'#ff9f43',a=p.yaw*Math.PI/180;ctx.strokeStyle=color;ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+Math.cos(a)*34,y-Math.sin(a)*34);ctx.stroke();ctx.fillStyle=color;ctx.beginPath();ctx.arc(x,y,10,0,Math.PI*2);ctx.fill();ctx.font='16px system-ui';ctx.fillStyle='#fff';ctx.fillText(p.name,x+14,y-12)}}
function step(delta){const max=Number(frameEl.max);frameEl.value=Math.min(max,Math.max(0,Number(frameEl.value)+delta));draw()}
function reset(){playing=false;clearInterval(timer);playEl.textContent='▶ Abspielen';const s=scene();frameEl.max=Math.max(0,(s?.frames.length||1)-1);frameEl.value=0;draw()}
sceneEl.onchange=reset;frameEl.oninput=draw;document.querySelector('#previous-frame').onclick=()=>step(-1);document.querySelector('#next-frame').onclick=()=>step(1);document.querySelector('#previous-scene').onclick=()=>{sceneEl.value=Math.max(0,Number(sceneEl.value)-1);reset()};document.querySelector('#next-scene').onclick=()=>{sceneEl.value=Math.min(replay.scenes.length-1,Number(sceneEl.value)+1);reset()};playEl.onclick=()=>{playing=!playing;playEl.textContent=playing?'⏸ Pause':'▶ Abspielen';clearInterval(timer);if(playing)timer=setInterval(()=>{const max=Number(frameEl.max);frameEl.value=Number(frameEl.value)>=max?0:Number(frameEl.value)+1;draw()},100/Number(speedEl.value))};speedEl.onchange=()=>{if(playing){playEl.onclick() ;playEl.onclick()}};reset();</script></body></html>'''


if __name__ == "__main__":
    raise SystemExit(main())
