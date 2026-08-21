from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from .replay_store import ReplayStore

FLOW_SCHEMA = "iy.analysis_flow/v1"
SelectionMode = Literal["full_demo", "player_select"]


@dataclass(frozen=True)
class PlayerSelection:
    mode: SelectionMode = "full_demo"
    player_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnalysisProfile:
    profile_id: str = "review_v1"
    purpose: str = "review"
    pre_ticks: int = 128
    post_ticks: int = 256
    merge_gap_ticks: int = 96


def _truthy(value: Any) -> bool:
    return value is True or (isinstance(value, (int, float)) and value > 0)


def _roster(manifest: dict[str, Any], chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    teams: dict[str, set[str]] = defaultdict(set)
    initial_team: dict[str, str] = {}
    for chunk in chunks:
        for frame in chunk["frames"]:
            for state in frame.get("players", []):
                if state.get("team") in ("CT", "T"):
                    teams[state["player_id"]].add(state["team"])
                    initial_team.setdefault(state["player_id"], state["team"])
    return [
        {
            "player_id": item["player_id"],
            "display_name": item.get("display_name") or item["player_id"],
            "steam_id": item.get("steam_id"),
            "teams": sorted(teams.get(item["player_id"], {"unknown"})),
            "initial_team": initial_team.get(item["player_id"], "unknown"),
        }
        for item in manifest["players"]
    ]


def build_analysis_flow(
    manifest: dict[str, Any],
    chunks: list[dict[str, Any]],
    *,
    selection: PlayerSelection = PlayerSelection(),
    profile: AnalysisProfile = AnalysisProfile(),
) -> dict[str, Any]:
    known_ids = {item["player_id"] for item in manifest["players"]}
    selected_ids = tuple(dict.fromkeys(selection.player_ids))
    chosen = set(selected_ids)
    if selection.mode == "player_select" and not chosen:
        raise ValueError("player_select requires at least one player")
    if selection.mode == "full_demo" and chosen:
        raise ValueError("full_demo must not carry explicit player IDs")
    unknown = chosen - known_ids
    if unknown:
        raise ValueError(f"unknown selected player IDs: {sorted(unknown)}")

    indicators: list[dict[str, Any]] = []
    kills_by_round: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        round_number = int(chunk["round_number"])
        for frame in chunk["frames"]:
            for event in frame.get("events", []):
                if event.get("type") != "kill" or len(event.get("player_ids", [])) < 2:
                    continue
                attacker, victim = event["player_ids"][:2]
                marker = {
                    "indicator_id": f"kill:{event['event_id']}", "type": "kill", "round_number": round_number,
                    "tick": event["tick"], "player_ids": [attacker, victim], "focus_player_id": attacker,
                    "event_ids": [event["event_id"]], "evidence": ["awpy:kills"],
                }
                indicators.append(marker)
                kills_by_round[round_number].append(marker)
                details = event.get("details", {})
                qualifiers = (
                    ("headshot", _truthy(details.get("headshot"))),
                    ("wallbang", _truthy(details.get("penetrated"))),
                    ("smoke_kill", _truthy(details.get("thrusmoke"))),
                    ("blind_kill", _truthy(details.get("attacker_blind"))),
                )
                for kind, present in qualifiers:
                    if present:
                        indicators.append({**marker, "indicator_id": f"{kind}:{event['event_id']}", "type": kind})

    for round_number, kills in kills_by_round.items():
        ordered = sorted(kills, key=lambda item: item["tick"])
        if ordered:
            indicators.append({**ordered[0], "indicator_id": f"entry:{ordered[0]['event_ids'][0]}", "type": "entry"})
        per_attacker: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for marker in ordered:
            per_attacker[marker["focus_player_id"]].append(marker)
        for attacker, markers in per_attacker.items():
            for index in range(1, len(markers)):
                pair = markers[index - 1 : index + 1]
                if pair[1]["tick"] - pair[0]["tick"] <= 320:
                    indicators.append({
                        "indicator_id": f"multi:{round_number}:{attacker}:{pair[0]['tick']}:{pair[1]['tick']}",
                        "type": "multi_kill", "round_number": round_number, "tick": pair[1]["tick"],
                        "player_ids": sorted(set(pair[0]["player_ids"] + pair[1]["player_ids"])),
                        "focus_player_id": attacker, "event_ids": pair[0]["event_ids"] + pair[1]["event_ids"],
                        "evidence": ["rule:two_kills_same_attacker_within_320_ticks"],
                    })

    selected_indicators = [
        item for item in indicators
        if selection.mode == "full_demo" or chosen.intersection(item["player_ids"])
    ]
    matches = [
        {
            "rule_id": f"objective_{item['type']}", "indicator_ids": [item["indicator_id"]],
            "round_number": item["round_number"], "tick": item["tick"], "focus_player_id": item["focus_player_id"],
            "player_ids": item["player_ids"], "event_ids": item["event_ids"], "anchor_type": item["type"],
        }
        for item in selected_indicators
    ]
    matches.sort(key=lambda item: (item["round_number"], item["tick"], item["rule_id"]))

    scenes: list[dict[str, Any]] = []
    for match in matches:
        start, end = max(0, match["tick"] - profile.pre_ticks), match["tick"] + profile.post_ticks
        if scenes and scenes[-1]["round_number"] == match["round_number"] and start <= scenes[-1]["end_tick"] + profile.merge_gap_ticks:
            scene = scenes[-1]
            scene["end_tick"] = max(scene["end_tick"], end)
            scene["review_tick"] = min(scene["review_tick"], match["tick"])
            scene["anchor_types"] = sorted(set(scene["anchor_types"] + [match["anchor_type"]]))
            scene["rule_ids"] = sorted(set(scene["rule_ids"] + [match["rule_id"]]))
            scene["event_ids"] = sorted(set(scene["event_ids"] + match["event_ids"]))
            scene["player_ids"] = sorted(set(scene["player_ids"] + match["player_ids"]))
            scene["marker_ticks"] = sorted(set(scene["marker_ticks"] + [match["tick"]]))
            continue
        scenes.append({
            "scene_id": f"r{match['round_number']}-t{match['tick']}-{len(scenes)}",
            "round_number": match["round_number"], "start_tick": start, "review_tick": match["tick"], "end_tick": end,
            "focus_player_id": match["focus_player_id"], "anchor_types": [match["anchor_type"]],
            "rule_ids": [match["rule_id"]], "event_ids": list(match["event_ids"]),
            "player_ids": list(match["player_ids"]), "marker_ticks": [match["tick"]],
            "review": {"command": f"demo_gototick {match['tick']}", "tick": match["tick"]},
        })
    return {
        "schema": FLOW_SCHEMA,
        "source": manifest["source"],
        "roster": _roster(manifest, chunks),
        "selection": {"mode": selection.mode, "player_ids": selected_ids},
        "profile": asdict(profile),
        "supported_profile_purposes": ["review", "highlight", "coaching", "custom"],
        "rounds": [
            {
                "round_number": chunk["round_number"],
                "first_tick": chunk["frames"][0]["tick"] if chunk["frames"] else None,
                "last_tick": chunk["frames"][-1]["tick"] if chunk["frames"] else None,
                "frame_count": len(chunk["frames"]),
            }
            for chunk in chunks
        ],
        "architecture": ["indicators", "rules", "analysis_profile", "analysis_result"],
        "rule_policy": {"objective_anchors_only": True, "weak_single_indicator_scenes": False},
        "indicators": selected_indicators,
        "rule_matches": matches,
        "scenes": scenes,
        "timeline": [{"tick": scene["review_tick"], "scene_id": scene["scene_id"], "anchor_types": scene["anchor_types"]} for scene in scenes],
        "limitations": {
            "trade": "disabled unless a reliable time basis and victim-attacker relation are available",
            "sound_information_rules": "not emitted from missing or incomplete evidence",
        },
    }


def build_from_store(store: ReplayStore, selection: PlayerSelection = PlayerSelection()) -> dict[str, Any]:
    chunks = [store.load_round(number) for number in store.round_numbers]
    return build_analysis_flow(store.manifest, chunks, selection=selection)


def render_analysis_review(payload: dict[str, Any], output: Path) -> Path:
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_REVIEW_HTML.replace("__DATA__", data), encoding="utf-8")
    return output


