from __future__ import annotations

import json
from pathlib import Path

from .replay_controller import ReplayController
from .replay_store import ReplayStore
from .tactical_2d import build_tactical_2d_projection
from .tactical_minimap import TacticalMinimap, load_tactical_minimap


class EmbeddedTacticalSession:
    """Native tactical presentation over the existing canonical 2D projection."""

    def __init__(self, replay_path: Path, flow_path: Path, source_sha256: str) -> None:
        flow = json.loads(flow_path.read_text(encoding="utf-8"))
        if flow.get("schema") != "iy.analysis_flow/v1":
            raise ValueError("expected iy.analysis_flow/v1")
        if flow.get("source", {}).get("sha256") != source_sha256:
            raise ValueError("tactical flow source hash differs from workflow")
        store = ReplayStore(replay_path)
        if store.manifest["source"]["sha256"] != source_sha256:
            raise ValueError("tactical replay source hash differs from workflow")
        raw_scenes = flow.get("scenes")
        if not isinstance(raw_scenes, list):
            raise ValueError("analysis flow scenes must be a list")
        store.manifest["scenes"] = [
            {
                "scene_id": item["scene_id"],
                "round_number": item["round_number"],
                "tick": item["review_tick"],
                "end_tick": item["end_tick"],
                "focus_player_id": item.get("focus_player_id"),
            }
            for item in raw_scenes
        ]
        self.projection = build_tactical_2d_projection(store, ReplayController(store))
        self.minimap: TacticalMinimap = load_tactical_minimap(str(self.projection["map_name"]))
        self.scenes = tuple(self.projection["scenes"])
        self._by_id = {scene["scene_id"]: scene for scene in self.scenes}
        if len(self._by_id) != len(self.scenes):
            raise ValueError("tactical projection contains duplicate scene_id")
        self.flow = flow
        self.source_sha256 = source_sha256
        self.selected_scene_id: str | None = None

    def select_scene(self, scene_id: str) -> dict:
        try:
            scene = self._by_id[scene_id]
        except KeyError as error:
            raise ValueError("unknown tactical scene") from error
        self.selected_scene_id = scene_id
        return scene

    def selected_scene(self) -> dict:
        if self.selected_scene_id is None:
            raise RuntimeError("no tactical scene selected")
        return self._by_id[self.selected_scene_id]

    def scene_index(self) -> int:
        return next(index for index, scene in enumerate(self.scenes) if scene["scene_id"] == self.selected_scene_id)

    def step_scene(self, delta: int) -> dict:
        if not self.scenes:
            raise RuntimeError("tactical projection has no scenes")
        current = self.scene_index() if self.selected_scene_id is not None else 0
        target = max(0, min(len(self.scenes) - 1, current + delta))
        return self.select_scene(self.scenes[target]["scene_id"])
