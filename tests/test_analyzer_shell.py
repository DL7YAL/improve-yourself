import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

from improve_yourself.analyzer_shell import (
    AnalyzerShellController,
    ShellPlayer,
    ShellResult,
    SIDEBAR_NAVIGATION,
    UI_REFERENCE_STATUS,
    analyzer_result_projection,
    analysis_profile_criteria_view,
    dashboard_layout_metrics,
    default_output_root,
    optimizer_domain_overview,
    optimizer_evidence_view,
    optimizer_product_view,
    optimizer_table_cell,
    optimizer_user_detail_sections,
    optimizer_visible_models,
    status_presentation,
    system_check_result_view,
    system_scan_home_view,
)


def test_analyzer_result_projection_repeats_only_workflow_facts_and_objective_anchors(tmp_path: Path) -> None:
    result = ShellResult(
        manifest_path=tmp_path / "demo-workflow.json", review_path=tmp_path / "review.html",
        players=(ShellPlayer("ct1", "CT One", "CT"), ShellPlayer("t1", "T One", "T")),
        selected_ids=(), selection_mode="full_demo", scene_count=2, map_id="de_ancient",
        source_demo_name="real.dem", source_sha256="a" * 64, status="READY_FOR_REVIEW",
        round_count=18, basic_event_count=3179, parser_status="PASS", profile_id="review_v1",
    )
    projection = analyzer_result_projection(result, {
        "source": {"sha256": "a" * 64},
        "scenes": [
            {"round_number": 2, "review": {"tick": 1200}, "anchor_types": ["KILL", "HEADSHOT"]},
            {"round_number": 4, "review": {"tick": 2400}, "anchor_types": ["KILL"]},
        ],
    })
    assert projection["scene_count"] == 2
    assert projection["anchor_summary"] == ({"anchor": "KILL", "count": 2}, {"anchor": "HEADSHOT", "count": 1})
    assert projection["situations"][0] == {"title": "Runde 2 · Tick 1200", "detail": "KILL, HEADSHOT"}
    with pytest.raises(ValueError, match="source differs"):
        analyzer_result_projection(result, {"source": {"sha256": "b" * 64}, "scenes": []})
from improve_yourself.local_profiles import built_in_profiles


def test_optimizer_product_view_is_domain_driven_read_only_and_accepts_synthetic_profile() -> None:
    from improve_yourself.optimizer_evidence import synthetic_system_matrix

    view = optimizer_product_view(synthetic_system_matrix()["systems"][36], internal_test=True)
    assert view["read_only"] is True
    assert view["internal_test"] is True
    assert set(view["domains"]) == {"SYSTEM_OPTIMIZER", "GRAPHICS_OPTIMIZER", "NETWORK_OPTIMIZER", "BIOS_OPTIMIZER"}
    assert view["counts"]["checked"] >= 5
    assert all(model["apply_available"] is False for model in view["models"])
    assert all(str(model["improve_recommendation"]).startswith("FIXTURE_ONLY") for model in view["models"])


def test_optimizer_evidence_view_keeps_missing_cs2_state_explicit() -> None:
    payload = {
        "schema": "iy.system_check/v1",
        "policy": {"read_only": True, "changes_applied": False},
        "checks": [
            {"id": "gpu", "evidence": {"adapters": [{"name": "AMD Radeon RX 7900 XTX", "driver_version": "24.10.1"}]}},
            {"id": "display", "evidence": {"refresh_rates_hz": [240]}},
            {"id": "memory", "evidence": {"total_gb": 32}},
        ],
    }
    view = optimizer_evidence_view(payload)
    assert view is not None
    assert view["profile_source"] == "READ_ONLY_SYSTEM_CHECK"
    assert view["performance_evidence"] == "NOT_MEASURED"
    assert "cs2.refresh_hz" in view["missing_input_data"]
    assert any(row["evidence_class"] == "CONDITIONAL" for row in view["rows"])


