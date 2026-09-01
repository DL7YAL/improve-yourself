"""Fail-closed resolver for self-owned 2D Base Overlay presentation assets."""
from __future__ import annotations

import base64
import hashlib
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

MAP_SURFACE_SCHEMA = "iy.map_surface/v1"
_MANIFEST_FIELDS = {"schema", "surfaces"}
_SURFACE_FIELDS = {
    "map_id", "asset_path", "sha256", "image", "asset_role",
    "source_classification", "distribution_status", "provenance",
    "presentation_only",
}


class MapSurfaceValidationError(ValueError):
    """Raised when an owned map-surface declaration is unsafe or ambiguous."""


@dataclass(frozen=True)
class MapSurfaceResolution:
    state: str
    label: str
    reason: str
    map_id: str | None
    data_uri: str = ""
    transform: dict[str, Any] | None = None
    canvas: dict[str, Any] | None = None


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _surface_root(repository_root: Path) -> Path:
    return repository_root / "resources" / "map_surfaces"


def _overview_path(repository_root: Path, map_id: str) -> Path:
    return repository_root / "resources" / "map_overviews" / "maps" / f"{map_id}.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise MapSurfaceValidationError("surface image must be a PNG with an IHDR header")
    width, height = struct.unpack(">II", data[16:24])
    if width <= 0 or height <= 0:
        raise MapSurfaceValidationError("surface image dimensions must be positive")
    return width, height


def _safe_asset_path(value: Any, map_id: str) -> PurePosixPath:
    if not isinstance(value, str):
        raise MapSurfaceValidationError("asset_path must be a string")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.parts != (map_id, "base_overlay.png"):
        raise MapSurfaceValidationError("asset_path must be the map-specific base_overlay.png path")
    return path


def _surface_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MapSurfaceValidationError(f"surface manifest is unreadable: {error}") from error
    if not isinstance(document, dict):
        raise MapSurfaceValidationError("surface manifest must be an object")
    if set(document) != _MANIFEST_FIELDS or document.get("schema") != MAP_SURFACE_SCHEMA:
        raise MapSurfaceValidationError("surface manifest contract differs")
    if not isinstance(document.get("surfaces"), list):
        raise MapSurfaceValidationError("surfaces must be a list")
    return document


