from dataclasses import FrozenInstanceError

import pytest

from improve_yourself.replay_contract import PlayerIdentity, ReplayFrame, Vec3, replay_frame_from_dict, to_dict


def test_contract_values_are_immutable_and_json_compatible() -> None:
    point = Vec3(1.0, 2.0, 3.0)
    with pytest.raises(FrozenInstanceError):
        point.x = 4.0  # type: ignore[misc]
    identity = PlayerIdentity("steam:7", "7", None, "Same Name", "steam")
    assert to_dict(identity) == {
        "player_id": "steam:7",
        "steam_id": "7",
        "entity_id": None,
        "display_name": "Same Name",
        "identity_quality": "steam",
    }


def test_typed_frame_restoration_uses_the_canonical_serialized_truth() -> None:
    frame = replay_frame_from_dict({
        "tick": 8, "round_number": 1, "time_in_round_seconds": None,
        "players": [{
            "player_id": "p", "active": True, "alive": True, "team": "CT",
            "position": {"x": 1, "y": 2, "z": 3}, "view_yaw_deg": 4, "view_pitch_deg": 5,
            "velocity": None, "health": 100, "armor": 0, "weapon": None, "availability": [],
        }],
        "utilities": [], "events": [],
    })
    assert isinstance(frame, ReplayFrame)
    assert frame.tick == 8
    assert frame.players[0].position == Vec3(1.0, 2.0, 3.0)
