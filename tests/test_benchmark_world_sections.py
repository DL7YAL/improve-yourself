import hashlib
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
MAP_ROOT = ROOT / "assets" / "maps" / "improve_yourself_benchmark"
CONTROLLER = MAP_ROOT / "scripts" / "benchmark_controller.js"
MAP = MAP_ROOT / "maps" / "improve_yourself_benchmark.vmap"
AUTHORING_TOOL = ROOT / "tools" / "benchmark" / "upgrade_benchmark_world_sections.py"


def load_authoring_tool():
    sys.path.insert(0, str(AUTHORING_TOOL.parent))
    spec = importlib.util.spec_from_file_location("upgrade_benchmark_world_sections", AUTHORING_TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_world_build_keeps_locked_camera_controller_byte_identical() -> None:
    assert hashlib.sha256(CONTROLLER.read_bytes()).hexdigest() == (
        "0038baacb132a907654e03fe3b42b27bf198d5d1a23f4f9f0d8c87b5df16723e"
    )


def test_cinema_layout_has_four_rows_and_all_team_spawn_slots() -> None:
    tool = load_authoring_tool()
    seats = [
        box
        for box in tool.INTRO_BOXES
        if box.name.startswith("cinema_seat_") and not box.name.startswith("cinema_seat_back_")
    ]
    seat_backs = [box for box in tool.INTRO_BOXES if box.name.startswith("cinema_seat_back_")]
    risers = [box for box in tool.INTRO_BOXES if box.name.startswith("cinema_riser_")]
    assert len(seats) == 32
    assert len(seat_backs) == 32
    assert len(risers) == 4
    assert any(message == "www.improve-yourself.com" for _, message, *_ in tool.WORLD_TEXTS)


def test_added_world_props_remain_inside_existing_provenance_set() -> None:
    tool = load_authoring_tool()
    record = json.loads((MAP_ROOT / "TRANSITION_WORLDS_ASSET_PROVENANCE.json").read_text())
    provenanced = {asset["asset_path"] for asset in record["assets"]}
    assert {model for _, model, *_ in tool.ADDED_PROPS} <= provenanced


def test_hammer_saved_map_contains_cinema_brand_and_world_materials() -> None:
    map_bytes = MAP.read_bytes()
    required = (
        b"iy_intro_url",
        b"www.improve-yourself.com",
        b"materials/de_ancient/hr_ancient_wall_plaster_01_red_wet.vmat",
        b"materials/de_inferno/plaster/inferno_plaster_01_orange.vmat",
    )
    for marker in required:
        assert marker in map_bytes
