import json
import shutil
from pathlib import Path

from improve_yourself.map_surfaces import MAP_SURFACE_SCHEMA, map_surface_status_presentation


ROOT = Path(__file__).parents[1]
ANCIENT_HASH = "55DA4F041436E50A4A788F2E1BBF5DE2652C20E621DFD89C3CA344C8139F3914"


def _root(tmp_path: Path) -> Path:
    overview_dir = tmp_path / "resources" / "map_overviews" / "maps"
    overview_dir.mkdir(parents=True)
    shutil.copy2(ROOT / "resources" / "map_overviews" / "maps" / "de_ancient.json", overview_dir / "de_ancient.json")
    surface_dir = tmp_path / "resources" / "map_surfaces" / "de_ancient"
    surface_dir.mkdir(parents=True)
    shutil.copy2(ROOT / "resources" / "map_surfaces" / "de_ancient" / "base_overlay.png", surface_dir / "base_overlay.png")
    return tmp_path


def _manifest(root: Path, **entry_changes: object) -> Path:
    entry = {
        "map_id": "de_ancient",
        "asset_path": "de_ancient/base_overlay.png",
        "sha256": ANCIENT_HASH,
        "image": {"format": "png", "width": 1024, "height": 1024},
        "asset_role": "base_overlay",
        "source_classification": "OWN_IMPROVE_CANVA",
        "distribution_status": "APPROVED_PRODUCT_ASSET",
        "provenance": "Original Improve Yourself Base Overlay created in Canva.",
        "presentation_only": True,
    }
    entry.update(entry_changes)
    manifest = root / "resources" / "map_surfaces" / "owned_base_overlays.v1.json"
    manifest.write_text(json.dumps({"schema": MAP_SURFACE_SCHEMA, "surfaces": [entry]}), encoding="utf-8")
    return manifest


def test_owned_ancient_surface_is_available_only_with_matching_verified_metadata(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _manifest(root)

    result = map_surface_status_presentation("de_ancient", repository_root=root)

    assert result.state == "AVAILABLE"
    assert result.map_id == "de_ancient"
    assert result.data_uri.startswith("data:image/png;base64,")
    assert result.transform is not None and result.transform["rotation_deg_clockwise"] == 0
    assert result.canvas == {"width": 1024, "height": 1024, "unit": "overview_pixel", "origin": "top_left", "x_direction": "right", "y_direction": "down"}


def test_missing_surface_does_not_make_another_map_available(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _manifest(root)

    assert map_surface_status_presentation("de_anubis", repository_root=root).state == "INVALID"
    assert map_surface_status_presentation("", repository_root=root).state == "UNKNOWN"


def test_invalid_overview_transform_fails_closed_without_a_second_transform_path(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _manifest(root)
    overview = root / "resources" / "map_overviews" / "maps" / "de_ancient.json"
    document = json.loads(overview.read_text(encoding="utf-8"))
    document["transform"]["rotation_deg_clockwise"] = 90
    overview.write_text(json.dumps(document), encoding="utf-8")

    assert map_surface_status_presentation("de_ancient", repository_root=root).state == "INVALID"


def test_missing_asset_and_integrity_mismatch_fail_closed(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _manifest(root)
    asset = root / "resources" / "map_surfaces" / "de_ancient" / "base_overlay.png"
    asset.unlink()
    assert map_surface_status_presentation("de_ancient", repository_root=root).state == "MISSING"

    shutil.copy2(ROOT / "resources" / "map_surfaces" / "de_ancient" / "base_overlay.png", asset)
    asset.write_bytes(asset.read_bytes() + b"changed")
    assert map_surface_status_presentation("de_ancient", repository_root=root).state == "INVALID"


def test_manifest_shape_and_path_traversal_fail_closed(tmp_path: Path) -> None:
    root = _root(tmp_path)
    manifest = _manifest(root, asset_path="../Cache.png")
    assert map_surface_status_presentation("de_ancient", repository_root=root).state == "INVALID"

    manifest.write_text(json.dumps({"schema": MAP_SURFACE_SCHEMA, "surfaces": [], "unknown": True}), encoding="utf-8")
    assert map_surface_status_presentation("de_ancient", repository_root=root).state == "INVALID"


def test_duplicate_surface_entries_and_non_canva_classification_fail_closed(tmp_path: Path) -> None:
    root = _root(tmp_path)
    manifest = _manifest(root)
    entry = json.loads(manifest.read_text(encoding="utf-8"))["surfaces"][0]
    manifest.write_text(json.dumps({"schema": MAP_SURFACE_SCHEMA, "surfaces": [entry, entry]}), encoding="utf-8")
    assert map_surface_status_presentation("de_ancient", repository_root=root).state == "INVALID"

    _manifest(root, source_classification="UNKNOWN")
    assert map_surface_status_presentation("de_ancient", repository_root=root).state == "INVALID"
