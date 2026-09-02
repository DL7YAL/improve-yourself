import json
from pathlib import Path

from improve_yourself.tactical_minimap import load_tactical_minimap


def _verified_blank_document(map_id: str = "de_example") -> dict:
    return {
        "schema": "iy.map_overview_metadata/v1",
        "map_id": map_id,
        "asset": {"status": "NOT_INCLUDED", "reference": None},
        "canvas": {"width": 1024, "height": 1024},
        "transform": {
            "verification_status": "VERIFIED",
            "origin_world": {"x": -100.0, "y": 200.0},
            "world_units_per_pixel": 5.0,
            "world_x_to_canvas": "positive_x",
            "world_y_to_canvas": "negative_y",
            "rotation_deg_clockwise": 0,
        },
    }


def test_verified_metadata_becomes_a_blank_benchmark_minimap_with_real_projection(tmp_path: Path) -> None:
    (tmp_path / "de_example.json").write_text(json.dumps(_verified_blank_document()), encoding="utf-8")
    minimap = load_tactical_minimap("de_example", maps_root=tmp_path)
    assert minimap.status == "VERIFIED_BLANK"
    assert minimap.projection_available is True
    assert minimap.project(-100.0, 200.0) == (0.0, 0.0, True)
    assert minimap.project(5020.0, -4920.0) == (1024.0, 1024.0, True)


def test_unknown_or_unverified_maps_never_get_a_guessed_minimap(tmp_path: Path) -> None:
    assert load_tactical_minimap("de_missing", maps_root=tmp_path).status == "UNAVAILABLE"
    document = _verified_blank_document()
    document["transform"]["verification_status"] = "UNVERIFIED"
    (tmp_path / "de_example.json").write_text(json.dumps(document), encoding="utf-8")
    assert load_tactical_minimap("de_example", maps_root=tmp_path).status == "UNAVAILABLE"