def test_packaged_windows_default_output_is_stable_and_user_writable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(os, "name", "nt")
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\tester\AppData\Local")
    assert default_output_root() == Path(
        r"C:\Users\tester\AppData\Local\Improve Yourself\Experimental\results"
    )


def test_experimental_shell_exposes_binding_product_sections_from_canonical_design_spec() -> None:
    assert tuple(UI_REFERENCE_STATUS) == (
        "Dashboard", "My Improvement", "Analyzer", "Reports",
        "System Check / Optimizer", "Settings", "Tactical Replay", "Benchmark",
    )
    assert UI_REFERENCE_STATUS["Analyzer"] == "IMPLEMENTED"
    assert UI_REFERENCE_STATUS["Tactical Replay"] == "IMPLEMENTED"
    assert "NEEDS_UI_REFERENCE" not in UI_REFERENCE_STATUS.values()
    assert UI_REFERENCE_STATUS["System Check / Optimizer"] == "IMPLEMENTED"
    assert UI_REFERENCE_STATUS["My Improvement"] == "IMPLEMENTED"
    assert UI_REFERENCE_STATUS["Benchmark"] == "IMPLEMENTED"
    assert "Demo Analyzer" not in SIDEBAR_NAVIGATION
    assert "Rules" not in SIDEBAR_NAVIGATION
    assert SIDEBAR_NAVIGATION == (
        "Dashboard", "Analyzer", "Tactical Replay", "My Improvement",
        "System Check / Optimizer", "Benchmark", "Reports", "Settings",
    )


def test_profile_criteria_view_is_semantic_and_reports_the_actual_profile_count() -> None:
    profiles = {profile.profile_id: profile for profile in built_in_profiles()}
    review = analysis_profile_criteria_view(profiles["review_v1"])
    highlight = analysis_profile_criteria_view(profiles["highlight_v1"])
    assert review == {"profile_id": "review_v1", "active": 7, "available": 7, "text": "Aktive Kriterien: 7 / 7"}
    assert highlight == {"profile_id": "highlight_v1", "active": 5, "available": 7, "text": "Aktive Kriterien: 5 / 7"}


def test_status_presentation_keeps_ready_conditional_unknown_and_warning_distinct() -> None:
    assert status_presentation("OK") == ("READY / OK", "ready")
    assert status_presentation("CONDITIONAL") == ("CONDITIONAL", "conditional")
    assert status_presentation("INSUFFICIENT_EVIDENCE") == ("UNKNOWN / NOT AVAILABLE", "unknown")
    assert status_presentation("ACTION_REQUIRED") == ("WARNING / ACTION REQUIRED", "warning")
    assert status_presentation("unrecognized") == ("UNKNOWN / NOT AVAILABLE", "unknown")


def test_optimizer_overview_keeps_four_areas_visible_and_does_not_claim_preview_capability() -> None:
    cards = optimizer_domain_overview()
    assert [card["title"] for card in cards] == [
        "System Optimizer", "Graphics Optimizer", "Network Optimizer", "BIOS Optimizer",
    ]
    assert all(card["state"].startswith("PREVIEW") for card in cards)
    assert "kein Apply" in cards[-1]["description"]


def test_optimizer_ui_keeps_master_grid_local_detail_scroll_and_domain_identity() -> None:
    source = (Path(__file__).parents[1] / "src" / "improve_yourself" / "analyzer_shell.py").read_text(encoding="utf-8")
    assert 'self.optimizer_domain_grid.columnconfigure(index, weight=1, uniform="optimizer-domains")' in source
    assert 'row=index // 2, column=index % 2' in source
    assert 'self.optimizer_detail_scroll_canvas = detail_canvas' in source
    assert '_OPTIMIZER_DOMAIN_ACCENTS[str(item["domain"])]' in source
    assert 'text="IMPROVE\\nYOURSELF"' in source
    assert 'text="LETZTER OPTIMIERUNGSLAUF"' in source
    assert 'self.system_canvas = None' in source


