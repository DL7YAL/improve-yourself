"""Pure data model for the local Improve map-generator prototype."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeometryGrid:
    map_id: str
    width: int
    height: int
    grid_size: int
    cells: frozenset[tuple[int, int]]
    triangle_count: int
    horizontal_triangle_count: int
    in_bounds_triangle_count: int
