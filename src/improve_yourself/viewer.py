"""Read-only Improve 2D presentation from canonical ReplayController truth."""
from __future__ import annotations
import argparse, base64, json, mimetypes
from pathlib import Path
from typing import Any
from .replay import REPLAY_SCHEMA
from .replay_contract import REPLAY_V2_SCHEMA
from .replay_controller import ReplayContext, ReplayController
from .replay_store import ReplayStore

def world_to_radar(x: float,y: float,pos_x: float,pos_y: float,scale: float)->tuple[float,float]:
    if scale<=0: raise ValueError("radar scale must be positive")
    return (x-pos_x)/scale,(pos_y-y)/scale
def visible_players_at_frame(players:list[dict[str,Any]])->list[dict[str,Any]]: return [p for p in players if p.get("alive") is not False]
def _uri(path:Path|None)->str:
    if path is None:return ""
    return "data:%s;base64,%s"%(mimetypes.guess_type(path.name)[0] or "application/octet-stream",base64.b64encode(path.read_bytes()).decode())
def _root()->Path:return Path(__file__).resolve().parents[2]
def viewer_state(store:ReplayStore,context:ReplayContext)->dict[str,Any]:
    ids={p["player_id"]:p for p in store.manifest["players"]}; players=[]
    for p in context.frame.get("players",[]):
        q=p.get("position"); yaw=p.get("view_yaw_deg")
        if q is not None and yaw is not None: players.append({"player_id":p["player_id"],"name":ids.get(p["player_id"],{}).get("display_name",p["player_id"]),"side":p.get("team","unknown"),"x":q["x"],"y":q["y"],"yaw":yaw,"alive":p.get("alive")})
    return {"schema":"iy.viewer_state/v1","map_id":store.manifest["source"]["map_id"],"round_number":context.current_round,"requested_tick":context.requested_tick,"resolved_tick":context.resolved_tick,"selected_player_id":context.selected_player_id,"selected_player":{"player_id":context.selected_player_id},"view_mode":context.view_mode,"frame":{"tick":context.frame["tick"],"players":players}}
def render_viewer(replay_path:Path,output_path:Path,*,radar_path:Path|None=None,pos_x:float=0,pos_y:float=0,scale:float=1,scenes:list[dict[str,Any]]|None=None)->Path:
    payload=json.loads(replay_path.read_text(encoding="utf-8"))
    if payload.get("schema")==REPLAY_SCHEMA:
        # Legacy artifacts remain viewable; the product path below is V2 only.
        frame=payload["scenes"][0]["frames"][0]; state={"schema":"iy.viewer_state/v1","map_id":payload["map_name"],"round_number":payload["scenes"][0]["round_number"],"requested_tick":frame["tick"],"resolved_tick":frame["tick"],"selected_player_id":None,"view_mode":"tactical_2d","frame":frame}; model={"state":state,"transform":{"origin_world":{"x":pos_x,"y":pos_y},"world_units_per_pixel":scale},"background":_uri(radar_path),"background_kind":"legacy"}; output_path.parent.mkdir(parents=True,exist_ok=True); output_path.write_text(_HTML.replace("__MODEL__",json.dumps(model,separators=(",",":")).replace("<","\\u003c")),encoding="utf-8"); return output_path
    if payload.get("schema")!=REPLAY_V2_SCHEMA: raise ValueError(f"expected {REPLAY_SCHEMA} or {REPLAY_V2_SCHEMA} replay payload")
    store=ReplayStore(replay_path); controller=ReplayController(store); scene=(scenes or store.manifest.get("scenes",[])); scene=scene[0] if scene else None; context=controller.seek(scene["round_number"],scene.get("review_tick",scene.get("tick"))) if scene else controller.snapshot(); context=controller.select_player(scene.get("focus_player_id")) if scene and scene.get("focus_player_id") else context; state=viewer_state(store,context); meta=json.loads((_root()/"resources/map_overviews/maps"/(state["map_id"]+".json")).read_text()); bg=radar_path or _root()/"resources/generated_overviews"/state["map_id"]/"overview.svg"; model={"state":state,"transform":meta["transform"],"background":_uri(bg if bg.is_file() else None),"background_kind":"local_override" if radar_path else "improve_generated"}; output_path.parent.mkdir(parents=True,exist_ok=True); output_path.write_text(_HTML.replace("__MODEL__",json.dumps(model,separators=(",",":")).replace("<","\\u003c")),encoding="utf-8"); return output_path
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("replay",type=Path);p.add_argument("--output",type=Path,default=Path("viewer.html"));p.add_argument("--radar",type=Path);a=p.parse_args();print(render_viewer(a.replay,a.output,radar_path=a.radar));return 0
_HTML='''<!doctype html><meta charset="utf-8"><title>Improve Viewer</title><style>body{margin:0;background:#08111d;color:#edf5ff;font:14px system-ui}.shell{max-width:1280px;margin:auto;padding:20px}.head,.panel{background:#101f31;border:1px solid #29435e;border-radius:14px;padding:16px}.grid{display:grid;grid-template-columns:1fr 240px;gap:16px;margin-top:16px}.stage{position:relative;aspect-ratio:1}.stage img{width:100%;height:100%}.m{position:absolute;width:14px;height:14px;border-radius:50%;transform:translate(-50%,-50%);background:#ff9d3f;border:2px solid white}.ct{background:#3b9bff}.sel{outline:4px solid #f5d66b}.player{padding:8px;margin:6px;background:#162b42;border-radius:7px}</style><main class=shell><header class=head><b>IMPROVE YOURSELF · TACTICAL VIEWER</b><div id=c></div></header><section class=grid><div class=panel><div id=s class=stage></div></div><aside class=panel><b>Spieler</b><div id=p></div></aside></section></main><script>const M=__MODEL__,S=M.state,T=M.transform,O=T.origin_world,sc=T.world_units_per_pixel,s=document.querySelector('#s'),i=new Image;i.src=M.background;s.append(i);c.textContent=`${S.map_id} · Runde ${S.round_number} · Tick ${S.resolved_tick} · angefordert ${S.requested_tick}`;for(const x of S.frame.players.filter(x=>x.alive!==false)){let e=document.createElement('i');e.className='m '+(x.side==='CT'?'ct':'')+(x.player_id===S.selected_player_id?' sel':'');e.style.left=(x.x-O.x)/sc/10.24+'%';e.style.top=(O.y-x.y)/sc/10.24+'%';s.append(e);let r=document.createElement('div');r.className='player';r.textContent=x.name+' · '+x.side;p.append(r)}</script>'''
if __name__=="__main__":raise SystemExit(main())
