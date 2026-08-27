"""Fail-closed validator for iy.3d_pov_prep/v1 preparation metadata."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "iy.3d_pov_prep/v1"
SUPPORTED_MAPS = {"de_anubis", "de_mirage"}
_REQUIRED = {"schema", "map_id", "purpose", "canonical_runtime", "geometry_inventory", "coordinate_contract", "camera_input_contract", "reference_anchors", "provenance", "redistribution", "verification"}


class PovPrepValidationError(ValueError):
    """Raised when preparation metadata could make an unsupported claim."""


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PovPrepValidationError(f"{field} must be an object")
    return value


def _finite(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise PovPrepValidationError(f"{field} must be a finite number")
    return float(value)


def _vec3(value: Any, field: str) -> tuple[float, float, float]:
    obj = _object(value, field)
    if set(obj) != {"x", "y", "z"}:
        raise PovPrepValidationError(f"{field} must contain only x, y and z")
    return (_finite(obj["x"], f"{field}.x"), _finite(obj["y"], f"{field}.y"), _finite(obj["z"], f"{field}.z"))


def _identity_transform(status: str) -> dict[str, Any]:
    return {"status": status, "scale": 1.0, "rotation_deg": [0.0, 0.0, 0.0], "translation": [0.0, 0.0, 0.0], "axis_swap": "none", "axis_inversion": "none"}


def validate_document(document: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise PovPrepValidationError("prep metadata must be an object")
    missing = _REQUIRED - set(document)
    if missing:
        raise PovPrepValidationError(f"missing required fields: {', '.join(sorted(missing))}")
    unexpected = set(document) - _REQUIRED
    if unexpected:
        raise PovPrepValidationError(f"unknown top-level fields: {', '.join(sorted(unexpected))}")
    map_id = document.get("map_id")
    if document.get("schema") != SCHEMA or map_id not in SUPPORTED_MAPS or document.get("purpose") != "data_research_evidence_only":
        raise PovPrepValidationError("prep identity contract is invalid")

    runtime = _object(document.get("canonical_runtime"), "canonical_runtime")
    expected_runtime = {"replay_schema": "iy.replay/v2", "store": "ReplayStore", "playback_authority": "ReplayController", "data_hub": "AnalyzerDataHub", "owns_tick": False, "parses_demo": False, "embeds_replay_frames": False}
    if runtime != expected_runtime:
        raise PovPrepValidationError("canonical runtime boundary differs")
    inventory = _object(document.get("geometry_inventory"), "geometry_inventory")
    if inventory.get("runtime_asset_contract") != "iy.map_asset/v1" or inventory.get("bundled_files") != []:
        raise PovPrepValidationError("geometry inventory must defer to iy.map_asset/v1 and bundle nothing")
    candidates = inventory.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise PovPrepValidationError("geometry candidates are required")
    for candidate in candidates:
        item = _object(candidate, "geometry candidate")
        for descriptor_name in ("source_vpk", "render_mesh", "visibility_mesh", "artifact"):
            descriptor = item.get(descriptor_name)
            if descriptor is not None:
                descriptor = _object(descriptor, f"geometry candidate {descriptor_name}")
                if descriptor.get("repository_path") is not None or descriptor.get("bundled") is True:
                    raise PovPrepValidationError("geometry assets must not be bundled")

    coordinate = _object(document.get("coordinate_contract"), "coordinate_contract")
    if coordinate.get("coordinate_space") != "cs2_world" or coordinate.get("units") != "source_unit" or coordinate.get("physical_unit_conversion") != "UNRESOLVED" or coordinate.get("handedness") != "UNRESOLVED":
        raise PovPrepValidationError("coordinate space contract is invalid")
    if _object(coordinate.get("axes"), "coordinate_contract.axes") != {"x": "engine_horizontal_x", "y": "engine_horizontal_y", "z": "up"}:
        raise PovPrepValidationError("coordinate axes are invalid")
    expected_status = "VERIFIED_LOCAL_REFERENCE" if map_id == "de_anubis" else "EXPECTED_IDENTITY_PENDING_LOCAL_VALIDATION"
    if _object(coordinate.get("transform_to_replay"), "coordinate_contract.transform_to_replay") != _identity_transform(expected_status):
        raise PovPrepValidationError("world-to-replay transform status or identity differs")
    floor = _object(coordinate.get("floor_model"), "coordinate_contract.floor_model")
    if floor.get("status") != "UNRESOLVED" or floor.get("selection_axis") != "UNRESOLVED" or floor.get("ranges") != []:
        raise PovPrepValidationError("floor data must remain unresolved")

    camera = _object(document.get("camera_input_contract"), "camera_input_contract")
    if camera.get("current_tick_source") != "ReplayController.committed_snapshot.resolved_tick" or "ReplayStore" not in str(camera.get("frame_source")) or "ReplayController" not in str(camera.get("frame_source")) or camera.get("selected_player_source") != "ReplayController.selected_player_id":
        raise PovPrepValidationError("canonical camera ownership differs")
    if _object(camera.get("eye_height"), "camera_input_contract.eye_height").get("world_units") is not None or _object(camera.get("fov"), "camera_input_contract.fov").get("degrees") is not None:
        raise PovPrepValidationError("camera evidence must not be invented")

    anchors = document.get("reference_anchors")
    if not isinstance(anchors, list):
        raise PovPrepValidationError("reference anchors must be an array")
    if map_id == "de_anubis" and len(anchors) < 3:
        raise PovPrepValidationError("at least three verified Anubis reference anchors are required")
    if map_id == "de_mirage" and anchors:
        raise PovPrepValidationError("Mirage anchors must remain absent until locally evidenced")
    for index, anchor in enumerate(anchors):
        item = _object(anchor, f"reference_anchors[{index}]")
        if _vec3(item.get("world"), f"reference_anchors[{index}].world") != _vec3(item.get("expected_scene"), f"reference_anchors[{index}].expected_scene"):
            raise PovPrepValidationError("identity scene anchor differs from world coordinate")

    redistribution = _object(document.get("redistribution"), "redistribution")
    if redistribution.get("bundled_proprietary_assets") is not False or redistribution.get("policy") != "REFERENCE_METADATA_ONLY":
        raise PovPrepValidationError("redistribution boundary is invalid")
    verification = _object(document.get("verification"), "verification")
    expected_verification = "PARTIAL_LOCAL_REFERENCE" if map_id == "de_anubis" else "PREP_READY_PENDING_LOCAL_VERIFICATION"
    if verification.get("status") != expected_verification or not isinstance(verification.get("unresolved"), list) or not verification["unresolved"]:
        raise PovPrepValidationError("verification status or unresolved evidence is invalid")
    return document


def load_and_validate(path: Path) -> dict[str, Any]:
    return validate_document(json.loads(path.read_text(encoding="utf-8")))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate static 3D/POV preparation metadata")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    try:
        for path in args.paths:
            load_and_validate(path); print(f"PASS {path}")
    except (OSError, json.JSONDecodeError, PovPrepValidationError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