def test_optimizer_visible_models_filters_one_domain_without_reinterpreting_results() -> None:
    view = {
        "domains": {
            "SYSTEM_OPTIMIZER": [
                {"title": "Real System State", "status": "CONDITIONAL", "current_state": "Unknown", "improve_recommendation": "Read-only", "why_for_this_system": "Evidence missing"},
                {"title": "Already matched", "status": "ALREADY_RECOMMENDED", "current_state": "Enabled", "improve_recommendation": "Keep", "why_for_this_system": "Known local fact"},
            ],
            "GRAPHICS_OPTIMIZER": [{"title": "Other domain", "status": "RECOMMENDED"}],
        }
    }
    assert [item["title"] for item in optimizer_visible_models(view, "SYSTEM_OPTIMIZER")] == ["Real System State", "Already matched"]
    assert [item["title"] for item in optimizer_visible_models(view, "SYSTEM_OPTIMIZER", query="unknown")] == ["Real System State"]
    assert [item["title"] for item in optimizer_visible_models(view, "SYSTEM_OPTIMIZER", status_filter="ALREADY_RECOMMENDED")] == ["Already matched"]
    assert optimizer_visible_models(view, "NETWORK_OPTIMIZER") == ()


def test_optimizer_table_cell_preserves_short_values_and_marks_visual_truncation() -> None:
    assert optimizer_table_cell("KNOWN_STATE") == "KNOWN STATE"
    assert optimizer_table_cell("x" * 40, maximum=12) == "xxxxxxxxxxx…"


def test_optimizer_detail_sections_keep_unknowns_read_only_and_do_not_invent_an_action() -> None:
    insufficient = optimizer_user_detail_sections({
        "status": "INSUFFICIENT_EVIDENCE",
        "current_state": "UNKNOWN / NOT AVAILABLE",
        "what_can_change": "No measured effect.",
        "evidence_validity": {"record": "MISSING INPUT"},
    })
    assert "reicht" in insufficient["why"]
    assert insufficient["state"] == "Unbekannt"
    assert insufficient["evidence"] == "Vorhandene Evidenzdaten · technische Details verfügbar."
    assert "keine Änderung" in insufficient["change"]
    empty = optimizer_user_detail_sections(None)
    assert "keine Änderung" in empty["change"]


def test_dashboard_layout_keeps_cards_readable_without_global_scaling() -> None:
    wide = dashboard_layout_metrics(1400, 860)
    compact = dashboard_layout_metrics(900, 720)
    tall = dashboard_layout_metrics(1400, 1080)
    assert wide[0] is False
    assert compact[0] is True
    assert wide[1:] == (213, 284, 138, 22)
    assert tall[1] > wide[1]
    assert tall[2] > wide[2]
    assert tall[3] > wide[3]
    assert tall[4] > wide[4]


def test_system_scan_home_view_projects_existing_read_only_evidence_without_fake_values() -> None:
    payload = {
        "schema": "iy.system_check/v1", "generated_at_utc": "2026-08-21T12:00:00+00:00",
        "summary": {"OK": 5, "REVIEW": 1, "ACTION_REQUIRED": 0},
        "checks": [
            {"id": "cpu", "status": "OK", "summary": "CPU", "evidence": {"name": "Real CPU"}},
            {"id": "gpu", "status": "OK", "summary": "GPU", "evidence": {"adapters": [{"name": "Real GPU", "driver_version": "1.2.3"}]}},
            {"id": "memory", "status": "OK", "summary": "RAM", "evidence": {"total_gb": 32}},
            {"id": "windows", "status": "OK", "summary": "Windows", "evidence": {"caption": "Windows 11"}},
            {"id": "display", "status": "REVIEW", "summary": "Display", "evidence": {"refresh_rates_hz": [144]}},
        ],
    }
    view = system_scan_home_view(payload)
    assert view is not None
    assert view["entries"]["cpu"] == ("CPU", "Real CPU", "OK")
    assert view["entries"]["gpu"] == ("GPU", "Real GPU", "OK")
    assert view["entries"]["memory"] == ("RAM", "32 GB", "OK")
    assert view["entries"]["drivers"] == ("Treiber", "1.2.3", "OK")
    assert view["entries"]["display"] == ("Monitor", "144 Hz", "REVIEW")
    assert view["attention"] == "Hinweise: Monitor"


