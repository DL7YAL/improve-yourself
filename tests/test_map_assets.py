import hashlib
import json

from improve_yourself.map_assets import MAP_ASSET_SCHEMA, assess_map_asset


def _manifest(tmp_path, *, status="verified", distribution="local_only", map_id="de_anubis"):
    render = tmp_path / "render.mesh"
    visibility = tmp_path / "visibility.tri"
    render.write_bytes(b"render")
    visibility.write_bytes(b"visibility")
    payload = {
        "schema": MAP_ASSET_SCHEMA,
        "map_id": map_id,
        "asset_version": "test",
        "source_kind": "controlled_derivative",
        "source_build_id": "test-build",
        "source_description": "synthetic test fixture",
        "coordinate_space": "cs2_world",
        "units": "source_unit",
        "axis": {"x": "east-west", "y": "north-south", "z": "up"},
        "transform_to_replay": {"scale": 1.0, "rotation_deg": [0, 0, 0], "translation": [0, 0, 0]},
        "render_mesh": {"path": render.name, "sha256": hashlib.sha256(render.read_bytes()).hexdigest()},
        "visibility_mesh": {"path": visibility.name, "sha256": hashlib.sha256(visibility.read_bytes()).hexdigest()},
        "dynamic_geometry": "unsupported",
        "distribution": distribution,
        "validation": {"status": status, "reference_demo_sha256": "a" * 64, "verified_at_utc": "2026-08-20T00:00:00Z"},
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_verified_local_bundle_is_available(tmp_path) -> None:
    assert assess_map_asset(_manifest(tmp_path), "de_anubis").availability == "available"


def test_unverified_or_old_bundle_is_version_mismatch(tmp_path) -> None:
    result = assess_map_asset(_manifest(tmp_path, status="version_mismatch"), "de_anubis")
    assert result.availability == "version_mismatch"


def test_distribution_must_be_explicitly_allowed(tmp_path) -> None:
    result = assess_map_asset(_manifest(tmp_path, distribution="prohibited"), "de_anubis")
    assert result.availability == "distribution_blocked"


def test_wrong_map_is_unsupported(tmp_path) -> None:
    assert assess_map_asset(_manifest(tmp_path, map_id="de_mirage"), "de_anubis").availability == "unsupported_map"


def test_hash_mismatch_fails_integrity(tmp_path) -> None:
    path = _manifest(tmp_path)
    (tmp_path / "render.mesh").write_bytes(b"changed")
    assert assess_map_asset(path, "de_anubis").availability == "integrity_failed"


def test_path_escape_fails_integrity(tmp_path) -> None:
    path = _manifest(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["render_mesh"]["path"] = "../outside.mesh"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert assess_map_asset(path, "de_anubis").availability == "integrity_failed"
