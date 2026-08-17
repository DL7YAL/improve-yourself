import json
from pathlib import Path

import pytest

from improve_yourself.optimizer_input import OPTIMIZER_INPUT_SCHEMA, build_optimizer_input, export_optimizer_input


def system_check() -> dict:
    return {
        "schema": "iy.system_check/v1",
        "generated_at_utc": "2026-08-17T12:00:00+00:00",
        "policy": {"read_only": True, "changes_applied": False},
        "user_summary": {"status": "Hinweis"},
        "checks": [{"id": "gpu", "status": "OK"}],
    }


def test_builds_read_only_optimizer_input_without_demo_or_apply_data() -> None:
    result = build_optimizer_input(system_check())
    assert result["schema"] == OPTIMIZER_INPUT_SCHEMA
    assert result["source"]["schema"] == "iy.system_check/v1"
    assert result["planning_items"] == [{
        "id": "gpu", "label": None, "observed_state": None, "technical_status": "OK",
        "classification": "not_implemented", "assessment_status": "Nicht prüfbar / unbekannt",
        "priority": "informativ", "recommendation": "Keine automatische Änderung wurde vorgenommen.",
        "relevance": "Keine zusätzliche Bewertung verfügbar.", "evidence": {},
    }]
    assert result["policy"] == {
        "planning_input_only": True,
        "changes_applied": False,
        "apply_or_restore_available": False,
        "demo_or_replay_data_included": False,
    }


def test_projects_status_priority_recommendation_and_evidence() -> None:
    value = system_check()
    value["checks"] = [{
        "id": "graphics", "label": "Grafikeinstellungen", "status": "REVIEW",
        "classification": "technically_investigated_not_reliably_readable", "summary": "Nicht belastbar auslesbar.",
        "evidence": {"provider": "AMD"},
        "user_view": {"status": "Nicht prüfbar / unbekannt", "priority": "informativ", "action": "Manuell prüfen.", "relevance": "Ehrlicher Unknown-Zustand."},
    }]
    result = build_optimizer_input(value)
    assert result["planning_items"][0]["evidence"] == {"provider": "AMD"}
    assert result["planning_items"][0]["recommendation"] == "Manuell prüfen."
    assert result["optimizer_readiness"]["unknown_or_unreadable_items"] == ["graphics"]


def test_rejects_non_read_only_system_check() -> None:
    value = system_check()
    value["policy"] = {"read_only": False, "changes_applied": True}
    with pytest.raises(ValueError, match="read-only"):
        build_optimizer_input(value)


def test_exports_from_explicit_system_check_path(tmp_path: Path) -> None:
    source = tmp_path / "system-check.json"
    source.write_text(json.dumps(system_check()), encoding="utf-8")
    output = export_optimizer_input(source, tmp_path / "optimizer-input.json")
    assert json.loads(output.read_text(encoding="utf-8"))["schema"] == OPTIMIZER_INPUT_SCHEMA