def test_system_scan_home_view_consumes_active_display_contract_without_legacy_projection() -> None:
    payload = {
        "schema": "iy.system_check/v1", "generated_at_utc": "2026-08-22T12:00:00+00:00",
        "summary": {"OK": 1, "REVIEW": 0, "ACTION_REQUIRED": 0},
        "checks": [
            {"id": "display", "status": "OK", "summary": "Display", "evidence": {"active_displays": [{"name": "Active output", "refresh_hz": 240}]}},
        ],
    }
    view = system_scan_home_view(payload)
    assert view is not None
    assert view["entries"]["display"] == ("Monitor", "240 Hz", "OK")


def test_system_scan_home_view_rejects_untrusted_or_missing_payloads() -> None:
    assert system_scan_home_view({}) is None
    assert system_scan_home_view({"schema": "iy.system_check/v1", "checks": "not-a-list"}) is None


def test_system_check_result_view_keeps_evidence_and_unknowns_separate() -> None:
    payload = {
        "schema": "iy.system_check/v1", "generated_at_utc": "2026-08-21T12:00:00+00:00",
        "summary": {"OK": 1, "REVIEW": 1, "ACTION_REQUIRED": 0},
        "policy": {"read_only": True, "changes_applied": False, "elevation_requested": False},
        "checks": [
            {"label": "CPU", "status": "OK", "summary": "CPU erkannt.", "evidence": {"name": "Real CPU", "logical_processors": 16}},
            {"label": "Secure Boot", "status": "REVIEW", "summary": "Status nicht sicher.", "evidence": {"enabled": None}},
        ],
    }
    view = system_check_result_view(payload)
    assert view is not None
    assert view["summary"] == {"OK": "1", "REVIEW": "1", "ACTION_REQUIRED": "0"}
    assert view["policy"] == "Read-only · keine Änderungen angewendet"
    assert view["rows"][0]["evidence"] == "name: Real CPU · logical_processors: 16"
    assert view["rows"][1]["evidence"] == "enabled: nicht sicher ermittelt"
    assert system_check_result_view({"schema": "iy.system_check/v1", "summary": {}, "checks": [], "policy": {}}) is None


