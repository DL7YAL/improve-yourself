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


def build_replay_payload(
    analysis: dict[str, Any], tick_rows: list[dict[str, Any]], max_frames: int = 256
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
        scenes.append({
            "round_number": marker["round_number"],
            "marker_player": marker["player"],
            "start_tick": start,
            "end_tick": end,
            "frames": frames,
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
        payload = build_replay_payload(analysis, _records(demo.ticks), max_frames=max_frames)
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
