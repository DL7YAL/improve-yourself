import json
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

import improve_yourself.v2_local_review as review


def _manifest(path: Path, *, status: str = "READY_FOR_REVIEW") -> Path:
    path.write_text(json.dumps({
        "schema": "iy.demo_workflow/v1", "status": status, "source_sha256": "a" * 64,
        "artifacts": {"review": "review.html", "analysis_flow": "analysis-flow.json", "replay_v2": "replay.json"},
    }), encoding="utf-8")
    for name in ("review.html", "analysis-flow.json", "replay.json"):
        (path.parent / name).write_text("{}", encoding="utf-8")
    return path


def test_load_requires_intact_hash_bound_v2_workflow(tmp_path: Path, monkeypatch) -> None:
    path = _manifest(tmp_path / "demo-workflow.json")
    calls: list[tuple[Path, str]] = []
    monkeypatch.setattr(review, "_validate_reusable_workflow", lambda value, digest: calls.append((value, digest)) or True)
    root, manifest, allowed = review.load_v2_review_workflow(path)
    assert root == tmp_path
    assert manifest["source_sha256"] == "a" * 64
    assert calls == [(path, "a" * 64)]
    assert "review.html" in allowed


def test_load_fails_closed_for_non_review_or_unvalidated_workflow(tmp_path: Path, monkeypatch) -> None:
    path = _manifest(tmp_path / "demo-workflow.json", status="READY_FOR_SELECTION")
    with pytest.raises(ValueError, match="READY_FOR_REVIEW"):
        review.load_v2_review_workflow(path)
    path = _manifest(tmp_path / "other.json")
    monkeypatch.setattr(review, "_validate_reusable_workflow", lambda *_args: False)
    with pytest.raises(ValueError, match="integrity validation failed"):
        review.load_v2_review_workflow(path)


def test_prepare_uses_existing_v2_tactical_export_only_after_validation(tmp_path: Path, monkeypatch) -> None:
    path = _manifest(tmp_path / "demo-workflow.json")
    monkeypatch.setattr(review, "_validate_reusable_workflow", lambda *_args: True)
    calls: list[Path] = []
    def export(value: Path) -> Path:
        calls.append(value)
        manifest = json.loads(value.read_text(encoding="utf-8"))
        manifest["artifacts"]["tactical_replay"] = "tactical-replay.html"
        value.write_text(json.dumps(manifest), encoding="utf-8")
        (value.parent / "tactical-replay.html").write_text("<html></html>", encoding="utf-8")
        return value.parent / "tactical-replay.html"
    monkeypatch.setattr(review, "ensure_tactical_replay_export", export)
    root, allowed = review.prepare_v2_local_review(path)
    assert calls == [path]
    assert root == tmp_path
    assert "tactical-replay.html" in allowed


def test_loopback_server_serves_only_registered_artifacts(tmp_path: Path) -> None:
    (tmp_path / "review.html").write_text("<h1>review</h1>", encoding="utf-8")
    (tmp_path / "private.txt").write_text("not served", encoding="utf-8")
    server = review.V2LocalReviewServer(("127.0.0.1", 0), tmp_path, {"review.html"})
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    root = f"http://127.0.0.1:{server.server_port}"
    try:
        assert urlopen(f"{root}/review.html").read() == b"<h1>review</h1>"
        with pytest.raises(HTTPError) as missing:
            urlopen(f"{root}/private.txt")
        assert missing.value.code == 404
        with pytest.raises(HTTPError) as post:
            urlopen(Request(f"{root}/review.html", data=b"{}", method="POST"))
        assert post.value.code == 404
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