def _write_result(root: Path, selected: tuple[str, ...] = (), source_hash: str = "a" * 64) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    roster = [
        {"player_id": "ct1", "display_name": "CT One", "initial_team": "CT"},
        {"player_id": "ct2", "display_name": "CT Two", "initial_team": "CT"},
        {"player_id": "t1", "display_name": "T One", "initial_team": "T"},
    ]
    source = {"sha256": source_hash, "map_id": "de_ancient", "tick_rate": 64.0, "parser": {"name": "awpy", "version": "2.0.2"}}
    flow = {
        "schema": "iy.analysis_flow/v1",
        "source": source,
        "roster": roster,
        "selection": {"mode": "player_select" if selected else "full_demo", "player_ids": list(selected)},
        "scenes": [{"scene_id": "one"}] if not selected or "ct1" in selected else [],
    }
    (root / "analysis-flow.json").write_text(json.dumps(flow), encoding="utf-8")
    (root / "analysis.json").write_text(json.dumps({"schema": "iy.analysis/v1", "source_sha256": source_hash}), encoding="utf-8")
    rounds = root / "replay-v2" / "rounds"
    rounds.mkdir(parents=True, exist_ok=True)
    chunk_path = rounds / "round-001.json.gz"
    with gzip.open(chunk_path, "wt", encoding="utf-8") as stream:
        json.dump({"schema": "iy.replay_round/v2", "round_number": 1, "frames": [{"tick": 1, "round_number": 1, "players": [], "utilities": [], "events": []}]}, stream)
    replay = {
        "schema": "iy.replay/v2", "source": source, "coordinate_space": "cs2_world",
        "players": [{"player_id": item["player_id"]} for item in roster],
        "rounds": [{"round_number": 1, "first_tick": 1, "last_tick": 1, "frame_count": 1, "chunk": "rounds/round-001.json.gz", "sha256": hashlib.sha256(chunk_path.read_bytes()).hexdigest()}],
        "capabilities": {name: "unavailable" for name in ("positions", "view_yaw", "view_pitch", "alive_state", "weapon_state", "velocity", "utility_lifetimes", "utility_trajectories", "flash_effect", "sound", "map_geometry")},
    }
    (root / "replay-v2" / "replay-v2.json").write_text(json.dumps(replay), encoding="utf-8")
    (root / "improve-match-data-v1.json").write_text(json.dumps({
        "schema": "iy.improve_match_data/v1",
        "metrics": {"source": {"sha256": source_hash}, "match": {"map_id": "de_ancient"}, "kills": [], "available_channels": [], "unavailable_channels": []},
        "validation": {"schema": "iy.validation_report/v1", "status": "PASS"},
        "replay": replay,
    }), encoding="utf-8")
    (root / "validation-report-v1.json").write_text(
        json.dumps({"schema": "iy.validation_report/v1", "status": "PASS"}), encoding="utf-8"
    )
    (root / "timeline.json").write_text(json.dumps({"source": source, "timeline": []}), encoding="utf-8")
    (root / "review.html").write_text("review", encoding="utf-8")
    (root / "cs2-review-commands.txt").write_text("demo_gototick 1\n", encoding="utf-8")
    manifest = {
        "schema": "iy.demo_workflow/v1",
        "status": "READY_FOR_REVIEW",
        "source_sha256": source_hash,
        "selection": flow["selection"],
        "counts": {"players": len(roster), "scenes": len(flow["scenes"])},
        "policy": {"real_demo_required": True, "fake_results": False, "local_only": True},
        "artifacts": {"analysis": "analysis.json", "replay_v2": "replay-v2/replay-v2.json", "improve_match_data": "improve-match-data-v1.json", "validation_report": "validation-report-v1.json", "analysis_flow": "analysis-flow.json", "timeline": "timeline.json", "review": "review.html", "cs2_review_commands": "cs2-review-commands.txt"},
    }
    path = root / "demo-workflow.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _write_preflight(root: Path) -> Path:
    path = _write_result(root)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["status"] = "READY_FOR_SELECTION"
    manifest["profile"] = None
    manifest["preflight"] = {
        "map_id": "de_ancient", "rounds": 1, "teams": {"CT": ["CT One", "CT Two"], "T": ["T One"]},
        "roster": [
            {"player_id": "ct1", "display_name": "CT One", "initial_team": "CT"},
            {"player_id": "ct2", "display_name": "CT Two", "initial_team": "CT"},
            {"player_id": "t1", "display_name": "T One", "initial_team": "T"},
        ],
        "parser_status": "PASS", "basic_event_count": 0,
    }
    manifest["counts"] = {"players": 3, "rounds": 1, "basic_events": 0, "scenes": 0}
    manifest["artifacts"] = {key: value for key, value in manifest["artifacts"].items() if key in {"analysis", "replay_v2", "improve_match_data", "validation_report"}}
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_shell_import_and_selection_reuse_existing_workflow(tmp_path: Path) -> None:
    demo = tmp_path / "match.dem"
    demo.write_bytes(b"real demo placeholder")
    calls: list[tuple[str, tuple[str, ...]]] = []

    def runner(source: Path, output: Path, *, max_bytes: int) -> Path:
        calls.append((source.name, ()))
        return _write_result(output / "run")

    def rerender(manifest: Path, *, player_ids: tuple[str, ...], profile) -> Path:
        calls.append(("rerender", player_ids))
        return _write_result(manifest.parent, player_ids)

    controller = AnalyzerShellController(tmp_path / "output", runner=runner, rerenderer=rerender)
    result = controller.import_demo(demo)
    assert result.map_id == "de_ancient"
    assert [player.display_name for player in result.players] == ["CT One", "CT Two", "T One"]

    controller.add_team("CT")
    controller.add_player("ct1")
    assert controller.selected_ids == ["ct1", "ct2"]
    assert [player.player_id for player in controller.available_players()] == ["t1"]
    selected = controller.analyze_selection()
    assert selected.selection_mode == "player_select"
    assert selected.selected_ids == ("ct1", "ct2")
    assert calls == [("match.dem", ()), ("rerender", ("ct1", "ct2"))]