def _verified_overview_for_surface(path: Path, map_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read only the existing verified overview fields needed to place a surface.

    This deliberately has no alternate transform formula or map catalog.  The
    static `iy.map_overview_metadata/v1` validator remains responsible for the
    full descriptor contract and reference-anchor validation.
    """
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MapSurfaceValidationError(f"the overview metadata is unreadable: {error}") from error
    if not isinstance(document, dict) or document.get("schema") != "iy.map_overview_metadata/v1" or document.get("map_id") != map_id:
        raise MapSurfaceValidationError("the overview metadata does not match the replay map_id")
    canvas = document.get("canvas")
    transform = document.get("transform")
    if not isinstance(canvas, dict) or not isinstance(transform, dict):
        raise MapSurfaceValidationError("the overview metadata lacks canvas or transform data")
    if (
        transform.get("verification_status") != "VERIFIED"
        or transform.get("world_x_to_canvas") != "positive_x"
        or transform.get("world_y_to_canvas") != "negative_y"
        or transform.get("rotation_deg_clockwise") != 0
    ):
        raise MapSurfaceValidationError("the overview metadata does not provide a supported verified transform")
    origin = transform.get("origin_world")
    scale = transform.get("world_units_per_pixel")
    if not isinstance(origin, dict) or any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
        for value in (origin.get("x"), origin.get("y"), scale)
    ) or scale <= 0:
        raise MapSurfaceValidationError("the overview metadata transform is not finite and positive")
    if (
        canvas.get("unit") != "overview_pixel" or canvas.get("origin") != "top_left"
        or canvas.get("x_direction") != "right" or canvas.get("y_direction") != "down"
        or any(isinstance(canvas.get(key), bool) or not isinstance(canvas.get(key), int) or canvas[key] <= 0 for key in ("width", "height"))
    ):
        raise MapSurfaceValidationError("the overview metadata canvas contract differs")
    return transform, canvas


def _validated_surfaces(path: Path) -> dict[str, dict[str, Any]]:
    surfaces: dict[str, dict[str, Any]] = {}
    for item in _surface_document(path)["surfaces"]:
        if not isinstance(item, dict) or set(item) != _SURFACE_FIELDS:
            raise MapSurfaceValidationError("surface entry contract differs")
        map_id = item.get("map_id")
        if not isinstance(map_id, str) or not map_id.startswith("de_") or not map_id.replace("_", "").isalnum():
            raise MapSurfaceValidationError("surface map_id must be a canonical de_* identifier")
        if map_id in surfaces:
            raise MapSurfaceValidationError(f"duplicate surface map_id: {map_id}")
        _safe_asset_path(item.get("asset_path"), map_id)
        image = item.get("image")
        if not isinstance(image, dict) or set(image) != {"format", "width", "height"}:
            raise MapSurfaceValidationError("surface image contract differs")
        if image.get("format") != "png" or any(
            isinstance(image.get(key), bool) or not isinstance(image.get(key), int) or image[key] <= 0
            for key in ("width", "height")
        ):
            raise MapSurfaceValidationError("surface image must declare positive PNG dimensions")
        if not isinstance(item.get("sha256"), str) or len(item["sha256"]) != 64 or any(c not in "0123456789ABCDEF" for c in item["sha256"]):
            raise MapSurfaceValidationError("surface sha256 must be an uppercase SHA-256")
        if item.get("asset_role") != "base_overlay" or item.get("source_classification") != "OWN_IMPROVE_CANVA":
            raise MapSurfaceValidationError("surface must be an owned Improve Canva base overlay")
        if item.get("distribution_status") != "APPROVED_PRODUCT_ASSET" or item.get("presentation_only") is not True:
            raise MapSurfaceValidationError("surface distribution/presentation contract differs")
        if not isinstance(item.get("provenance"), str) or not item["provenance"].strip():
            raise MapSurfaceValidationError("surface provenance must be explicit")
        surfaces[map_id] = item
    return surfaces


def map_surface_status_presentation(map_id: Any, *, repository_root: Path | None = None) -> MapSurfaceResolution:
    """Resolve only a matching verified overview plus self-owned surface asset."""
    if not isinstance(map_id, str) or not map_id:
        return MapSurfaceResolution("UNKNOWN", "2D-Kartenfläche unbekannt", "Die kanonische Replay-Map-ID fehlt oder ist ungültig.", None)
    root = repository_root or _repository_root()
    overview_path = _overview_path(root, map_id)
    if not overview_path.is_file():
        return MapSurfaceResolution("INVALID", "2D-Kartenfläche ungültig", "Für diese Map-ID liegt keine kompatible geprüfte Kartenmetadaten-Datei vor.", map_id)
    try:
        transform, canvas = _verified_overview_for_surface(overview_path, map_id)
    except MapSurfaceValidationError as error:
        return MapSurfaceResolution("INVALID", "2D-Kartenfläche ungültig", str(error), map_id)
    manifest_path = _surface_root(root) / "owned_base_overlays.v1.json"
    if not manifest_path.is_file():
        return MapSurfaceResolution("MISSING", "2D-Kartenfläche fehlt", "Für diese Map ist keine zugelassene eigene Base-Overlay-Fläche registriert.", map_id)
    try:
        surface = _validated_surfaces(manifest_path).get(map_id)
        if surface is None:
            return MapSurfaceResolution("MISSING", "2D-Kartenfläche fehlt", "Für diese Map ist keine zugelassene eigene Base-Overlay-Fläche registriert.", map_id)
        asset_path = _surface_root(root) / _safe_asset_path(surface["asset_path"], map_id)
        if not asset_path.is_file():
            return MapSurfaceResolution("MISSING", "2D-Kartenfläche fehlt", "Die registrierte eigene Base-Overlay-Datei fehlt.", map_id)
        dimensions = _png_dimensions(asset_path)
        image = surface["image"]
        if dimensions != (image["width"], image["height"]):
            raise MapSurfaceValidationError("surface image dimensions differ from the manifest")
        if _sha256(asset_path) != surface["sha256"]:
            raise MapSurfaceValidationError("surface image SHA-256 differs from the manifest")
    except MapSurfaceValidationError as error:
        return MapSurfaceResolution("INVALID", "2D-Kartenfläche ungültig", str(error), map_id)
    data_uri = "data:image/png;base64," + base64.b64encode(asset_path.read_bytes()).decode("ascii")
    return MapSurfaceResolution(
        "AVAILABLE", "2D-Kartenfläche verfügbar",
        "Eigene Improve-Base-Overlay-Fläche ist map-spezifisch geprüft geladen.",
        map_id, data_uri, transform, canvas,
    )
