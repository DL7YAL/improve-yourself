import gzip
import hashlib
import json

import pytest

from improve_yourself.replay_contract import REPLAY_V2_SCHEMA, ROUND_CHUNK_SCHEMA
from improve_yourself.replay_store import ReplayStore


def test_store_loads_round_and_resolves_at_or_before(tmp_path) -> None:
    rounds = tmp_path / "rounds"
    rounds.mkdir()
    chunk = {
        "schema": ROUND_CHUNK_SCHEMA,
        "round_number": 1,
        "frames": [
            {"tick": 10, "round_number": 1, "players": [{"player_id": "steam:7"}], "utilities": [], "events": []},
            {"tick": 20, "round_number": 1, "players": [{"player_id": "steam:7"}], "utilities": [], "events": []},
        ],
    }
    chunk_path = rounds / "round-001.json.gz"
    with gzip.open(chunk_path, "wt", encoding="utf-8") as stream:
        json.dump(chunk, stream)
    manifest = {
        "schema": REPLAY_V2_SCHEMA,
        "source": {"sha256": "a" * 64, "map_id": "de_anubis", "tick_rate": 64.0},
        "coordinate_space": "cs2_world",
        "players": [{"player_id": "steam:7"}],
        "rounds": [{
            "round_number": 1, "first_tick": 10, "last_tick": 20,
            "frame_count": 2, "chunk": "rounds/round-001.json.gz",
            "sha256": hashlib.sha256(chunk_path.read_bytes()).hexdigest(),
        }],
        "capabilities": {
            "positions": "full", "view_yaw": "full", "view_pitch": "full",
            "alive_state": "partial", "weapon_state": "full", "velocity": "full",
            "utility_lifetimes": "unavailable", "utility_trajectories": "unavailable",
            "flash_effect": "unavailable", "sound": "unavailable", "map_geometry": "unavailable",
        },
    }
    manifest_path = tmp_path / "replay-v2.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    store = ReplayStore(manifest_path)
    assert store.round_numbers == (1,)
    assert store.frame_at_or_before(1, 19)["tick"] == 10
    assert store.exact_frame(1, 20)["tick"] == 20
    with pytest.raises(KeyError):
        store.exact_frame(1, 19)


def test_store_rejects_modified_round_chunk(tmp_path) -> None:
    rounds = tmp_path / "rounds"
    rounds.mkdir()
    chunk_path = rounds / "round-001.json.gz"
    with gzip.open(chunk_path, "wt", encoding="utf-8") as stream:
        json.dump({"schema": ROUND_CHUNK_SCHEMA, "round_number": 1, "frames": [{"tick": 10, "round_number": 1, "players": []}]}, stream)
    manifest = {
        "schema": REPLAY_V2_SCHEMA,
        "source": {"sha256": "a" * 64, "map_id": "de_anubis", "tick_rate": None},
        "coordinate_space": "cs2_world", "players": [],
        "rounds": [{"round_number": 1, "first_tick": 10, "last_tick": 10, "frame_count": 1, "chunk": "rounds/round-001.json.gz", "sha256": "0" * 64}],
        "capabilities": {"positions": "unavailable", "view_yaw": "unavailable", "view_pitch": "unavailable", "alive_state": "unavailable", "weapon_state": "unavailable", "velocity": "unavailable", "utility_lifetimes": "unavailable", "utility_trajectories": "unavailable", "flash_effect": "unavailable", "sound": "unavailable", "map_geometry": "unavailable"},
    }
    path = tmp_path / "replay-v2.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="hash differs"):
        ReplayStore(path).load_round(1)
