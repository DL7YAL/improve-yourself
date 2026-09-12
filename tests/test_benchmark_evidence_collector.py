import importlib.util
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).parents[1]
TOOL_ROOT = ROOT / "tools" / "benchmark"
VALIDATOR = TOOL_ROOT / "validate_benchmark_runtime.py"
COLLECTOR = TOOL_ROOT / "collect_benchmark_evidence.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_tools():
    validator = load_module("validate_benchmark_runtime", VALIDATOR)
    collector = load_module("collect_benchmark_evidence", COLLECTOR)
    return validator, collector


def complete_log(validator) -> bytes:
    return (
        "\n".join(f"[IYBENCH] {event}" for event in validator.EXPECTED_EVENTS) + "\n"
    ).encode()


def create_inputs(root: Path, validator, collector):
    log = root / "iy_benchmark_console.log"
    log.write_bytes(complete_log(validator))
    captures = {}
    for index, (key, _, _, _) in enumerate(collector.CAPTURE_TARGETS, start=1):
        path = root / f"{key}.png"
        path.write_bytes(b"synthetic-test-image-" + bytes([index]))
        captures[key] = path
    return log, captures


def test_manifest_contains_hashes_but_no_absolute_capture_paths() -> None:
    validator, collector = load_tools()
    with tempfile.TemporaryDirectory() as directory:
        log, captures = create_inputs(Path(directory), validator, collector)
        manifest = collector.build_manifest(log, captures)
    assert manifest["runtime"]["status"] == "PASS"
    assert manifest["runtime"]["measurement_status"] == "unverified"
    assert manifest["assignment_status"] == "PARTIAL"
    assert len(manifest["captures"]) == 5
    serialized = json.dumps(manifest)
    assert directory not in serialized
    assert all(record["visual_status"] == "UNREVIEWED" for record in manifest["captures"])


def test_partial_runtime_log_is_rejected() -> None:
    validator, collector = load_tools()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        log, captures = create_inputs(root, validator, collector)
        log.write_text(f"[IYBENCH] {validator.EXPECTED_EVENTS[0]}\n", encoding="utf-8")
        try:
            collector.build_manifest(log, captures)
        except ValueError as error:
            assert "runtime log is not PASS" in str(error)
        else:
            raise AssertionError("partial runtime log was accepted")


def test_duplicate_capture_files_are_rejected() -> None:
    validator, collector = load_tools()
    with tempfile.TemporaryDirectory() as directory:
        log, captures = create_inputs(Path(directory), validator, collector)
        captures["inferno_apps"].write_bytes(captures["inferno_stairs"].read_bytes())
        try:
            collector.build_manifest(log, captures)
        except ValueError as error:
            assert "distinct SHA-256" in str(error)
        else:
            raise AssertionError("duplicate captures were accepted")