def test_shell_import_stops_at_objective_preflight_before_analysis(tmp_path: Path) -> None:
    demo = tmp_path / "match.dem"
    demo.write_bytes(b"demo")
    calls: list[str] = []

    def runner(_source: Path, output: Path, *, max_bytes: int) -> Path:
        calls.append("preflight")
        return _write_preflight(output / "run")

    def rerender(manifest: Path, *, player_ids: tuple[str, ...], profile) -> Path:
        calls.append(f"analyze:{profile.profile_id}")
        return _write_result(manifest.parent, player_ids)

    controller = AnalyzerShellController(tmp_path / "output", runner=runner, rerenderer=rerender)
    preflight = controller.import_demo(demo)
    assert preflight.status == "READY_FOR_SELECTION"
    assert preflight.scene_count == 0
    assert preflight.basic_event_count == 0
    assert [player.display_name for player in preflight.players] == ["CT One", "CT Two", "T One"]
    assert calls == ["preflight"]
    review = controller.analyze_selection()
    assert review.status == "READY_FOR_REVIEW"
    assert calls == ["preflight", "analyze:review_v1"]


def test_shell_begin_import_clears_the_prior_workflow_until_the_new_parse_confirms(tmp_path: Path) -> None:
    manifest = _write_preflight(tmp_path / "run")
    demo = tmp_path / "match.dem"
    demo.write_bytes(b"demo")
    controller = AnalyzerShellController(tmp_path, runner=lambda *_args, **_kwargs: manifest)
    controller.import_demo(demo)
    controller.add_player("ct1")

    controller.begin_import()

    assert controller.result is None
    assert controller.selected_ids == []
    assert controller.selection_mode == "full_demo"
    with pytest.raises(RuntimeError, match="import a demo first"):
        controller.analyze_selection()


def test_shell_full_demo_reset_and_validation(tmp_path: Path) -> None:
    manifest = _write_result(tmp_path / "run")
    controller = AnalyzerShellController(tmp_path, runner=lambda *_args, **_kwargs: manifest)
    demo = tmp_path / "match.dem"
    demo.write_bytes(b"demo")
    controller.import_demo(demo)
    controller.add_player("t1")
    controller.set_full_demo()
    assert controller.selected_ids == []
    assert controller.selection_mode == "full_demo"
    controller.reset_players()
    assert controller.selection_mode == "player_select"
    with pytest.raises(ValueError, match="requires at least one"):
        controller.analyze_selection()
    with pytest.raises(ValueError, match="unknown player"):
        controller.add_player("missing")
    with pytest.raises(ValueError, match="team must"):
        controller.add_team("both")


