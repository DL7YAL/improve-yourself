from pathlib import Path

from improve_yourself.embedded_tactical import EmbeddedTacticalSession
from test_replay_controller import _store


def test_embedded_tactical_uses_existing_projection_and_preserves_scene_identity(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    store_root.mkdir()
    store = _store(store_root, tick_rate=None)
    source_hash = store.manifest["source"]["sha256"]
    flow = tmp_path / "flow.json"
    flow.write_text(
        '{"schema":"iy.analysis_flow/v1","source":{"sha256":"' + source_hash + '"},'
        '"selection":{"mode":"player_select","player_ids":["steam:8"]},'
        '"profile":{"profile_id":"review_v1"},"scenes":['
        '{"scene_id":"scene-1","round_number":1,"review_tick":14,"end_tick":14,'
        '"focus_player_id":"steam:8"}]}',
        encoding="utf-8",
    )
    session = EmbeddedTacticalSession(store.manifest_path, flow, source_hash)
    scene = session.select_scene("scene-1")
    assert session.projection["schema"] == "iy.tactical_2d_projection/v1"
    assert scene["scene_id"] == "scene-1"
    assert scene["round_number"] == 1
    assert scene["requested_tick"] == 14
    assert scene["resolved_tick"] == 12
    assert scene["focus_player_id"] == "steam:8"
    assert session.flow["selection"]["player_ids"] == ["steam:8"]
    assert session.flow["profile"]["profile_id"] == "review_v1"


def test_embedded_tactical_steps_without_creating_scene_copies(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    store_root.mkdir()
    store = _store(store_root, tick_rate=64.0)
    store.manifest["scenes"].append(
        {"scene_id": "scene-2", "round_number": 1, "tick": 14, "focus_player_id": "steam:8"}
    )
    source_hash = store.manifest["source"]["sha256"]
    flow = tmp_path / "flow.json"
    flow.write_text(
        '{"schema":"iy.analysis_flow/v1","source":{"sha256":"' + source_hash + '"},"scenes":['
        '{"scene_id":"scene-1","round_number":1,"review_tick":14,"end_tick":14,"focus_player_id":"steam:8"},'
        '{"scene_id":"scene-2","round_number":1,"review_tick":14,"end_tick":14,"focus_player_id":"steam:8"}]}',
        encoding="utf-8",
    )
    session = EmbeddedTacticalSession(store.manifest_path, flow, source_hash)
    session.select_scene("scene-1")
    assert session.step_scene(1)["scene_id"] == "scene-2"
    assert session.step_scene(-1)["scene_id"] == "scene-1"
