import base64
import hashlib
import json
from pathlib import Path

from improve_yourself import tactical_minimap
from improve_yourself.tactical_minimap import LOCAL_SURFACE_REGISTRATION, load_tactical_minimap


_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _projection(map_id: str = "de_example") -> dict:
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


def _write_projection(root: Path, document: dict | None = None) -> None:
    payload = document or _projection()
    (root / f"{payload['map_id']}.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_manifest(root: Path, *, digest: str, relative: str = "images/de_example.png") -> Path:
    manifest = root / "local-map-surfaces.json"
    manifest.write_text(json.dumps({
        "schema": "iy.local_test_map_surfaces/v1",
        "distribution": "LOCAL_ONLY",
        "surfaces": {"de_example": {
            "path": relative,
            "sha256": digest,
            "registration": LOCAL_SURFACE_REGISTRATION,
        }},
    }), encoding="utf-8")
    return manifest


def test_verified_projection_is_available_without_shipping_an_image(tmp_path: Path) -> None:
    _write_projection(tmp_path)
    minimap = load_tactical_minimap("de_example", maps_root=tmp_path)
    assert minimap.projection_available is True
    assert minimap.has_local_test_image is False
    assert minimap.project(-100.0, 200.0) == (0.0, 0.0, True)
    assert minimap.project(5020.0, -4920.0) == (1024.0, 1024.0, True)


def test_packaged_runtime_resolves_bundled_projection_metadata(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(tactical_minimap.sys, "_MEIPASS", str(tmp_path), raising=False)
    assert tactical_minimap.map_overview_root() == tmp_path / "resources" / "map_overviews" / "maps"


def test_unknown_or_unverified_map_never_gets_guessed_projection(tmp_path: Path) -> None:
    assert load_tactical_minimap("de_missing", maps_root=tmp_path).status == "UNAVAILABLE"
    assert load_tactical_minimap("de_../../private", maps_root=tmp_path).status == "UNAVAILABLE"
    document = _projection()
    document["transform"]["verification_status"] = "UNVERIFIED"
    _write_projection(tmp_path, document)
    assert load_tactical_minimap("de_example", maps_root=tmp_path).status == "UNAVAILABLE"


def test_sha_bound_local_only_png_is_accepted_as_presentation_only(tmp_path: Path) -> None:
    maps = tmp_path / "maps"
    maps.mkdir()
    _write_projection(maps)
    image = tmp_path / "images" / "de_example.png"
    image.parent.mkdir()
    image.write_bytes(_ONE_PIXEL_PNG)
    digest = hashlib.sha256(_ONE_PIXEL_PNG).hexdigest()
    minimap = load_tactical_minimap(
        "de_example", maps_root=maps,
        local_manifest_path=_write_manifest(tmp_path, digest=digest),
    )
    assert minimap.has_local_test_image is True
    assert minimap.local_surface is not None
    assert minimap.local_surface.path == image
    assert minimap.local_surface.sha256 == digest
    assert "nicht produktverifiziert" in minimap.detail


def test_changed_or_escaping_surface_fails_closed_to_image_free_projection(tmp_path: Path) -> None:
    maps = tmp_path / "maps"
    maps.mkdir()
    _write_projection(maps)
    image = tmp_path / "images" / "de_example.png"
    image.parent.mkdir()
    image.write_bytes(_ONE_PIXEL_PNG)
    rejected = load_tactical_minimap(
        "de_example", maps_root=maps,
        local_manifest_path=_write_manifest(tmp_path, digest="0" * 64),
    )
    assert rejected.projection_available is True
    assert rejected.has_local_test_image is False
    assert "SHA-256" in rejected.detail
    escaping = load_tactical_minimap(
        "de_example", maps_root=maps,
        local_manifest_path=_write_manifest(
            tmp_path, digest=hashlib.sha256(_ONE_PIXEL_PNG).hexdigest(), relative="../outside.png",
        ),
    )
    assert escaping.has_local_test_image is False
    assert "verlässt" in escaping.detail