def test_shell_rejects_non_demo_before_runner(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("no", encoding="utf-8")
    controller = AnalyzerShellController(tmp_path)
    with pytest.raises(ValueError, match="select a .dem"):
        controller.import_demo(source)


def test_shell_opens_validated_existing_workflow_without_runner(tmp_path: Path) -> None:
    manifest = _write_result(tmp_path / "run", ("ct1",))
    controller = AnalyzerShellController(
        tmp_path / "unused",
        runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not parse")),
    )
    result = controller.open_existing_workflow(manifest)
    assert result.map_id == "de_ancient"
    assert result.selection_mode == "player_select"
    assert controller.selected_ids == ["ct1"]


@pytest.mark.parametrize("mutation, message", [
    (lambda manifest: manifest.update(source_sha256="BAD"), "source_sha256"),
    (lambda manifest: manifest["artifacts"].update(review="../review.html"), "escapes workflow root"),
    (lambda manifest: manifest["artifacts"].pop("timeline"), "required artifact is missing"),
])
def test_shell_rejects_untrusted_existing_workflow(tmp_path: Path, mutation, message: str) -> None:
    path = _write_result(tmp_path / "run")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    mutation(manifest)
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        AnalyzerShellController(tmp_path).open_existing_workflow(path)


def test_shell_rejects_replay_hash_mismatch(tmp_path: Path) -> None:
    path = _write_result(tmp_path / "run")
    replay_path = path.parent / "replay-v2" / "replay-v2.json"
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    replay["source"]["sha256"] = "b" * 64
    replay_path.write_text(json.dumps(replay), encoding="utf-8")
    with pytest.raises(ValueError, match="replay source metadata differs"):
        AnalyzerShellController(tmp_path).open_existing_workflow(path)


def test_shell_links_explicit_matching_source_by_basename_only(tmp_path: Path) -> None:
    demo = tmp_path / "private" / "match.dem"
    demo.parent.mkdir()
    demo.write_bytes(b"matching real demo")
    source_hash = hashlib.sha256(demo.read_bytes()).hexdigest()
    manifest_path = _write_result(tmp_path / "run", source_hash=source_hash)
    controller = AnalyzerShellController(tmp_path)
    controller.open_existing_workflow(manifest_path)
    result = controller.link_source_demo(demo)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert result.source_demo_name == "match.dem"
    assert manifest["source_demo_name"] == "match.dem"
    assert str(demo.parent) not in manifest_path.read_text(encoding="utf-8")


def test_shell_rejects_source_hash_mismatch_without_modifying_manifest(tmp_path: Path) -> None:
    manifest_path = _write_result(tmp_path / "run")
    controller = AnalyzerShellController(tmp_path)
    controller.open_existing_workflow(manifest_path)
    before = manifest_path.read_bytes()
    demo = tmp_path / "wrong.dem"
    demo.write_bytes(b"wrong")
    with pytest.raises(ValueError, match="SHA-256 differs"):
        controller.link_source_demo(demo)
    assert manifest_path.read_bytes() == before
    assert not manifest_path.with_name("demo-workflow.json.tmp").exists()


def test_shell_revalidates_before_rerender_and_does_not_call_renderer_on_change(tmp_path: Path) -> None:
    manifest_path = _write_result(tmp_path / "run")
    called = False

    def rerenderer(_manifest: Path, *, player_ids: tuple[str, ...], profile) -> Path:
        nonlocal called
        called = True
        return manifest_path

    controller = AnalyzerShellController(tmp_path, rerenderer=rerenderer)
    controller.open_existing_workflow(manifest_path)
    (manifest_path.parent / "review.html").write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="review artifact is empty"):
        controller.analyze_selection()
    assert called is False


def test_shell_revalidates_before_review_boundary(tmp_path: Path) -> None:
    manifest_path = _write_result(tmp_path / "run")
    controller = AnalyzerShellController(tmp_path)
    controller.open_existing_workflow(manifest_path)
    flow_path = manifest_path.parent / "analysis-flow.json"
    flow_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="analysis flow source metadata differs"):
        controller.validate_current_workflow()
