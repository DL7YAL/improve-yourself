import gzip
import hashlib
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
    source_hash = "a" * 64
    source = {"sha256": source_hash, "map_id": "de_ancient", "tick_rate": 64.0, "parser": {"name": "awpy", "version": "2.0.2"}}
    flow = {
        "schema": "iy.analysis_flow/v1",
        "source": source,
        "roster": roster,
        "selection": {"mode": "player_select" if selected else "full_demo", "player_ids": list(selected)},
        "scenes": [{"scene_id": "one"}] if not selected or "ct1" in selected else [],
    }
    (root / "analysis-flow.json").write_text(json.dumps(flow), encoding="utf-8")
    (root / "analysis.json").write_text(json.dumps({"schema": "iy.analysis/v1", "source_sha256": source_hash}), encoding="utf-8")
    rounds = root / "replay-v2" / "rounds"
    rounds.mkdir(parents=True, exist_ok=True)
    chunk_path = rounds / "round-001.json.gz"
    with gzip.open(chunk_path, "wt", encoding="utf-8") as stream:
        json.dump({"schema": "iy.replay_round/v2", "round_number": 1, "frames": [{"tick": 1, "round_number": 1, "players": [], "utilities": [], "events": []}]}, stream)
    replay = {
        "schema": "iy.replay/v2", "source": source, "coordinate_space": "cs2_world",
        "players": [{"player_id": item["player_id"]} for item in roster],
        "rounds": [{"round_number": 1, "first_tick": 1, "last_tick": 1, "frame_count": 1, "chunk": "rounds/round-001.json.gz", "sha256": hashlib.sha256(chunk_path.read_bytes()).hexdigest()}],
        "capabilities": {name: "unavailable" for name in ("positions", "view_yaw", "view_pitch", "alive_state", "weapon_state", "velocity", "utility_lifetimes", "utility_trajectories", "flash_effect", "sound", "map_geometry")},
    }
    (root / "replay-v2" / "replay-v2.json").write_text(json.dumps(replay), encoding="utf-8")
    (root / "timeline.json").write_text(json.dumps({"source": source, "timeline": []}), encoding="utf-8")
    (root / "review.html").write_text("review", encoding="utf-8")
    (root / "cs2-review-commands.txt").write_text("demo_gototick 1\n", encoding="utf-8")
    manifest = {
        "schema": "iy.demo_workflow/v1",
        "status": "READY_FOR_REVIEW",
        "source_sha256": source_hash,
        "selection": flow["selection"],
        "counts": {"players": len(roster), "scenes": len(flow["scenes"])},
        "policy": {"real_demo_required": True, "fake_results": False, "local_only": True},
        "artifacts": {"analysis": "analysis.json", "replay_v2": "replay-v2/replay-v2.json", "analysis_flow": "analysis-flow.json", "timeline": "timeline.json", "review": "review.html", "cs2_review_commands": "cs2-review-commands.txt"},
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


def test_shell_opens_validated_existing_workflow_without_runner(tmp_path: Path) -> None:
    manifest = _write_result(tmp_path / "run", ("ct1",))
    controller = AnalyzerShellController(
        tmp_path / "unused",
        runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not parse")),
    )
    result = controller.open_existing_workflow(manifest)
    assert result.map_id == "de_ancient"
    assert result.selection_mode == "player_select"
    assert controller.selected_ids == ["ct1"]


@pytest.mark.parametrize("mutation, message", [
    (lambda manifest: manifest.update(source_sha256="BAD"), "source_sha256"),
    (lambda manifest: manifest["artifacts"].update(review="../review.html"), "escapes workflow root"),
    (lambda manifest: manifest["artifacts"].pop("timeline"), "required artifact is missing"),
])
def test_shell_rejects_untrusted_existing_workflow(tmp_path: Path, mutation, message: str) -> None:
    path = _write_result(tmp_path / "run")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    mutation(manifest)
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        AnalyzerShellController(tmp_path).open_existing_workflow(path)


def test_shell_rejects_replay_hash_mismatch(tmp_path: Path) -> None:
    path = _write_result(tmp_path / "run")
    replay_path = path.parent / "replay-v2" / "replay-v2.json"
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    replay["source"]["sha256"] = "b" * 64
    replay_path.write_text(json.dumps(replay), encoding="utf-8")
    with pytest.raises(ValueError, match="replay source metadata differs"):
        AnalyzerShellController(tmp_path).open_existing_workflow(path)
