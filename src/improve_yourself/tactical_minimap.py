"""Fail-closed local map surfaces for the canonical Tactical Replay path."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MAP_OVERVIEW_SCHEMA = "iy.map_overview_metadata/v1"
LOCAL_MAP_SURFACES_SCHEMA = "iy.local_test_map_surfaces/v1"
LOCAL_MAP_SURFACES_ENV = "IMPROVE_YOURSELF_LOCAL_MAP_SURFACES_MANIFEST"
LOCAL_SURFACE_REGISTRATION = "FULL_OVERVIEW_CANVAS_UNVERIFIED_LOCAL_TEST"
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_MAX_LOCAL_SURFACE_BYTES = 32 * 1024 * 1024
_MAX_LOCAL_SURFACE_DIMENSION = 8192


@dataclass(frozen=True)
class LocalTestMapSurface:
    path: Path
    sha256: str
    pixel_width: int
    pixel_height: int
    registration: str = LOCAL_SURFACE_REGISTRATION


@dataclass(frozen=True)
class TacticalMinimap:
    map_id: str
    status: str
    detail: str
    width: int | None = None
    height: int | None = None
    origin_x: float | None = None
    origin_y: float | None = None
    world_units_per_pixel: float | None = None
    local_surface: LocalTestMapSurface | None = None

    @property
    def projection_available(self) -> bool:
        return self.status == "VERIFIED_PROJECTION" and None not in (
            self.width, self.height, self.origin_x, self.origin_y,
            self.world_units_per_pixel,
        )

    @property
    def has_local_test_image(self) -> bool:
        return self.local_surface is not None

    def project(self, world_x: float, world_y: float) -> tuple[float, float, bool] | None:
        if not self.projection_available:
            return None
        assert self.width is not None and self.height is not None
        assert self.origin_x is not None and self.origin_y is not None
        assert self.world_units_per_pixel is not None
        x = (world_x - self.origin_x) / self.world_units_per_pixel
        y = (self.origin_y - world_y) / self.world_units_per_pixel
        return x, y, 0 <= x <= self.width and 0 <= y <= self.height


def map_overview_root() -> Path:
    if frozen_root := getattr(sys, "_MEIPASS", None):
        return Path(frozen_root) / "resources" / "map_overviews" / "maps"
    return Path(__file__).resolve().parents[2] / "resources" / "map_overviews" / "maps"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        if path.stat().st_size > _MAX_LOCAL_SURFACE_BYTES:
            return None
        with path.open("rb") as stream:
            header = stream.read(24)
    except OSError:
        return None
    if len(header) != 24 or header[:8] != _PNG_SIGNATURE or header[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", header[16:24])
    if not (0 < width <= _MAX_LOCAL_SURFACE_DIMENSION and 0 < height <= _MAX_LOCAL_SURFACE_DIMENSION):
        return None
    return width, height


def _load_local_test_surface(
    map_id: str,
    manifest_path: Path | None,
) -> tuple[LocalTestMapSurface | None, str | None]:
    configured = manifest_path or (
        Path(value).expanduser() if (value := os.environ.get(LOCAL_MAP_SURFACES_ENV)) else None
    )
    if configured is None:
        return None, None
    try:
        resolved_manifest = configured.resolve()
        document = json.loads(resolved_manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None, "Manifest nicht lesbar"
    if (
        not isinstance(document, dict)
        or document.get("schema") != LOCAL_MAP_SURFACES_SCHEMA
        or document.get("distribution") != "LOCAL_ONLY"
    ):
        return None, "Manifestvertrag oder Verteilungsgrenze ungültig"
    surfaces = document.get("surfaces")
    item = surfaces.get(map_id) if isinstance(surfaces, dict) else None
    if not isinstance(item, dict):
        return None, "keine lokale Oberfläche für diese Map"
    relative = item.get("path")
    expected_hash = item.get("sha256")
    registration = item.get("registration")
    if (
        not isinstance(relative, str)
        or not relative
        or not isinstance(expected_hash, str)
        or re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash) is None
        or registration != LOCAL_SURFACE_REGISTRATION
    ):
        return None, "lokaler Oberflächeneintrag unvollständig"
    relative_path = Path(relative)
    if relative_path.is_absolute():
        return None, "absolute Bildpfade sind nicht erlaubt"
    root = resolved_manifest.parent.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None, "Bildpfad verlässt den lokalen Manifestordner"
    if candidate.suffix.lower() != ".png" or not candidate.is_file():
        return None, "lokale PNG-Oberfläche fehlt"
    dimensions = _png_dimensions(candidate)
    if dimensions is None:
        return None, "lokale PNG-Oberfläche ist ungültig oder zu groß"
    if _sha256(candidate).lower() != expected_hash.lower():
        return None, "lokale PNG-Oberfläche stimmt nicht mit SHA-256 überein"
    return LocalTestMapSurface(
        path=candidate,
        sha256=expected_hash.lower(),
        pixel_width=dimensions[0],
        pixel_height=dimensions[1],
    ), None


def load_tactical_minimap(
    map_id: str,
    *,
    maps_root: Path | None = None,
    local_manifest_path: Path | None = None,
) -> TacticalMinimap:
    """Load verified projection metadata and one optional local-only surface."""
    if not isinstance(map_id, str) or re.fullmatch(r"de_[a-z0-9_]+", map_id) is None:
        return TacticalMinimap(str(map_id), "UNAVAILABLE", "Map-ID ist nicht kanonisch belegt.")
    path = (maps_root or map_overview_root()) / f"{map_id}.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return TacticalMinimap(map_id, "UNAVAILABLE", "Keine verifizierte Map-Overview-Metadatei vorhanden.")
    if document.get("schema") != MAP_OVERVIEW_SCHEMA or document.get("map_id") != map_id:
        return TacticalMinimap(map_id, "UNAVAILABLE", "Map-Overview-Vertrag stimmt nicht mit der Demo-Map überein.")
    asset = document.get("asset")
    canvas = document.get("canvas")
    transform = document.get("transform")
    if not isinstance(asset, dict) or not isinstance(canvas, dict) or not isinstance(transform, dict):
        return TacticalMinimap(map_id, "UNAVAILABLE", "Map-Overview enthält keine vollständige Darstellungsbasis.")
    if asset.get("status") != "NOT_INCLUDED":
        return TacticalMinimap(map_id, "UNAVAILABLE", "Kartenbildstatus ist für diese lokale Ausgabe nicht freigegeben.")
    origin = transform.get("origin_world")
    values: tuple[Any, ...] = (
        canvas.get("width"), canvas.get("height"),
        origin.get("x") if isinstance(origin, dict) else None,
        origin.get("y") if isinstance(origin, dict) else None,
        transform.get("world_units_per_pixel"),
    )
    if (
        transform.get("verification_status") != "VERIFIED"
        or transform.get("world_x_to_canvas") != "positive_x"
        or transform.get("world_y_to_canvas") != "negative_y"
        or transform.get("rotation_deg_clockwise") != 0
        or not isinstance(values[0], int)
        or isinstance(values[0], bool)
        or not isinstance(values[1], int)
        or isinstance(values[1], bool)
        or not all(
            isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
            for value in values
        )
        or values[0] <= 0
        or values[1] <= 0
        or values[4] <= 0
    ):
        return TacticalMinimap(map_id, "UNAVAILABLE", "Kartenprojektion ist nicht verifiziert.")
    local_surface, local_error = _load_local_test_surface(map_id, local_manifest_path)
    if local_surface is not None:
        detail = "Verifizierte Projektion; lokale interne Testoberfläche aktiv (Ausrichtung noch nicht produktverifiziert)."
    elif local_error is not None:
        detail = f"Verifizierte Projektion; lokale Testoberfläche abgelehnt ({local_error})."
    else:
        detail = "Verifizierte Projektionsbasis; Kartenbild wird nicht mitgeliefert."
    return TacticalMinimap(
        map_id=map_id,
        status="VERIFIED_PROJECTION",
        detail=detail,
        width=int(values[0]),
        height=int(values[1]),
        origin_x=float(values[2]),
        origin_y=float(values[3]),
        world_units_per_pixel=float(values[4]),
        local_surface=local_surface,
    )
