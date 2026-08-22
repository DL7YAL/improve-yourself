import json
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import improve_yourself.demo_workflow as workflow


class _Store:
    def __init__(self, _path: Path) -> None:
        self.manifest = {
            "source": {"map_id": "de_ancient", "parser": {"name": "awpy", "version": "2.0.2"}},
            "players": [{"player_id": "steam:1", "display_name": "Alpha"}],
        }
        self.round_numbers = (1,)

    def load_round(self, _number: int) -> dict:
        return {
            "frames": [{
                "events": [{"type": "kill"}],
                "players": [{"player_id": "steam:1", "team": "CT"}],
            }]
        }


def test_preflight_shares_one_source_hash_and_one_awpy_parse(tmp_path: Path, monkeypatch) -> None:
    demo = tmp_path / "match.dem"
    demo.write_bytes(b"demo")
    source_hash = "a" * 64
    calls: list[object] = []

    monkeypatch.setattr(workflow, "validate_source", lambda path, max_bytes: calls.append(("validate", path, max_bytes)))
    monkeypatch.setattr(workflow, "_sha256", lambda path: calls.append(("hash", path)) or source_hash)

    @contextmanager
    def materialize(path: Path, *, max_bytes: int):
        calls.append(("materialize", path, max_bytes))
        yield path

    parsed = object()
    prepared = SimpleNamespace(
        parsed_demo=parsed,
        validation_report=SimpleNamespace(to_dict=lambda: {"schema": "iy.validation_report/v1", "status": "PASS"}),
        request=SimpleNamespace(to_dict=lambda: {"schema": "iy.analysis_request/v1"}),
        analysis_input=({}, [], [], object()),
    )
    monkeypatch.setattr(workflow, "materialize_demo", materialize)
    monkeypatch.setattr(workflow.AnalyzerCore, "prepare", lambda _self, _request, *, parser_path, **_kwargs: calls.append(("parse", parser_path)) or prepared)
    monkeypatch.setattr(workflow.AnalyzerCore, "finalize", lambda _self, _prepared, replay: {
        "schema": "iy.improve_match_data/v1", "metrics": {"source": {"sha256": source_hash}}, "replay": replay,
    })

    def analyze(source: Path, output: Path, *, source_sha256: str, core_result: object, **_kwargs) -> Path:
        calls.append(("analysis", source_sha256, core_result))
        output.mkdir(parents=True)
        path = output / "analysis.json"
        path.write_text("{}", encoding="utf-8")
        return path

    def replay(source: Path, analysis_path: Path, output: Path, *, source_sha256: str, parsed_demo: object) -> Path:
        calls.append(("replay", source_sha256, parsed_demo))
        path = output / source_hash[:12] / "replay-v2.json"
        path.parent.mkdir(parents=True)
        path.write_text("{}", encoding="utf-8")
        return path

    monkeypatch.setattr(workflow, "analyze", analyze)
    monkeypatch.setattr(workflow, "export_replay_v2", replay)
    monkeypatch.setattr(workflow, "ReplayStore", _Store)

    manifest_path = workflow.preflight_demo_workflow(demo, tmp_path / "out")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert [entry[0] for entry in calls].count("hash") == 1
    assert [entry[0] for entry in calls].count("parse") == 1
    assert ("analysis", source_hash, prepared) in calls
    assert ("replay", source_hash, parsed) in calls
    assert set(manifest["timing"]["phases"]) == {
        "T0_DEMO_SELECTED",
        "T1_TYPE_AND_SIZE_VALIDATED",
        "T2_SHA256_COMPLETE",
        "T3_AWPY_PARSE_STARTED",
        "T4_AWPY_PARSE_COMPLETE",
        "T5_REPLAY_V2_WRITTEN_AND_VALIDATED",
        "T6_WORKFLOW_READY_FOR_SELECTION",
    }
    assert manifest["analysis_request"]["schema"] == "iy.analysis_request/v1"
    assert set(manifest["artifacts"]) == {"analysis", "replay_v2", "improve_match_data", "validation_report"}
    assert json.loads((manifest_path.parent / manifest["artifacts"]["validation_report"]).read_text(encoding="utf-8"))["status"] == "PASS"


def test_preflight_reuses_only_a_prevalidated_hash_bound_workflow(tmp_path: Path, monkeypatch) -> None:
    demo = tmp_path / "match.dem"
    demo.write_bytes(b"demo")
    source_hash = "b" * 64
    existing = tmp_path / "out" / source_hash[:12] / "demo-workflow.json"
    existing.parent.mkdir(parents=True)
    existing.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(workflow, "validate_source", lambda *_args: None)
    monkeypatch.setattr(workflow, "_sha256", lambda _path: source_hash)
    monkeypatch.setattr(workflow, "_validate_reusable_workflow", lambda path, digest: path == existing and digest == source_hash)
    monkeypatch.setattr(workflow.AnalyzerCore, "prepare", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not parse reused workflow")))

    assert workflow.preflight_demo_workflow(demo, tmp_path / "out") == existing


def test_reuse_validation_fails_closed_for_invalid_or_incomplete_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "demo-workflow.json"
    manifest.write_text(json.dumps({"schema": "iy.demo_workflow/v1", "source_sha256": "c" * 64}), encoding="utf-8")

    assert workflow._validate_reusable_workflow(manifest, "c" * 64) is False
    assert workflow._validate_reusable_workflow(manifest, "d" * 64) is False


def test_tactical_html_export_is_lazy_and_preserves_the_canonical_flow(tmp_path: Path, monkeypatch) -> None:
    source_hash = "e" * 64
    replay = tmp_path / "replay-v2" / "replay-v2.json"
    flow = tmp_path / "analysis-flow.json"
    replay.parent.mkdir()
    replay.write_text("{}", encoding="utf-8")
    flow.write_text(json.dumps({"source": {"sha256": source_hash}, "scenes": [{"scene_id": "one"}]}), encoding="utf-8")
    manifest_path = tmp_path / "demo-workflow.json"
    manifest_path.write_text(json.dumps({
        "schema": "iy.demo_workflow/v1", "status": "READY_FOR_REVIEW", "source_sha256": source_hash,
        "artifacts": {"replay_v2": "replay-v2/replay-v2.json", "analysis_flow": "analysis-flow.json"},
    }), encoding="utf-8")

    def render(replay_path: Path, output_path: Path, *, scenes: list[dict]) -> Path:
        assert replay_path == replay
        assert scenes == [{"scene_id": "one"}]
        output_path.write_text("<html>fallback</html>", encoding="utf-8")
        return output_path

    monkeypatch.setattr(workflow, "render_viewer", render)
    result = workflow.ensure_tactical_replay_export(manifest_path)

    assert result == tmp_path / "tactical-replay.html"
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["artifacts"]["tactical_replay"] == "tactical-replay.html"
