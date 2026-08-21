from improve_yourself.replay_builder import (
    CapabilityAccumulator,
    IdentityRegistry,
    build_round_chunk,
    normalize_events,
    normalize_utilities,
)


def tick_row(tick: int, steamid: int = 7, name: str = "Player") -> dict:
    return {
        "round_num": 1,
        "tick": tick,
        "steamid": steamid,
        "name": name,
        "side": "CT",
        "X": 1,
        "Y": 2,
        "Z": 3,
        "pitch": 4,
        "yaw": 5,
        "health": 100,
        "armor": 50,
        "active_weapon_name": "m4a1",
        "velocity_X": 6,
        "velocity_Y": 7,
        "velocity_Z": 8,
    }


def test_builds_complete_tick_state_and_exact_event_tick() -> None:
    registry = IdentityRegistry("a" * 64)
    kills = [{
        "round_num": 1,
        "tick": 101,
        "attacker_steamid": 7,
        "attacker_name": "Player",
        "victim_steamid": 8,
        "victim_name": "Other",
        "attacker_X": 1,
        "attacker_Y": 2,
        "attacker_Z": 3,
        "weapon": "m4a1",
        "headshot": True,
    }]
    events = normalize_events("kills", kills, registry)
    chunk = build_round_chunk(
        1,
        [tick_row(100), tick_row(102)],
        round_start_tick=100,
        tick_rate=64.0,
        events_by_tick=events,
        utilities=[],
        registry=registry,
        capabilities=CapabilityAccumulator(),
    )
    assert [frame["tick"] for frame in chunk["frames"]] == [100, 101, 102]
    assert chunk["frames"][1]["players"] == []
    assert chunk["frames"][1]["events"][0]["type"] == "kill"
    assert chunk["frames"][1]["events"][0]["details"]["headshot"] is True
    assert chunk["frames"][0]["players"][0]["player_id"] == "steam:7"
    assert chunk["frames"][0]["players"][0]["velocity"] == {"x": 6.0, "y": 7.0, "z": 8.0}


def test_kill_event_retains_objective_awpy_qualifiers() -> None:
    registry = IdentityRegistry("a" * 64)
    events = normalize_events("kills", [{
        "tick": 5, "attacker_steamid": 7, "attacker_name": "A", "victim_steamid": 8,
        "victim_name": "B", "penetrated": 2, "through_smoke": True, "attacker_blind": True,
    }], registry)
    assert events[5][0].details == {"penetrated": 2, "attacker_blind": True, "thrusmoke": True}


def test_duplicate_display_names_keep_distinct_steam_identity() -> None:
    registry = IdentityRegistry("a" * 64)
    chunk = build_round_chunk(
        1,
        [tick_row(100, 7, "Same"), tick_row(100, 8, "Same")],
        round_start_tick=100,
        tick_rate=None,
        events_by_tick={},
        utilities=[],
        registry=registry,
        capabilities=CapabilityAccumulator(),
    )
    assert [player["player_id"] for player in chunk["frames"][0]["players"]] == ["steam:7", "steam:8"]
    assert len(registry.identities) == 2


def test_unresolved_player_is_omitted_without_zero_fallback() -> None:
    registry = IdentityRegistry("a" * 64)
    row = tick_row(100)
    row.update({"steamid": None, "X": None})
    chunk = build_round_chunk(
        1, [row], round_start_tick=None, tick_rate=None,
        events_by_tick={}, utilities=[], registry=registry,
        capabilities=CapabilityAccumulator(),
    )
    assert chunk["frames"][0]["players"] == []
    assert registry.omitted_unresolved_snapshots == 1


def test_utility_lifetime_is_applied_only_to_evidenced_ticks() -> None:
    registry = IdentityRegistry("a" * 64)
    utilities = normalize_utilities("smokes", [{
        "entity_id": 3, "start_tick": 101, "end_tick": 102,
        "thrower_steamid": 7, "thrower_name": "Player", "X": 9, "Y": 8, "Z": 7,
    }], registry)
    chunk = build_round_chunk(
        1, [tick_row(tick) for tick in (100, 101, 102, 103)],
        round_start_tick=100, tick_rate=64.0, events_by_tick={},
        utilities=utilities, registry=registry, capabilities=CapabilityAccumulator(),
    )
    assert [len(frame["utilities"]) for frame in chunk["frames"]] == [0, 1, 1, 0]
    assert chunk["frames"][1]["utilities"][0]["evidence"] == "lifetime"
