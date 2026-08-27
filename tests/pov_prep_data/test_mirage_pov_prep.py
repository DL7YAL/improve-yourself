from __future__ import annotations

import json
from pathlib import Path

from tools.pov_prep_data.validate import load_and_validate

ROOT = Path(__file__).resolve().parents[2]
RESOURCE_ROOT = ROOT / "resources" / "3d_pov"
PREP = RESOURCE_ROOT / "de_mirage" / "prep.json"
HANDOFF = RESOURCE_ROOT / "de_mirage" / "HANDOFF_V2.md"
BUILDER = ROOT / "tools" / "dev" / "Build-LocalAnubisAsset.py"


def test_mirage_prep_validates_without_claiming_local_verification() -> None:
    document = load_and_validate(PREP)
    assert document["map_id"] == "de_mirage"
    assert document["verification"]["status"] == "PREPARED_PENDING_LOCAL_VERIFICATION"
    assert document["reference_anchors"] == []
    assert document["coordinate_contract"]["transform_to_replay"]["status"] == "EXPECTED_IDENTITY_PENDING_LOCAL_VALIDATION"
    assert document["geometry_inventory"]["bundled_files"] == []


def test_mirage_resource_candidates_remain_explicit_and_non_invented() -> None:
    document = json.loads(PREP.read_text(encoding="utf-8"))
    resources = document["geometry_inventory"]["candidates"][0]["expected_resource_candidates"]
    by_path = {item["path"]: item for item in resources}
    assert by_path["maps/de_mirage/world_physics.vmdl_c"]["classification"] == "EXPECTED_FROM_SOURCE2_CONVENTION"
    assert by_path["maps/de_mirage/world_physics.vrman_c"]["classification"] == "UNKNOWN"
    assert by_path["maps/de_mirage/world_physics.vphys_c"]["classification"] == "UNKNOWN"


def test_mirage_handoff_keeps_canonical_runtime_and_local_only_boundary() -> None:
    handoff = HANDOFF.read_text(encoding="utf-8")
    for heading in ("## KNOWN GOOD", "## LOCAL ACTIONS", "## DO NOT RESEARCH AGAIN", "## MUST VERIFY LOCALLY", "## STOP CONDITIONS", "## EXACT EXECUTION ORDER", "## EXPECTED OUTPUT ARTIFACTS", "## FINAL VIEWER COMMAND TEMPLATE"):
        assert heading in handoff
    assert "iy.replay/v2 → ReplayStore → ReplayController → ReplayRendererSession → PandaReplayRenderer" in handoff
    assert "Run-AnubisViewerDemo.py" in handoff
    assert "local_only" in handoff
    assert "do not commit" in handoff.lower()


def test_generic_local_builder_requires_map_id_and_leaves_bounds_unverified() -> None:
    source = BUILDER.read_text(encoding="utf-8")
    assert 'parser.add_argument("--map-id", required=True)' in source
    assert '"map_id": args.map_id' in source
    assert '"geometry_bounds": {"status": "PENDING_LOCAL_MEASUREMENT"}' in source


def test_mirage_directory_contains_metadata_only() -> None:
    forbidden = {".vpk", ".vmdl", ".vmdl_c", ".vrman_c", ".vphys", ".vphys_c", ".tri", ".glb", ".dem", ".zst"}
    assert not any(path.is_file() and path.suffix.lower() in forbidden for path in (RESOURCE_ROOT / "de_mirage").rglob("*"))
