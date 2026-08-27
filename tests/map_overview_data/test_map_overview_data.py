from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from tools.map_overview_data.validate import (
    OverviewValidationError,
    load_and_validate,
    transform_world,
    validate_document,
)

ROOT = Path(__file__).resolve().parents[2]
PILOT = ROOT / "resources" / "map_overviews" / "maps" / "de_ancient.json"


def pilot() -> dict:
    return deepcopy(load_and_validate(PILOT))


def test_pilot_schema_and_required_fields_are_valid() -> None:
    document = pilot()
    assert document["schema"] == "iy.map_overview_metadata/v1"
    assert document["map_id"] == "de_ancient"
    assert document["asset"]["status"] == "NOT_INCLUDED"
    assert document["asset"]["reference"] is None


def test_missing_required_field_fails_closed() -> None:
    document = pilot()
    del document["transform"]
    with pytest.raises(OverviewValidationError, match="missing required fields"):
        validate_document(document)


def test_unknown_top_level_field_fails_closed() -> None:
    document = pilot()
    document["untrusted_extra"] = {"status": "VERIFIED"}
    with pytest.raises(OverviewValidationError, match="unknown top-level fields: untrusted_extra"):
        validate_document(document)


@pytest.mark.parametrize("scale", [0, -1, float("inf"), "5"])
def test_invalid_scale_is_rejected(scale) -> None:
    document = pilot()
    document["transform"]["world_units_per_pixel"] = scale
    with pytest.raises(OverviewValidationError):
        validate_document(document)


@pytest.mark.parametrize("width,height", [(0, 1024), (-1, 1024), (1024, 0), (1.5, 1024), (1024, "1024")])
def test_invalid_dimensions_are_rejected(width, height) -> None:
    document = pilot()
    document["canvas"]["width"] = width
    document["canvas"]["height"] = height
    with pytest.raises(OverviewValidationError):
        validate_document(document)


@pytest.mark.parametrize(
    "field,value",
    [
        ("world_x_to_canvas", "negative_x"),
        ("world_y_to_canvas", "positive_y"),
        ("rotation_deg_clockwise", 90),
        ("rotation_deg_clockwise", "0"),
    ],
)
def test_malformed_rotation_or_orientation_is_rejected(field, value) -> None:
    document = pilot()
    document["transform"][field] = value
    with pytest.raises(OverviewValidationError):
        validate_document(document)


def test_verified_transform_examples_are_deterministic() -> None:
    document = pilot()
    assert transform_world(document, -2953, 2164) == {"x": 0.0, "y": 0.0, "in_bounds": True}
    assert transform_world(document, -393, -396) == {"x": 512.0, "y": 512.0, "in_bounds": True}
    assert transform_world(document, 2167, -2956) == {"x": 1024.0, "y": 1024.0, "in_bounds": True}


def test_out_of_bounds_values_are_not_clamped() -> None:
    result = transform_world(pilot(), -2958, 2164)
    assert result == {"x": -1.0, "y": 0.0, "in_bounds": False}


def test_reference_point_mismatch_is_rejected() -> None:
    document = pilot()
    document["reference_points"][1]["expected_overview"]["x"] = 511
    with pytest.raises(OverviewValidationError, match="does not match"):
        validate_document(document)


def test_unverified_values_cannot_silently_become_trusted() -> None:
    document = pilot()
    document["transform"].update({
        "verification_status": "UNVERIFIED",
        "origin_world": {"x": None, "y": None, "convention": "upper_left_world_coordinate"},
        "world_units_per_pixel": None,
        "world_x_to_canvas": "UNRESOLVED",
        "world_y_to_canvas": "UNRESOLVED",
        "rotation_deg_clockwise": None,
    })
    document["reference_points"] = []
    validate_document(document)
    with pytest.raises(OverviewValidationError, match="not verified"):
        transform_world(document, 0, 0)


def test_unverified_status_rejects_leftover_numeric_claims() -> None:
    document = pilot()
    document["transform"]["verification_status"] = "UNVERIFIED"
    with pytest.raises(OverviewValidationError, match="must remain null"):
        validate_document(document)
