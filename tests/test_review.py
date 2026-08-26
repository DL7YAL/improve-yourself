import json
from pathlib import Path

import pytest

from improve_yourself.review import render_review_surface


def write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_renders_reduced_review_surface_and_escapes_content(tmp_path: Path) -> None:
    source_hash = "a" * 64
    system = write(tmp_path / "system.json", {"schema": "iy.system_check/v1", "user_summary": {"next_steps": [
        {"label": "Anzeige", "priority": "wichtig", "action": "Aktive Bildwiederholrate prüfen."}
    ], "anti_cheat_readiness": {"status": "bestätigt", "message": "Secure Boot und TPM 2.0 bestätigt.", "criteria": [
        {"label": "Secure Boot", "status": "OK"}, {"label": "TPM 2.0", "status": "OK"}
    ]}}, "checks": [
        {"label": "CPU <fast>", "status": "OK", "summary": "Detected & safe", "user_view": {
            "status": "OK", "priority": "informativ", "relevance": "Kein Handlungsbedarf.", "action": "Keine Aktion erforderlich."
        }, "evidence": {"installed_version": "1.0", "official_version": "2.0", "official_source": "https://example.test", "checked_at_utc": "2026-08-17T00:00:00+00:00"}}
    ]})
    analysis = write(tmp_path / "analysis.json", {
        "schema": "iy.analysis/v1", "source_sha256": source_hash, "map_name": "de_mirage",
        "kills": [{}, {}], "data_quality": {"status": "limited", "warnings": ["footsteps: KeyError: raw", "No <sound>"]},
        "user_view": {"facts": ["2 Kills wurden gelesen."], "indicators": ["Kein Cheat-Nachweis."],
                      "limitations": ["Schritt-Ereignisse fehlen."], "assessment": {"status": "Hinweis", "message": "Teilweise Daten.", "action": "Nicht hineininterpretieren."}},
    })
    replay = write(tmp_path / "replay.json", {
        "schema": "iy.replay/v1", "source_sha256": source_hash,
        "scenes": [{"round_number": 2, "marker_player": "</script>", "start_tick": 10, "end_tick": 20, "frames": [{}]}],
    })
    viewer = tmp_path / "viewer.html"
    viewer.write_text("viewer", encoding="utf-8")
    result = render_review_surface(system, analysis, replay, viewer, tmp_path / "review.html")
    document = result.read_text(encoding="utf-8")
    assert "Tactical Replay öffnen" in document
    assert "Clipwürdig" not in document
    assert "Näher ansehen" in document
    assert 'href="viewer.html"' in document
    assert "CPU &lt;fast&gt;" in document
    assert "Detected &amp; safe" in document
    assert "Installierte Software:" in document
    assert "Offizieller Stand:" in document
    assert "https://example.test" in document
    assert "&lt;/script&gt;" in document
    assert "kein Cheat-Nachweis" in document
    assert "KeyError" not in document
    assert "No &lt;sound&gt;" in document
    assert "Was jetzt wichtig ist" in document
    assert "Aktive Bildwiederholrate prüfen." in document
    assert "Sicher beobachtet" in document
    assert "Kein Cheat-Nachweis." in document
    assert "Datenqualität und Grenzen" in document
    assert "Anti-Cheat-Readiness" in document
    assert "Secure Boot und TPM 2.0 bestätigt." in document


def test_rejects_mismatched_sources(tmp_path: Path) -> None:
    system = write(tmp_path / "system.json", {"schema": "iy.system_check/v1", "checks": []})
    analysis = write(tmp_path / "analysis.json", {"schema": "iy.analysis/v1", "source_sha256": "a" * 64, "data_quality": {}})
    replay = write(tmp_path / "replay.json", {"schema": "iy.replay/v1", "source_sha256": "b" * 64, "scenes": []})
    with pytest.raises(ValueError, match="source hashes differ"):
        render_review_surface(system, analysis, replay, tmp_path / "viewer.html", tmp_path / "review.html")


def test_renders_analyzer_review_without_implicit_system_check(tmp_path: Path) -> None:
    source_hash = "c" * 64
    analysis = write(tmp_path / "analysis.json", {
        "schema": "iy.analysis/v1", "source_sha256": source_hash, "map_name": "de_mirage",
        "kills": [], "data_quality": {}, "user_view": {},
    })
    replay = write(tmp_path / "replay.json", {
        "schema": "iy.replay/v1", "source_sha256": source_hash, "scenes": [],
    })
    viewer = tmp_path / "viewer.html"
    viewer.write_text("viewer", encoding="utf-8")
    document = render_review_surface(None, analysis, replay, viewer, tmp_path / "review.html").read_text(encoding="utf-8")
    assert "Tactical Replay öffnen" in document
    assert "System Check" not in document
    assert "Anti-Cheat-Readiness" not in document
