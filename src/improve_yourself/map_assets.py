from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

MAP_ASSET_SCHEMA = "iy.map_asset/v1"
MapAvailability = Literal[
    "available", "missing", "version_mismatch", "integrity_failed", "distribution_blocked", "unsupported_map"
]


@dataclass(frozen=True)
class MapAssetAssessment:
    availability: MapAvailability
    reason: str
    manifest: dict[str, Any] | None = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _asset_path(root: Path, relative: Any) -> Path | None:
    if not isinstance(relative, str) or not relative:
        return None
    path = (root / relative).resolve()
    return path if root == path.parent or root in path.parents else None


def assess_map_asset(manifest_path: Path, replay_map_id: str) -> MapAssetAssessment:
    """Assess a bundle without weakening any V1 asset acceptance gate."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        return MapAssetAssessment("missing", f"manifest unavailable: {error}")
    if manifest.get("schema") != MAP_ASSET_SCHEMA:
        return MapAssetAssessment("integrity_failed", f"expected schema {MAP_ASSET_SCHEMA}", manifest)
    if manifest.get("map_id") != replay_map_id:
        return MapAssetAssessment("unsupported_map", "asset map_id differs from replay map", manifest)
    if manifest.get("distribution") not in ("local_only", "approved_derivative"):
        return MapAssetAssessment("distribution_blocked", "asset distribution is not approved for this run", manifest)
    validation = manifest.get("validation")
    if not isinstance(validation, dict) or validation.get("status") != "verified":
        status = validation.get("status") if isinstance(validation, dict) else "missing"
        return MapAssetAssessment("version_mismatch", f"asset validation status is {status}", manifest)
    transform = manifest.get("transform_to_replay")
    if not isinstance(transform, dict) or set(transform) != {"scale", "rotation_deg", "translation"}:
        return MapAssetAssessment("integrity_failed", "coordinate transform is incomplete", manifest)
    root = manifest_path.resolve().parent
    for field in ("render_mesh", "visibility_mesh"):
        item = manifest.get(field)
        if not isinstance(item, dict):
            return MapAssetAssessment("integrity_failed", f"{field} descriptor is missing", manifest)
        path = _asset_path(root, item.get("path"))
        if path is None:
            return MapAssetAssessment("integrity_failed", f"{field} path is invalid", manifest)
        if not path.is_file():
            return MapAssetAssessment("missing", f"{field} file is missing", manifest)
        expected = item.get("sha256")
        if not isinstance(expected, str) or _sha256(path).lower() != expected.lower():
            return MapAssetAssessment("integrity_failed", f"{field} hash differs", manifest)
    return MapAssetAssessment("available", "asset bundle passed all machine-checkable gates", manifest)
