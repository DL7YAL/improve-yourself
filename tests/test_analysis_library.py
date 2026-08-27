import json
from pathlib import Path

import pytest

from improve_yourself.analysis_library import LocalAnalysisLibrary


def _workflow(root: Path, *, source_name: str = "match.dem", valid: bool = True) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "demo-workflow.json"
    path.write_text(json.dumps({"schema": "iy.demo_workflow/v1", "status": "READY_FOR_REVIEW", "source_sha256": "a" * 64, "source_demo_name": source_name, "preflight": {"map_id": "de_ancient"}, "counts": {"scenes": 3}, "valid": valid}), encoding="utf-8")
    return path


def _validator(path: Path) -> Path:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if path.name != "demo-workflow.json" or payload.get("valid") is not True:
        raise ValueError("invalid canonical workflow")
    return path


def test_register_reload_deduplicate_and_remove_reference(tmp_path: Path) -> None:
    manifest = _workflow(tmp_path / "analysis")
    library = LocalAnalysisLibrary(tmp_path / "index.json", _validator)
    library.register(manifest); library.register(manifest)
    assert len(library.entries()) == 1 and library.entries()[0]["state"] == "READY"
    reloaded = LocalAnalysisLibrary(tmp_path / "index.json", _validator)
    assert reloaded.entries()[0]["map_id"] == "de_ancient"
    reloaded.remove(manifest)
    assert reloaded.entries() == () and manifest.exists()


def test_corrupt_or_broken_entry_does_not_break_other_registered_entry(tmp_path: Path) -> None:
    good = _workflow(tmp_path / "good")
    index = tmp_path / "index.json"
    library = LocalAnalysisLibrary(index, _validator); library.register(good)
    document = json.loads(index.read_text(encoding="utf-8")); document["entries"].append({"manifest_path": "../bad"})
    index.write_text(json.dumps(document), encoding="utf-8")
    states = [item["state"] for item in library.entries()]
    assert states == ["READY", "INVALID"]


def test_tampered_missing_source_and_legacy_v1_are_disabled(tmp_path: Path) -> None:
    tampered = _workflow(tmp_path / "tampered", valid=False)
    missing_source = _workflow(tmp_path / "missing", source_name="")
    legacy = tmp_path / "legacy" / "demo-workflow.json"; legacy.parent.mkdir(); legacy.write_text(json.dumps({"schema": "iy.workflow/v1"}), encoding="utf-8")
    index = tmp_path / "index.json"
    index.write_text(json.dumps({"schema": "iy.local_analysis_library/v1", "entries": [
        {"manifest_path": str(tampered)}, {"manifest_path": str(missing_source)}, {"manifest_path": str(legacy)}]}), encoding="utf-8")
    states = [item["state"] for item in LocalAnalysisLibrary(index, _validator).entries()]
    assert states == ["TAMPERED", "MISSING SOURCE", "LEGACY V1"]


def test_bad_index_recovers_and_registration_never_selects_latest(tmp_path: Path) -> None:
    index = tmp_path / "index.json"; index.write_text("{", encoding="utf-8")
    first = _workflow(tmp_path / "first"); second = _workflow(tmp_path / "second")
    library = LocalAnalysisLibrary(index, _validator); library.register(first)
    assert [item["demo_basename"] for item in library.entries()] == ["match.dem"]
    assert second not in [Path(str(item.get("manifest_path", ""))) for item in library.entries()]


def test_registration_rejects_invalid_or_traversal_path(tmp_path: Path) -> None:
    library = LocalAnalysisLibrary(tmp_path / "index.json", _validator)
    with pytest.raises((ValueError, FileNotFoundError)):
        library.register(tmp_path / ".." / "not-a-workflow.json")
