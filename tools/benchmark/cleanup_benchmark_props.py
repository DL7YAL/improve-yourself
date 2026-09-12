"""Remove runtime props that failed the in-engine composition check."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from author_nuke_outside import matching_delimiter, world_children


REMOVE_MODELS = {
    "models/props/de_ancient/ancient_doors/ancient_door_largewood_02_frame.vmdl": 2,
    "models/props/de_ancient/ancient_scaffolding/ancient_scaffold_assembly_03.vmdl": 1,
    "models/props/de_ancient/ancient_walls/ancient_wall_stone_04_building_top_01.vmdl": 1,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    text = args.input.read_text(encoding="utf-8")
    start, end = world_children(text)
    removals = []
    cursor = start + 1
    found = {model: 0 for model in REMOVE_MODELS}
    while cursor < end:
        match = re.search(r'"CMapEntity"\s*\{', text[cursor:end])
        if not match:
            break
        block_start = cursor + match.start()
        brace = text.index("{", block_start, end)
        block_end = matching_delimiter(text, brace, "{", "}") + 1
        block = text[block_start:block_end]
        for model in REMOVE_MODELS:
            if f'"model" "string" "{model}"' in block:
                remove_start, remove_end = block_start, block_end
                following = re.match(r'\s*,', text[remove_end:end])
                if following:
                    remove_end += following.end()
                else:
                    preceding = re.search(r',\s*$', text[start:remove_start])
                    if not preceding:
                        raise ValueError("entity is not comma-delimited")
                    remove_start = start + preceding.start()
                removals.append((remove_start, remove_end))
                found[model] += 1
                break
        cursor = block_end
    if found != REMOVE_MODELS:
        raise ValueError(f"unexpected removable prop inventory: {found}")
    for remove_start, remove_end in reversed(removals):
        text = text[:remove_start] + text[remove_end:]
    old_floor = "materials/de_ancient/hr_ancient_blend_grounddirt01-groundgrass01-groundrock01-wet.vmat"
    new_floor = "materials/de_ancient/hr_ancient_ground_rock_01_base.vmat"
    if text.count(old_floor) != 1:
        raise ValueError("Ancient blend floor reference was not unique")
    text = text.replace(old_floor, new_floor)
    args.output.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
