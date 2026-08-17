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
    assert result["checks"] == [{"id": "gpu", "status": "OK"}]
    assert result["policy"] == {
        "planning_input_only": True,
        "changes_applied": False,
        "apply_or_restore_available": False,
        "demo_or_replay_data_included": False,
    }


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
