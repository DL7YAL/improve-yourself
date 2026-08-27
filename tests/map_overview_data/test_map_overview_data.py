from __future__ import annotations

from copy import deepcopy
import math
from pathlib import Path

import pytest

from tools.map_overview_data.validate import (
    OverviewValidationError,
    load_and_validate,
    transform_world,
    validate_document,
)

ROOT = Path(__file__).resolve().parents[2]
MAPS = ROOT / "resources" / "map_overviews" / "maps"
PILOT = MAPS / "de_ancient.json"
SUPPORTED_MAPS = {"de_ancient", "de_mirage", "de_anubis", "de_dust2", "de_inferno", "de_nuke", "de_overpass", "de_train", "de_vertigo"}


def pilot() -> dict:
    return deepcopy(load_and_validate(PILOT))


def map_document(map_id: str) -> dict:
    return deepcopy(load_and_validate(MAPS / f"{map_id}.json"))


def test_supported_map_packages_match_current_repository_scope() -> None:
    assert {path.stem for path in MAPS.glob("*.json")} == SUPPORTED_MAPS


@pytest.mark.parametrize("map_id", sorted(SUPPORTED_MAPS))
def test_every_supported_map_package_validates_and_preserves_identity(map_id: str) -> None:
    document = map_document(map_id)
    assert document["schema"] == "iy.map_overview_metadata/v1"
    assert document["map_id"] == map_id
    assert document["asset"]["status"] == "NOT_INCLUDED"
    assert document["asset"]["reference"] is None
    assert document["provenance"]["sources"]


def test_pilot_schema_and_required_fields_are_valid() -> None:
    document = pilot()
    assert document["schema"] == "iy.map_overview_metadata/v1"
    assert document["map_id"] == "de_ancient"
    assert document["asset"]["status"] == "NOT_INCLUDED"
    assert document["asset"]["reference"] is None


def test_missing_required_field_fails_closed() -> None:
    document = pilot(); del document["transform"]
    with pytest.raises(OverviewValidationError, match="missing required fields"):
        validate_document(document)


def test_unknown_top_level_field_fails_closed() -> None:
    document = pilot(); document["untrusted_extra"] = {"status": "VERIFIED"}
    with pytest.raises(OverviewValidationError, match="unknown top-level fields: untrusted_extra"):
        validate_document(document)


@pytest.mark.parametrize("scale", [0, -1, float("inf"), "5"])
def test_invalid_scale_is_rejected(scale) -> None:
    document = pilot(); document["transform"]["world_units_per_pixel"] = scale
    with pytest.raises(OverviewValidationError): validate_document(document)


@pytest.mark.parametrize("width,height", [(0, 1024), (-1, 1024), (1024, 0), (1.5, 1024), (1024, "1024")])
def test_invalid_dimensions_are_rejected(width, height) -> None:
    document = pilot(); document["canvas"]["width"] = width; document["canvas"]["height"] = height
    with pytest.raises(OverviewValidationError): validate_document(document)


@pytest.mark.parametrize("field,value", [("world_x_to_canvas", "negative_x"), ("world_y_to_canvas", "positive_y"), ("rotation_deg_clockwise", 90), ("rotation_deg_clockwise", "0")])
def test_malformed_rotation_or_orientation_is_rejected(field, value) -> None:
    document = pilot(); document["transform"][field] = value
    with pytest.raises(OverviewValidationError): validate_document(document)


