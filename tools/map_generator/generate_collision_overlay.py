"""Generate a local-only, evidence-limited 2D collision-surface SVG overlay.

This tool deliberately does not read radar images or infer map semantics.  It
uses only horizontal-ish triangles from a local Awpy ``.tri`` soup, projects
their centroids through an existing ``iy.map_overview_metadata/v1`` document,
and renders occupied grid cells.  The SVG is a local PoC derivative and must
not be committed as a distributable product asset without a rights review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class OverlayResult:
    triangle_count: int
    horizontal_triangle_count: int
    in_bounds_triangle_count: int
    occupied_cells: int
    canvas_width: int
    canvas_height: int


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def iter_triangles(path: Path) -> Iterator[tuple[tuple[float, float, float], ...]]:
    size = path.stat().st_size
    if size == 0 or size % 36:
        raise ValueError("collision triangle soup must contain complete float32 triangles")
    with path.open("rb") as stream:
        while data := stream.read(36):
            values = struct.unpack("<9f", data)
            yield tuple((values[index], values[index + 1], values[index + 2]) for index in range(0, 9, 3))


def load_projection(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    transform = document.get("transform", {})
    canvas = document.get("canvas", {})
    if document.get("schema") != "iy.map_overview_metadata/v1":
        raise ValueError("expected iy.map_overview_metadata/v1")
    if transform.get("verification_status") != "VERIFIED":
        raise ValueError("projection transform is not VERIFIED")
    if transform.get("rotation_deg_clockwise") != 0:
        raise ValueError("PoC supports only the existing verified zero-rotation projection")
    if not all(isinstance(canvas.get(field), int) and canvas[field] > 0 for field in ("width", "height")):
        raise ValueError("projection canvas is invalid")
    return document


def project(document: dict, x: float, y: float) -> tuple[float, float]:
    transform = document["transform"]
    origin = transform["origin_world"]
    scale = transform["world_units_per_pixel"]
    return ((x - origin["x"]) / scale, (origin["y"] - y) / scale)


def build_overlay(tri_path: Path, projection_path: Path, output_path: Path, *, grid_size: int = 128) -> OverlayResult:
    if grid_size < 8:
        raise ValueError("grid_size must be at least 8")
    document = load_projection(projection_path)
    canvas = document["canvas"]
    width, height = canvas["width"], canvas["height"]
    cells: set[tuple[int, int]] = set()
    total = horizontal = in_bounds = 0
    for triangle in iter_triangles(tri_path):
        total += 1
        first, second, third = triangle
        ux, uy, uz = (second[index] - first[index] for index in range(3))
        vx, vy, vz = (third[index] - first[index] for index in range(3))
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        magnitude = math.sqrt(nx * nx + ny * ny + nz * nz)
        if magnitude == 0 or abs(nz) / magnitude < 0.85:
            continue
        horizontal += 1
        x = (first[0] + second[0] + third[0]) / 3
        y = (first[1] + second[1] + third[1]) / 3
        px, py = project(document, x, y)
        if not (0 <= px <= width and 0 <= py <= height):
            continue
        in_bounds += 1
        cells.add((min(grid_size - 1, int(px / width * grid_size)), min(grid_size - 1, int(py / height * grid_size))))
    cell_width, cell_height = width / grid_size, height / grid_size
    rectangles = "".join(
        f'<rect x="{column * cell_width:.3f}" y="{row * cell_height:.3f}" width="{cell_width:.3f}" height="{cell_height:.3f}"/>'
        for column, row in sorted(cells)
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<title>Improve local-only collision surface candidate — {document["map_id"]}</title>
<desc>Generated from local collision triangles. Cells are horizontal-surface candidates only; they do not assert walls, walkability, callouts, or layers.</desc>
<rect width="100%" height="100%" fill="#06131e"/>
<g fill="#183a52" stroke="#24516f" stroke-width="0.5">{rectangles}</g>
<rect x="0" y="0" width="{width}" height="{height}" fill="none" stroke="#3d79a0" stroke-width="2"/>
</svg>\n'''
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return OverlayResult(total, horizontal, in_bounds, len(cells), width, height)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a local-only collision-surface SVG PoC")
    parser.add_argument("triangles", type=Path)
    parser.add_argument("projection", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--grid-size", type=int, default=128)
    args = parser.parse_args()
    result = build_overlay(args.triangles, args.projection, args.output, grid_size=args.grid_size)
    print(json.dumps({"source_sha256": sha256(args.triangles), **result.__dict__}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
