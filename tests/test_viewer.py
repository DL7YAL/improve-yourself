import json
from pathlib import Path

import pytest

from improve_yourself.viewer import render_viewer, world_to_radar


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


def test_rejects_wrong_schema(tmp_path: Path) -> None:
    source = tmp_path / "replay.json"
    source.write_text('{"schema":"wrong","coordinate_space":"cs2_world","scenes":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="iy.replay/v1"):
        render_viewer(source, tmp_path / "viewer.html")
