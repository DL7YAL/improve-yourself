from dataclasses import FrozenInstanceError

import pytest

from improve_yourself.replay_contract import PlayerIdentity, Vec3, to_dict


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
