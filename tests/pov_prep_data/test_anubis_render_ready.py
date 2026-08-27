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
SCENE = RESOURCE_ROOT / "de_anubis" / "reference_scene.json"


def package() -> dict:
    return deepcopy(load_and_validate(PACKAGE))


def test_render_ready_package_validates_and_owns_no_runtime_state() -> None:
    document = package()
    assert document["canonical_runtime"]["owns_tick"] is False
    assert document["canonical_runtime"]["parses_demo"] is False
    assert document["canonical_runtime"]["embeds_replay_frames"] is False
    assert document["map_geometry"]["runtime_contract"] == "iy.map_asset/v1"
    assert document["map_geometry"]["bundled"] is False


def test_original_assets_are_present_cc0_and_integrity_bound() -> None:
    document = package()
    for asset in document["assets"]:
        assert asset["license"] == "CC0-1.0"
        assert asset["classification"].startswith("FALLBACK")
        assert len(asset["git_blob_sha1"]) == 40
        path = (PACKAGE.parent / asset["path"]).resolve()
        assert path.is_file()
        assert RESOURCE_ROOT in path.parents


def test_original_obj_and_texture_assets_are_structurally_loadable() -> None:
    assets = RESOURCE_ROOT / "original_assets"
    for name in ("player_proxy.obj", "weapon_proxy.obj", "reference_bounds.obj"):
        lines = (assets / name).read_text(encoding="utf-8").splitlines()
        assert len([line for line in lines if line.startswith("v ")]) >= 8
        assert any(line.startswith(("f ", "l ")) for line in lines)
    materials = (assets / "materials.mtl").read_text(encoding="utf-8")
    assert all(name in materials for name in ("newmtl player_ct", "newmtl player_t", "newmtl weapon_neutral"))
    texture = (assets / "neutral_grid.ppm").read_text(encoding="utf-8")
    assert texture.startswith("P3\n") and "4 4\n255\n" in texture


def test_asset_tampering_fails_integrity_without_touching_repository(tmp_path: Path) -> None:
    copied = tmp_path / "3d_pov"
    shutil.copytree(RESOURCE_ROOT, copied)
    copied_package = copied / "de_anubis" / "render_ready.json"
    player = copied / "original_assets" / "player_proxy.obj"
    player.write_text(player.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
    with pytest.raises(RenderReadyValidationError, match="asset integrity differs"):
        load_and_validate(copied_package)


def test_no_proprietary_or_executable_assets_are_bundled() -> None:
    forbidden = {".vpk", ".vmdl", ".vmdl_c", ".vphys", ".vphys_c", ".tri", ".glb", ".dll", ".exe", ".wav", ".mp3", ".ogg"}
    assert not any(path.suffix.lower() in forbidden for path in RESOURCE_ROOT.rglob("*"))
    assert package()["licensing"]["valve_assets_bundled"] is False


def test_camera_reference_math_is_deterministic() -> None:
    scene = json.loads(SCENE.read_text(encoding="utf-8"))
    camera = scene["camera"]
    observer = next(item for item in scene["anchors"] if item["id"] == camera["anchor_id"])["position"]
    eye = [observer[0], observer[1], observer[2] + 64.0]
    assert eye == camera["expected_eye_position"]
    yaw = math.radians(camera["yaw_deg"]["value"])
    pitch = math.radians(camera["pitch_deg"]["value"])
    forward = [math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), -math.sin(pitch)]
    assert forward == camera["expected_forward"]
    target = [eye[index] + forward[index] * 320.0 for index in range(3)]
    assert target == camera["expected_target"]
    assert camera["yaw_deg"]["classification"] == "FALLBACK_TEST_ORIENTATION"


def test_semantic_weapon_mapping_has_unknown_fallback_without_reclassification() -> None:
    semantic = json.loads((PACKAGE.parent / "semantic_assets.json").read_text(encoding="utf-8"))
    categories = semantic["weapon_representations"]["categories"]
    assert "unknown" in categories and categories["unknown"]["ids"] == []
    assert "preserve the canonical weapon semantic string" in semantic["weapon_representations"]["unknown_policy"]
    all_ids = [weapon_id for category in categories.values() for weapon_id in category["ids"]]
    assert len(all_ids) == len(set(all_ids))


def test_environment_camera_sound_and_floor_values_are_explicitly_classified() -> None:
    profile = json.loads((PACKAGE.parent / "render_profile.json").read_text(encoding="utf-8"))
    semantic = json.loads((PACKAGE.parent / "semantic_assets.json").read_text(encoding="utf-8"))
    assert profile["environment"]["classification"] == "FALLBACK"
    assert all(value["classification"] == "FALLBACK" for key, value in profile["camera"].items() if key != "canonical_orientation")
    assert profile["floors"] == {"classification": "UNRESOLVED", "ranges": [], "policy": "Use canonical world Z for placement but do not assign named floors."}
    assert semantic["sound_mapping"]["classification"] == "FALLBACK"
    assert semantic["sound_mapping"]["asset_files"] == []


def test_invalid_runtime_or_fallback_claims_fail_closed(tmp_path: Path) -> None:
    runtime = package(); runtime["canonical_runtime"]["owns_tick"] = True
    with pytest.raises(RenderReadyValidationError, match="runtime boundary"):
        validate_document(runtime, PACKAGE)
    licensing = package(); licensing["licensing"]["valve_assets_bundled"] = True
    with pytest.raises(RenderReadyValidationError, match="licensing boundary"):
        validate_document(licensing, PACKAGE)

    copied = tmp_path / "3d_pov"
    shutil.copytree(RESOURCE_ROOT, copied)
    copied_package = copied / "de_anubis" / "render_ready.json"
    copied_document = json.loads(copied_package.read_text(encoding="utf-8"))
    profile_path = copied / "de_anubis" / "render_profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["floors"]["classification"] = "VERIFIED"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    with pytest.raises(RenderReadyValidationError, match="floor policy"):
        validate_document(copied_document, copied_package)
