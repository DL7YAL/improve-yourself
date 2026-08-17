from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REVIEW_STATE_SCHEMA = "iy.review_state/v1"
ALLOWED_STATES = {"unreviewed", "reviewed", "discarded", "clip-worthy"}
MAX_NOTE_LENGTH = 2_000


def scene_id(scene: dict[str, Any]) -> str:
    return f"r{int(scene['round_number'])}-t{int(scene['start_tick'])}-{int(scene['end_tick'])}-{scene['marker_player']}"


def initial_review_state(source_sha256: str, scenes: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": REVIEW_STATE_SCHEMA,
        "source_sha256": source_sha256,
        "updated_at_utc": datetime.now(UTC).isoformat(),
        "scenes": [
            {"scene_id": scene_id(scene), "state": "unreviewed", "note": ""}
            for scene in scenes
        ],
    }


def validate_review_state(
    payload: Any, source_sha256: str, expected_scene_ids: set[str]
) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != REVIEW_STATE_SCHEMA:
        raise ValueError(f"expected {REVIEW_STATE_SCHEMA}")
    if payload.get("source_sha256") != source_sha256:
        raise ValueError("review state source hash differs")
    scenes = payload.get("scenes")
    if not isinstance(scenes, list):
        raise ValueError("review state scenes must be a list")
    normalized = []
    seen: set[str] = set()
    for index, item in enumerate(scenes):
        if not isinstance(item, dict):
            raise ValueError(f"scenes[{index}] must be an object")
        identifier = item.get("scene_id")
        state = item.get("state")
        note = item.get("note", "")
        if identifier not in expected_scene_ids or identifier in seen:
            raise ValueError(f"scenes[{index}] has unknown or duplicate scene_id")
        if state not in ALLOWED_STATES:
            raise ValueError(f"scenes[{index}] has invalid state")
        if not isinstance(note, str) or len(note) > MAX_NOTE_LENGTH:
            raise ValueError(f"scenes[{index}] note must be at most {MAX_NOTE_LENGTH} characters")
        seen.add(identifier)
        normalized.append({"scene_id": identifier, "state": state, "note": note})
    if seen != expected_scene_ids:
        raise ValueError("review state must contain every replay scene exactly once")
    return {
        "schema": REVIEW_STATE_SCHEMA,
        "source_sha256": source_sha256,
        "updated_at_utc": datetime.now(UTC).isoformat(),
        "scenes": normalized,
    }


def write_review_state(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)
    return path


def load_or_create_review_state(path: Path, source_sha256: str, scenes: list[dict[str, Any]]) -> dict[str, Any]:
    expected = {scene_id(scene) for scene in scenes}
    if path.exists():
        return validate_review_state(json.loads(path.read_text(encoding="utf-8")), source_sha256, expected)
    payload = initial_review_state(source_sha256, scenes)
    write_review_state(path, payload)
    return payload
