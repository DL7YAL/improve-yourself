import json
from pathlib import Path

import pytest

from improve_yourself.analyzer_shell import AnalyzerShellController


def _write_result(root: Path, selected: tuple[str, ...] = ()) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    roster = [
        {"player_id": "ct1", "display_name": "CT One", "initial_team": "CT"},
        {"player_id": "ct2", "display_name": "CT Two", "initial_team": "CT"},
        {"player_id": "t1", "display_name": "T One", "initial_team": "T"},
    ]
    flow = {
        "source": {"map_id": "de_ancient"},
        "roster": roster,
        "selection": {"mode": "player_select" if selected else "full_demo", "player_ids": list(selected)},
        "scenes": [{"scene_id": "one"}] if not selected or "ct1" in selected else [],
    }
    (root / "analysis-flow.json").write_text(json.dumps(flow), encoding="utf-8")
    (root / "review.html").write_text("review", encoding="utf-8")
    manifest = {
        "schema": "iy.demo_workflow/v1",
        "artifacts": {"analysis_flow": "analysis-flow.json", "review": "review.html"},
    }
    path = root / "demo-workflow.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_shell_import_and_selection_reuse_existing_workflow(tmp_path: Path) -> None:
    demo = tmp_path / "match.dem"
    demo.write_bytes(b"real demo placeholder")
    calls: list[tuple[str, tuple[str, ...]]] = []

    def runner(source: Path, output: Path, *, max_bytes: int) -> Path:
        calls.append((source.name, ()))
        return _write_result(output / "run")

    def rerender(manifest: Path, *, player_ids: tuple[str, ...]) -> Path:
        calls.append(("rerender", player_ids))
        return _write_result(manifest.parent, player_ids)

    controller = AnalyzerShellController(tmp_path / "output", runner=runner, rerenderer=rerender)
    result = controller.import_demo(demo)
    assert result.map_id == "de_ancient"
    assert [player.display_name for player in result.players] == ["CT One", "CT Two", "T One"]

    controller.add_team("CT")
    controller.add_player("ct1")
    assert controller.selected_ids == ["ct1", "ct2"]
    assert [player.player_id for player in controller.available_players()] == ["t1"]
    selected = controller.analyze_selection()
    assert selected.selection_mode == "player_select"
    assert selected.selected_ids == ("ct1", "ct2")
    assert calls == [("match.dem", ()), ("rerender", ("ct1", "ct2"))]


def test_shell_full_demo_reset_and_validation(tmp_path: Path) -> None:
    manifest = _write_result(tmp_path / "run")
    controller = AnalyzerShellController(tmp_path, runner=lambda *_args, **_kwargs: manifest)
    demo = tmp_path / "match.dem"
    demo.write_bytes(b"demo")
    controller.import_demo(demo)
    controller.add_player("t1")
    controller.set_full_demo()
    assert controller.selected_ids == []
    assert controller.selection_mode == "full_demo"
    controller.reset_players()
    assert controller.selection_mode == "player_select"
    with pytest.raises(ValueError, match="requires at least one"):
        controller.analyze_selection()
    with pytest.raises(ValueError, match="unknown player"):
        controller.add_player("missing")
    with pytest.raises(ValueError, match="team must"):
        controller.add_team("both")


def test_shell_rejects_non_demo_before_runner(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("no", encoding="utf-8")
    controller = AnalyzerShellController(tmp_path)
    with pytest.raises(ValueError, match="select a .dem"):
        controller.import_demo(source)
