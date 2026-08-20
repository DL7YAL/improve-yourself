from improve_yourself.replay_controller import ReplayController
from improve_yourself.tactical_2d import _sample_frames, build_tactical_2d_projection
from test_replay_controller import _store


def test_projection_uses_controller_scene_resolution_and_stable_identity(tmp_path) -> None:
    store = _store(tmp_path, tick_rate=None)
    projection = build_tactical_2d_projection(store, ReplayController(store))
    assert projection["schema"] == "iy.tactical_2d_projection/v1"
    assert projection["source_schema"] == "iy.replay/v2"
    assert projection["controller"]["timing_available"] is False
    scene = projection["scenes"][0]
    assert scene["requested_tick"] == 14
    assert scene["resolved_tick"] == 12
    assert scene["focus_player_id"] == "steam:8"
    assert scene["marker_player"] == "steam:8"
    assert scene["frames"][0]["tick"] == 12


def test_projection_omits_only_unrenderable_player_state(tmp_path) -> None:
    store = _store(tmp_path)
    chunk = store.load_round(1)
    chunk["frames"][1]["players"] = [
        {"player_id": "steam:7", "team": "CT", "position": {"x": 1, "y": 2, "z": 3}, "view_yaw_deg": 90},
        {"player_id": "steam:8", "team": "T", "position": None, "view_yaw_deg": 45},
    ]
    projection = build_tactical_2d_projection(store, ReplayController(store))
    assert [player["player_id"] for player in projection["scenes"][0]["frames"][0]["players"]] == ["steam:7"]


def test_sampling_preserves_boundaries_and_event_frames() -> None:
    frames = [{"tick": tick, "events": ([{"type": "kill"}] if tick == 5 else [])} for tick in range(10)]
    sampled = _sample_frames(frames, 5)
    ticks = [frame["tick"] for frame in sampled]
    assert len(ticks) == 5
    assert ticks[0] == 0
    assert ticks[-1] == 9
    assert 5 in ticks
