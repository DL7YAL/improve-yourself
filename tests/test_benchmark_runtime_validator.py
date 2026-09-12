import hashlib
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
VALIDATOR = ROOT / "tools" / "benchmark" / "validate_benchmark_runtime.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_benchmark_runtime", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_text(module, events=None) -> str:
    selected = module.EXPECTED_EVENTS if events is None else events
    lines = []
    for event in selected:
        lines.append(f"[IYBENCH] {event}")
        lines.append(f'"[IYBENCH] {event}"')
    return "\n".join(lines) + "\n"


def test_complete_latest_segment_passes_and_quoted_echoes_are_ignored() -> None:
    module = load_validator()
    text = canonical_text(module)
    result = module.validate_latest(text)
    assert result.status == "PASS"
    assert result.segment_count == 1
    assert result.canonical_event_count == len(module.EXPECTED_EVENTS)
    assert result.errors == ()


def test_latest_partial_restart_cannot_hide_behind_older_complete_run() -> None:
    module = load_validator()
    complete = canonical_text(module)
    partial = canonical_text(module, module.EXPECTED_EVENTS[:8])
    result = module.validate_latest(complete + partial)
    assert result.status == "PARTIAL"
    assert result.segment_count == 2
    assert result.segment_index == 2
    assert "got '<missing>'" in result.errors[0]


def test_duplicate_or_reordered_contract_event_fails() -> None:
    module = load_validator()
    events = list(module.EXPECTED_EVENTS)
    events.insert(5, events[4])
    result = module.validate_latest(canonical_text(module, events))
    assert result.status == "PARTIAL"
    assert "contract mismatch" in result.errors[0]


def test_runtime_error_fails_even_when_remaining_contract_is_complete() -> None:
    module = load_validator()
    events = list(module.EXPECTED_EVENTS)
    events.insert(-1, "ERROR scope=think detail=boom")
    result = module.validate_latest(canonical_text(module, events))
    assert result.status == "PARTIAL"
    assert result.errors[0] == "ERROR scope=think detail=boom"


def test_validation_payload_is_fail_honest_about_measurement() -> None:
    module = load_validator()
    text = canonical_text(module)
    result = module.validate_latest(text)
    digest = hashlib.sha256(text.encode()).hexdigest()
    payload = result.as_dict(digest)
    assert payload["runtime_status"] == "complete"
    assert payload["measurement_status"] == "unverified"
    assert payload["input_sha256"] == digest.upper()
    json.dumps(payload)


def test_missing_ready_is_blocked() -> None:
    module = load_validator()
    result = module.validate_latest("[IYBENCH] PASS_START type=warmup\n")
    assert result.status == "BLOCKED"
    assert result.segment_count == 0
