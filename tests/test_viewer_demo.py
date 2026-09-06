from pathlib import Path

from improve_yourself.map_assets import assess_map_asset
from improve_yourself.renderer import first_person_camera
from improve_yourself.replay_controller import ReplayController
from improve_yourself import viewer_demo
from improve_yourself.viewer_demo import select_viewer_demo_state, write_selected_2d_viewer
from test_replay_controller import _store


def test_demo_selection_uses_one_controller_context_and_canonical_camera_state(tmp_path) -> None:
    store = _store(tmp_path)
    chunk = store.load_round(1)
    chunk["frames"][1]["players"] = [{
        "player_id": "steam:7", "active": True, "alive": True, "team": "CT",
        "position": {"x": 1.25, "y": -2.5, "z": 3.75},
        "view_yaw_deg": 22.5, "view_pitch_deg": 3.5, "weapon": "knife",
    }]
    controller = ReplayController(store)
    selection = select_viewer_demo_state(
        store, controller, round_number=1, tick=12, player_id="steam:7",
    )

    assert selection.context == controller.snapshot()
    assert selection.context.resolved_tick == 12
    assert selection.context.selected_player_id == "steam:7"
    assert selection.context.view_mode == "first_person"
    assert selection.player.position == selection.frame.players[0].position
    pose = first_person_camera(selection.frame, "steam:7")
    assert pose.origin.x == 1.25
    assert pose.origin.y == -2.5
    assert pose.origin.z == 67.75
    assert pose.yaw_deg == 22.5
    assert pose.pitch_deg == 3.5


def test_2d_output_remains_usable_when_the_3d_asset_gate_is_missing(tmp_path) -> None:
    store = _store(tmp_path)
    chunk = store.load_round(1)
    chunk["frames"][1]["players"] = [{
        "player_id": "steam:7", "active": True, "alive": True, "team": "CT",
        "position": {"x": 10, "y": 20, "z": 30},
        "view_yaw_deg": 90, "view_pitch_deg": 0, "weapon": "knife",
    }]
    controller = ReplayController(store)
    selection = select_viewer_demo_state(
        store, controller, round_number=1, tick=12, player_id="steam:7",
    )
    output = write_selected_2d_viewer(store, controller, tmp_path / "viewer.html", selection)

    assert output.is_file()
    html = output.read_text(encoding="utf-8")
    assert '"tick":12' in html
    assert '"player_id":"steam:7"' in html
    unavailable = assess_map_asset(Path("missing-manifest.json"), "de_anubis")
    assert unavailable.availability == "missing"


def test_selected_2d_export_passes_the_existing_store_and_controller_to_the_viewer(tmp_path, monkeypatch) -> None:
    store = _store(tmp_path)
    chunk = store.load_round(1)
    chunk["frames"][1]["players"] = [{
        "player_id": "steam:7", "active": True, "alive": True, "team": "CT",
        "position": {"x": 10, "y": 20, "z": 30},
        "view_yaw_deg": 90, "view_pitch_deg": 0, "weapon": "knife",
    }]
    controller = ReplayController(store)
    selection = select_viewer_demo_state(
        store, controller, round_number=1, tick=12, player_id="steam:7",
    )
    received = {}

    def render(replay_path, output_path, **kwargs):
        received.update(replay_path=replay_path, output_path=output_path, **kwargs)
        output_path.write_text("<html></html>", encoding="utf-8")
        return output_path

    monkeypatch.setattr(viewer_demo, "render_viewer", render)

    write_selected_2d_viewer(store, controller, tmp_path / "viewer.html", selection)

    assert received["replay_path"] == store.manifest_path
    assert received["store"] is store
    assert received["controller"] is controller
