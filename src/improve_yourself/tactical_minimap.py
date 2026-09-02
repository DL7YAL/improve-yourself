"""Fail-closed minimap descriptor for the existing Tactical Replay V2 path.

This module owns no replay state and ships no game artwork.  It only turns a
declared ``iy.map_overview_metadata/v1`` document into a renderer-facing map
surface.  A missing or non-redistributable radar image remains an explicit
benchmark blank state instead of becoming guessed map artwork.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MAP_OVERVIEW_SCHEMA = "iy.map_overview_metadata/v1"


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

    @property
    def projection_available(self) -> bool:
        return self.status == "VERIFIED_BLANK" and None not in (
            self.width, self.height, self.origin_x, self.origin_y, self.world_units_per_pixel,
        )

    def project(self, world_x: float, world_y: float) -> tuple[float, float, bool] | None:
        """Project world coordinates only when the declared transform is verified."""
        if not self.projection_available:
            return None
        assert self.width is not None and self.height is not None
        assert self.origin_x is not None and self.origin_y is not None
        assert self.world_units_per_pixel is not None
        x = (world_x - self.origin_x) / self.world_units_per_pixel
        y = (self.origin_y - world_y) / self.world_units_per_pixel
        return x, y, 0 <= x <= self.width and 0 <= y <= self.height


def map_overview_root() -> Path:
    return Path(__file__).resolve().parents[2] / "resources" / "map_overviews" / "maps"


def load_tactical_minimap(map_id: str, *, maps_root: Path | None = None) -> TacticalMinimap:
    """Load only a matching, verified map descriptor; every other case is blank."""
    if not isinstance(map_id, str) or not map_id.startswith("de_"):
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
        or not all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in values)
        or values[0] <= 0 or values[1] <= 0 or values[4] <= 0
    ):
        return TacticalMinimap(map_id, "UNAVAILABLE", "Kartenprojektion ist nicht verifiziert.")
    return TacticalMinimap(
        map_id, "VERIFIED_BLANK",
        "Verifizierte Projektionsbasis; Kartenbild wird nicht mitgeliefert.",
        int(values[0]), int(values[1]), float(values[2]), float(values[3]), float(values[4]),
    )
