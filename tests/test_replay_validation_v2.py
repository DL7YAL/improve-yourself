from improve_yourself.replay_contract import REPLAY_V2_SCHEMA, ROUND_CHUNK_SCHEMA
from improve_yourself.replay_validation import validate_replay_manifest, validate_round_chunk


def valid_manifest() -> dict:
    return {
        "schema": REPLAY_V2_SCHEMA,
        "source": {"sha256": "a" * 64, "map_id": "de_anubis", "tick_rate": 64.0},
        "coordinate_space": "cs2_world",
        "players": [{"player_id": "steam:7"}],
        "rounds": [{"round_number": 1, "first_tick": 10, "last_tick": 20, "frame_count": 2, "chunk": "rounds/round-001.json.gz"}],
        "capabilities": {
            "positions": "full", "view_yaw": "full", "view_pitch": "full",
            "alive_state": "partial", "weapon_state": "full", "velocity": "full",
            "utility_lifetimes": "partial", "utility_trajectories": "partial",
            "flash_effect": "unavailable", "sound": "unavailable", "map_geometry": "unavailable",
        },
    }


def test_valid_manifest_passes() -> None:
    assert validate_replay_manifest(valid_manifest()) == []


def test_duplicate_players_and_invalid_capability_fail() -> None:
    payload = valid_manifest()
    payload["players"].append({"player_id": "steam:7"})
    payload["capabilities"]["positions"] = "guessed"
    errors = validate_replay_manifest(payload)
    assert any("duplicated" in error for error in errors)
    assert any("positions" in error for error in errors)


def test_round_chunk_rejects_duplicate_ticks_and_player_ids() -> None:
    chunk = {
        "schema": ROUND_CHUNK_SCHEMA,
        "round_number": 1,
        "frames": [
            {"tick": 10, "round_number": 1, "players": [{"player_id": "steam:7"}, {"player_id": "steam:7"}]},
            {"tick": 10, "round_number": 1, "players": []},
        ],
    }
    errors = validate_round_chunk(chunk, {"steam:7"})
    assert any("duplicates player_id" in error for error in errors)
    assert any("strictly increasing" in error for error in errors)


def test_round_chunk_rejects_shifted_event_and_utility_lifetime() -> None:
    chunk = {
        "schema": ROUND_CHUNK_SCHEMA,
        "round_number": 1,
        "frames": [{
            "tick": 10,
            "round_number": 1,
            "players": [],
            "events": [{"tick": 11}],
            "utilities": [{"active": True, "start_tick": 11, "end_tick": 20}],
        }],
    }
    errors = validate_round_chunk(chunk)
    assert any("frame tick" in error for error in errors)
    assert any("evidenced lifetime" in error for error in errors)
