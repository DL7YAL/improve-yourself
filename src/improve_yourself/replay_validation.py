from __future__ import annotations

import re
from typing import Any

from .replay_contract import REPLAY_V2_SCHEMA, ROUND_CHUNK_SCHEMA

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
CAPABILITY_LEVELS = {"full", "partial", "unavailable"}


def validate_replay_manifest(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["replay root must be an object"]
    if payload.get("schema") != REPLAY_V2_SCHEMA:
        errors.append(f"schema must be {REPLAY_V2_SCHEMA!r}")
    source = payload.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
        source = {}
    digest = source.get("sha256")
    if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
        errors.append("source.sha256 must be 64 lowercase hexadecimal characters")
    if not isinstance(source.get("map_id"), str) or not source.get("map_id"):
        errors.append("source.map_id must be a non-empty string")
    tick_rate = source.get("tick_rate")
    if tick_rate is not None and (not isinstance(tick_rate, (int, float)) or tick_rate <= 0):
        errors.append("source.tick_rate must be null or positive")
    if payload.get("coordinate_space") != "cs2_world":
        errors.append("coordinate_space must be 'cs2_world'")

    players = payload.get("players")
    if not isinstance(players, list):
        errors.append("players must be a list")
        players = []
    ids: set[str] = set()
    for index, player in enumerate(players):
        player_id = player.get("player_id") if isinstance(player, dict) else None
        if not isinstance(player_id, str) or not player_id:
            errors.append(f"players[{index}].player_id must be non-empty")
        elif player_id in ids:
            errors.append(f"players[{index}].player_id is duplicated")
        else:
            ids.add(player_id)

    rounds = payload.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        errors.append("rounds must be a non-empty list")
        rounds = []
    previous = 0
    for index, round_item in enumerate(rounds):
        number = round_item.get("round_number") if isinstance(round_item, dict) else None
        if not isinstance(number, int) or number <= previous:
            errors.append(f"rounds[{index}].round_number must be strictly increasing")
        elif number > 0:
            previous = number
        for field in ("first_tick", "last_tick", "frame_count"):
            if not isinstance(round_item.get(field), int) or round_item[field] < 0:
                errors.append(f"rounds[{index}].{field} must be a non-negative integer")
        if isinstance(round_item, dict) and round_item.get("first_tick", 0) > round_item.get("last_tick", 0):
            errors.append(f"rounds[{index}] tick range is invalid")
        if not isinstance(round_item.get("chunk"), str) or not round_item["chunk"]:
            errors.append(f"rounds[{index}].chunk must be non-empty")

    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, dict):
        errors.append("capabilities must be an object")
    else:
        for key, value in capabilities.items():
            if key == "map_geometry":
                if value not in {"verified", "mismatch", "unavailable"}:
                    errors.append("capabilities.map_geometry is invalid")
            elif value not in CAPABILITY_LEVELS:
                errors.append(f"capabilities.{key} is invalid")
    return errors


def validate_round_chunk(payload: Any, known_player_ids: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["round chunk root must be an object"]
    if payload.get("schema") != ROUND_CHUNK_SCHEMA:
        errors.append(f"schema must be {ROUND_CHUNK_SCHEMA!r}")
    round_number = payload.get("round_number")
    if not isinstance(round_number, int) or round_number <= 0:
        errors.append("round_number must be positive")
    frames = payload.get("frames")
    if not isinstance(frames, list) or not frames:
        errors.append("frames must be a non-empty list")
        return errors
    previous_tick = -1
    for frame_index, frame in enumerate(frames):
        tick = frame.get("tick") if isinstance(frame, dict) else None
        if not isinstance(tick, int) or tick <= previous_tick:
            errors.append(f"frames[{frame_index}].tick must be strictly increasing")
            continue
        previous_tick = tick
        if frame.get("round_number") != round_number:
            errors.append(f"frames[{frame_index}].round_number differs from chunk")
        players = frame.get("players")
        if not isinstance(players, list):
            errors.append(f"frames[{frame_index}].players must be a list")
            continue
        seen: set[str] = set()
        for player_index, player in enumerate(players):
            player_id = player.get("player_id") if isinstance(player, dict) else None
            if not isinstance(player_id, str) or not player_id:
                errors.append(f"frames[{frame_index}].players[{player_index}] has invalid player_id")
            elif player_id in seen:
                errors.append(f"frames[{frame_index}] duplicates player_id {player_id!r}")
            else:
                seen.add(player_id)
                if known_player_ids is not None and player_id not in known_player_ids:
                    errors.append(f"frames[{frame_index}] references unknown player_id {player_id!r}")
        events = frame.get("events", [])
        if not isinstance(events, list):
            errors.append(f"frames[{frame_index}].events must be a list")
        else:
            for event_index, event in enumerate(events):
                if not isinstance(event, dict) or event.get("tick") != tick:
                    errors.append(f"frames[{frame_index}].events[{event_index}] must use the frame tick")
        utilities = frame.get("utilities", [])
        if not isinstance(utilities, list):
            errors.append(f"frames[{frame_index}].utilities must be a list")
        else:
            for utility_index, utility in enumerate(utilities):
                if not isinstance(utility, dict):
                    errors.append(f"frames[{frame_index}].utilities[{utility_index}] must be an object")
                    continue
                start = utility.get("start_tick")
                end = utility.get("end_tick")
                if utility.get("active") is not True or not isinstance(start, int) or start > tick or (end is not None and (not isinstance(end, int) or tick > end)):
                    errors.append(f"frames[{frame_index}].utilities[{utility_index}] is active outside its evidenced lifetime")
    return errors
