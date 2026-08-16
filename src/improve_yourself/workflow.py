from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .replay import export_replay
from .service import analyze
from .system_check import run_system_check
from .viewer import render_viewer

WORKFLOW_SCHEMA = "iy.workflow/v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_workflow(
    demo: Path,
    output_root: Path,
    *,
    max_bytes: int = 2_000_000_000,
    max_frames: int = 256,
    radar_path: Path | None = None,
    pos_x: float = 0,
    pos_y: float = 0,
    scale: float = 1,
) -> Path:
    demo = demo.resolve()
    if not demo.is_file():
        raise FileNotFoundError(f"demo does not exist: {demo}")
    source_hash = _sha256(demo)
    run_directory = output_root.resolve() / source_hash[:12]
    run_directory.mkdir(parents=True, exist_ok=True)

    system_path = run_system_check(run_directory / "system-check.json")
    analysis_path = analyze(demo, run_directory / "analysis", max_bytes=max_bytes)
    replay_path = export_replay(demo, analysis_path, run_directory / "replay", max_frames=max_frames)
    viewer_path = render_viewer(
        replay_path, run_directory / "viewer.html", radar_path=radar_path,
        pos_x=pos_x, pos_y=pos_y, scale=scale,
    )

    artifacts = {
        "system_check": system_path.relative_to(run_directory).as_posix(),
        "analysis": analysis_path.relative_to(run_directory).as_posix(),
        "replay": replay_path.relative_to(run_directory).as_posix(),
        "viewer": viewer_path.relative_to(run_directory).as_posix(),
    }
    payload: dict[str, Any] = {
        "schema": WORKFLOW_SCHEMA,
        "status": "READY_FOR_REVIEW",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_sha256": source_hash,
        "policy": {
            "local_only": True,
            "system_check_read_only": True,
            "changes_applied": False,
            "automated_cheat_verdict": False,
        },
        "artifacts": artifacts,
        "review": {
            "required": True,
            "reason": "Automated markers and replay scenes require human context review.",
        },
    }
    manifest = run_directory / "workflow.json"
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the integrated local Improve Yourself V1 workflow")
    parser.add_argument("demo", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/workflow"))
    parser.add_argument("--max-mib", type=int, default=2048)
    parser.add_argument("--max-frames", type=int, default=256)
    parser.add_argument("--radar", type=Path)
    parser.add_argument("--pos-x", type=float, default=0)
    parser.add_argument("--pos-y", type=float, default=0)
    parser.add_argument("--scale", type=float, default=1)
    args = parser.parse_args()
    if args.max_mib <= 0:
        parser.error("max-mib must be positive")
    try:
        result = run_workflow(
            args.demo, args.output, max_bytes=args.max_mib * 1024 * 1024,
            max_frames=args.max_frames, radar_path=args.radar,
            pos_x=args.pos_x, pos_y=args.pos_y, scale=args.scale,
        )
    except (FileNotFoundError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
