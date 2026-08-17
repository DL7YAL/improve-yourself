import json
from pathlib import Path

import pytest

from improve_yourself.viewer import active_players_at_tick, render_viewer, world_to_radar
from improve_yourself.replay import build_replay_payload


def replay_payload() -> dict:
    return {
        "schema": "iy.replay/v1", "source_sha256": "a" * 64,
        "map_name": "de_mirage", "coordinate_space": "cs2_world",
        "data_quality": {"omitted_incomplete_player_snapshots": 0},
        "scenes": [{"round_number": 1, "marker_player": "Player", "start_tick": 1,
                    "end_tick": 1, "frames": [{"tick": 1, "players": []}]}],
    }


def test_world_to_radar_uses_source_transform() -> None:
    assert world_to_radar(-3230, 1713, -3230, 1713, 5) == (0, 0)
    assert world_to_radar(1890, -3407, -3230, 1713, 5) == (1024, 1024)


def test_world_to_radar_rejects_invalid_scale() -> None:
    with pytest.raises(ValueError, match="scale"):
        world_to_radar(0, 0, 0, 0, 0)


def test_known_kill_hides_only_the_documented_victim_from_its_tick() -> None:
    players = [
        {"name": "Alive", "side": "CT"},
        {"name": "Victim", "side": "T"},
    ]
    events = [{"tick": 200, "attacker": "Alive", "victim": "Victim", "weapon": "ak47"}]

    assert [player["name"] for player in active_players_at_tick(players, events, 199)] == ["Alive", "Victim"]
    assert [player["name"] for player in active_players_at_tick(players, events, 200)] == ["Alive"]
    assert [player["name"] for player in active_players_at_tick(players, events, 300)] == ["Alive"]


def test_missing_or_malformed_kill_evidence_does_not_hide_a_player() -> None:
    players = [{"name": "Player", "side": "CT"}]
    events = [{"tick": "200", "victim": "Player"}, {"tick": 200, "victim": ""}]

    assert active_players_at_tick(players, events, 300) == players


def test_renders_self_contained_html_and_escapes_script_end(tmp_path: Path) -> None:
    payload = replay_payload()
    payload["scenes"][0]["marker_player"] = "</script><script>alert(1)</script>"
    source = tmp_path / "replay.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    radar = tmp_path / "radar.png"
    radar.write_bytes(b"test-radar")
    result = render_viewer(source, tmp_path / "viewer.html", radar_path=radar, scale=5)
    html = result.read_text(encoding="utf-8")
    assert "__IY_VIEWER_MODEL__" not in html
    assert "data:image/png;base64,dGVzdC1yYWRhcg==" in html
    assert "</script><script>alert(1)</script>" not in html
    assert "\\u003c/script>" in html
    assert 'id="previous-frame"' in html
    assert 'id="next-scene"' in html
    assert 'id="speed"' in html
    assert 'id="event-info"' in html
    assert 'active_players' in html
    assert 'Utility: Rauch' in html
    assert 'u.area' in html
    assert 'dokumentierten Kill-Tick' in html


def test_rejects_wrong_schema(tmp_path: Path) -> None:
    source = tmp_path / "replay.json"
    source.write_text('{"schema":"wrong","coordinate_space":"cs2_world","scenes":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="iy.replay/v1"):
        render_viewer(source, tmp_path / "viewer.html")


def test_replay_exports_only_documented_utility_paths_and_effect_points() -> None:
    analysis = {
        "schema": "iy.analysis/v1", "source_name": "match.dem", "source_sha256": "a" * 64, "map_name": "de_mirage", "disclaimer": "Automatische Marker sind Prüfhinweise und kein Cheat-Nachweis.",
        "kills": [{"round_number": 1, "tick": 20, "attacker": "Player", "victim": "Victim", "weapon": "ak47", "headshot": False}, {"round_number": 1, "tick": 30, "attacker": "Player", "victim": "Victim2", "weapon": "ak47", "headshot": False}, {"round_number": 1, "tick": 40, "attacker": "Player", "victim": "Victim3", "weapon": "ak47", "headshot": False}],
        "multikills": [{"round_number": 1, "player": "Player", "kill_count": 3, "first_tick": 20, "last_tick": 40, "victims": ["Victim", "Victim2", "Victim3"]}],
        "data_quality": {"status": "ok", "missing_channels": [], "warnings": []}, "available_channels": ["rounds", "kills"],
    }
    ticks = [{"tick": 20, "round_num": 1, "name": "Player", "side": "CT", "X": 0, "Y": 0, "Z": 0, "pitch": 0, "yaw": 0}]
    smokes = [{"round_num": 1, "start_tick": 21, "end_tick": 35, "thrower_name": "Player", "thrower_X": 1, "thrower_Y": 2, "thrower_Z": 3, "X": 4, "Y": 5, "Z": 6}]
    grenades = [{"round_num": 1, "entity_id": 4, "grenade_type": "CFlashbangProjectile", "thrower": "Player", "tick": 22, "X": 1, "Y": 2, "Z": 3}, {"round_num": 1, "entity_id": 4, "grenade_type": "CFlashbangProjectile", "thrower": "Player", "tick": 24, "X": 4, "Y": 5, "Z": 6}]
    replay = build_replay_payload(analysis, ticks, grenade_rows=grenades, smoke_rows=smokes)
    utility = replay["scenes"][0]["utility"]
    assert [(item["kind"], item["target"]) for item in utility] == [("smoke", {"x": 4.0, "y": 5.0, "z": 6.0}), ("flash", {"x": 4.0, "y": 5.0, "z": 6.0})]
    assert all("effectiveness" not in item for item in utility)
