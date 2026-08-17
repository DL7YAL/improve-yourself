import json
from pathlib import Path

from improve_yourself.system_review import render_system_review


def test_renders_separate_system_and_optimizer_review(tmp_path: Path) -> None:
    system = tmp_path / "system.json"
    optimizer = tmp_path / "optimizer.json"
    system.write_text(json.dumps({"schema": "iy.system_check/v1", "checks": [{
        "label": "GPU <safe>", "summary": "Erkannt", "classification": "reliably_automatically_checked",
        "user_view": {"status": "OK", "relevance": "Klar", "action": "Keine Aktion."},
    }]}), encoding="utf-8")
    optimizer.write_text(json.dumps({"schema": "iy.optimizer_input/v1", "optimizer_readiness": {"unknown_or_unreadable_items": ["graphics"]}}), encoding="utf-8")
    document = render_system_review(system, optimizer, tmp_path / "system-review.html").read_text(encoding="utf-8")
    assert "GPU &lt;safe&gt;" in document
    assert "Zuverlässig automatisch geprüft" in document
    assert "graphics" in document
    assert "Demo Analyzer" in document
