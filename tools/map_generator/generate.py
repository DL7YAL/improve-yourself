"""Local-only deterministic collision-surface preview generator."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .model import GeometryGrid
from .project import load_projection, project
from .render_svg import render_png, render_svg
from .validate import is_horizontal_surface_candidate, iter_triangles


def sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def build_grid(triangles: Path, projection_path: Path, *, grid_size: int = 128) -> GeometryGrid:
    if grid_size < 8:
        raise ValueError("grid_size must be at least 8")
    document = load_projection(projection_path)
    width, height = document["canvas"]["width"], document["canvas"]["height"]
    cells: set[tuple[int, int]] = set(); total = horizontal = in_bounds = 0
    for triangle in iter_triangles(triangles):
        total += 1
        if not is_horizontal_surface_candidate(triangle):
            continue
        horizontal += 1
        x = sum(point[0] for point in triangle) / 3; y = sum(point[1] for point in triangle) / 3
        px, py = project(document, x, y)
        if not (0 <= px <= width and 0 <= py <= height):
            continue
        in_bounds += 1
        cells.add((min(grid_size - 1, int(px / width * grid_size)), min(grid_size - 1, int(py / height * grid_size))))
    return GeometryGrid(document["map_id"], width, height, grid_size, frozenset(cells), total, horizontal, in_bounds)


def generate(triangles: Path, projection: Path, style_path: Path, output_dir: Path, *, grid_size: int = 128) -> GeometryGrid:
    grid = build_grid(triangles, projection, grid_size=grid_size)
    style = json.loads(style_path.read_text(encoding="utf-8"))
    render_svg(grid, style, output_dir / f"{grid.map_id}_preview.svg")
    render_png(grid, style, output_dir / f"{grid.map_id}_preview.png")
    return grid


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate local-only Improve collision-surface previews")
    parser.add_argument("triangles", type=Path); parser.add_argument("projection", type=Path); parser.add_argument("style", type=Path); parser.add_argument("output_dir", type=Path); parser.add_argument("--grid-size", type=int, default=128)
    args = parser.parse_args(); grid = generate(args.triangles, args.projection, args.style, args.output_dir, grid_size=args.grid_size)
    print(json.dumps({"source_sha256": sha256(args.triangles), **grid.__dict__, "cells": len(grid.cells)}, sort_keys=True, default=list))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
