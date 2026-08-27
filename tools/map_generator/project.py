"""Adapter over the canonical iy.map_overview_metadata/v1 transform."""
from __future__ import annotations

import json
from pathlib import Path


def load_projection(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    transform, canvas = document.get("transform", {}), document.get("canvas", {})
    if document.get("schema") != "iy.map_overview_metadata/v1":
        raise ValueError("expected iy.map_overview_metadata/v1")
    if transform.get("verification_status") != "VERIFIED" or transform.get("rotation_deg_clockwise") != 0:
        raise ValueError("expected the existing verified zero-rotation projection")
    if not all(isinstance(canvas.get(key), int) and canvas[key] > 0 for key in ("width", "height")):
        raise ValueError("projection canvas is invalid")
    return document


def project(document: dict, x: float, y: float) -> tuple[float, float]:
    transform, origin = document["transform"], document["transform"]["origin_world"]
    return ((x - origin["x"]) / transform["world_units_per_pixel"], (origin["y"] - y) / transform["world_units_per_pixel"])
