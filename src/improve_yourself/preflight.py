from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from awpy import Demo

from .awpy_adapter import OPTIONAL_CHANNELS, _read_optional_channel, _records, _regular_round_numbers, _value
from .criteria import DEFAULT_PROFILE, profile_capabilities
from .importer import materialize_demo

PREFLIGHT_SCHEMA = "iy.analyzer_preflight/v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _side_label(side: str) -> str:
    return {"ct": "CT", "t": "T"}.get(side.lower(), "Nicht zuverlässig zuordenbar")


def build_preflight_payload(
    source: Path, header: dict[str, Any], rounds: list[dict[str, Any]], kill_rows: list[dict[str, Any]],
    available: list[str], missing: list[str], warnings: list[str], *, positions_available: bool, view_angles_available: bool,
) -> dict[str, Any]:
    regular_numbers = _regular_round_numbers(rounds)
    regular = [row for row in rounds if int(_value(row, ("round_num", "round_number"), 0) or 0) in regular_numbers]
    winner_counts = Counter(str(_value(row, ("winner",), "")).lower() for row in regular)
    player_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"kills": 0, "deaths": 0, "headshots": 0, "first_side": ""})
    for row in kill_rows:
        number = _value(row, ("round_num", "round_number"))
        try:
            if int(number) not in regular_numbers:
                continue
        except (TypeError, ValueError):
            continue
        attacker = str(_value(row, ("attacker_name", "attacker"), "") or "").strip()
        victim = str(_value(row, ("victim_name", "victim", "user_name"), "") or "").strip()
        if attacker:
            player_stats[attacker]["kills"] += 1
            player_stats[attacker]["headshots"] += int(bool(_value(row, ("headshot",), False)))
            player_stats[attacker]["first_side"] = player_stats[attacker]["first_side"] or str(_value(row, ("attacker_side",), "")).lower()
        if victim:
            player_stats[victim]["deaths"] += 1
            player_stats[victim]["first_side"] = player_stats[victim]["first_side"] or str(_value(row, ("victim_side",), "")).lower()
    players = []
    for name, stats in player_stats.items():
        side = stats["first_side"]
        players.append({"name": name, "side": _side_label(side), "kills": stats["kills"], "deaths": stats["deaths"], "headshots": stats["headshots"]})
    players.sort(key=lambda item: (-item["kills"], item["name"].casefold()))
    actual_available = [*available]
    if positions_available:
        actual_available.append("positions")
    if view_angles_available:
        actual_available.append("view_angles")
    return {
        "schema": PREFLIGHT_SCHEMA,
        "source_sha256": _sha256(source), "source_name": source.name, "profile": DEFAULT_PROFILE,
        "match": {"map_name": str(header.get("map_name", "") or "Unbekannt"), "regular_rounds": len(regular),
                  "teams": [{"id": "ct", "label": "CT", "rounds_won": winner_counts["ct"]}, {"id": "t", "label": "T", "rounds_won": winner_counts["t"]}],
                  "score_status": "available" if regular else "not_assessable", "players": players},
        "data_quality": {"available_channels": sorted(set(actual_available)), "missing_channels": sorted(set(missing)), "warnings": warnings},
        "criteria": profile_capabilities(actual_available, missing),
        "policy": {"changes_applied": False, "automated_cheat_verdict": False},
    }


def preflight_demo(source: Path, output_directory: Path, max_bytes: int = 2_000_000_000) -> Path:
    source = source.resolve()
    with materialize_demo(source, max_bytes=max_bytes) as demo_path:
        demo = Demo(str(demo_path), verbose=False)
        demo.parse(player_props=["pitch", "yaw"])
        rounds = _records(getattr(demo, "rounds", None))
        kill_rows = _records(getattr(demo, "kills", None))
        ticks = _records(getattr(demo, "ticks", None))
        available = ["rounds", "kills"] if rounds and kill_rows else []
        missing: list[str] = []
        warnings: list[str] = []
        for channel in OPTIONAL_CHANNELS:
            value, error = _read_optional_channel(demo, channel)
            if value is None:
                missing.append(channel)
                if error:
                    warnings.append(f"{channel}: nicht verfügbar")
            else:
                available.append(channel)
        sample = ticks[0] if ticks else {}
        positions = bool(sample and all(key in sample for key in ("X", "Y", "Z")))
        view_angles = bool(sample and all(key in sample for key in ("pitch", "yaw")))
        if not positions:
            missing.append("positions")
        if not view_angles:
            missing.append("view_angles")
        payload = build_preflight_payload(source, getattr(demo, "header", {}) or {}, rounds, kill_rows, available, missing, warnings, positions_available=positions, view_angles_available=view_angles)
    output_directory.mkdir(parents=True, exist_ok=True)
    path = output_directory / f"{payload['source_sha256'][:12]}.preflight.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
