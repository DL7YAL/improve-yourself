from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .analysis_flow import AnalysisProfile, PlayerSelection, build_from_store, render_analysis_review
from .analyzer_core import (
    ANALYSIS_REQUEST_V1_SCHEMA,
    IMPROVE_MATCH_DATA_V1_SCHEMA,
    VALIDATION_REPORT_V1_SCHEMA,
    AnalysisRequestV1,
    AnalyzerCore,
)
from .importer import materialize_demo, validate_source
from .replay_builder import export_replay_v2
from .replay_store import ReplayStore, validate_store
from .service import analyze
from .validation import validate_analysis_payload
from .viewer import render_viewer


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _timing_payload(start: float, phases: dict[str, float]) -> dict[str, Any]:
    """Persist only actual local monotonic phase measurements, never estimates."""
    return {
        "schema": "iy.demo_timing/v1",
        "clock": "time.monotonic",
        "phases": {
            phase: {"monotonic_seconds": value, "elapsed_seconds": round(value - start, 6)}
            for phase, value in phases.items()
        },
    }


def _validate_reusable_workflow(path: Path, source_hash: str) -> bool:
    """Return true only for an intact, hash-bound local workflow.

    This deliberately validates the replay store (including every chunk hash)
    before reuse. A missing, incompatible, or modified artifact falls through to
    the normal fresh import path instead of becoming a best-effort cache hit.
    """
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest.get("schema") != "iy.demo_workflow/v1":
            return False
        if manifest.get("source_sha256") != source_hash:
            return False
        if manifest.get("status") not in {"READY_FOR_SELECTION", "READY_FOR_REVIEW"}:
            return False
        parser = manifest.get("parser")
        if not isinstance(parser, dict) or parser != {"name": "awpy", "version": "2.0.2"}:
            return False
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, dict):
            return False
        root = path.parent.resolve()

        def artifact(name: str) -> Path:
            value = artifacts.get(name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"missing artifact: {name}")
            candidate = (root / value).resolve()
            if root not in candidate.parents or not candidate.is_file() or candidate.stat().st_size <= 0:
                raise ValueError(f"invalid artifact: {name}")
            return candidate

        analysis_path = artifact("analysis")
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        if validate_analysis_payload(analysis) or analysis.get("source_sha256") != source_hash:
            return False
        replay_path = artifact("replay_v2")
        store_summary = validate_store(replay_path)
        if store_summary.get("source_sha256") != source_hash:
            return False
        match_data = json.loads(artifact("improve_match_data").read_text(encoding="utf-8"))
        validation = json.loads(artifact("validation_report").read_text(encoding="utf-8"))
        if (
            match_data.get("schema") != IMPROVE_MATCH_DATA_V1_SCHEMA
            or match_data.get("metrics", {}).get("source", {}).get("sha256") != source_hash
            or validation.get("schema") != VALIDATION_REPORT_V1_SCHEMA
            or validation.get("status") != "PASS"
        ):
            return False
        if manifest["status"] == "READY_FOR_REVIEW":
            for name in ("analysis_flow", "timeline", "review", "cs2_review_commands", "report"):
                artifact(name)
            flow = json.loads(artifact("analysis_flow").read_text(encoding="utf-8"))
            timeline = json.loads(artifact("timeline").read_text(encoding="utf-8"))
            if flow.get("source", {}).get("sha256") != source_hash or timeline.get("source", {}).get("sha256") != source_hash:
                return False
            hashes = manifest.get("artifact_sha256")
            if not isinstance(hashes, dict): return False
            for name in ("review",):
                artifact_path = artifact(name)
                if hashes.get(name) != _sha256(artifact_path): return False
    except (FileNotFoundError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return False
    return True


def _write_flow_artifacts(
    root: Path, replay_path: Path, selection: PlayerSelection, profile: AnalysisProfile = AnalysisProfile()
) -> tuple[dict, dict]:
    flow = build_from_store(ReplayStore(replay_path), selection, profile)
    flow_path = root / "analysis-flow.json"
    flow_path.write_text(json.dumps(flow, ensure_ascii=False, indent=2), encoding="utf-8")
    timeline_path = root / "timeline.json"
    timeline_path.write_text(
        json.dumps({"source": flow["source"], "timeline": flow["timeline"]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    review_path = render_analysis_review(flow, root / "review.html")
    commands_path = root / "cs2-review-commands.txt"
    commands_path.write_text("\n".join(scene["review"]["command"] for scene in flow["scenes"]) + "\n", encoding="utf-8")
    report_path = root / "report.json"
    report_path.write_text(json.dumps({
        "schema": "iy.analysis_report/v1", "source": flow["source"], "selection": flow["selection"],
        "profile": flow["profile"], "rounds": flow["rounds"],
        "counts": {"players": len(flow["roster"]), "indicators": len(flow["indicators"]), "rule_matches": len(flow["rule_matches"]), "scenes": len(flow["scenes"])},
        "scenes": flow["scenes"],
        "interpretation_boundary": "Scenes match selected criteria; interpretation remains with the user.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    artifacts = {
        "analysis_flow": flow_path.name,
        "timeline": timeline_path.name,
        "review": review_path.name,
        "cs2_review_commands": commands_path.name,
        "report": report_path.name,
    }
    return flow, artifacts


def ensure_tactical_replay_export(manifest_path: Path) -> Path:
    """Render the legacy HTML Tactical export only when a user asks for it.

    The native Tactical view already consumes ``analysis-flow.json`` and
    ``iy.replay/v2`` directly. This keeps the browser-only fallback out of the
    synchronous analysis path while retaining the existing export capability.
    """
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "iy.demo_workflow/v1" or manifest.get("status") != "READY_FOR_REVIEW":
        raise ValueError("workflow is not ready for a tactical export")
    root = manifest_path.parent
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("workflow artifacts must be an object")
    replay_relative = artifacts.get("replay_v2")
    flow_relative = artifacts.get("analysis_flow")
    if not isinstance(replay_relative, str) or not isinstance(flow_relative, str):
        raise ValueError("workflow lacks canonical replay or analysis flow")
    replay_path = (root / replay_relative).resolve()
    flow_path = (root / flow_relative).resolve()
    if root not in replay_path.parents or root not in flow_path.parents:
        raise ValueError("workflow artifact escapes root")
    flow = json.loads(flow_path.read_text(encoding="utf-8"))
    source_hash = manifest.get("source_sha256")
    if flow.get("source", {}).get("sha256") != source_hash:
        raise ValueError("analysis flow source differs from workflow")
    tactical_path = root / "tactical-replay.html"
    render_viewer(replay_path, tactical_path, scenes=flow.get("scenes", []))
    artifacts["tactical_replay"] = tactical_path.name
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return tactical_path


def preflight_demo_workflow(demo: Path, output_root: Path, *, max_bytes: int = 2_000_000_000) -> Path:
    started = time.monotonic()
    phases = {"T0_DEMO_SELECTED": started}
    demo = demo.resolve()
    validate_source(demo, max_bytes)
    phases["T1_TYPE_AND_SIZE_VALIDATED"] = time.monotonic()
    source_hash = _sha256(demo)
    phases["T2_SHA256_COMPLETE"] = time.monotonic()
    root = output_root.resolve() / source_hash[:12]
    reusable = root / "demo-workflow.json"
    if reusable.is_file() and _validate_reusable_workflow(reusable, source_hash):
        return reusable
    root.mkdir(parents=True, exist_ok=True)
    with materialize_demo(demo, max_bytes=max_bytes) as demo_path:
        phases["T3_AWPY_PARSE_STARTED"] = time.monotonic()
        request = AnalysisRequestV1.create(demo)
        prepared = AnalyzerCore().prepare(
            request, parser_path=demo_path, source_sha256=source_hash, source_name=demo.name
        )
        phases["T4_AWPY_PARSE_COMPLETE"] = time.monotonic()
        analysis_path = analyze(
            demo, root / "analysis", max_bytes=max_bytes, source_sha256=source_hash, core_result=prepared
        )
        replay_path = export_replay_v2(
            demo, analysis_path, root / "replay-v2", source_sha256=source_hash, parsed_demo=prepared.parsed_demo
        )
    replay_manifest = json.loads(replay_path.read_text(encoding="utf-8"))
    match_data = AnalyzerCore().finalize(prepared, replay_manifest)
    match_data_path = root / "improve-match-data-v1.json"
    match_data_path.write_text(json.dumps(match_data, ensure_ascii=False, indent=2), encoding="utf-8")
    validation_path = root / "validation-report-v1.json"
    validation_path.write_text(json.dumps(prepared.validation_report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    store = ReplayStore(replay_path)
    chunks = [store.load_round(number) for number in store.round_numbers]
    teams: dict[str, set[str]] = {"CT": set(), "T": set()}
    initial: dict[str, str] = {}
    event_count = 0
    for chunk in chunks:
        for frame in chunk["frames"]:
            event_count += len(frame.get("events", []))
            for state in frame.get("players", []):
                if state.get("team") in teams:
                    initial.setdefault(state["player_id"], state["team"])
    roster = [{
        "player_id": player["player_id"], "display_name": player.get("display_name") or player["player_id"],
        "initial_team": initial.get(player["player_id"], "unknown"),
    } for player in store.manifest["players"]]
    for player in roster:
        if player["initial_team"] in teams:
            teams[player["initial_team"]].add(player["display_name"])
    artifacts = {
        "analysis": analysis_path.relative_to(root).as_posix(), "replay_v2": replay_path.relative_to(root).as_posix(),
        "improve_match_data": match_data_path.name, "validation_report": validation_path.name,
    }
    phases["T5_REPLAY_V2_WRITTEN_AND_VALIDATED"] = time.monotonic()
    phases["T6_WORKFLOW_READY_FOR_SELECTION"] = time.monotonic()
    manifest = {
        "schema": "iy.demo_workflow/v1", "status": "READY_FOR_SELECTION", "source_sha256": source_hash,
        "source_demo_name": demo.name,
        "analysis_request": request.to_dict(),
        "parser": store.manifest["source"]["parser"], "selection": {"mode": "full_demo", "player_ids": []},
        "profile": None,
        "preflight": {"map_id": store.manifest["source"]["map_id"], "rounds": len(store.round_numbers),
                      "teams": {side: sorted(names) for side, names in teams.items()}, "roster": roster,
                      "parser_status": "PASS", "basic_event_count": event_count},
        "counts": {"players": len(roster), "rounds": len(store.round_numbers), "basic_events": event_count, "scenes": 0},
        "artifacts": artifacts,
        "timing": _timing_payload(started, phases),
        "policy": {"real_demo_required": True, "fake_results": False, "automated_cheat_verdict": False, "local_only": True},
    }
    path = root / "demo-workflow.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_demo_workflow(demo: Path, output_root: Path, *, player_ids: tuple[str, ...] = (), max_bytes: int = 2_000_000_000) -> Path:
    manifest = preflight_demo_workflow(demo, output_root, max_bytes=max_bytes)
    return rerender_demo_workflow(manifest, player_ids=player_ids)


def rerender_demo_workflow(
    manifest_path: Path, *, player_ids: tuple[str, ...] = (), profile: AnalysisProfile = AnalysisProfile()
) -> Path:
    started = time.monotonic()
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "iy.demo_workflow/v1":
        raise ValueError("expected iy.demo_workflow/v1 manifest")
    root = manifest_path.parent
    replay_path = root / manifest["artifacts"]["replay_v2"]
    selection = PlayerSelection("player_select", tuple(dict.fromkeys(player_ids))) if player_ids else PlayerSelection()
    flow, flow_artifacts = _write_flow_artifacts(root, replay_path, selection, profile)
    manifest["status"] = "READY_FOR_REVIEW"
    manifest["selection"] = flow["selection"]
    manifest["profile"] = flow["profile"]
    manifest["counts"] = {
        "players": len(flow["roster"]),
        "indicators": len(flow["indicators"]),
        "rule_matches": len(flow["rule_matches"]),
        "scenes": len(flow["scenes"]),
    }
    manifest["artifacts"].update(flow_artifacts)
    manifest["artifact_sha256"] = {"review": _sha256(root / flow_artifacts["review"])}
    timing = manifest.get("timing")
    if isinstance(timing, dict):
        phases = dict(timing.get("phases", {}))
        phases["T7_ANALYSIS_READY_FOR_REVIEW"] = {
            "monotonic_seconds": time.monotonic(), "elapsed_seconds": round(time.monotonic() - started, 6)
        }
        timing["analysis"] = {"clock": "time.monotonic", "phases": {"T7_ANALYSIS_READY_FOR_REVIEW": phases["T7_ANALYSIS_READY_FOR_REVIEW"]}}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


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
