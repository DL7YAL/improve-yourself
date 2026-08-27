from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.pov_prep_data.validate_mapset import TARGET_MAPS, VERTICAL_MAPS, validate_mapset

ROOT = Path(__file__).resolve().parents[2]


def test_remaining_mapset_static_preparation_validates() -> None:
    validate_mapset(ROOT)


@pytest.mark.parametrize("map_id", TARGET_MAPS)
def test_each_map_is_pending_local_geometry_and_reuses_canonical_runtime(map_id: str) -> None:
    prep = json.loads((ROOT / "resources" / "3d_pov" / map_id / "prep.json").read_text(encoding="utf-8"))
    assert prep["canonical_runtime"] == {
        "replay_schema": "iy.replay/v2", "store": "ReplayStore",
        "playback_authority": "ReplayController", "data_hub": "AnalyzerDataHub",
        "owns_tick": False, "parses_demo": False, "embeds_replay_frames": False,
    }
    assert prep["geometry_inventory"]["runtime_asset_contract"] == "iy.map_asset/v1"
    assert prep["geometry_inventory"]["bundled_files"] == []
    assert prep["coordinate_contract"]["transform_to_replay"]["status"] == "EXPECTED_IDENTITY_PENDING_LOCAL_VALIDATION"
    assert prep["verification"]["status"] == "PREPARED_PENDING_LOCAL_VERIFICATION"


def test_vertical_maps_preserve_2d_provenance_without_claiming_3d_thresholds() -> None:
    for map_id in VERTICAL_MAPS:
        prep = json.loads((ROOT / "resources" / "3d_pov" / map_id / "prep.json").read_text(encoding="utf-8"))
        coordinate = prep["coordinate_contract"]
        assert coordinate["vertical_structure"] == "KNOWN_PRESENT"
        assert coordinate["layer_thresholds_3d"] == "UNRESOLVED_PENDING_LOCAL_GEOMETRY"
        assert coordinate["floor_model"]["status"] == "UNRESOLVED"
        overview = json.loads((ROOT / coordinate["overview_2d_reference"]["repository_path"]).read_text(encoding="utf-8"))
        assert overview["layers"]["status"] == "VERIFIED"


def test_only_ancient_has_partial_replay_provenance() -> None:
    statuses = {}
    for map_id in TARGET_MAPS:
        prep = json.loads((ROOT / "resources" / "3d_pov" / map_id / "prep.json").read_text(encoding="utf-8"))
        statuses[map_id] = prep["provenance"]["canonical_replay_source"]["status"]
    assert statuses["de_ancient"] == "PARTIAL"
    assert all(statuses[map_id] == "UNKNOWN" for map_id in TARGET_MAPS if map_id != "de_ancient")
