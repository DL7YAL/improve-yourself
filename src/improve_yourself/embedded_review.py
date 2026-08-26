from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .review_state import ALLOWED_STATES, load_or_create_review_state, validate_review_state, write_review_state


class SceneOpener(Protocol):
    def open_scene(self, scene_id: str, tick: int) -> dict[str, object]: ...


@dataclass(frozen=True)
class EmbeddedScene:
    scene_id: str
    round_number: int
    start_tick: int
    review_tick: int
    end_tick: int
    timecode: str
    anchor_types: tuple[str, ...]
    rule_ids: tuple[str, ...]
    player_names: tuple[str, ...]
    marker_ticks: tuple[int, ...]


class EmbeddedReviewSession:
    """Native review presentation over the canonical analysis flow and coordinator."""

    def __init__(self, flow_path: Path, state_path: Path, source_sha256: str, opener: SceneOpener) -> None:
        flow = json.loads(flow_path.read_text(encoding="utf-8"))
        if flow.get("schema") != "iy.analysis_flow/v1":
            raise ValueError("expected iy.analysis_flow/v1")
        if flow.get("source", {}).get("sha256") != source_sha256:
            raise ValueError("embedded review source hash differs from workflow")
        raw_scenes = flow.get("scenes")
        if not isinstance(raw_scenes, list):
            raise ValueError("analysis flow scenes must be a list")
        roster = {
            item["player_id"]: item.get("display_name") or item["player_id"]
            for item in flow.get("roster", ())
            if isinstance(item, dict) and isinstance(item.get("player_id"), str)
        }
        tick_rate = flow.get("source", {}).get("tick_rate")
        self.scenes = tuple(self._scene(item, roster, tick_rate) for item in raw_scenes)
        if len({scene.scene_id for scene in self.scenes}) != len(self.scenes):
            raise ValueError("analysis flow contains duplicate scene_id")
        self.flow = flow
        self.state_path = state_path
        self.source_sha256 = source_sha256
        self.opener = opener
        state = load_or_create_review_state(state_path, source_sha256, raw_scenes)
        self._state = {item["scene_id"]: item for item in state["scenes"]}

    @staticmethod
    def _scene(item: dict, roster: dict[str, str], tick_rate: object) -> EmbeddedScene:
        identifier = item.get("scene_id")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("analysis scene requires scene_id")
        tick = int(item["review"]["tick"])
        if isinstance(tick_rate, (int, float)) and not isinstance(tick_rate, bool) and tick_rate > 0:
            total_seconds = tick / float(tick_rate)
            minutes, seconds = divmod(total_seconds, 60)
            timecode = f"{int(minutes):02d}:{seconds:06.3f}"
        else:
            timecode = "Zeit nicht belegt"
        return EmbeddedScene(
            scene_id=identifier,
            round_number=int(item["round_number"]),
            start_tick=int(item["start_tick"]),
            review_tick=tick,
            end_tick=int(item["end_tick"]),
            timecode=timecode,
            anchor_types=tuple(str(value) for value in item.get("anchor_types", ())),
            rule_ids=tuple(str(value) for value in item.get("rule_ids", ())),
            player_names=tuple(roster.get(str(value), str(value)) for value in item.get("player_ids", ())),
            marker_ticks=tuple(int(value) for value in item.get("marker_ticks", ())),
        )

    def review(self, scene_id: str) -> dict[str, str]:
        try:
            return dict(self._state[scene_id])
        except KeyError as error:
            raise ValueError("unknown embedded review scene") from error

    def save_review(self, scene_id: str, state: str, note: str) -> None:
        if scene_id not in self._state:
            raise ValueError("unknown embedded review scene")
        if state not in ALLOWED_STATES:
            raise ValueError("invalid embedded review state")
        updated = [
            {"scene_id": scene.scene_id, "state": state, "note": note}
            if scene.scene_id == scene_id else dict(self._state[scene.scene_id])
            for scene in self.scenes
        ]
        payload = validate_review_state(
            {"schema": "iy.review_state/v1", "source_sha256": self.source_sha256, "scenes": updated},
            self.source_sha256,
            {scene.scene_id for scene in self.scenes},
        )
        write_review_state(self.state_path, payload)
        self._state = {item["scene_id"]: item for item in payload["scenes"]}

    def open_in_cs2(self, scene_id: str) -> dict[str, object]:
        scene = next((item for item in self.scenes if item.scene_id == scene_id), None)
        if scene is None:
            raise ValueError("unknown embedded review scene")
        return self.opener.open_scene(scene.scene_id, scene.review_tick)
