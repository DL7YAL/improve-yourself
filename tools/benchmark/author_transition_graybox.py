"""Add the project-owned Ancient/Inferno transition graybox to a text VMAP.

The input is the keyvalues2 representation produced by Valve's dmxconvert.
This deliberately clones the map's existing project-authored block primitive so
Hammer remains the authority for mesh serialization and material references.
"""

from __future__ import annotations

import argparse
import re
import uuid
from pathlib import Path


BOXES = [
    # Ancient B ramp/water/Red Room graybox, y=2300.
    ("ancient_floor", (0, 2300, -32), (2.5, 3.0, 32), "materials/dev/dev_measuregeneric01.vmat"),
    ("ancient_water", (0, 2250, 6), (1.8, 1.15, 4), "materials/dev/reflectivity_30.vmat"),
    ("ancient_left_wall", (-672, 2300, 192), (0.125, 3.0, 192), "materials/dev/dev_measuregeneric01.vmat"),
    ("ancient_right_wall", (672, 2300, 192), (0.125, 3.0, 192), "materials/dev/dev_measuregeneric01.vmat"),
    ("ancient_end_wall", (0, 3072, 192), (2.5, 0.125, 192), "materials/dev/dev_measuregeneric01.vmat"),
    ("ancient_roof", (0, 2300, 400), (2.5, 3.0, 16), "materials/dev/dev_measuregeneric01.vmat"),
    ("ancient_red_left", (-420, 2860, 128), (0.125, 0.75, 128), "materials/dev/reflectivity_30.vmat"),
    ("ancient_red_right", (420, 2860, 128), (0.125, 0.75, 128), "materials/dev/reflectivity_30.vmat"),
    ("ancient_red_ceiling", (0, 3000, 270), (1.65, 0.75, 16), "materials/dev/reflectivity_30.vmat"),
    # Inferno Apps/stairs graybox, y=4500.
    ("inferno_floor", (0, 4500, -32), (2.5, 3.0, 32), "materials/dev/dev_measuregeneric01.vmat"),
    ("inferno_left_wall", (-672, 4500, 224), (0.125, 3.0, 224), "materials/dev/dev_measuregeneric01.vmat"),
    ("inferno_right_wall", (672, 4500, 224), (0.125, 3.0, 224), "materials/dev/dev_measuregeneric01.vmat"),
    ("inferno_end_wall", (0, 5272, 224), (2.5, 0.125, 224), "materials/dev/dev_measuregeneric01.vmat"),
    ("inferno_roof", (0, 4500, 464), (2.5, 3.0, 16), "materials/dev/dev_measuregeneric01.vmat"),
    ("inferno_step_1", (0, 3740, 8), (1.25, 0.28, 8), "materials/dev/reflectivity_30.vmat"),
    ("inferno_step_2", (0, 3880, 16), (1.25, 0.28, 16), "materials/dev/reflectivity_30.vmat"),
    ("inferno_step_3", (0, 4020, 24), (1.25, 0.28, 24), "materials/dev/reflectivity_30.vmat"),
    ("inferno_step_4", (0, 4160, 32), (1.25, 0.28, 32), "materials/dev/reflectivity_30.vmat"),
    ("inferno_step_5", (0, 4300, 40), (1.25, 0.28, 40), "materials/dev/reflectivity_30.vmat"),
]


def matching_delimiter(text: str, start: int, opener: str, closer: str) -> int:
    depth = 0
    quoted = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index
    raise ValueError(f"unmatched {opener}")


def replace_ids(block: str, node_id: int) -> str:
    mapping: dict[str, str] = {}

    def uuid_replacement(match: re.Match[str]) -> str:
        old = match.group(0)
        mapping.setdefault(old, str(uuid.uuid4()))
        return mapping[old]

    block = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", uuid_replacement, block)
    block = re.sub(r'("nodeID" "int" ")\d+(")', rf"\g<1>{node_id}\2", block, count=1)
    reference = uuid.uuid4().int & ((1 << 64) - 1)
    block = re.sub(r'("referenceID" "uint64" ")0x[0-9a-f]+(")', rf"\g<1>0x{reference:016x}\2", block, count=1)
    return block


def format_number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def specialize(block: str, node_id: int, name: str, origin: tuple[float, float, float], scales: tuple[float, float, float], material: str) -> str:
    block = replace_ids(block, node_id)
    origin_text = " ".join(format_number(value) for value in origin)
    scales_text = " ".join(format_number(value) for value in scales)
    block = re.sub(r'(?m)^(\s*)"origin" "vector3" "[^"]+"$', rf'\1"origin" "vector3" "{origin_text}"', block, count=1)
    block = re.sub(r'(?m)^(\s*)"scales" "vector3" "[^"]+"$', rf'\1"scales" "vector3" "{scales_text}"', block, count=1)
    block = re.sub(r'"materials/dev/dev_measuregeneric01\.vmat"', f'"{material}"', block)
    return block


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    text = args.input.read_text(encoding="utf-8")
    if '"origin" "vector3" "0 2300 -32"' in text:
        raise SystemExit("transition graybox already present")

    # Extend the existing upper-area light/reflection probe over both added
    # corridors. Without this, the meshes compile but render overexposed and
    # lose their faces outside the original Nuke-only probe bounds.
    old_probe_mins = '"box_mins" "string" "-576.000000 -144.000000 -112.000000"'
    old_probe_maxs = '"box_maxs" "string" "640.000000 336.000000 144.000000"'
    if text.count(old_probe_mins) != 1 or text.count(old_probe_maxs) != 1:
        raise SystemExit("expected upper light probe bounds were not found exactly once")
    text = text.replace(old_probe_mins, '"box_mins" "string" "-1400.000000 -500.000000 -256.000000"')
    text = text.replace(old_probe_maxs, '"box_maxs" "string" "1400.000000 4300.000000 640.000000"')

    world = text.index('"world" "CMapWorld"')
    children = text.index('"children" "element_array"', world)
    array_start = text.index("[", children)
    array_end = matching_delimiter(text, array_start, "[", "]")
    mesh_start = text.index('"CMapMesh"', array_start, array_end)
    brace_start = text.index("{", mesh_start, array_end)
    brace_end = matching_delimiter(text, brace_start, "{", "}")
    primitive = text[mesh_start:brace_end + 1]
    node_ids = [int(value) for value in re.findall(r'"nodeID" "int" "(\d+)"', text)]
    next_node = max(node_ids) + 1
    generated = []
    for offset, (name, origin, scales, material) in enumerate(BOXES):
        generated.append("\t\t\t" + specialize(primitive, next_node + offset, name, origin, scales, material).replace("\n", "\n\t\t\t"))
    insertion = ",\n" + ",\n".join(generated) + "\n"
    args.output.write_text(text[:array_end] + insertion + text[array_end:], encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
