import json
import hashlib
from pathlib import Path

import improve_yourself.workflow as workflow


def test_integrates_artifacts_and_writes_review_manifest(tmp_path: Path, monkeypatch) -> None:
    demo = tmp_path / "match.dem"
    demo.write_bytes(b"demo")

    def fake_analyze(source: Path, output: Path, max_bytes: int) -> Path:
        output.mkdir(parents=True)
        path = output / "analysis.json"
        path.write_text("{}", encoding="utf-8")
        return path

    def fake_replay(source: Path, analysis: Path, output: Path, max_frames: int) -> Path:
        output.mkdir(parents=True)
        path = output / "replay.json"
        path.write_text(json.dumps({"source_sha256": hashlib.sha256(b"demo").hexdigest(), "scenes": []}), encoding="utf-8")
        return path

    def fake_viewer(replay: Path, output: Path, **kwargs) -> Path:
        output.write_text("<html></html>", encoding="utf-8")
        return output

    def fake_excel(analysis: Path, output: Path) -> Path:
        output.write_bytes(b"xlsx")
        return output

    def fake_preflight(source: Path, output: Path, max_bytes: int) -> Path:
        output.mkdir(parents=True)
        path = output / "preflight.json"
        path.write_text(json.dumps({"source_sha256": hashlib.sha256(b"demo").hexdigest()}), encoding="utf-8")
        return path

    def fake_review(system: Path | None, analysis: Path, replay: Path, viewer: Path, output: Path, **kwargs: object) -> Path:
        assert system is None
        output.write_text("<html></html>", encoding="utf-8")
        return output

    monkeypatch.setattr(workflow, "analyze", fake_analyze)
    monkeypatch.setattr(workflow, "preflight_demo", fake_preflight)
    monkeypatch.setattr(workflow, "export_replay", fake_replay)
    monkeypatch.setattr(workflow, "render_viewer", fake_viewer)
    monkeypatch.setattr(workflow, "build_excel_report", fake_excel)
    monkeypatch.setattr(workflow, "render_review_surface", fake_review)

    manifest_path = workflow.run_workflow(demo, tmp_path / "output")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "iy.workflow/v1"
    assert payload["status"] == "READY_FOR_REVIEW"
    assert payload["policy"]["changes_applied"] is False
    assert payload["policy"]["automated_cheat_verdict"] is False
    assert payload["artifacts"] == {
        "preflight": "preflight/" + hashlib.sha256(b"demo").hexdigest()[:12] + ".preflight.json",
        "analysis": "analysis/analysis.json",
        "replay": "replay/replay.json", "viewer": "viewer.html",
        "review": "review.html",
        "excel_report": "Improve-Yourself-Analyzer-Report.xlsx",
        "review_state": "review-state.json",
    }


def test_rejects_missing_demo(tmp_path: Path) -> None:
    try:
        workflow.run_workflow(tmp_path / "missing.dem", tmp_path / "output")
    except FileNotFoundError as error:
        assert "demo does not exist" in str(error)
    else:
        raise AssertionError("expected FileNotFoundError")
