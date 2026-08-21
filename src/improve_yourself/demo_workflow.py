from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .analysis_flow import PlayerSelection, build_from_store, render_analysis_review
from .replay_builder import export_replay_v2
from .replay_store import ReplayStore
from .service import analyze


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_demo_workflow(demo: Path, output_root: Path, *, player_ids: tuple[str, ...] = (), max_bytes: int = 2_000_000_000) -> Path:
    demo = demo.resolve()
    if not demo.is_file():
        raise FileNotFoundError(f"demo does not exist: {demo}")
    source_hash = _sha256(demo)
    root = output_root.resolve() / source_hash[:12]
    root.mkdir(parents=True, exist_ok=True)
    analysis_path = analyze(demo, root / "analysis", max_bytes=max_bytes)
    replay_path = export_replay_v2(demo, analysis_path, root / "replay-v2")
    selection = PlayerSelection("player_select", tuple(dict.fromkeys(player_ids))) if player_ids else PlayerSelection()
    flow = build_from_store(ReplayStore(replay_path), selection)
    flow_path = root / "analysis-flow.json"
    flow_path.write_text(json.dumps(flow, ensure_ascii=False, indent=2), encoding="utf-8")
    timeline_path = root / "timeline.json"
    timeline_path.write_text(json.dumps({"source": flow["source"], "timeline": flow["timeline"]}, ensure_ascii=False, indent=2), encoding="utf-8")
    review_path = render_analysis_review(flow, root / "review.html")
    commands_path = root / "cs2-review-commands.txt"
    commands_path.write_text("\n".join(scene["review"]["command"] for scene in flow["scenes"]) + "\n", encoding="utf-8")
    artifacts = {
        "analysis": analysis_path.relative_to(root).as_posix(), "replay_v2": replay_path.relative_to(root).as_posix(),
        "analysis_flow": flow_path.name, "timeline": timeline_path.name, "review": review_path.name,
        "cs2_review_commands": commands_path.name,
    }
    manifest = {
        "schema": "iy.demo_workflow/v1", "status": "READY_FOR_REVIEW", "source_sha256": source_hash,
        "parser": flow["source"]["parser"], "selection": flow["selection"], "profile": flow["profile"],
        "counts": {"players": len(flow["roster"]), "indicators": len(flow["indicators"]), "rule_matches": len(flow["rule_matches"]), "scenes": len(flow["scenes"])},
        "artifacts": artifacts,
        "policy": {"real_demo_required": True, "fake_results": False, "automated_cheat_verdict": False, "local_only": True},
    }
    path = root / "demo-workflow.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run real CS2 demo -> Awpy -> scenes -> review")
    parser.add_argument("demo", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/demo-workflow"))
    parser.add_argument("--player", action="append", default=[])
    parser.add_argument("--max-mib", type=int, default=2048)
    args = parser.parse_args()
    if args.max_mib <= 0:
        parser.error("max-mib must be positive")
    try:
        print(run_demo_workflow(args.demo, args.output, player_ids=tuple(args.player), max_bytes=args.max_mib * 1024 * 1024))
    except (FileNotFoundError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
