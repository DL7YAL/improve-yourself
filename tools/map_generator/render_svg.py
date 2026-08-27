"""Deterministic project-owned SVG and PNG renderers."""
from __future__ import annotations

from pathlib import Path

from .model import GeometryGrid


def render_svg(grid: GeometryGrid, style: dict, output: Path) -> None:
    cell_width, cell_height = grid.width / grid.grid_size, grid.height / grid.grid_size
    cells = "".join(f'<rect x="{column * cell_width:.3f}" y="{row * cell_height:.3f}" width="{cell_width:.3f}" height="{cell_height:.3f}"/>' for column, row in sorted(grid.cells))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{grid.width}" height="{grid.height}" viewBox="0 0 {grid.width} {grid.height}">
<title>Improve local-only collision surface candidate — {grid.map_id}</title>
<desc>Generated only from local collision triangles. Cells are horizontal-surface candidates; no walkability, walls, callouts, sites, or floors are asserted.</desc>
<rect width="100%" height="100%" fill="{style["background"]}"/>
<g fill="{style["surface_fill"]}" stroke="{style["surface_stroke"]}" stroke-width="{style["surface_stroke_width"]}">{cells}</g>
<rect x="0" y="0" width="{grid.width}" height="{grid.height}" fill="none" stroke="{style["border"]}" stroke-width="{style["border_width"]}"/>
</svg>\n'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")


def render_png(grid: GeometryGrid, style: dict, output: Path) -> None:
    from PIL import Image, ImageDraw
    image = Image.new("RGB", (grid.width, grid.height), style["background"])
    draw = ImageDraw.Draw(image)
    for column, row in sorted(grid.cells):
        left, top = int(column * grid.width / grid.grid_size), int(row * grid.height / grid.grid_size)
        right, bottom = int((column + 1) * grid.width / grid.grid_size), int((row + 1) * grid.height / grid.grid_size)
        draw.rectangle((left, top, right, bottom), fill=style["surface_fill"], outline=style["surface_stroke"])
    draw.rectangle((0, 0, grid.width - 1, grid.height - 1), outline=style["border"], width=style["border_width"])
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=False)
