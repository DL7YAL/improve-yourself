import json
import struct

import pytest

from tools.map_generator.generate_collision_overlay import build_overlay, load_projection


def projection(path):
    path.write_text(json.dumps({"schema": "iy.map_overview_metadata/v1", "map_id": "de_test", "canvas": {"width": 100, "height": 100}, "transform": {"origin_world": {"x": 0, "y": 100}, "world_units_per_pixel": 1, "rotation_deg_clockwise": 0, "verification_status": "VERIFIED"}}), encoding="utf-8")
    return path


def triangle(path, values):
    path.write_bytes(struct.pack("<9f", *values))
    return path


def test_generates_deterministic_svg_from_horizontal_in_bounds_triangle(tmp_path):
    source = triangle(tmp_path / "ancient.tri", (10, 90, 2, 20, 90, 2, 10, 80, 2))
    result = build_overlay(source, projection(tmp_path / "projection.json"), tmp_path / "one.svg", grid_size=10)
    again = build_overlay(source, projection(tmp_path / "projection.json"), tmp_path / "two.svg", grid_size=10)
    assert result == again
    assert result.triangle_count == result.horizontal_triangle_count == result.in_bounds_triangle_count == 1
    assert result.occupied_cells == 1
    assert (tmp_path / "one.svg").read_text(encoding="utf-8") == (tmp_path / "two.svg").read_text(encoding="utf-8")
    assert "walkability" in (tmp_path / "one.svg").read_text(encoding="utf-8")


def test_omits_vertical_and_out_of_bounds_triangles(tmp_path):
    vertical = triangle(tmp_path / "vertical.tri", (10, 90, 0, 10, 90, 10, 10, 80, 0))
    result = build_overlay(vertical, projection(tmp_path / "projection.json"), tmp_path / "out.svg")
    assert result.horizontal_triangle_count == result.occupied_cells == 0
    outside = triangle(tmp_path / "outside.tri", (1000, 90, 0, 1010, 90, 0, 1000, 80, 0))
    result = build_overlay(outside, projection(tmp_path / "projection.json"), tmp_path / "out.svg")
    assert result.horizontal_triangle_count == 1
    assert result.in_bounds_triangle_count == result.occupied_cells == 0


def test_rejects_incomplete_triangles_and_unverified_projection(tmp_path):
    broken = tmp_path / "broken.tri"; broken.write_bytes(b"bad")
    with pytest.raises(ValueError, match="complete"):
        build_overlay(broken, projection(tmp_path / "projection.json"), tmp_path / "out.svg")
    document = json.loads(projection(tmp_path / "projection.json").read_text(encoding="utf-8"))
    document["transform"]["verification_status"] = "UNVERIFIED"
    (tmp_path / "projection.json").write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="VERIFIED"):
        load_projection(tmp_path / "projection.json")
