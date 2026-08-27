# Map generator prototype

The generator is tooling only. It consumes local geometry, validates it, applies the existing `iy.map_overview_metadata/v1` transform, and renders deterministic SVG/PNG previews. It does not alter the Viewer or replay pipeline. Geometry, transform, and style are separate inputs.

The Ancient PoC accepts collision triangles and renders only horizontal-surface candidates. It makes no claim about walls, walkability, sites, callouts, or floors.
