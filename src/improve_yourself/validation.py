from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .model import SCHEMA_VERSION

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
QUALITY_STATUSES = {"ok", "limited", "not_assessable"}


def validate_analysis_payload(payload: Any) -> list[str]:
    """Return portable analysis-contract violations without exposing match data."""
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["analysis root must be an object"]

    if payload.get("schema") != SCHEMA_VERSION:
        errors.append(f"schema must be {SCHEMA_VERSION!r}")
    source_hash = payload.get("source_sha256")
    if not isinstance(source_hash, str) or not SHA256_PATTERN.fullmatch(source_hash):
        errors.append("source_sha256 must be 64 lowercase hexadecimal characters")
    if not isinstance(payload.get("source_name"), str) or not payload.get("source_name"):
        errors.append("source_name must be a non-empty string")
    if not isinstance(payload.get("map_name"), str):
        errors.append("map_name must be a string")
    tickrate = payload.get("tickrate")
    if tickrate is not None and (not isinstance(tickrate, (int, float)) or tickrate <= 0):
        errors.append("tickrate must be null or a positive number")
    disclaimer = payload.get("disclaimer")
    if not isinstance(disclaimer, str) or "kein Cheat-Nachweis" not in disclaimer:
        errors.append("disclaimer must state that markers are not cheat proof")

    kills = payload.get("kills")
    if not isinstance(kills, list):
        errors.append("kills must be a list")
        kills = []
    valid_kills: list[dict[str, Any]] = []
    for index, kill in enumerate(kills):
        if not isinstance(kill, dict):
            errors.append(f"kills[{index}] must be an object")
            continue
        if not isinstance(kill.get("round_number"), int) or kill["round_number"] < 0:
            errors.append(f"kills[{index}].round_number must be a non-negative integer")
        if not isinstance(kill.get("tick"), int) or kill["tick"] < 0:
            errors.append(f"kills[{index}].tick must be a non-negative integer")
        for field in ("attacker", "victim", "weapon"):
            if not isinstance(kill.get(field), str):
                errors.append(f"kills[{index}].{field} must be a string")
        if not isinstance(kill.get("headshot"), bool):
            errors.append(f"kills[{index}].headshot must be boolean")
        if isinstance(kill.get("round_number"), int) and isinstance(kill.get("attacker"), str):
            valid_kills.append(kill)

    expected_counts = Counter(
        (kill["round_number"], kill["attacker"])
        for kill in valid_kills
        if kill["attacker"]
    )
    multikills = payload.get("multikills")
    if not isinstance(multikills, list):
        errors.append("multikills must be a list")
        multikills = []
    seen_markers: set[tuple[int, str]] = set()
    for index, marker in enumerate(multikills):
        if not isinstance(marker, dict):
            errors.append(f"multikills[{index}] must be an object")
            continue
        round_number = marker.get("round_number")
        player = marker.get("player")
        if not isinstance(round_number, int) or round_number < 0:
            errors.append(f"multikills[{index}].round_number must be a non-negative integer")
        if not isinstance(player, str) or not player:
            errors.append(f"multikills[{index}].player must be a non-empty string")
        if not isinstance(round_number, int) or not isinstance(player, str):
            continue
        key = (round_number, player)
        if key in seen_markers:
            errors.append(f"multikills[{index}] duplicates a player/round marker")
        seen_markers.add(key)
        count = marker.get("kill_count")
        victims = marker.get("victims")
        if not isinstance(count, int) or count < 3:
            errors.append(f"multikills[{index}].kill_count must be at least 3")
        if not isinstance(victims, list) or not all(isinstance(value, str) for value in victims):
            errors.append(f"multikills[{index}].victims must be a list of strings")
        elif isinstance(count, int) and len(victims) != count:
            errors.append(f"multikills[{index}] victim count must equal kill_count")
        first_tick = marker.get("first_tick")
        last_tick = marker.get("last_tick")
        if not isinstance(first_tick, int) or not isinstance(last_tick, int) or first_tick > last_tick:
            errors.append(f"multikills[{index}] tick range is invalid")
        if key not in expected_counts or expected_counts[key] != count:
            errors.append(f"multikills[{index}] does not match round-wide kill data")

    expected_markers = {key for key, count in expected_counts.items() if count >= 3}
    if seen_markers != expected_markers:
        errors.append("multikills must contain exactly one marker per player/round with at least 3 kills")

    quality = payload.get("data_quality")
    if not isinstance(quality, dict):
        errors.append("data_quality must be an object")
        quality = {}
    status = quality.get("status")
    missing = quality.get("missing_channels")
    warnings = quality.get("warnings")
    available = payload.get("available_channels")
    if status not in QUALITY_STATUSES:
        errors.append("data_quality.status is invalid")
    if not isinstance(missing, list) or not all(isinstance(value, str) for value in missing):
        errors.append("data_quality.missing_channels must be a list of strings")
        missing = []
    if not isinstance(warnings, list) or not all(isinstance(value, str) for value in warnings):
        errors.append("data_quality.warnings must be a list of strings")
        warnings = []
    if not isinstance(available, list) or not all(isinstance(value, str) for value in available):
        errors.append("available_channels must be a list of strings")
        available = []
    if set(missing) & set(available):
        errors.append("available and missing channels must not overlap")
    if "footsteps" in missing:
        if status not in {"limited", "not_assessable"}:
            errors.append("missing footsteps must limit assessability")
        if not any("Footstep-Ereignisse fehlen" in warning for warning in warnings):
            errors.append("missing footsteps must produce the material limitation warning")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an iy.analysis/v1 result")
    parser.add_argument("analysis", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.analysis.read_text(encoding="utf-8"))
    errors = validate_analysis_payload(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("PASS: iy.analysis/v1 contract and invariants are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
