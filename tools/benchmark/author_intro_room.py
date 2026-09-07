"""Move technical team spawns into a project-owned dark benchmark intro room."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from author_nuke_outside import matching_delimiter, world_children
from author_transition_graybox import specialize


ROOM_BOXES = [
    ((-4000, -4000, -32), (2.2, 1.5, 32), "materials/dev/csgo_grey.vmat"),
    ((-4576, -4000, 176), (0.125, 1.5, 208), "materials/dev/black_simple.vmat"),
    ((-3424, -4000, 176), (0.125, 1.5, 208), "materials/dev/black_simple.vmat"),
    ((-4000, -4384, 176), (2.2, 0.125, 208), "materials/dev/black_simple.vmat"),
    ((-4000, -3616, 176), (2.2, 0.125, 208), "materials/dev/black_simple.vmat"),
    ((-4000, -4000, 400), (2.2, 1.5, 16), "materials/dev/black_simple.vmat"),
    ((-4000, -4370, 96), (1.25, 0.04, 56), "materials/dev/reflectivity_30.vmat"),
]


def entity_blocks(text: str):
    cursor = 0
    while True:
        match = re.search(r'"CMapEntity"\s*\{', text[cursor:])
        if not match:
            return
        start = cursor + match.start()
        brace = text.index("{", start)
        end = matching_delimiter(text, brace, "{", "}") + 1
        yield start, end, text[start:end]
        cursor = end


def move_spawns(text: str) -> str:
    counters = {"info_player_terrorist": 0, "info_player_counterterrorist": 0, "info_player_start": 0}
    replacements = []
    for start, end, block in entity_blocks(text):
        match = re.search(r'"classname" "string" "(info_player_(?:terrorist|counterterrorist|start))"', block)
        if not match:
            continue
        kind = match.group(1)
        index = counters[kind]
        counters[kind] += 1
        if kind == "info_player_start":
            position = (-4000, -4100, 16)
        else:
            row = -4050 if kind == "info_player_terrorist" else -3950
            position = (-4400 + (index % 10) * 88, row, 16)
        origin = " ".join(str(value) for value in position)
        refined, count = re.subn(r'"origin" "vector3" "[^"]+"', f'"origin" "vector3" "{origin}"', block, count=1)
        if count != 1:
            raise ValueError(f"spawn origin missing for {kind}")
        replacements.append((start, end, refined))
    if counters["info_player_terrorist"] < 10 or counters["info_player_counterterrorist"] < 10:
        raise ValueError(f"unexpected spawn inventory: {counters}")
    for start, end, refined in reversed(replacements):
        text = text[:start] + refined + text[end:]
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    text = args.input.read_text(encoding="utf-8")
    if '"origin" "vector3" "-4000 -4000 -32"' in text:
        raise SystemExit("intro room already present")
    text = move_spawns(text)
    array_start, array_end = world_children(text)
    mesh_start = text.index('"CMapMesh"', array_start, array_end)
    brace = text.index("{", mesh_start, array_end)
    mesh_end = matching_delimiter(text, brace, "{", "}") + 1
    primitive = text[mesh_start:mesh_end]
    node_ids = [int(value) for value in re.findall(r'"nodeID" "int" "(\d+)"', text)]
    generated = []
    for offset, (origin, scales, material) in enumerate(ROOM_BOXES):
        block = specialize(primitive, max(node_ids) + 1 + offset, f"intro_room_{offset}", origin, scales, material)
        generated.append("\t\t\t" + block.replace("\n", "\n\t\t\t"))
    insertion = ",\n" + ",\n".join(generated) + "\n"
    args.output.write_text(text[:array_end] + insertion + text[array_end:], encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
