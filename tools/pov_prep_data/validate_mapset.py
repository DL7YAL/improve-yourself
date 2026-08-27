"""Static fail-closed validation for the remaining 3D POV mapset handoffs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.map_overview_data.validate import load_and_validate as load_overview
from tools.pov_prep_data.validate import load_and_validate as load_prep

TARGET_MAPS = (
    "de_ancient", "de_dust2", "de_inferno", "de_nuke",
    "de_overpass", "de_train", "de_vertigo",
)
VERTICAL_MAPS = {"de_nuke", "de_train", "de_vertigo"}
RESOURCE_CLASSES = {
    "vmdl_c": "EXPECTED_FROM_SOURCE2_CONVENTION",
    "vrman_c": "UNKNOWN",
    "vphys_c": "UNKNOWN",
}
HANDOFF_HEADINGS = (
    "## KNOWN GOOD", "## LOCAL ACTIONS", "## DO NOT RESEARCH AGAIN",
    "## MUST VERIFY LOCALLY", "## STOP CONDITIONS", "## EXACT EXECUTION ORDER",
    "## EXPECTED OUTPUT ARTIFACTS", "## FINAL VIEWER COMMAND TEMPLATE",
)


class MapsetValidationError(ValueError):
    pass


def validate_map(root: Path, map_id: str) -> None:
    package = root / "resources" / "3d_pov" / map_id
    prep_path = package / "prep.json"
    handoff_path = package / "HANDOFF_V3.md"
    prep = load_prep(prep_path)
    if prep["map_id"] != map_id:
        raise MapsetValidationError(f"{map_id}: prep identity differs")
    overview_ref = prep["coordinate_contract"].get("overview_2d_reference")
    if not isinstance(overview_ref, dict):
        raise MapsetValidationError(f"{map_id}: 2D authority is missing")
    overview_path = root / str(overview_ref.get("repository_path"))
    overview = load_overview(overview_path)
    if overview["map_id"] != map_id:
        raise MapsetValidationError(f"{map_id}: 2D authority map differs")
    transform = prep["coordinate_contract"]["transform_to_replay"]
    if transform.get("status") != "EXPECTED_IDENTITY_PENDING_LOCAL_VALIDATION":
        raise MapsetValidationError(f"{map_id}: 3D transform is overclaimed")
    coordinate = prep["coordinate_contract"]
    expected_vertical = "KNOWN_PRESENT" if map_id in VERTICAL_MAPS else "NOT_DESIGNATED_VERTICAL_MAP"
    if coordinate.get("vertical_structure") != expected_vertical:
        raise MapsetValidationError(f"{map_id}: vertical structure differs")
    if coordinate.get("layer_thresholds_3d") != "UNRESOLVED_PENDING_LOCAL_GEOMETRY":
        raise MapsetValidationError(f"{map_id}: 3D layer thresholds must remain unresolved")
    candidate = prep["geometry_inventory"]["candidates"][0]
    resources = candidate.get("expected_resource_candidates")
    if not isinstance(resources, list) or len(resources) != 3:
        raise MapsetValidationError(f"{map_id}: resource candidates are incomplete")
    by_suffix = {str(item.get("path", "")).rsplit(".", 1)[-1]: item for item in resources if isinstance(item, dict)}
    for suffix, classification in RESOURCE_CLASSES.items():
        item = by_suffix.get(suffix)
        if item is None or item.get("path") != f"maps/{map_id}/world_physics.{suffix}" or item.get("classification") != classification:
            raise MapsetValidationError(f"{map_id}: {suffix} classification differs")
    replay = prep.get("provenance", {}).get("canonical_replay_source", {})
    if replay.get("status") not in {"KNOWN", "PARTIAL", "UNKNOWN"}:
        raise MapsetValidationError(f"{map_id}: replay provenance classification is invalid")
    redistribution = prep["redistribution"]
    if redistribution.get("bundled_proprietary_assets") is not False or "local_only" not in str(redistribution.get("notes")):
        raise MapsetValidationError(f"{map_id}: local-only boundary differs")
    handoff = handoff_path.read_text(encoding="utf-8")
    for heading in HANDOFF_HEADINGS:
        if heading not in handoff:
            raise MapsetValidationError(f"{map_id}: missing handoff section {heading}")
    if map_id not in handoff or "Run-AnubisViewerDemo.py" not in handoff or "--map-id" not in handoff and "builder" not in handoff.lower():
        raise MapsetValidationError(f"{map_id}: execution handoff is incomplete")


def validate_mapset(root: Path) -> None:
    for map_id in TARGET_MAPS:
        validate_map(root, map_id)
    forbidden = {".vpk", ".vmdl", ".vmdl_c", ".vrman_c", ".vphys", ".vphys_c", ".tri", ".glb", ".dem", ".zst", ".dll", ".exe"}
    for map_id in TARGET_MAPS:
        for path in (root / "resources" / "3d_pov" / map_id).rglob("*"):
            if path.is_file() and path.suffix.lower() in forbidden:
                raise MapsetValidationError(f"proprietary or executable artifact is bundled: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate remaining 3D POV mapset static preparation")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        validate_mapset(args.root)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))
    print("PASS remaining 3D POV mapset static preparation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
