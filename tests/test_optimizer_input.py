from __future__ import annotations

import json
from pathlib import Path

import pytest

from improve_yourself.optimizer_evidence import profile_from_system_check
from improve_yourself.optimizer_input import OPTIMIZER_INPUT_SCHEMA, build_optimizer_input, export_optimizer_input


def _system_check(*, checks: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "iy.system_check/v1",
        "generated_at_utc": "2026-08-26T12:00:00+00:00",
        "policy": {"read_only": True, "changes_applied": False, "elevation_requested": False},
        "checks": checks,
    }


def test_known_system_check_evidence_is_projected_through_the_existing_boundary() -> None:
    payload = _system_check(checks=[
        {"id": "cpu", "evidence": {"name": "AMD Ryzen"}},
        {"id": "gpu", "evidence": {"adapters": [{"name": "AMD Radeon", "driver_version": "1.2.3"}]}},
        {"id": "memory", "evidence": {"total_gb": 32}},
        {"id": "motherboard", "evidence": {"manufacturer": "Vendor", "product": "Board", "bios_version": "B1"}},
    ])

    result = build_optimizer_input(payload)

    assert result["schema"] == OPTIMIZER_INPUT_SCHEMA
    assert result["foundation_profile"] == profile_from_system_check(payload)
    assert result["foundation_profile"]["gpu"]["driver_version"] == "1.2.3"
    assert result["foundation_profile"]["bios"]["version"] == "B1"
    assert result["source"] == {
        "schema": "iy.system_check/v1",
        "generated_at_utc": "2026-08-26T12:00:00+00:00",
        "read_only": True,
        "changes_applied": False,
    }


def test_missing_evidence_stays_unknown_and_is_not_manufactured() -> None:
    payload = _system_check(checks=[
        {"id": "graphics_settings_profile", "classification": "technically_investigated_not_reliably_readable", "evidence": {}},
    ])

    result = build_optimizer_input(payload)
    profile = result["foundation_profile"]

    assert profile["gpu"] == {"name": None, "vendor": None, "driver_version": None}
    assert profile["bios"] == {"version": None, "date": None}
    assert "cs2" not in profile
    assert "network" not in profile
    assert result["optimizer_readiness"]["unknown_or_unreadable_items"] == ["graphics_settings_profile"]


def test_optimizer_input_drops_demo_and_replay_data_and_has_no_apply_authority() -> None:
    payload = _system_check(checks=[{"id": "cpu", "evidence": {"name": "CPU"}}])
    payload["demo"] = {"source": "must-not-flow"}
    payload["replay"] = {"schema": "iy.replay/v2"}

    result = build_optimizer_input(payload)

    assert "demo" not in result
    assert "replay" not in result
    assert result["policy"] == {
        "planning_input_only": True,
        "changes_applied": False,
        "apply_or_restore_available": False,
        "demo_or_replay_data_included": False,
    }
    assert result["optimizer_readiness"]["automatic_apply_authorized"] is False


def test_unsafe_or_non_read_only_system_check_is_rejected() -> None:
    payload = _system_check(checks=[])
    payload["policy"] = {"read_only": False, "changes_applied": True}

    assert profile_from_system_check(payload) is None
    with pytest.raises(ValueError, match="read-only evidence"):
        build_optimizer_input(payload)


def test_export_uses_only_an_explicit_system_check_artifact(tmp_path: Path) -> None:
    source = tmp_path / "system-check.json"
    source.write_text(json.dumps(_system_check(checks=[{"id": "cpu", "evidence": {"name": "CPU"}}])), encoding="utf-8")

    output = export_optimizer_input(source, tmp_path / "optimizer-input.json")

    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["schema"] == OPTIMIZER_INPUT_SCHEMA
    assert result["policy"]["demo_or_replay_data_included"] is False
