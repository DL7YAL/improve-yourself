import json
import re
from pathlib import Path


MAP_ROOT = Path("assets/maps/improve_yourself_benchmark")
MAP = MAP_ROOT / "maps" / "improve_yourself_benchmark.vmap"
PROVENANCE_FILES = (
    MAP_ROOT / "NUKE_OUTSIDE_ASSET_PROVENANCE.json",
    MAP_ROOT / "TRANSITION_WORLDS_ASSET_PROVENANCE.json",
)
SCENE_REFERENCE_PREFIXES = (
    b"materials/de_nuke/",
    b"materials/de_ancient/",
    b"materials/de_inferno/",
    b"models/props/de_nuke/",
    b"models/props/de_ancient/",
    b"models/props/de_inferno/",
)


def records() -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in PROVENANCE_FILES]


def test_benchmark_runtime_references_are_fail_closed() -> None:
    nuke, transitions = records()
    assert nuke["scene"] == "nuke_outside"
    assert transitions["scenes"] == ["benchmark_intro", "ancient_b", "inferno_apps_a"]

    for record in (nuke, transitions):
        assert record["schema"] == "iy.cs2-workshop-asset-provenance/v1"
        assert record["verification"] == {
            "method": "Installed CS2 pak01_dir.vpk directory-index lookup only",
            "runtime_reference_only": True,
            "vpk_payload_extracted": False,
            "repository_asset_copy_created": False,
        }
        paths = set()
        for asset in record["assets"]:
            assert asset["rights_class"] == "VALVE_RUNTIME_REFERENCE"
            assert asset["distribution"] == "CS2_WORKSHOP_RUNTIME"
            assert asset["runtime_reference_only"] is True
            assert asset["asset_path"].endswith((".vmdl", ".vmat"))
            assert not asset["asset_path"].endswith("_c")
            paths.add(asset["asset_path"])
        assert len(paths) == len(record["assets"])


def test_all_provenanced_runtime_references_exist_in_hammer_map() -> None:
    map_bytes = MAP.read_bytes()
    for record in records():
        for asset in record["assets"]:
            assert asset["asset_path"].encode("ascii") in map_bytes


def test_all_scene_runtime_references_are_provenanced() -> None:
    provenanced = {
        asset["asset_path"].encode("ascii")
        for record in records()
        for asset in record["assets"]
        if asset["asset_path"].encode("ascii").startswith(SCENE_REFERENCE_PREFIXES)
    }
    scene_references = {
        match
        for match in re.findall(
            rb"(?:materials|models)/[A-Za-z0-9_./-]+\.(?:vmat|vmdl)",
            MAP.read_bytes(),
        )
        if match.startswith(SCENE_REFERENCE_PREFIXES)
    }
    assert scene_references == provenanced
