"""Deterministic validator for iy.map_overview_metadata/v1.

This module validates static projection metadata only. It has no demo, replay,
tick, Analyzer, network, or cloud dependency.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "iy.map_overview_metadata/v1"
_REQUIRED_TOP_LEVEL = {
    "schema", "map_id", "asset", "canvas", "transform", "layers",
    "reference_points", "provenance", "verification",
}


class OverviewValidationError(ValueError):
    """Raised when map overview metadata is unsafe or incomplete."""


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise OverviewValidationError(f"{field} must be an object")
    return value


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise OverviewValidationError(f"{field} must be a finite number")
    return float(value)


def _positive_dimension(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise OverviewValidationError(f"{field} must be a positive integer")
    return value


def validate_document(document: dict[str, Any]) -> dict[str, Any]:
    """Validate one metadata document and return it unchanged on success."""
    if not isinstance(document, dict):
        raise OverviewValidationError("overview metadata must be an object")
    missing = _REQUIRED_TOP_LEVEL - set(document)
    if missing:
        raise OverviewValidationError(f"missing required fields: {', '.join(sorted(missing))}")
    if document.get("schema") != SCHEMA:
        raise OverviewValidationError(f"schema must be {SCHEMA}")
    map_id = document.get("map_id")
    if not isinstance(map_id, str) or not map_id.startswith("de_") or not map_id.replace("_", "").isalnum():
        raise OverviewValidationError("map_id must be a canonical de_* identifier")

    asset = _object(document.get("asset"), "asset")
    if asset.get("status") not in {"INCLUDED", "NOT_INCLUDED", "UNRESOLVED"}:
        raise OverviewValidationError("asset.status is invalid")
    if asset.get("status") != "INCLUDED" and asset.get("reference") is not None:
        raise OverviewValidationError("an unavailable asset reference must remain null")

    canvas = _object(document.get("canvas"), "canvas")
    width = _positive_dimension(canvas.get("width"), "canvas.width")
    height = _positive_dimension(canvas.get("height"), "canvas.height")
    expected_canvas = {
        "unit": "overview_pixel", "origin": "top_left",
        "x_direction": "right", "y_direction": "down",
    }
    for key, expected in expected_canvas.items():
        if canvas.get(key) != expected:
            raise OverviewValidationError(f"canvas.{key} must be {expected}")

    transform = _object(document.get("transform"), "transform")
    status = transform.get("verification_status")
    if status not in {"VERIFIED", "UNVERIFIED"}:
        raise OverviewValidationError("transform.verification_status is invalid")
    origin = _object(transform.get("origin_world"), "transform.origin_world")
    if origin.get("convention") != "upper_left_world_coordinate":
        raise OverviewValidationError("transform origin convention is invalid")
    if transform.get("input_coordinate_space") != "cs2_world_xy":
        raise OverviewValidationError("transform input coordinate space is invalid")
    if transform.get("rounding") != "none_float":
        raise OverviewValidationError("transform rounding must preserve floats")
    if transform.get("clipping") != "classify_only_no_clamp" or transform.get("bounds_inclusive") is not True:
        raise OverviewValidationError("transform clipping contract is invalid")

    numeric_fields = (origin.get("x"), origin.get("y"), transform.get("world_units_per_pixel"))
    orientation_fields = (transform.get("world_x_to_canvas"), transform.get("world_y_to_canvas"))
    rotation = transform.get("rotation_deg_clockwise")
    if status == "UNVERIFIED":
        if any(value is not None for value in numeric_fields) or rotation is not None:
            raise OverviewValidationError("unverified transform numeric values must remain null")
        if orientation_fields != ("UNRESOLVED", "UNRESOLVED"):
            raise OverviewValidationError("unverified transform orientation must remain unresolved")
    else:
        _finite_number(origin.get("x"), "transform.origin_world.x")
        _finite_number(origin.get("y"), "transform.origin_world.y")
        scale = _finite_number(transform.get("world_units_per_pixel"), "transform.world_units_per_pixel")
        if scale <= 0:
            raise OverviewValidationError("transform.world_units_per_pixel must be positive")
        if orientation_fields != ("positive_x", "negative_y"):
            raise OverviewValidationError("transform axis orientation is invalid")
        if rotation != 0:
            raise OverviewValidationError("V1 accepts only verified zero rotation")

    layers = _object(document.get("layers"), "layers")
    if layers.get("status") not in {"VERIFIED", "UNRESOLVED"} or not isinstance(layers.get("items"), list):
        raise OverviewValidationError("layers contract is invalid")
    if layers.get("status") == "UNRESOLVED" and (layers.get("selection_axis") != "UNRESOLVED" or layers.get("items")):
        raise OverviewValidationError("unresolved layer data must not contain inferred thresholds")

    references = document.get("reference_points")
    if not isinstance(references, list):
        raise OverviewValidationError("reference_points must be a list")
    if status == "UNVERIFIED" and references:
        raise OverviewValidationError("unverified transforms cannot claim reference points")
    for index, reference in enumerate(references):
        item = _object(reference, f"reference_points[{index}]")
        if item.get("verification_status") != "VERIFIED_DERIVED_FROM_TRANSFORM" or item.get("meaning") != "projection_basis_only":
            raise OverviewValidationError(f"reference_points[{index}] verification is invalid")
        world = _object(item.get("world"), f"reference_points[{index}].world")
        expected = _object(item.get("expected_overview"), f"reference_points[{index}].expected_overview")
        result = transform_world(document, world.get("x"), world.get("y"))
        expected_x = _finite_number(expected.get("x"), f"reference_points[{index}].expected_overview.x")
        expected_y = _finite_number(expected.get("y"), f"reference_points[{index}].expected_overview.y")
        if not math.isclose(result["x"], expected_x, abs_tol=1e-9) or not math.isclose(result["y"], expected_y, abs_tol=1e-9):
            raise OverviewValidationError(f"reference_points[{index}] does not match the transform")

    provenance = _object(document.get("provenance"), "provenance")
    if not isinstance(provenance.get("sources"), list) or not provenance["sources"]:
        raise OverviewValidationError("provenance.sources must not be empty")
    verification = _object(document.get("verification"), "verification")
    if verification.get("status") not in {"VERIFIED", "PARTIAL", "UNVERIFIED"}:
        raise OverviewValidationError("verification.status is invalid")
    if not isinstance(verification.get("verified_fields"), list) or not isinstance(verification.get("unresolved_fields"), list):
        raise OverviewValidationError("verification field lists are invalid")

    # Width and height are intentionally read above and retained as validation
    # dependencies even when a document contains no reference points.
    assert width > 0 and height > 0
    return document


def transform_world(document: dict[str, Any], world_x: Any, world_y: Any) -> dict[str, Any]:
    """Transform canonical world X/Y without clamping or gameplay interpretation."""
    transform = _object(document.get("transform"), "transform")
    if transform.get("verification_status") != "VERIFIED":
        raise OverviewValidationError("transform is not verified")
    canvas = _object(document.get("canvas"), "canvas")
    origin = _object(transform.get("origin_world"), "transform.origin_world")
    origin_x = _finite_number(origin.get("x"), "transform.origin_world.x")
    origin_y = _finite_number(origin.get("y"), "transform.origin_world.y")
    scale = _finite_number(transform.get("world_units_per_pixel"), "transform.world_units_per_pixel")
    if scale <= 0 or transform.get("world_x_to_canvas") != "positive_x" or transform.get("world_y_to_canvas") != "negative_y" or transform.get("rotation_deg_clockwise") != 0:
        raise OverviewValidationError("transform is not a supported verified V1 transform")
    x = (_finite_number(world_x, "world_x") - origin_x) / scale
    y = (origin_y - _finite_number(world_y, "world_y")) / scale
    width = _positive_dimension(canvas.get("width"), "canvas.width")
    height = _positive_dimension(canvas.get("height"), "canvas.height")
    return {"x": x, "y": y, "in_bounds": 0 <= x <= width and 0 <= y <= height}


def load_and_validate(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return validate_document(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate static 2D map overview metadata")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    try:
        for path in args.paths:
            load_and_validate(path)
            print(f"PASS {path}")
    except (OSError, json.JSONDecodeError, OverviewValidationError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
