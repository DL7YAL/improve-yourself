"""Apply the Nuke Outside visual-authenticity pass to a text VMAP.

The input map and template are keyvalues2 files produced by Valve's
``dmxconvert``.  The script clones a Valve-authored ``prop_static`` element so
Hammer remains responsible for Source 2 serialization.  Referenced models and
materials are resolved from the installed CS2 runtime; no Valve asset is copied
into the addon or repository.
"""

from __future__ import annotations

import argparse
import re
import uuid
from pathlib import Path


PROPS = [
    ("cooling_tower_left", "models/props/de_nuke/hr_nuke/nuke_cooling_tower/nuke_cooling_tower.vmdl", (1700, 1450, 0), (0, 210, 0), 1.0),
    ("cooling_tower_right", "models/props/de_nuke/hr_nuke/nuke_cooling_tower/nuke_cooling_tower.vmdl", (2500, 1750, 0), (0, 205, 0), 1.0),
    ("outside_silo", "models/props/de_nuke/hr_nuke/medium_silo/medium_silo.vmdl", (1050, 1180, 0), (0, 180, 0), 1.0),
    ("outside_crane", "models/props/de_nuke/hr_nuke/nuke_cargo_crane/nuke_cargo_crane_base.vmdl", (-1450, 620, 0), (0, 20, 0), 1.0),
    ("outside_truck", "models/props/de_nuke/hr_nuke/nuke_cars/nuke_truck_01.vmdl", (-150, 180, 0), (0, 90, 0), 1.0),
    ("outside_trailer", "models/props/de_nuke/hr_nuke/nuke_cars/nuke_truck_01_trailer.vmdl", (190, 250, 0), (0, 90, 0), 1.0),
    ("outside_forklift", "models/props/de_nuke/hr_nuke/nuke_forklift/nuke_forklift_small.vmdl", (630, 460, 0), (0, 155, 0), 1.0),
    ("secret_sign", "models/props/de_nuke/hr_nuke/nuke_signs/nuke_sign_secret.vmdl", (445, 975, 82), (0, 200, 0), 1.0),
    ("garage_sign", "models/props/de_nuke/hr_nuke/nuke_signs/nuke_sign_garage.vmdl", (-580, 525, 90), (0, 90, 0), 1.0),
    ("outside_barrier", "models/props/de_nuke/hr_nuke/nuke_concrete_barrier/nuke_concrete_barrier.vmdl", (-520, 80, 0), (0, 15, 0), 1.0),
]


MATERIALS = {
    "-384 256 -32": "materials/de_nuke/hr_nuke/hr_asphalt_002.vmat",
    "-1760 -1024 200": "materials/de_nuke/hr_nuke/nuke_concrete_wall_001.vmat",
    "-64 1184 288": "materials/de_nuke/hr_nuke/nuke_concrete_wall_001.vmat",
    "-320 480 96": "materials/de_nuke/hr_nuke/nuke_concrete_wall_001.vmat",
    "800 1120 160": "materials/de_nuke/hr_nuke/nuke_concrete_wall_001.vmat",
}


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


def world_children(text: str) -> tuple[int, int]:
    world = text.index('"world" "CMapWorld"')
    children = text.index('"children" "element_array"', world)
    start = text.index("[", children)
    return start, matching_delimiter(text, start, "[", "]")


def clone_ids(block: str, node_id: int) -> str:
    mapping: dict[str, str] = {}

    def replacement(match: re.Match[str]) -> str:
        old = match.group(0)
        mapping.setdefault(old, str(uuid.uuid4()))
        return mapping[old]

    block = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", replacement, block)
    block, count = re.subn(r'("nodeID" "int" ")\d+(")', rf"\g<1>{node_id}\2", block, count=1)
    if count != 1:
        raise ValueError("prop template nodeID did not match exactly once")
    reference = uuid.uuid4().int & ((1 << 64) - 1)
    return re.sub(r'("referenceID" "uint64" ")0x[0-9a-f]+(")', rf"\g<1>0x{reference:016x}\2", block, count=1)


