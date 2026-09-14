import gzip
import hashlib
import json

import pytest

from improve_yourself.replay_contract import REPLAY_V2_SCHEMA, ROUND_CHUNK_SCHEMA
from improve_yourself.replay_store import ReplayStore


def write_test_store(tmp_path, *, chunk_round=1, ticks=(10, 20), descriptor_updates=None):
    chunk = {
        "schema": ROUND_CHUNK_SCHEMA,
        "round_number": chunk_round,
        "frames": [{"tick": tick, "round_number": chunk_round, "players": []} for tick in ticks],
    }
    chunk_path = tmp_path / "round.json.gz"
    with gzip.open(chunk_path, "wt", encoding="utf-8") as stream:
        json.dump(chunk, stream)
    descriptor = {
        "round_number": 1, "first_tick": 10, "last_tick": 20, "frame_count": 2,
        "chunk": chunk_path.name, "sha256": hashlib.sha256(chunk_path.read_bytes()).hexdigest(),
    }
    descriptor.update(descriptor_updates or {})
    manifest = {
        "schema": REPLAY_V2_SCHEMA,
        "source": {"sha256": "a" * 64, "map_id": "de_anubis", "tick_rate": 64.0},
        "coordinate_space": "cs2_world", "players": [], "rounds": [descriptor],
        "capabilities": {"positions": "unavailable"},
    }
    path = tmp_path / "replay-v2.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


@pytest.mark.parametrize("field,value", [("first_tick", 9), ("last_tick", 21), ("frame_count", 3)])
def test_store_rejects_hash_valid_descriptor_mismatch(tmp_path, field, value) -> None:
    store = ReplayStore(write_test_store(tmp_path, descriptor_updates={field: value}))
    for _ in range(2):
        with pytest.raises(ValueError, match=field):
            store.load_round(1)
    assert store._cache == {}


def test_store_rejects_hash_valid_wrong_round(tmp_path) -> None:
    store = ReplayStore(write_test_store(tmp_path, chunk_round=2))
    for _ in range(2):
        with pytest.raises(ValueError, match="round_number"):
            store.load_round(1)
    assert store._cache == {}


def test_store_rejects_empty_frames_before_descriptor_comparison(tmp_path) -> None:
    store = ReplayStore(write_test_store(tmp_path, ticks=()))
    with pytest.raises(ValueError, match="frames"):
        store.load_round(1)
    assert store._cache == {}


@pytest.mark.parametrize("ticks", [(10, 20), (10,)])
def test_store_accepts_matching_descriptor_and_caches_round(tmp_path, ticks) -> None:
    path = write_test_store(tmp_path, ticks=ticks, descriptor_updates={
        "last_tick": ticks[-1], "frame_count": len(ticks),
    })
    store = ReplayStore(path)
    chunk = store.load_round(1)
    assert [frame["tick"] for frame in chunk["frames"]] == list(ticks)
    assert store.load_round(1) is chunk


@pytest.mark.parametrize("entry", [None, 7, "round", [], True])
def test_store_rejects_non_object_manifest_round_with_value_error(tmp_path, entry) -> None:
    path = write_test_store(tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["rounds"] = [entry]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match=r"rounds\[0\]"):
        ReplayStore(path)


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
