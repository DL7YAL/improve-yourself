from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
import shutil

import pytest

from tools.pov_prep_data.validate_render_ready import RenderReadyValidationError, load_and_validate, validate_document

ROOT = Path(__file__).resolve().parents[2]
RESOURCE_ROOT = ROOT / "resources" / "3d_pov"
PACKAGE = RESOURCE_ROOT / "de_anubis" / "render_ready.json"
MIRAGE = RESOURCE_ROOT / "de_mirage" / "render_ready.json"
SCENE = RESOURCE_ROOT / "de_anubis" / "reference_scene.json"
SCHEMA = RESOURCE_ROOT / "schema" / "iy.3d_pov_render_ready.v1.schema.json"


def package() -> dict:
    return deepcopy(load_and_validate(PACKAGE))


def test_render_ready_package_validates_and_owns_no_runtime_state() -> None:
    document = package()
    assert document["canonical_runtime"]["owns_tick"] is False
    assert document["canonical_runtime"]["parses_demo"] is False
    assert document["canonical_runtime"]["embeds_replay_frames"] is False
    assert document["map_geometry"]["runtime_contract"] == "iy.map_asset/v1"
    assert document["map_geometry"]["bundled"] is False


def test_mirage_reuses_shared_fallback_assets_without_map_geometry() -> None:
    document = load_and_validate(MIRAGE)
    assert document["map_id"] == "de_mirage"
    assert document["map_geometry"]["bundled"] is False
    assert document["semantic_mapping"] == "../de_anubis/semantic_assets.json"
    assert document["camera_policy"] == "../de_anubis/render_profile.json"
    assert document["verification"]["status"] == "PREP_READY_PENDING_LOCAL_EXECUTION"


def test_committed_render_ready_document_matches_json_schema_top_level_contract() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8")); document = json.loads(PACKAGE.read_text(encoding="utf-8"))
    expected_types = {"canonical_runtime": "object", "map_geometry": "object", "assets": "array", "semantic_mapping": "string", "camera_policy": "string", "environment": "string", "collision_visibility": "object", "dynamic_objects": "string", "floor_policy": "string", "fallbacks": "array", "reference_scene": "string", "licensing": "object", "verification": "object"}
    assert schema["additionalProperties"] is False and set(schema["required"]) == set(document)
    json_type_to_python_type = {"object": dict, "array": list, "string": str}
    for field, expected_type in expected_types.items(): assert schema["properties"][field]["type"] == expected_type and isinstance(document[field], json_type_to_python_type[expected_type])
    assert schema["properties"]["schema"]["const"] == document["schema"]
    assert document["map_id"] in schema["properties"]["map_id"]["enum"]
    assert schema["properties"]["purpose"]["const"] == document["purpose"]


def test_original_assets_are_present_cc0_and_integrity_bound() -> None:
    for asset in package()["assets"]:
        assert asset["license"] == "CC0-1.0" and asset["classification"].startswith("FALLBACK") and len(asset["git_blob_sha1"]) == 40
        assert (PACKAGE.parent / asset["path"]).resolve().is_file()


def test_asset_tampering_fails_integrity_without_touching_repository(tmp_path: Path) -> None:
    copied = tmp_path / "3d_pov"; shutil.copytree(RESOURCE_ROOT, copied); player = copied / "original_assets" / "player_proxy.obj"
    player.write_text(player.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
    with pytest.raises(RenderReadyValidationError, match="asset integrity differs"): load_and_validate(copied / "de_anubis" / "render_ready.json")


def test_no_proprietary_or_executable_assets_are_bundled() -> None:
    forbidden = {".vpk", ".vmdl", ".vmdl_c", ".vphys", ".vphys_c", ".tri", ".glb", ".dll", ".exe", ".wav", ".mp3", ".ogg"}
    assert not any(path.suffix.lower() in forbidden for path in RESOURCE_ROOT.rglob("*"))


def test_camera_reference_math_is_deterministic() -> None:
    scene = json.loads(SCENE.read_text(encoding="utf-8")); camera = scene["camera"]
    observer = next(item for item in scene["anchors"] if item["id"] == camera["anchor_id"])["position"]; eye = [observer[0], observer[1], observer[2] + 64.0]
    assert eye == camera["expected_eye_position"]
    yaw = math.radians(camera["yaw_deg"]["value"]); pitch = math.radians(camera["pitch_deg"]["value"])
    forward = [math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), -math.sin(pitch)]
    assert forward == camera["expected_forward"]


def test_invalid_runtime_or_fallback_claims_fail_closed(tmp_path: Path) -> None:
    runtime = package(); runtime["canonical_runtime"]["owns_tick"] = True
    with pytest.raises(RenderReadyValidationError, match="runtime boundary"): validate_document(runtime, PACKAGE)
    licensing = package(); licensing["licensing"]["valve_assets_bundled"] = True
    with pytest.raises(RenderReadyValidationError, match="licensing boundary"): validate_document(licensing, PACKAGE)
    copied = tmp_path / "3d_pov"; shutil.copytree(RESOURCE_ROOT, copied); copied_package = copied / "de_anubis" / "render_ready.json"
    profile_path = copied / "de_anubis" / "render_profile.json"; profile = json.loads(profile_path.read_text(encoding="utf-8")); profile["floors"]["classification"] = "VERIFIED"; profile_path.write_text(json.dumps(profile), encoding="utf-8")
    with pytest.raises(RenderReadyValidationError, match="floor policy"): validate_document(json.loads(copied_package.read_text(encoding="utf-8")), copied_package)
