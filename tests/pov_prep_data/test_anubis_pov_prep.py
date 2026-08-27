from __future__ import annotations

from copy import deepcopy
import inspect
import math
from pathlib import Path

import pytest

from tools.map_overview_data.validate import transform_world
from tools.pov_prep_data.validate import PovPrepValidationError, load_and_validate, validate_document

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "resources" / "3d_pov" / "de_anubis" / "prep.json"
OVERVIEW = ROOT / "resources" / "map_overviews" / "maps" / "de_anubis.json"


def package() -> dict:
    return deepcopy(load_and_validate(PACKAGE))


def test_package_validates_and_defers_to_canonical_runtime() -> None:
    document = package()
    assert document["schema"] == "iy.3d_pov_prep/v1"
    assert document["canonical_runtime"] == {
        "replay_schema": "iy.replay/v2", "store": "ReplayStore",
        "playback_authority": "ReplayController", "data_hub": "AnalyzerDataHub",
        "owns_tick": False, "parses_demo": False, "embeds_replay_frames": False,
    }
    assert document["geometry_inventory"]["runtime_asset_contract"] == "iy.map_asset/v1"


def test_required_and_unknown_top_level_fields_fail_closed() -> None:
    missing = package(); del missing["coordinate_contract"]
    with pytest.raises(PovPrepValidationError, match="missing required fields"):
        validate_document(missing)
    extra = package(); extra["runtime_frame"] = {"tick": 6401}
    with pytest.raises(PovPrepValidationError, match="unknown top-level fields"):
        validate_document(extra)


@pytest.mark.parametrize("mutation", [
    lambda value: value["coordinate_contract"]["transform_to_replay"].__setitem__("scale", 0),
    lambda value: value["coordinate_contract"]["transform_to_replay"].__setitem__("rotation_deg", [0, 90, 0]),
    lambda value: value["coordinate_contract"]["transform_to_replay"].__setitem__("axis_inversion", "z"),
    lambda value: value["coordinate_contract"].__setitem__("handedness", "left_handed"),
])
def test_invalid_or_unverified_coordinate_metadata_is_rejected(mutation) -> None:
    document = package(); mutation(document)
    with pytest.raises(PovPrepValidationError):
        validate_document(document)


def test_unknown_values_remain_unknown() -> None:
    document = package()
    assert document["coordinate_contract"]["physical_unit_conversion"] == "UNRESOLVED"
    assert document["coordinate_contract"]["handedness"] == "UNRESOLVED"
    assert document["coordinate_contract"]["floor_model"]["status"] == "UNRESOLVED"
    assert document["camera_input_contract"]["eye_height"]["world_units"] is None
    assert document["camera_input_contract"]["fov"]["degrees"] is None


def test_reference_anchors_preserve_identity_and_match_2d_overview() -> None:
    document = package()
    overview = __import__("json").loads(OVERVIEW.read_text(encoding="utf-8"))
    for anchor in document["reference_anchors"]:
        assert anchor["world"] == anchor["expected_scene"]
        result = transform_world(overview, anchor["world"]["x"], anchor["world"]["y"])
        assert math.isclose(result["x"], anchor["expected_overview"]["x"], abs_tol=1e-9)
        assert math.isclose(result["y"], anchor["expected_overview"]["y"], abs_tol=1e-9)


def test_no_asset_is_bundled_or_referenced_by_repository_path() -> None:
    document = package()
    assert document["geometry_inventory"]["bundled_files"] == []
    for candidate in document["geometry_inventory"]["candidates"]:
        for name in ("source_vpk", "render_mesh", "visibility_mesh", "artifact"):
            descriptor = candidate.get(name)
            if isinstance(descriptor, dict):
                assert descriptor.get("repository_path") is None
                assert descriptor.get("bundled", False) is False
    forbidden = {".vpk", ".glb", ".gltf", ".tri", ".vmdl", ".vmdl_c", ".vphys", ".vphys_c", ".png", ".dds", ".vtf"}
    assert not any(path.suffix.lower() in forbidden for path in (ROOT / "resources" / "3d_pov").rglob("*"))


def test_tick_and_entity_state_are_not_duplicated() -> None:
    document = package()
    assert document["canonical_runtime"]["owns_tick"] is False
    assert document["canonical_runtime"]["embeds_replay_frames"] is False
    assert "ReplayController" in document["camera_input_contract"]["current_tick_source"]
    assert "ReplayStore" in document["camera_input_contract"]["frame_source"]


def test_validator_has_no_network_execution_or_product_runtime_imports() -> None:
    source = inspect.getsource(__import__("tools.pov_prep_data.validate", fromlist=["validate_document"]))
    for forbidden in ("urllib", "requests", "socket", "subprocess", "azure", "ReplayStore", "ReplayController", "AnalyzerDataHub"):
        assert f"import {forbidden}" not in source and f"from {forbidden}" not in source
