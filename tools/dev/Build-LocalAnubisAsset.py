from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from improve_yourself.local_map_derivative import build_local_derivative


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an ignored local-only Anubis asset derivative")
    parser.add_argument("source_glb", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-build-id", required=True)
    parser.add_argument("--source-vpk-sha256", required=True)
    parser.add_argument("--reference-demo-sha256", required=True)
    args = parser.parse_args()
    result = build_local_derivative(args.source_glb, args.output)
    manifest = {
        "schema": "iy.map_asset/v1",
        "map_id": "de_anubis",
        "asset_version": f"local-cs2-{args.source_build_id}",
        "source_kind": "local_cs2_extraction",
        "source_build_id": args.source_build_id,
        "source_description": f"Local-only physics derivative from installed de_anubis.vpk sha256:{args.source_vpk_sha256}",
        "coordinate_space": "cs2_world",
        "units": "source_unit",
        "axis": {"x": "east-west", "y": "north-south", "z": "up"},
        "transform_to_replay": {"scale": 1.0, "rotation_deg": [0, 0, 0], "translation": [0, 0, 0]},
        "render_mesh": {"path": result["render_mesh"].name, "sha256": sha256(result["render_mesh"])},
        "visibility_mesh": {"path": result["visibility_mesh"].name, "sha256": sha256(result["visibility_mesh"])},
        "dynamic_geometry": "unsupported",
        "distribution": "local_only",
        "validation": {
            "status": "unverified",
            "reference_demo_sha256": args.reference_demo_sha256,
            "verified_at_utc": None,
        },
        "derivative": {
            "normal_world_nodes": result["normal_world_nodes"],
            "triangles": result["triangles"],
            "generated_at_utc": datetime.now(UTC).isoformat(),
        },
    }
    path = args.output / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
