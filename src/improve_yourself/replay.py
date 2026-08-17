from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from awpy import Demo

from .importer import materialize_demo
from .validation import validate_analysis_payload

REPLAY_SCHEMA = "iy.replay/v1"


def _records(frame: Any) -> list[dict[str, Any]]:
    converter = getattr(frame, "to_dicts", None)
    return converter() if converter else list(frame or [])


def _finite_point(row: dict[str, Any], prefix: str = "") -> dict[str, float] | None:
    try:
        return {"x": float(row[f"{prefix}X"]), "y": float(row[f"{prefix}Y"]), "z": float(row[f"{prefix}Z"])}
    except (KeyError, TypeError, ValueError):
        return None


def _utility_type(value: object) -> str | None:
    text = str(value)
    if "Smoke" in text:
        return "smoke"
    if "Flash" in text:
        return "flash"
    if "HE" in text:
        return "he"
    if "Molotov" in text or "Incendiary" in text:
        return "fire"
    if "Decoy" in text:
        return "decoy"
    return None


def _sample_path(rows: list[dict[str, Any]], maximum: int = 24) -> list[dict[str, float]]:
    points = [point for row in sorted(rows, key=lambda item: int(item.get("tick", 0))) if (point := _finite_point(row))]
    if len(points) <= maximum:
        return points
    return [points[round(index * (len(points) - 1) / (maximum - 1))] for index in range(maximum)]


def _scene_utility(
    round_number: int, start: int, end: int, grenade_rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]], inferno_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in [*smoke_rows, *inferno_rows]:
        if int(row.get("round_num", -1)) != round_number:
            continue
        try:
            item_start, item_end = int(row.get("start_tick")), int(row.get("end_tick"))
        except (TypeError, ValueError):
            continue
        if item_end < start or item_start > end:
            continue
        target, origin = _finite_point(row), _finite_point(row, "thrower_")
        if target is None:
            continue
        kind = "smoke" if row in smoke_rows else "fire"
        items.append({"kind": kind, "thrower": str(row.get("thrower_name", "")), "start_tick": item_start, "end_tick": item_end, "origin": origin, "target": target, "path": [], "area": True})
    grouped: dict[tuple[object, str], list[dict[str, Any]]] = {}
    for row in grenade_rows:
        if int(row.get("round_num", -1)) != round_number:
            continue
        tick = int(row.get("tick", -1))
        if not start <= tick <= end:
            continue
        kind = _utility_type(row.get("grenade_type"))
        if kind is None:
            continue
        grouped.setdefault((row.get("entity_id"), kind), []).append(row)
    for (_, kind), rows in grouped.items():
        path = _sample_path(rows)
        if not path:
            continue
        items.append({"kind": kind, "thrower": str(rows[0].get("thrower", "")), "start_tick": int(rows[0].get("tick", 0)), "end_tick": int(rows[-1].get("tick", 0)), "origin": path[0], "target": path[-1], "path": path, "area": False})
    return sorted(items, key=lambda item: (item["start_tick"], item["kind"]))


def build_replay_payload(
    analysis: dict[str, Any], tick_rows: list[dict[str, Any]], max_frames: int = 256,
    grenade_rows: list[dict[str, Any]] | None = None, smoke_rows: list[dict[str, Any]] | None = None, inferno_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if max_frames <= 0:
        raise ValueError("max_frames must be positive")
    errors = validate_analysis_payload(analysis)
    if errors:
        raise ValueError("invalid analysis payload: " + "; ".join(errors))

    scenes: list[dict[str, Any]] = []
    omitted_snapshots = 0
    for marker in analysis["multikills"]:
        start, end = marker["first_tick"], marker["last_tick"]
        rows = [
            row for row in tick_rows
            if start <= int(row.get("tick", -1)) <= end
            and int(row.get("round_num", -1)) == marker["round_number"]
        ]
        ticks = sorted({int(row["tick"]) for row in rows})
        if len(ticks) <= max_frames:
            selected = set(ticks)
        elif max_frames == 1:
            selected = {ticks[-1]}
        else:
            selected = {
                ticks[round(index * (len(ticks) - 1) / (max_frames - 1))]
                for index in range(max_frames)
            }
        frames = []
        for tick in sorted(selected):
            players = []
            for row in rows:
                if int(row["tick"]) != tick:
                    continue
                numeric = [row.get(key) for key in ("X", "Y", "Z", "pitch", "yaw")]
                if any(value is None for value in numeric):
                    omitted_snapshots += 1
                    continue
                players.append({
                    "name": str(row.get("name", "")),
                    "side": str(row.get("side", "")),
                    "x": float(row.get("X", 0.0)),
                    "y": float(row.get("Y", 0.0)),
                    "z": float(row.get("Z", 0.0)),
                    "pitch": float(row.get("pitch", 0.0)),
                    "yaw": float(row.get("yaw", 0.0)),
                })
            frames.append({"tick": tick, "players": sorted(players, key=lambda p: (p["side"], p["name"]))})
        events = [
            {
                "tick": kill["tick"], "attacker": kill["attacker"], "victim": kill["victim"],
                "weapon": kill["weapon"], "headshot": kill["headshot"],
                "marker_multikill": kill["attacker"] == marker["player"],
            }
            for kill in analysis["kills"]
            if kill["round_number"] == marker["round_number"] and start <= kill["tick"] <= end
        ]
        scenes.append({
            "round_number": marker["round_number"],
            "marker_player": marker["player"],
            "start_tick": start,
            "end_tick": end,
            "frames": frames,
            "events": events,
            "utility": _scene_utility(marker["round_number"], start, end, grenade_rows or [], smoke_rows or [], inferno_rows or []),
        })
    return {
        "schema": REPLAY_SCHEMA,
        "source_sha256": analysis["source_sha256"],
        "map_name": analysis["map_name"],
        "selection": "multikill_first_to_last_kill",
        "sampling": {"method": "uniform_unique_ticks", "max_frames_per_scene": max_frames},
        "coordinate_space": "cs2_world",
        "data_quality": {"omitted_incomplete_player_snapshots": omitted_snapshots},
        "scenes": scenes,
    }


def export_replay(source: Path, analysis_path: Path, output: Path, max_frames: int = 256) -> Path:
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != analysis.get("source_sha256"):
        raise ValueError("demo and analysis source hashes differ")
    with materialize_demo(source.resolve(), max_bytes=2_000_000_000) as demo_path:
        demo = Demo(str(demo_path), verbose=False)
        demo.parse(player_props=["pitch", "yaw"])
        payload = build_replay_payload(analysis, _records(demo.ticks), max_frames=max_frames, grenade_rows=_records(demo.grenades), smoke_rows=_records(demo.smokes), inferno_rows=_records(demo.infernos))
    output.mkdir(parents=True, exist_ok=True)
    destination = output / f"{digest[:12]}.replay.json"
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Export an iy.replay/v1 2D viewer artifact")
    parser.add_argument("demo", type=Path)
    parser.add_argument("analysis", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/replay"))
    parser.add_argument("--max-frames", type=int, default=256)
    args = parser.parse_args()
    print(export_replay(args.demo, args.analysis, args.output, args.max_frames))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
