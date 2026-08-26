import json
from pathlib import Path

import pytest

from improve_yourself.viewer import render_viewer, visible_players_at_frame, world_to_radar
from test_replay_controller import _store


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


def test_viewer_hides_only_explicitly_dead_v2_players() -> None:
    players = [
        {"player_id": "alive", "name": "Alive", "alive": True},
        {"player_id": "dead", "name": "Dead", "alive": False},
        {"player_id": "unknown", "name": "Unknown"},
    ]

    assert [player["player_id"] for player in visible_players_at_frame(players)] == ["alive", "unknown"]


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
    assert "explizit belegtem Todeszustand" in html


def test_rejects_wrong_schema(tmp_path: Path) -> None:
    source = tmp_path / "replay.json"
    source.write_text('{"schema":"wrong","coordinate_space":"cs2_world","scenes":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="iy.replay/v1"):
        render_viewer(source, tmp_path / "viewer.html")


def test_renders_v2_store_with_controller_state_and_timing_boundary(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    store_root.mkdir()
    store = _store(store_root, tick_rate=None)
    result = render_viewer(store.manifest_path, tmp_path / "viewer-v2.html")
    html = result.read_text(encoding="utf-8")
    assert '"source_schema":"iy.replay/v2"' in html
    assert '"requested_tick":14,"resolved_tick":12' in html
    assert '"timing_available":false' in html
    assert "Zeitbasis nicht verfügbar" in html
    assert "gemeinsame Replay-Wahrheit v2" in html
    assert 'id="player-wrap"' in html