_REVIEW_HTML = '''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Improve Yourself Demo Review</title><style>
body{font:15px system-ui;background:#08111e;color:#edf3fb;margin:0;padding:24px}main{max-width:1100px;margin:auto}.card{background:#111f32;border:1px solid #2a3d58;border-radius:12px;padding:16px;margin:14px 0}button,select{background:#162842;color:#fff;border:1px solid #496382;border-radius:7px;padding:8px;margin:4px}.teams{display:grid;grid-template-columns:1fr 1fr;gap:12px}.scene{border-top:1px solid #2a3d58;padding:12px 0}.pill{display:inline-block;background:#263b58;border-radius:99px;padding:4px 9px;margin:3px}.muted{color:#9eb1c9}code{color:#8bd5ff}@media(max-width:650px){.teams{grid-template-columns:1fr}}</style></head><body><main><h1>Demo → Review</h1><div id="summary" class="card"></div><section class="card"><h2>Teams & Spielerauswahl</h2><div class="teams"><div><h3>CT</h3><div id="ct"></div></div><div><h3>T</h3><div id="t"></div></div></div><p><button id="full">Full Demo</button><button id="ctAll">CT</button><button id="tAll">T</button><button id="reset">Reset</button></p><select id="player"></select><button id="add">+ Add Player</button><div id="chosen"></div></section><section class="card"><h2>Timeline / Szenen</h2><div id="scenes"></div></section></main><script>const data=__DATA__,selected=new Set();let mode='full_demo';const byId=new Map(data.roster.map(p=>[p.player_id,p]));
function team(side){return data.roster.filter(p=>p.initial_team===side).map(p=>p.display_name).join(' · ')||'Keine belegte Line-up'}ct.textContent=team('CT');t.textContent=team('T');
function draw(){summary.textContent=`${data.source.map_id} · ${data.roster.length} Spieler · ${data.scenes.length} zusammengeführte Szenen · ${mode==='full_demo'?'Full Demo':selected.size+' Spieler gewählt'}`;chosen.innerHTML=[...selected].map(id=>`<span class="pill">${byId.get(id)?.display_name||id}</span>`).join('');player.innerHTML='';for(const p of data.roster.filter(p=>!selected.has(p.player_id)))player.add(new Option(`${p.display_name} · ${p.teams.join('/')}`,p.player_id));const visible=data.scenes.filter(s=>mode==='full_demo'||s.player_ids.some(id=>selected.has(id)));scenes.innerHTML=visible.map(s=>`<div class="scene"><strong>Runde ${s.round_number} · ${s.anchor_types.join(', ')}</strong><div class="muted">Kontext ${s.start_tick}–${s.end_tick} · Marker ${s.marker_ticks.join(', ')}</div><code>${s.review.command}</code></div>`).join('')||'<p>Keine Szenen für diese Auswahl.</p>'}
full.onclick=()=>{mode='full_demo';selected.clear();draw()};reset.onclick=()=>{mode='player_select';selected.clear();draw()};add.onclick=()=>{if(player.value){mode='player_select';selected.add(player.value);draw()}};ctAll.onclick=()=>{mode='player_select';data.roster.filter(p=>p.initial_team==='CT').forEach(p=>selected.add(p.player_id));draw()};tAll.onclick=()=>{mode='player_select';data.roster.filter(p=>p.initial_team==='T').forEach(p=>selected.add(p.player_id));draw()};draw();</script></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Build neutral V1 scenes from an iy.replay/v2 store")
    parser.add_argument("replay", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/analysis-flow.json"))
    parser.add_argument("--review", type=Path)
    parser.add_argument("--player", action="append", default=[])
    args = parser.parse_args()
    selection = PlayerSelection("player_select", tuple(dict.fromkeys(args.player))) if args.player else PlayerSelection()
    payload = build_from_store(ReplayStore(args.replay), selection)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.review:
        render_analysis_review(payload, args.review)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
