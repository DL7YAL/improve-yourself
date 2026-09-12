"""Create a path-safe evidence manifest for a completed Windows CS2 run."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from validate_benchmark_runtime import validate_latest


CAPTURE_TARGETS = (
    ("intro", "benchmark_intro", "boot_delay", None),
    ("ancient_water", "ancient_b", "water_reflection", 27),
    ("ancient_red_room", "ancient_b", "red_room", 38),
    ("inferno_stairs", "inferno_apps_a", "stairs", 48),
    ("inferno_apps", "inferno_apps_a", "apps_details", 53),
)
ALLOWED_CAPTURE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tga"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def capture_record(key: str, scene: str, landmark: str, marker: int | None, path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"capture is missing for {key}: {path}")
    if path.suffix.lower() not in ALLOWED_CAPTURE_SUFFIXES:
        raise ValueError(f"unsupported capture extension for {key}: {path.suffix}")
    data = path.read_bytes()
    if not data:
        raise ValueError(f"capture is empty for {key}: {path}")
    stat = path.stat()
    return {
        "key": key,
        "scene": scene,
        "landmark": landmark,
        "expected_t": marker,
        "filename": path.name,
        "sha256": sha256(data),
        "size_bytes": len(data),
        "modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "visual_status": "UNREVIEWED",
    }


def build_manifest(log_path: Path, captures: dict[str, Path]) -> dict:
    log_data = log_path.read_bytes()
    validation = validate_latest(log_data.decode("utf-8", errors="replace"))
    if validation.status != "PASS":
        detail = "; ".join(validation.errors)
        raise ValueError(f"runtime log is not PASS: {detail}")

    expected_keys = {target[0] for target in CAPTURE_TARGETS}
    if set(captures) != expected_keys:
        missing = sorted(expected_keys - set(captures))
        extra = sorted(set(captures) - expected_keys)
        raise ValueError(f"capture keys mismatch; missing={missing}, extra={extra}")

    capture_records = [
        capture_record(key, scene, landmark, marker, captures[key])
        for key, scene, landmark, marker in CAPTURE_TARGETS
    ]
    hashes = [record["sha256"] for record in capture_records]
    if len(set(hashes)) != len(hashes):
        raise ValueError("capture files must have distinct SHA-256 values")

    return {
        "schema": "iy.cs2-benchmark-world-evidence/v1",
        "runtime": validation.as_dict(sha256(log_data)),
        "captures": capture_records,
        "visual_review_complete": False,
        "assignment_status": "PARTIAL",
        "notes": [
            "Raw log and capture paths are intentionally not stored.",
            "Hashes prove file identity, not visual correctness.",
            "A human or visual-review agent must replace every UNREVIEWED status.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Hash a complete Windows CS2 benchmark log and five captures."
    )
    parser.add_argument("--log", required=True, type=Path)
    for key, scene, landmark, marker in CAPTURE_TARGETS:
        help_text = f"Capture for {scene}/{landmark}"
        if marker is not None:
            help_text += f" at {marker}s"
        parser.add_argument(f"--{key.replace('_', '-')}", required=True, type=Path, help=help_text)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    captures = {
        key: getattr(args, key)
        for key, _, _, _ in CAPTURE_TARGETS
    }
    manifest = build_manifest(args.log, captures)
    output = args.output
    if not output.parent.is_dir():
        raise ValueError(f"output directory does not exist: {output.parent}")
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: wrote path-safe evidence manifest to {output}")
    print(f"runtime_log_sha256={manifest['runtime']['input_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
