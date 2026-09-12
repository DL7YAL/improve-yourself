"""Build the cinema intro and the second Ancient/Inferno world-detail pass.

The input is Valve ``dmxconvert`` keyvalues2 output from the V1.2 candidate.2
VMAP.  Geometry is project-authored by cloning the map's existing Hammer box
primitive.  Referenced Valve materials and props already belong to the locked
runtime-reference provenance set; no VPK payload is extracted or copied.

This pass deliberately does not edit ``benchmark_controller.js``.  It builds
the destination worlds around the current 64-second camera route and prepares
the intro spawn/seating layout for the later camera/animation assignment.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from author_nuke_outside import matching_delimiter, prop_template, specialize_prop, world_children
from author_transition_graybox import specialize


@dataclass(frozen=True)
class Box:
    name: str
    origin: tuple[float, float, float]
    half_extents: tuple[float, float, float]
    material: str


BLACK = "materials/dev/black_simple.vmat"
GREY = "materials/dev/csgo_grey.vmat"
METAL = "materials/dev/reflectivity_30.vmat"
ANCIENT_STONE = "materials/de_ancient/hr_ancient_wall_stone_01_base.vmat"
ANCIENT_RED = "materials/de_ancient/hr_ancient_wall_plaster_01_red_wet.vmat"
ANCIENT_WET = "materials/de_ancient/hr_ancient_ground_rock_01_wet.vmat"
INFERNO_FLOOR = "materials/de_inferno/ground/inferno_stone_floor_01.vmat"
INFERNO_ORANGE = "materials/de_inferno/plaster/inferno_plaster_01_orange.vmat"
INFERNO_YELLOW = "materials/de_inferno/plaster/inferno_plaster_01_yellow.vmat"
INFERNO_BRICK = "materials/de_inferno/brick/inferno_brick_01.vmat"


def _seat_boxes() -> list[Box]:
    boxes: list[Box] = []
    xs = (-4400, -4300, -4200, -4100, -3900, -3800, -3700, -3600)
    # Screen is at negative Y. Rear rows are raised to keep the screen visible.
    rows = ((-3830, 48), (-3950, 36), (-4070, 24), (-4190, 12))
    for row_index, (y, platform_top) in enumerate(rows):
        boxes.append(
            Box(
                f"cinema_riser_{row_index + 1}",
                (-4000, y + 18, platform_top / 2),
                (500, 54, platform_top / 2),
                GREY,
            )
        )
        for seat_index, x in enumerate(xs):
            # Bots stand just in front of these compact industrial cinema seats.
            boxes.extend(
                (
                    Box(
                        f"cinema_seat_{row_index + 1}_{seat_index + 1}",
                        (x, y + 25, platform_top + 8),
                        (36, 28, 8),
                        METAL,
                    ),
                    Box(
                        f"cinema_seat_back_{row_index + 1}_{seat_index + 1}",
                        (x, y + 48, platform_top + 45),
                        (36, 7, 38),
                        BLACK,
                    ),
                )
            )
    return boxes


INTRO_BOXES = [
    # Deep screen, metal surround and an industrial proscenium.
    Box("cinema_screen", (-4000, -4366, 160), (410, 7, 132), BLACK),
    Box("cinema_screen_frame_top", (-4000, -4355, 300), (438, 12, 9), METAL),
    Box("cinema_screen_frame_bottom", (-4000, -4355, 20), (438, 12, 9), METAL),
    Box("cinema_screen_frame_left", (-4447, -4355, 160), (9, 12, 149), METAL),
    Box("cinema_screen_frame_right", (-3553, -4355, 160), (9, 12, 149), METAL),
    Box("cinema_stage", (-4000, -4298, 12), (470, 48, 12), GREY),
    Box("cinema_stage_lip", (-4000, -4244, 25), (470, 8, 25), BLACK),
    # Side pilasters, ceiling beams and low aisle guides sell the converted hall.
    Box("cinema_pilaster_left", (-4510, -4230, 185), (30, 120, 185), GREY),
    Box("cinema_pilaster_right", (-3490, -4230, 185), (30, 120, 185), GREY),
    Box("cinema_ceiling_beam_front", (-4000, -4230, 365), (510, 28, 24), GREY),
    Box("cinema_ceiling_beam_mid", (-4000, -3990, 365), (510, 22, 20), GREY),
    Box("cinema_ceiling_beam_rear", (-4000, -3750, 365), (510, 22, 20), GREY),
    Box("cinema_aisle_left", (-4028, -3980, 4), (5, 250, 4), METAL),
    Box("cinema_aisle_right", (-3972, -3980, 4), (5, 250, 4), METAL),
] + _seat_boxes()


ANCIENT_BOXES = [
    # A readable temple threshold at the smoke exit.
    Box("ancient_entry_pillar_left", (-285, 1780, 118), (58, 42, 118), ANCIENT_STONE),
    Box("ancient_entry_pillar_right", (285, 1780, 118), (58, 42, 118), ANCIENT_STONE),
    Box("ancient_entry_lintel", (0, 1780, 250), (345, 42, 18), ANCIENT_STONE),
    # Wet approach with raised banks and broken stepping stones.
    Box("ancient_water_bank_left", (-520, 2260, 24), (70, 360, 24), ANCIENT_STONE),
    Box("ancient_water_bank_right", (520, 2260, 24), (70, 360, 24), ANCIENT_STONE),
    Box("ancient_water_step_1", (-170, 2070, 15), (78, 48, 13), ANCIENT_WET),
    Box("ancient_water_step_2", (85, 2200, 14), (92, 52, 12), ANCIENT_WET),
    Box("ancient_water_step_3", (-80, 2360, 14), (82, 50, 12), ANCIENT_WET),
    Box("ancient_water_step_4", (180, 2495, 15), (74, 46, 13), ANCIENT_WET),
    Box("ancient_bank_buttress_left", (-535, 2600, 108), (54, 58, 108), ANCIENT_STONE),
    Box("ancient_bank_buttress_right", (535, 2600, 108), (54, 58, 108), ANCIENT_STONE),
    # Red Room gains depth, a threshold, a rear wall and a central dark niche.
    Box("ancient_red_threshold_left", (-305, 2700, 122), (45, 42, 122), ANCIENT_RED),
    Box("ancient_red_threshold_right", (305, 2700, 122), (45, 42, 122), ANCIENT_RED),
    Box("ancient_red_threshold_lintel", (0, 2700, 252), (350, 42, 18), ANCIENT_RED),
    Box("ancient_red_wall_left", (-350, 3050, 132), (28, 320, 132), ANCIENT_RED),
    Box("ancient_red_wall_right", (350, 3050, 132), (28, 320, 132), ANCIENT_RED),
    Box("ancient_red_back_wall", (0, 3370, 132), (378, 28, 132), ANCIENT_RED),
    Box("ancient_red_niche", (0, 3336, 132), (125, 9, 86), BLACK),
    Box("ancient_red_dais", (0, 3260, 14), (205, 105, 14), ANCIENT_STONE),
    Box("ancient_red_ceiling_beam", (0, 3180, 248), (375, 24, 22), ANCIENT_STONE),
]


INFERNO_BOXES = [
    # Narrow stairwell and side stringers replace the empty oversized-room read.
    Box("inferno_stair_stringer_left", (-252, 4030, 64), (26, 390, 64), INFERNO_BRICK),
    Box("inferno_stair_stringer_right", (252, 4030, 64), (26, 390, 64), INFERNO_BRICK),
    Box("inferno_stair_landing", (0, 4405, 84), (230, 78, 8), INFERNO_FLOOR),
    # Apartments facades, window recesses and ceiling beams form a dense corridor.
    Box("inferno_apps_left_lower", (-350, 4480, 210), (25, 330, 210), INFERNO_ORANGE),
    Box("inferno_apps_right_lower", (350, 4480, 210), (25, 330, 210), INFERNO_YELLOW),
    Box("inferno_apps_left_upper", (-350, 5010, 210), (25, 200, 210), INFERNO_ORANGE),
    Box("inferno_apps_right_upper", (350, 5010, 210), (25, 200, 210), INFERNO_YELLOW),
    Box("inferno_apps_floor", (0, 4815, 88), (325, 330, 8), INFERNO_FLOOR),
    Box("inferno_window_left_1", (-321, 4590, 230), (7, 58, 72), BLACK),
    Box("inferno_window_left_2", (-321, 4860, 230), (7, 58, 72), BLACK),
    Box("inferno_window_right_1", (321, 4590, 230), (7, 58, 72), BLACK),
    Box("inferno_window_right_2", (321, 4860, 230), (7, 58, 72), BLACK),
    Box("inferno_window_sill_left_1", (-310, 4590, 153), (18, 68, 8), INFERNO_BRICK),
    Box("inferno_window_sill_left_2", (-310, 4860, 153), (18, 68, 8), INFERNO_BRICK),
    Box("inferno_window_sill_right_1", (310, 4590, 153), (18, 68, 8), INFERNO_BRICK),
    Box("inferno_window_sill_right_2", (310, 4860, 153), (18, 68, 8), INFERNO_BRICK),
    Box("inferno_beam_entrance", (0, 4450, 430), (382, 24, 20), INFERNO_BRICK),
    Box("inferno_beam_mid", (0, 4770, 430), (382, 20, 18), INFERNO_BRICK),
    Box("inferno_beam_end", (0, 5100, 430), (382, 20, 18), INFERNO_BRICK),
]


ADDED_PROPS = [
    (
        "ancient_red_candles_right",
        "models/props/de_ancient/ancient_lighting/ancient_lighting_candle_cluster_01_lit.vmdl",
        (185, 3260, 28),
        (0, 25, 0),
        1.0,
    ),
    (
        "ancient_red_crates",
        "models/props/de_ancient/ancient_crates/ancient_crate_assembly_100x100_01.vmdl",
        (-245, 3190, 0),
        (0, 160, 0),
        0.62,
    ),
    (
        "inferno_arch_repeat",
        "models/props/de_inferno/hr_i/arch_a/arch_a.vmdl",
        (0, 5010, 88),
        (0, 90, 0),
        1.0,
    ),
    (
        "inferno_barrel_repeat",
        "models/props/de_inferno/hr_i/barrel_a/barrel_a_full.vmdl",
        (230, 4650, 88),
        (0, 20, 0),
        1.0,
    ),
    (
        "inferno_planter_repeat",
        "models/props/de_inferno/hr_i/inferno_planter/inferno_planter.vmdl",
        (-285, 4870, 158),
        (0, 0, 0),
        0.9,
    ),
]


WORLD_TEXTS = [
    # ASCII-only glyphs keep dmxconvert/Source 2 font behavior predictable.
    ("iy_intro_mark_1", "I", (-4315, -4346, 128), 52, "0 178 255 255"),
    ("iy_intro_mark_2", "I", (-4287, -4346, 142), 66, "0 178 255 255"),
    ("iy_intro_mark_3", "I", (-4259, -4346, 156), 80, "0 178 255 255"),
    ("iy_intro_mark_4", "I", (-4231, -4346, 170), 94, "0 178 255 255"),
    ("iy_intro_mark_accent", "/", (-4212, -4346, 231), 34, "0 178 255 255"),
    ("iy_intro_title", "IMPROVE", (-3905, -4346, 186), 94, "238 245 255 255"),
    ("iy_intro_subtitle", "-  B E N C H M A R K  -", (-3905, -4346, 126), 34, "0 178 255 255"),
    ("iy_intro_url", "www.improve-yourself.com", (-4000, -4346, 68), 28, "180 220 245 255"),
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


def _format_vector(values: tuple[float, float, float]) -> str:
    return " ".join(str(int(value)) if float(value).is_integer() else str(value) for value in values)


def _box_scales(box: Box) -> tuple[float, float, float]:
    x, y, z = box.half_extents
    # The cloned Hammer primitive is 512 x 512 x 2 units before baking.
    return x / 256, y / 256, z


def move_spawn_layout(text: str) -> str:
    inventory = {
        "info_player_start": [],
        "info_player_terrorist": [],
        "info_player_counterterrorist": [],
    }
    for start, end, block in entity_blocks(text):
        for classname in inventory:
            if f'"classname" "string" "{classname}"' in block:
                inventory[classname].append((start, end, block))

    if len(inventory["info_player_start"]) != 1:
        raise ValueError("expected exactly one info_player_start")
    if len(inventory["info_player_terrorist"]) != 16:
        raise ValueError("expected exactly sixteen terrorist spawns")
    if len(inventory["info_player_counterterrorist"]) != 16:
        raise ValueError("expected exactly sixteen counter-terrorist spawns")

    replacements: list[tuple[int, int, str]] = []
    player = inventory["info_player_start"][0]
    block = player[2]
    block = re.sub(r'"origin" "vector3" "[^"]+"', '"origin" "vector3" "-4000 -3675 64"', block, count=1)
    block = re.sub(r'"angles" "qangle" "[^"]+"', '"angles" "qangle" "0 -90 0"', block, count=1)
    replacements.append((player[0], player[1], block))

    team_xs = {
        "info_player_counterterrorist": (-4400, -4200, -3900, -3700),
        "info_player_terrorist": (-4300, -4100, -3800, -3600),
    }
    rows = ((-3852, 50), (-3972, 38), (-4092, 26), (-4212, 14))
    for classname, xs in team_xs.items():
        for index, (start, end, block) in enumerate(inventory[classname]):
            row = index // 4
            column = index % 4
            origin = (xs[column], rows[row][0], rows[row][1])
            block, origin_count = re.subn(
                r'"origin" "vector3" "[^"]+"',
                f'"origin" "vector3" "{_format_vector(origin)}"',
                block,
                count=1,
            )
            block, angle_count = re.subn(
                r'"angles" "qangle" "[^"]+"',
                '"angles" "qangle" "0 -90 0"',
                block,
                count=1,
            )
            if origin_count != 1 or angle_count != 1:
                raise ValueError(f"spawn transform missing for {classname} #{index}")
            replacements.append((start, end, block))

    for start, end, block in sorted(replacements, reverse=True):
        text = text[:start] + block + text[end:]
    return text


def move_existing_landmarks(text: str) -> str:
    replacements = {
        # Pull the former Ancient end wall behind the new Red Room focal area.
        '"origin" "vector3" "0 3072 192"': '"origin" "vector3" "0 3430 192"',
        # Align existing Inferno railings to the narrowed staircase.
        '"origin" "vector3" "-285 4050 70"': '"origin" "vector3" "-235 4050 70"',
        '"origin" "vector3" "285 4050 70"': '"origin" "vector3" "235 4050 70"',
    }
    for old, new in replacements.items():
        if text.count(old) != 1:
            raise ValueError(f"expected landmark transform exactly once: {old}")
        text = text.replace(old, new)
    return text


def shrink_inferno_steps(text: str) -> str:
    origins = ("0 3740 8", "0 3880 16", "0 4020 24", "0 4160 32", "0 4300 40")
    for origin in origins:
        for start, end, block in list(map_blocks(text)):
            if f'"origin" "vector3" "{origin}"' not in block:
                continue
            stream = re.compile(
                r'("name" "string" "position:0".*?"data" "vector3_array"\s*\[)(.*?)(\n\s*\])',
                re.DOTALL,
            )
            match = stream.search(block)
            if not match:
                raise ValueError(f"position stream missing for Inferno step at {origin}")

            def shrink(value: re.Match[str]) -> str:
                coordinates = [float(item) for item in value.group(1).split()]
                coordinates[0] *= 0.7
                return '"' + " ".join(f"{item:g}" for item in coordinates) + '"'

            data = re.sub(
                r'"([+-]?[\d.]+\s+[+-]?[\d.]+\s+[+-]?[\d.]+)"',
                shrink,
                match.group(2),
            )
            refined = block[: match.start(2)] + data + block[match.end(2) :]
            text = text[:start] + refined + text[end:]
            break
        else:
            raise ValueError(f"Inferno step mesh missing at {origin}")
    return text


def worldtext_template(text: str) -> str:
    marker = '"classname" "string" "point_worldtext"'
    marker_at = text.index(marker)
    start = text.rfind('"CMapEntity"', 0, marker_at)
    brace = text.index("{", start, marker_at)
    end = matching_delimiter(text, brace, "{", "}")
    return text[start : end + 1]


def specialize_worldtext(
    template: str,
    node_id: int,
    targetname: str,
    message: str,
    origin: tuple[float, float, float],
    font_size: int,
    color: str,
) -> str:
    # Reuse Hammer-safe entity cloning from the prop helper, then overwrite only
    # fields shared by point_worldtext. A harmless known model is temporary.
    # Calling specialize_prop is inappropriate because worldtext has no model;
    # specialize() is mesh-only, so clone IDs through its shared behavior by
    # directly importing the proven implementation here.
    import uuid

    mapping: dict[str, str] = {}

    def uuid_replacement(match: re.Match[str]) -> str:
        old = match.group(0)
        mapping.setdefault(old, str(uuid.uuid4()))
        return mapping[old]

    block = re.sub(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        uuid_replacement,
        template,
    )
    block = re.sub(r'("nodeID" "int" ")\d+(")', rf"\g<1>{node_id}\2", block, count=1)
    reference = uuid.uuid4().int & ((1 << 64) - 1)
    block = re.sub(
        r'("referenceID" "uint64" ")0x[0-9a-f]+(")',
        rf"\g<1>0x{reference:016x}\2",
        block,
        count=1,
    )
    fields = {
        "targetname": targetname,
        "message": message,
        "fullbright": "1",
        "color": color,
        "world_units_per_pixel": "0.25",
        "font_size": str(font_size),
        "font_name": "Arial Black",
        "justify_horizontal": "1",
        "justify_vertical": "1",
        "reorient_mode": "0",
    }
    for field, value in fields.items():
        block, count = re.subn(
            rf'("{re.escape(field)}" "string" ")[^"]*(")',
            rf"\g<1>{value}\2",
            block,
            count=1,
        )
        if count != 1:
            raise ValueError(f"point_worldtext field missing: {field}")
    block = re.sub(
        r'"origin" "vector3" "[^"]+"',
        f'"origin" "vector3" "{_format_vector(origin)}"',
        block,
        count=1,
    )
    block = re.sub(
        r'"angles" "qangle" "[^"]+"',
        '"angles" "qangle" "0 0 90"',
        block,
        count=1,
    )
    return block


def append_authored_content(text: str) -> str:
    array_start, array_end = world_children(text)
    mesh_start = text.index('"CMapMesh"', array_start, array_end)
    mesh_brace = text.index("{", mesh_start, array_end)
    mesh_end = matching_delimiter(text, mesh_brace, "{", "}") + 1
    primitive = text[mesh_start:mesh_end]
    prop = prop_template(text)
    label = worldtext_template(text)
    node_ids = [int(value) for value in re.findall(r'"nodeID" "int" "(\d+)"', text)]
    next_node = max(node_ids) + 1

    generated: list[str] = []
    for box in INTRO_BOXES + ANCIENT_BOXES + INFERNO_BOXES:
        block = specialize(
            primitive,
            next_node,
            box.name,
            box.origin,
            _box_scales(box),
            box.material,
        )
        generated.append(block)
        next_node += 1
    for _, model, origin, angles, scale in ADDED_PROPS:
        generated.append(specialize_prop(prop, next_node, model, origin, angles, scale))
        next_node += 1
    for targetname, message, origin, font_size, color in WORLD_TEXTS:
        generated.append(
            specialize_worldtext(label, next_node, targetname, message, origin, font_size, color)
        )
        next_node += 1

    indented = ["\t\t\t" + block.replace("\n", "\n\t\t\t") for block in generated]
    insertion = ",\n" + ",\n".join(indented) + "\n"
    return text[:array_end] + insertion + text[array_end:]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    text = args.input.read_text(encoding="utf-8")
    if "iy_intro_url" in text:
        raise SystemExit("benchmark world-sections upgrade already present")
    if '"origin" "vector3" "0 4500 700"' not in text:
        raise SystemExit("expected V1.2 refined Inferno enclosure is missing")
    if '"origin" "vector3" "-4000 -4000 -32"' not in text:
        raise SystemExit("expected V1.2 intro room is missing")

    text = move_spawn_layout(text)
    text = move_existing_landmarks(text)
    text = shrink_inferno_steps(text)
    text = append_authored_content(text)
    args.output.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
