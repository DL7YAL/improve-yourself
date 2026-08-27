"""Offline validation for isolated 3D POV render-ready preparation packages."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "iy.3d_pov_render_ready/v1"
SUPPORTED_MAPS = {"de_anubis", "de_mirage"}
_REQUIRED = {"schema", "map_id", "purpose", "canonical_runtime", "map_geometry", "assets", "semantic_mapping", "camera_policy", "environment", "collision_visibility", "dynamic_objects", "floor_policy", "fallbacks", "reference_scene", "licensing", "verification"}


class RenderReadyValidationError(ValueError):
    pass


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict): raise RenderReadyValidationError(f"{field} must be an object")
    return value


def _resolve(root: Path, relative: Any, field: str) -> Path:
    if not isinstance(relative, str) or not relative: raise RenderReadyValidationError(f"{field} must be a relative path")
    candidate = (root / relative).resolve(); allowed_root = root.parent.resolve()
    if candidate != allowed_root and allowed_root not in candidate.parents: raise RenderReadyValidationError(f"{field} escapes resources/3d_pov")
    if not candidate.is_file(): raise RenderReadyValidationError(f"{field} file is missing")
    return candidate


def _git_blob_sha1(path: Path) -> str:
    body = path.read_bytes(); return hashlib.sha1(f"blob {len(body)}\0".encode("ascii") + body).hexdigest()


def _validate_original_asset(path: Path, kind: str) -> None:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".obj":
        if len([line for line in text.splitlines() if line.startswith("v ")]) < 8 or not [line for line in text.splitlines() if line.startswith(("f ", "l "))]: raise RenderReadyValidationError(f"{kind} OBJ lacks deterministic geometry")
    elif path.suffix == ".mtl":
        if "newmtl player_ct" not in text or "newmtl player_t" not in text or "newmtl weapon_neutral" not in text: raise RenderReadyValidationError("material library lacks required semantic materials")
    elif path.suffix == ".ppm":
        if not text.startswith("P3\n") or "4 4\n255\n" not in text: raise RenderReadyValidationError("diagnostic texture is not the expected ASCII PPM")
    else: raise RenderReadyValidationError(f"unsupported original asset format: {path.suffix}")


def validate_document(document: dict[str, Any], package_path: Path) -> dict[str, Any]:
    if not isinstance(document, dict): raise RenderReadyValidationError("render-ready metadata must be an object")
    missing = _REQUIRED - set(document)
    if missing: raise RenderReadyValidationError(f"missing required fields: {', '.join(sorted(missing))}")
    unexpected = set(document) - _REQUIRED
    if unexpected: raise RenderReadyValidationError(f"unknown top-level fields: {', '.join(sorted(unexpected))}")
    map_id = document.get("map_id")
    if document.get("schema") != SCHEMA or map_id not in SUPPORTED_MAPS or document.get("purpose") != "renderer_preparation_only": raise RenderReadyValidationError("render-ready identity is invalid")
    expected = {"replay_schema": "iy.replay/v2", "store": "ReplayStore", "playback_authority": "ReplayController", "data_hub": "AnalyzerDataHub", "renderer_interface": "ReplayRenderer", "owns_tick": False, "parses_demo": False, "embeds_replay_frames": False}
    if _object(document.get("canonical_runtime"), "canonical_runtime") != expected: raise RenderReadyValidationError("canonical runtime boundary differs")
    geometry = _object(document.get("map_geometry"), "map_geometry")
    if geometry.get("runtime_contract") != "iy.map_asset/v1" or geometry.get("bundled") is not False or geometry.get("fallback") != "explicit_3d_unavailable": raise RenderReadyValidationError("map geometry boundary is invalid")
    root = package_path.resolve().parent; assets = document.get("assets")
    if not isinstance(assets, list) or len(assets) < 4: raise RenderReadyValidationError("original renderer assets are incomplete")
    ids: set[str] = set()
    for index, item in enumerate(assets):
        item = _object(item, f"assets[{index}]"); asset_id = item.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id or asset_id in ids: raise RenderReadyValidationError("asset IDs must be unique non-empty strings")
        ids.add(asset_id)
        if item.get("license") != "CC0-1.0" or not str(item.get("classification", "")).startswith("FALLBACK"): raise RenderReadyValidationError("bundled assets must be original fallback assets")
        path = _resolve(root, item.get("path"), f"assets[{index}].path")
        if not isinstance(item.get("git_blob_sha1"), str) or len(item["git_blob_sha1"]) != 40 or _git_blob_sha1(path) != item["git_blob_sha1"].lower(): raise RenderReadyValidationError(f"asset integrity differs: {asset_id}")
        _validate_original_asset(path, str(item.get("kind")))
    semantic = json.loads(_resolve(root, document.get("semantic_mapping"), "semantic_mapping").read_text(encoding="utf-8"))
    profile = json.loads(_resolve(root, str(document.get("camera_policy")).split("#", 1)[0], "camera_policy").read_text(encoding="utf-8"))
    scene = json.loads(_resolve(root, document.get("reference_scene"), "reference_scene").read_text(encoding="utf-8"))
    if semantic.get("schema") != "iy.3d_pov_semantic_assets/v1" or semantic.get("license") != "CC0-1.0": raise RenderReadyValidationError("semantic asset mapping is invalid")
    categories = _object(_object(semantic.get("weapon_representations"), "weapon_representations").get("categories"), "weapon categories")
    if "unknown" not in categories or categories["unknown"].get("ids") != []: raise RenderReadyValidationError("weapon mapping requires a non-inventing unknown fallback")
    if profile.get("schema") != "iy.3d_pov_render_profile/v1" or _object(profile.get("floors"), "render_profile.floors").get("classification") != "UNRESOLVED": raise RenderReadyValidationError("render profile is invalid")
    if scene.get("schema") != "iy.3d_pov_reference_scene/v1" or scene.get("classification") != "FALLBACK_RENDER_SAMPLE_NOT_REPLAY_EVIDENCE": raise RenderReadyValidationError("reference scene classification is invalid")
    licensing = _object(document.get("licensing"), "licensing")
    if licensing.get("original_assets") != "CC0-1.0" or licensing.get("valve_assets_bundled") is not False or licensing.get("valve_geometry_required_for_redistributable_package") is not False: raise RenderReadyValidationError("licensing boundary is invalid")
    return document


def load_and_validate(path: Path) -> dict[str, Any]: return validate_document(json.loads(path.read_text(encoding="utf-8")), path)

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate 3D POV render-ready preparation metadata"); parser.add_argument("path", type=Path); args = parser.parse_args()
    try: load_and_validate(args.path); print(f"PASS {args.path}")
    except (OSError, json.JSONDecodeError, RenderReadyValidationError) as error: parser.error(str(error))
    return 0

if __name__ == "__main__": raise SystemExit(main())