def format_vector(values: tuple[float, float, float]) -> str:
    return " ".join(str(int(value)) if float(value).is_integer() else str(value) for value in values)


def specialize_prop(template: str, node_id: int, model: str, origin: tuple[float, float, float], angles: tuple[float, float, float], scale: float) -> str:
    block = clone_ids(template, node_id)
    replacements = {
        r'("model" "string" ")[^"]+("$)': rf"\g<1>{model}\2",
        r'("solid" "string" ")[^"]+("$)': r'\g<1>0\2',
        r'("disableshadows" "string" ")[^"]+("$)': r'\g<1>0\2',
        r'("fademindist" "string" ")[^"]+("$)': r'\g<1>-1\2',
        r'("fademaxdist" "string" ")[^"]+("$)': r'\g<1>0\2',
        r'("rendercolor" "string" ")[^"]+("$)': r'\g<1>255 255 255\2',
        r'("origin" "vector3" ")[^"]+("$)': rf"\g<1>{format_vector(origin)}\2",
        r'("angles" "qangle" ")[^"]+("$)': rf"\g<1>{format_vector(angles)}\2",
        r'("scales" "vector3" ")[^"]+("$)': rf"\g<1>{scale} {scale} {scale}\2",
    }
    for pattern, replacement in replacements.items():
        block, count = re.subn(pattern, replacement, block, count=1, flags=re.MULTILINE)
        if count != 1:
            raise ValueError(f"prop template field did not match exactly once: {pattern}")
    return block


def prop_template(text: str) -> str:
    marker = '"classname" "string" "prop_static"'
    marker_at = text.index(marker)
    start = text.rfind('"CMapEntity"', 0, marker_at)
    brace = text.index("{", start, marker_at)
    end = matching_delimiter(text, brace, "{", "}")
    return text[start : end + 1]


def apply_materials(text: str) -> str:
    start, end = world_children(text)
    cursor = start + 1
    replacements = 0
    while cursor < end:
        match = re.search(r'"CMap(?:Mesh|Entity)"\s*\{', text[cursor:end])
        if not match:
            break
        block_start = cursor + match.start()
        brace = text.index("{", block_start, end)
        block_end = matching_delimiter(text, brace, "{", "}") + 1
        block = text[block_start:block_end]
        for origin, material in MATERIALS.items():
            if f'"origin" "vector3" "{origin}"' not in block:
                continue
            block, count = re.subn(
                r'"materials/dev/(?:dev_measuregeneric01|reflectivity_30)\.vmat"',
                f'"{material}"',
                block,
            )
            if count == 0:
                raise ValueError(f"no replaceable material at {origin}")
            text = text[:block_start] + block + text[block_end:]
            delta = len(block) - (block_end - block_start)
            end += delta
            block_end += delta
            replacements += 1
            break
        cursor = block_end
    if replacements != len(MATERIALS):
        raise ValueError(f"replaced {replacements} of {len(MATERIALS)} Nuke materials")
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("prop_template", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8")
    if PROPS[0][1] in text:
        raise SystemExit("Nuke Outside authenticity props already present")
    text = apply_materials(text)
    template = prop_template(args.prop_template.read_text(encoding="utf-8"))
    array_start, array_end = world_children(text)
    node_ids = [int(value) for value in re.findall(r'"nodeID" "int" "(\d+)"', text)]
    next_node = max(node_ids) + 1
    generated = []
    for offset, (_, model, origin, angles, scale) in enumerate(PROPS):
        prop = specialize_prop(template, next_node + offset, model, origin, angles, scale)
        generated.append("\t\t\t" + prop.replace("\n", "\n\t\t\t"))
    insertion = ",\n" + ",\n".join(generated) + "\n"
    args.output.write_text(text[:array_end] + insertion + text[array_end:], encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