@pytest.mark.parametrize("map_id,world_x,world_y,expected_x,expected_y", [
    ("de_ancient", -2953, 2164, 0.0, 0.0), ("de_ancient", -393, -396, 512.0, 512.0), ("de_ancient", 2167, -2956, 1024.0, 1024.0),
    ("de_mirage", -3230, 1713, 0.0, 0.0), ("de_mirage", -670, -847, 512.0, 512.0), ("de_mirage", 1890, -3407, 1024.0, 1024.0),
    ("de_anubis", -2796, 3328, 0.0, 0.0), ("de_anubis", -123.36, 655.36, 512.0, 512.0), ("de_anubis", 2549.28, -2017.28, 1024.0, 1024.0),
    ("de_dust2", -2476, 3239, 0.0, 0.0), ("de_dust2", -223.2, 986.2, 512.0, 512.0), ("de_dust2", 2029.6, -1266.6, 1024.0, 1024.0),
    ("de_inferno", -2087, 3870, 0.0, 0.0), ("de_inferno", 421.8, 1361.2, 512.0, 512.0),
    ("de_nuke", -3453, 2887, 0.0, 0.0), ("de_nuke", 131, -697, 512.0, 512.0),
    ("de_overpass", -4831, 1781, 0.0, 0.0), ("de_overpass", -2168.6, -881.4, 512.0, 512.0),
    ("de_train", -2308, 2078, 0.0, 0.0), ("de_train", -217.976576, -12.023424, 512.0, 512.0),
    ("de_vertigo", -3168, 1762, 0.0, 0.0), ("de_vertigo", -1120, -286, 512.0, 512.0),
])
def test_verified_map_transform_examples_are_deterministic(map_id: str, world_x: float, world_y: float, expected_x: float, expected_y: float) -> None:
    result = transform_world(map_document(map_id), world_x, world_y)
    assert result["in_bounds"] is True
    assert math.isclose(result["x"], expected_x, abs_tol=1e-9)
    assert math.isclose(result["y"], expected_y, abs_tol=1e-9)


def test_vertical_overview_metadata_is_2d_authority_only() -> None:
    expected = {
        "de_nuke": ((-495, 10000), (-10000, -495)),
        "de_train": ((-50, 20000), (-5000, -50)),
        "de_vertigo": ((11700, 20000), (-10000, 11700)),
    }
    for map_id, ranges in expected.items():
        document = map_document(map_id)
        assert document["layers"]["status"] == "VERIFIED"
        assert tuple((item["altitude_min"], item["altitude_max"]) for item in document["layers"]["items"]) == ranges
        assert "not 3D geometry/floor proof" in document["layers"]["reason"]


def test_dust2_source_presentation_rotate_flag_does_not_pre_rotate_intrinsic_coordinates() -> None:
    document = map_document("de_dust2")
    provenance = document["provenance"]["sources"][0]["values_used"]
    assert provenance["source_rotate_flag"] == 1
    assert provenance["intrinsic_rotation_deg_clockwise"] == 0
    assert transform_world(document, -2476, 3239) == {"x": 0.0, "y": 0.0, "in_bounds": True}


def test_out_of_bounds_values_are_not_clamped() -> None:
    assert transform_world(pilot(), -2958, 2164) == {"x": -1.0, "y": 0.0, "in_bounds": False}


def test_reference_point_mismatch_is_rejected() -> None:
    document = pilot(); document["reference_points"][1]["expected_overview"]["x"] = 511
    with pytest.raises(OverviewValidationError, match="does not match"): validate_document(document)


def test_unverified_values_cannot_silently_become_trusted() -> None:
    document = pilot()
    document["transform"].update({"verification_status": "UNVERIFIED", "origin_world": {"x": None, "y": None, "convention": "upper_left_world_coordinate"}, "world_units_per_pixel": None, "world_x_to_canvas": "UNRESOLVED", "world_y_to_canvas": "UNRESOLVED", "rotation_deg_clockwise": None})
    document["reference_points"] = []
    validate_document(document)
    with pytest.raises(OverviewValidationError, match="not verified"): transform_world(document, 0, 0)


def test_unverified_status_rejects_leftover_numeric_claims() -> None:
    document = pilot(); document["transform"]["verification_status"] = "UNVERIFIED"
    with pytest.raises(OverviewValidationError, match="must remain null"): validate_document(document)
