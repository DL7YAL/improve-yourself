"""Input validation and conservative collision-surface classification."""
from __future__ import annotations

import math
import struct
from pathlib import Path
from typing import Iterator


def iter_triangles(path: Path) -> Iterator[tuple[tuple[float, float, float], ...]]:
    if path.stat().st_size == 0 or path.stat().st_size % 36:
        raise ValueError("collision triangle soup must contain complete float32 triangles")
    with path.open("rb") as stream:
        while data := stream.read(36):
            values = struct.unpack("<9f", data)
            yield tuple((values[index], values[index + 1], values[index + 2]) for index in range(0, 9, 3))


def is_horizontal_surface_candidate(triangle: tuple[tuple[float, float, float], ...]) -> bool:
    first, second, third = triangle
    ux, uy, uz = (second[index] - first[index] for index in range(3))
    vx, vy, vz = (third[index] - first[index] for index in range(3))
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    magnitude = math.sqrt(nx * nx + ny * ny + nz * nz)
    return magnitude != 0 and abs(nz) / magnitude >= 0.85
