import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
VALIDATOR = ROOT / "tools" / "benchmark" / "validate_benchmark_save.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_benchmark_save", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("completed_at", [134, 135.1875, 10**400])
def test_complete_fail_honest_save_passes(completed_at) -> None:
    module = load_validator()
    record = {
        "version": module.VERSION,
        "runtimeStatus": "complete",
        "measurementStatus": "unverified",
        "completedAt": completed_at,
    }
    assert module.validate_record(record) == []


def test_verified_measurement_claim_is_rejected() -> None:
    module = load_validator()
    record = {
        "version": module.VERSION,
        "runtimeStatus": "complete",
        "measurementStatus": "verified",
        "completedAt": 135.1875,
    }
    assert "measurementStatus" in module.validate_record(record)[0]


def test_early_completion_is_rejected() -> None:
    module = load_validator()
    record = {
        "version": module.VERSION,
        "runtimeStatus": "complete",
        "measurementStatus": "unverified",
        "completedAt": 70,
    }
    assert module.validate_record(record) == ["completedAt is too early for the full run: 70"]


def test_non_object_save_is_rejected() -> None:
    module = load_validator()
    assert module.validate_record([]) == ["save data must be a JSON object"]


@pytest.mark.parametrize("completed_at", [float("nan"), float("inf"), float("-inf"), 133.999, True, False, "134", None])
def test_invalid_completion_is_rejected(completed_at) -> None:
    module = load_validator()
    record = {
        "version": module.VERSION,
        "runtimeStatus": "complete",
        "measurementStatus": "unverified",
        "completedAt": completed_at,
    }
    errors = module.validate_record(record)
    assert errors
    assert any("completedAt" in error for error in errors)


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity", "1e400"])
def test_non_finite_json_save_is_rejected(number, tmp_path, monkeypatch, capsys) -> None:
    module = load_validator()
    save = tmp_path / "save.json"
    save.write_text(
        '{"version":"' + module.VERSION + '","runtimeStatus":"complete",'
        '"measurementStatus":"unverified","completedAt":' + number + '}',
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "argv", [str(VALIDATOR), str(save), "--json"])
    assert module.main() == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "PARTIAL"
    assert any("completedAt" in error for error in result["errors"])
