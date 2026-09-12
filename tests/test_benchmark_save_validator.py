import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
VALIDATOR = ROOT / "tools" / "benchmark" / "validate_benchmark_save.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_benchmark_save", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_complete_fail_honest_save_passes() -> None:
    module = load_validator()
    record = {
        "version": module.VERSION,
        "runtimeStatus": "complete",
        "measurementStatus": "unverified",
        "completedAt": 135.1875,
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
