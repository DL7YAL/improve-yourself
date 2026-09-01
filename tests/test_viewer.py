import json
from pathlib import Path

import pytest

from improve_yourself.map_assets import MapAssetAssessment
from improve_yourself.viewer import (
    render_viewer,
    three_d_geometry_status_presentation,
    visible_players_at_frame,
    world_to_radar,
)
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


def test_three_d_geometry_statuses_remain_explicitly_separate_from_the_two_d_surface() -> None:
    assert three_d_geometry_status_presentation(None)["state"] == "NOT PROVIDED"
    assert three_d_geometry_status_presentation(MapAssetAssessment("available", "verified"))["state"] == "AVAILABLE"
    assert three_d_geometry_status_presentation(MapAssetAssessment("missing", "manifest unavailable"))["state"] == "MISSING"
    assert three_d_geometry_status_presentation(MapAssetAssessment("integrity_failed", "hash differs"))["state"] == "INVALID"


def test_renders_self_contained_html_and_escapes_script_end(tmp_path: Path) -> None:
    payload = replay_payload()
    payload["scenes"][0]["marker_player"] = "</script><script>alert(1)</script>"
    source = tmp_path / "replay.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    result = render_viewer(source, tmp_path / "viewer.html")
    html = result.read_text(encoding="utf-8")
    assert "__IY_VIEWER_MODEL__" not in html
    assert '"map_surface":{"state":"MISSING"' in html
    assert "</script><script>alert(1)</script>" not in html
    assert "\\u003c/script>" in html
    assert 'id="previous-frame"' in html
    assert 'id="next-scene"' in html
    assert 'id="speed"' in html
    assert "explizit belegtem Todeszustand" in html
    assert 'class="app-shell"' in html
    assert 'class="sidebar"' in html
    assert 'id="surface-state"' in html
    assert '"three_d_geometry":{"state":"NOT PROVIDED"' in html
    assert "2D-Kartenfläche fehlt" in html
    assert "3D-lokale Geometrie" in html
    assert "tactical_viewer_MASTER.png" not in html
    assert "dashboard_home_MASTER.png" not in html
    assert "my_improvement_MASTER.png" not in html
    assert "Cache.png" not in html
    assert "radar_path" not in Path(__file__).parents[1].joinpath("src", "improve_yourself", "viewer.py").read_text(encoding="utf-8")


def test_viewer_renders_the_existing_three_d_gate_result_without_changing_two_d_surface(tmp_path: Path) -> None:
    source = tmp_path / "replay.json"
    source.write_text(json.dumps(replay_payload()), encoding="utf-8")
    assessment = MapAssetAssessment("available", "asset bundle passed all machine-checkable gates")

    result = render_viewer(source, tmp_path / "viewer.html", map_asset_assessment=assessment)

    html = result.read_text(encoding="utf-8")
    assert '"map_surface":{"state":"MISSING"' in html
    assert '"three_d_geometry":{"state":"AVAILABLE"' in html
    assert "asset bundle passed all machine-checkable gates" in html
    source = Path(__file__).parents[1].joinpath("src", "improve_yourself", "viewer.py").read_text(encoding="utf-8")
    assert "assess_map_asset(" not in source


def test_approved_owned_ancient_surface_is_selected_from_the_canonical_map_id(tmp_path: Path) -> None:
    payload = replay_payload()
    payload["map_name"] = "de_ancient"
    source = tmp_path / "replay.json"
    source.write_text(json.dumps(payload), encoding="utf-8")

    html = render_viewer(source, tmp_path / "viewer.html").read_text(encoding="utf-8")

    assert '"map_surface":{"state":"AVAILABLE"' in html
    assert "OWN_IMPROVE_CANVA" not in html
    assert "data:image/png;base64," in html
    assert '"rotation_deg_clockwise":0' in html


def test_tactical_composition_uses_only_versioned_brand_assets_and_honest_unavailable_regions(tmp_path: Path) -> None:
    payload = replay_payload()
    payload["map_name"] = "de_ancient"
    source = tmp_path / "replay.json"
    source.write_text(json.dumps(payload), encoding="utf-8")

    html = render_viewer(source, tmp_path / "viewer.html").read_text(encoding="utf-8")

    assert "context-panel" in html
    assert "Filterdaten" in html
    assert "Ereignis-Timeline" in html
    assert html.count("NOT AVAILABLE") >= 4
    assert "Keine kanonische Filterprojektion bereitgestellt." in html
    assert "Keine kanonischen Ereignisdaten bereitgestellt." in html
    assert 'id="brand-wordmark"' in html
    assert "improve-yourself-wordmark-v3.png" not in html
    assert "data:image/png;base64," in html
    assert "data:font/ttf;base64," in html
    for prohibited in (
        "Cache.png",
        "tactical_viewer_MASTER.png",
        "dashboard_home_MASTER.png",
        "my_improvement_MASTER.png",
        "TERRORISTEN",
        "Wirtschaft",
        "Rauch geworfen",
        "Molotov",
        "B Site",
        "steamapps",
        "AppData\\Local\\Temp",
        "http://",
        "https://",
    ):
        assert prohibited not in html


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
