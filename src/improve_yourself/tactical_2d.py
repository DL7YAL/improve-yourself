from __future__ import annotations

from typing import Any

from .replay_controller import ReplayController
from .replay_store import ReplayStore

TACTICAL_2D_PROJECTION_SCHEMA = "iy.tactical_2d_projection/v1"


def _sample_frames(frames: list[dict[str, Any]], maximum: int) -> list[dict[str, Any]]:
    if maximum < 2:
        raise ValueError("maximum scene frames must be at least 2")
    if len(frames) <= maximum:
        return frames
    required = {0, len(frames) - 1}
    required.update(index for index, frame in enumerate(frames) if frame.get("events"))
    if len(required) >= maximum:
        return [frames[index] for index in sorted(required)]
    slots = maximum - len(required)
    candidates = [index for index in range(1, len(frames) - 1) if index not in required]
    if slots:
        required.update(candidates[round(position * (len(candidates) - 1) / max(slots - 1, 1))] for position in range(slots))
    return [frames[index] for index in sorted(required)]


def build_tactical_2d_projection(
    store: ReplayStore, controller: ReplayController, *, max_frames_per_scene: int = 256
) -> dict[str, Any]:
    """Project canonical replay contexts into renderer-ready 2D scene data."""
    identities = {item["player_id"]: item for item in store.manifest["players"]}
    scenes: list[dict[str, Any]] = []
    for source_scene in store.manifest.get("scenes", []):
        context = controller.seek_scene(source_scene["scene_id"])
        chunk = store.load_round(context.current_round)
        end_tick = source_scene.get("end_tick", source_scene["tick"])
        canonical_frames = [
            frame for frame in chunk["frames"]
            if context.resolved_tick <= frame["tick"] <= end_tick
        ]
        sampled_frames = _sample_frames(canonical_frames, max_frames_per_scene)
        frames = []
        for frame in sampled_frames:
            players = []
            for state in frame.get("players", []):
                position = state.get("position")
                yaw = state.get("view_yaw_deg")
                if position is None or yaw is None:
                    continue
                identity = identities[state["player_id"]]
                players.append({
                    "player_id": state["player_id"],
                    "name": identity.get("display_name", state["player_id"]),
                    "side": state.get("team", "unknown"),
                    "x": position["x"],
                    "y": position["y"],
                    "z": position["z"],
                    "pitch": state.get("view_pitch_deg"),
                    "yaw": yaw,
                    "active": state.get("active"),
                    "alive": state.get("alive"),
                })
            frames.append({
                "tick": frame["tick"],
                "players": sorted(players, key=lambda item: (item["side"], item["name"], item["player_id"])),
                "event_count": len(frame.get("events", [])),
                "utility_count": len(frame.get("utilities", [])),
            })
        focus = identities.get(context.selected_player_id or "", {})
        scenes.append({
            "scene_id": source_scene["scene_id"],
            "round_number": context.current_round,
            "marker_player": focus.get("display_name", context.selected_player_id or "Kein eindeutiger Fokusspieler"),
            "focus_player_id": context.selected_player_id,
            "requested_tick": context.requested_tick,
            "resolved_tick": context.resolved_tick,
            "start_tick": context.resolved_tick,
            "end_tick": end_tick,
            "frames": frames,
            "canonical_frame_count": len(canonical_frames),
        })
    initial = ReplayController(store).snapshot()
    return {
        "schema": TACTICAL_2D_PROJECTION_SCHEMA,
        "source_schema": store.manifest["schema"],
        "source_sha256": store.manifest["source"]["sha256"],
        "map_name": store.manifest["source"]["map_id"],
        "coordinate_space": store.manifest["coordinate_space"],
        "controller": {
            "current_round": initial.current_round,
            "requested_tick": initial.requested_tick,
            "resolved_tick": initial.resolved_tick,
            "play_state": initial.play_state,
            "playback_speed": initial.playback_speed,
            "selected_player_id": initial.selected_player_id,
            "selected_scene_id": initial.selected_scene_id,
            "view_mode": initial.view_mode,
            "tick_rate": initial.tick_rate,
            "timing_available": initial.timing_available,
        },
        "players": list(store.manifest["players"]),
        "data_quality": store.manifest.get("data_quality", {}),
        "sampling": {"method": "event_preserving_uniform", "max_frames_per_scene": max_frames_per_scene},
        "scenes": scenes,
    }
