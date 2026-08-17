from improve_yourself.replay import build_replay_payload
from test_analysis_validation import valid_payload


def test_builds_deterministic_bounded_multikill_scene() -> None:
    rows = [
        {
            "round_num": 4, "tick": tick, "name": "Player", "side": "T",
            "X": tick, "Y": 2, "Z": 3, "pitch": 4, "yaw": 5,
        }
        for tick in range(100, 9_001, 100)
    ]
    payload = build_replay_payload(valid_payload(), rows, max_frames=10)
    scene = payload["scenes"][0]
    assert payload["schema"] == "iy.replay/v1"
    assert payload["coordinate_space"] == "cs2_world"
    assert scene["start_tick"] == 100
    assert scene["end_tick"] == 9_000
    assert len(scene["frames"]) <= 10
    assert scene["frames"][-1]["tick"] == 9_000
    assert scene["frames"][0]["players"][0]["yaw"] == 5.0
    assert [event["tick"] for event in scene["events"]] == [100, 2_000, 9_000]
    assert all(event["marker_multikill"] for event in scene["events"])


def test_rejects_non_positive_frame_budget() -> None:
    try:
        build_replay_payload(valid_payload(), [], max_frames=0)
    except ValueError as error:
        assert "max_frames" in str(error)
    else:
        raise AssertionError("expected ValueError")


def test_omits_and_discloses_incomplete_player_snapshot() -> None:
    row = {
        "round_num": 4, "tick": 100, "name": "Player", "side": "T",
        "X": None, "Y": 2, "Z": 3, "pitch": 4, "yaw": 5,
    }
    payload = build_replay_payload(valid_payload(), [row])
    assert payload["data_quality"]["omitted_incomplete_player_snapshots"] == 1
    assert payload["scenes"][0]["frames"][0]["players"] == []
