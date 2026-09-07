"""Apply the Ancient B and Inferno Apps/A visual world pass to a text VMAP.

The map geometry remains project-authored.  Valve resources are referenced from
the installed CS2 runtime only; this tool neither extracts nor copies them.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from author_nuke_outside import prop_template, specialize_prop, world_children


MATERIALS = {
    # Ancient approach, shallow water, temple walls and Red Room.
    "0 2300 -32": "materials/de_ancient/hr_ancient_blend_grounddirt01-groundgrass01-groundrock01-wet.vmat",
    "0 2250 6": "materials/de_ancient/hr_ancient_ground_rock_01_wet.vmat",
    "-672 2300 192": "materials/de_ancient/hr_ancient_wall_stone_01_base.vmat",
    "672 2300 192": "materials/de_ancient/hr_ancient_wall_stone_01_base.vmat",
    "0 3072 192": "materials/de_ancient/hr_ancient_wall_stone_04_base.vmat",
    "0 2300 400": "materials/de_ancient/hr_ancient_ceiling_wood_01_base.vmat",
    "-420 2860 128": "materials/de_ancient/hr_ancient_wall_plaster_01_red_wet.vmat",
    "420 2860 128": "materials/de_ancient/hr_ancient_wall_plaster_01_red_wet.vmat",
    "0 3000 270": "materials/de_ancient/hr_ancient_wall_plaster_01_red_wet.vmat",
    # Inferno stair approach and enclosed apartments/A transition corridor.
    "0 4500 -32": "materials/de_inferno/ground/inferno_stone_floor_01.vmat",
    "-672 4500 224": "materials/de_inferno/plaster/inferno_plaster_01_orange.vmat",
    "672 4500 224": "materials/de_inferno/plaster/inferno_plaster_01_yellow.vmat",
    "0 5272 224": "materials/de_inferno/brick/inferno_brick_01.vmat",
    "0 4500 464": "materials/de_inferno/plaster/inferno_plaster_01_orange.vmat",
    "0 3740 8": "materials/de_inferno/ground/inferno_stone_floor_01.vmat",
    "0 3880 16": "materials/de_inferno/ground/inferno_stone_floor_01.vmat",
    "0 4020 24": "materials/de_inferno/ground/inferno_stone_floor_01.vmat",
    "0 4160 32": "materials/de_inferno/ground/inferno_stone_floor_01.vmat",
    "0 4300 40": "materials/de_inferno/ground/inferno_stone_floor_01.vmat",
}


PROPS = [
    ("ancient_crates_left", "models/props/de_ancient/ancient_crates/ancient_crate_assembly_100x100_01.vmdl", (-390, 2440, 22), (0, 20, 0), 0.85),
    ("ancient_crates_right", "models/props/de_ancient/ancient_crates/ancient_crate_assembly_100x100_01.vmdl", (390, 2630, 22), (0, 205, 0), 0.75),
    ("ancient_double_door_frame_left", "models/props/de_ancient/ancient_doors/ancient_door_largewood_02_frame.vmdl", (-180, 2035, 40), (0, 90, 0), 0.95),
    ("ancient_double_door_frame_right", "models/props/de_ancient/ancient_doors/ancient_door_largewood_02_frame.vmdl", (180, 2035, 40), (0, 270, 0), 0.95),
    ("ancient_b_top", "models/props/de_ancient/ancient_walls/ancient_wall_stone_04_building_top_01.vmdl", (0, 3000, 245), (0, 180, 0), 1.0),
    ("ancient_scaffold_left", "models/props/de_ancient/ancient_scaffolding/ancient_scaffold_assembly_03.vmdl", (-520, 2800, 0), (0, 0, 0), 0.8),
    ("ancient_candles_red", "models/props/de_ancient/ancient_lighting/ancient_lighting_candle_cluster_01_lit.vmdl", (-245, 2870, 48), (0, 0, 0), 1.0),
    ("inferno_apps_arch", "models/props/de_inferno/hr_i/arch_a/arch_a.vmdl", (0, 4380, 55), (0, 90, 0), 1.0),
    ("inferno_apps_door", "models/props/de_inferno/hr_i/door_a/door_a.vmdl", (-330, 4760, 35), (0, 90, 0), 1.0),
    ("inferno_railing_left", "models/props/de_inferno/hr_i/inferno_stair_railing/inferno_stair_railing.vmdl", (-285, 4050, 70), (0, 0, 0), 1.0),
    ("inferno_railing_right", "models/props/de_inferno/hr_i/inferno_stair_railing/inferno_stair_railing.vmdl", (285, 4050, 70), (0, 180, 0), 1.0),
    ("inferno_balcony", "models/props/de_inferno/hr_i/inferno_balcony/inferno_balcony_railing01.vmdl", (420, 4720, 180), (0, 270, 0), 0.8),
    ("inferno_barrel", "models/props/de_inferno/hr_i/barrel_a/barrel_a_full.vmdl", (-430, 4620, 25), (0, 0, 0), 1.0),
    ("inferno_wine_crates", "models/props/de_inferno/hr_i/inferno_wine_crate/inferno_wine_crate_01.vmdl", (430, 5000, 25), (0, 35, 0), 1.0),
    ("inferno_flower_planter", "models/props/de_inferno/hr_i/inferno_planter/inferno_planter.vmdl", (500, 4550, 115), (0, 180, 0), 1.0),
    ("inferno_street_lamp", "models/props/de_inferno/hr_i/ornate_lamp/ornate_lamp.vmdl", (-520, 5000, 90), (0, 0, 0), 1.0),
]


def apply_materials(text: str) -> str:
    start, end = world_children(text)
    for origin, material in MATERIALS.items():
        candidates = list(re.finditer(r'"CMapMesh"\s*\{', text[start:end]))
        found = False
        for candidate in candidates:
            block_start = start + candidate.start()
            next_block = text.find('\n\t\t\t"CMap', block_start + 1, end)
            block_end = next_block if next_block >= 0 else end
            block = text[block_start:block_end]
            if f'"origin" "vector3" "{origin}"' not in block:
                continue
            block, count = re.subn(r'"materials/dev/(?:dev_measuregeneric01|reflectivity_30)\.vmat"', f'"{material}"', block)
            if count == 0:
                raise ValueError(f"no project graybox material at {origin}")
            text = text[:block_start] + block + text[block_end:]
            end += len(block) - (block_end - block_start)
            found = True
            break
        if not found:
            raise ValueError(f"project graybox mesh not found at {origin}")
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("prop_template", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    text = args.input.read_text(encoding="utf-8")
    if PROPS[0][1] in text:
        raise SystemExit("Ancient/Inferno visual props already present")
    text = apply_materials(text)
    template = prop_template(args.prop_template.read_text(encoding="utf-8"))
    _, array_end = world_children(text)
    node_ids = [int(value) for value in re.findall(r'"nodeID" "int" "(\d+)"', text)]
    generated = []
    for offset, (_, model, origin, angles, scale) in enumerate(PROPS):
        prop = specialize_prop(template, max(node_ids) + 1 + offset, model, origin, angles, scale)
        generated.append("\t\t\t" + prop.replace("\n", "\n\t\t\t"))
    insertion = ",\n" + ",\n".join(generated) + "\n"
    args.output.write_text(text[:array_end] + insertion + text[array_end:], encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
