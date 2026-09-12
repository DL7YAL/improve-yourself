"""Refine prop grounding and room closure in the authored benchmark worlds."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from author_nuke_outside import matching_delimiter, world_children


PROP_ORIGINS = {
    "models/props/de_ancient/ancient_crates/ancient_crate_assembly_100x100_01.vmdl": {
        "-390 2440 22": "-390 2440 0",
        "390 2630 22": "390 2630 0",
    },
    "models/props/de_ancient/ancient_doors/ancient_door_largewood_02_frame.vmdl": {
        "-180 2035 40": "-180 2035 0",
        "180 2035 40": "180 2035 0",
    },
    "models/props/de_ancient/ancient_walls/ancient_wall_stone_04_building_top_01.vmdl": {
        "0 3000 245": "0 3000 72",
    },
    "models/props/de_ancient/ancient_lighting/ancient_lighting_candle_cluster_01_lit.vmdl": {
        "-245 2870 48": "-245 2870 4",
    },
    "models/props/de_inferno/hr_i/door_a/door_a.vmdl": {"-330 4760 35": "-330 4760 0"},
    "models/props/de_inferno/hr_i/barrel_a/barrel_a_full.vmdl": {"-430 4620 25": "-430 4620 0"},
    "models/props/de_inferno/hr_i/inferno_wine_crate/inferno_wine_crate_01.vmdl": {"430 5000 25": "430 5000 0"},
    "models/props/de_inferno/hr_i/inferno_planter/inferno_planter.vmdl": {"500 4550 115": "500 4550 80"},
    "models/props/de_inferno/hr_i/ornate_lamp/ornate_lamp.vmdl": {"-520 5000 90": "-635 5000 155"},
}


def map_blocks(text: str):
    start, end = world_children(text)
    cursor = start + 1
    while cursor < end:
        match = re.search(r'"CMap(?:Mesh|Entity)"\s*\{', text[cursor:end])
        if not match:
            return
        block_start = cursor + match.start()
        brace = text.index("{", block_start, end)
        block_end = matching_delimiter(text, brace, "{", "}") + 1
        yield block_start, block_end, text[block_start:block_end]
        cursor = block_end


def scale_mesh_z(block: str, factor: float) -> str:
    stream = re.compile(r'("name" "string" "position:0".*?"data" "vector3_array"\s*\[)(.*?)(\n\s*\])', re.DOTALL)
    match = stream.search(block)
    if not match:
        raise ValueError("mesh has no position stream")

    def scale(value: re.Match[str]) -> str:
        parts = [float(item) for item in value.group(1).split()]
        parts[2] *= factor
        return '"' + " ".join(f"{item:g}" for item in parts) + '"'

    data = re.sub(r'"([+-]?[\d.]+\s+[+-]?[\d.]+\s+[+-]?[\d.]+)"', scale, match.group(2))
    return block[:match.start(2)] + data + block[match.end(2):]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    text = args.input.read_text(encoding="utf-8")
    if '"origin" "vector3" "0 4500 700"' in text:
        raise SystemExit("benchmark world refinement already present")

    # Ground props using model-specific substitutions so unrelated entities are untouched.
    prop_changes = 0
    for model, origins in PROP_ORIGINS.items():
        if text.count(f'"model" "string" "{model}"') != len(origins):
            raise ValueError(f"unexpected reference count for {model}")
        for old, new in origins.items():
            marker = f'"origin" "vector3" "{old}"'
            if text.count(marker) != 1:
                raise ValueError(f"unexpected prop origin count at {old}")
            text = text.replace(marker, f'"origin" "vector3" "{new}"')
            prop_changes += 1

    # Extend Inferno's three enclosing walls above the high opening shot.
    for origin in ("-672 4500 224", "672 4500 224", "0 5272 224"):
        for start, end, block in list(map_blocks(text)):
            if f'"origin" "vector3" "{origin}"' not in block:
                continue
            refined = scale_mesh_z(block, 1.65)
            text = text[:start] + refined + text[end:]
            break
        else:
            raise ValueError(f"Inferno wall mesh missing at {origin}")

    roof = '"origin" "vector3" "0 4500 464"'
    if text.count(roof) != 1:
        raise ValueError("Inferno roof mesh missing")
    text = text.replace(roof, '"origin" "vector3" "0 4500 700"')
    if prop_changes != 11:
        raise ValueError(f"expected 11 grounded prop changes, got {prop_changes}")
    args.output.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
