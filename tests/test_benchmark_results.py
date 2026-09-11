from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from improve_yourself.benchmark_results import (
    BenchmarkResultStore,
    build_benchmark_result,
    export_benchmark_result,
    render_result_html,
)


MAP_HASH = "DBBE5A05C541D2AB47354449FC16A1495E6934E85734484CE6E09C2AE27D5645"
CONTROLLER_HASH = "0038BAACB132A907654E03FE3B42B27BF198D5D1A23F4F9F0D8C87B5DF16723E"
SETTINGS_HASH = "A" * 64


def controller_log() -> str:
    return "\n".join((
        "[IYBENCH] READY version=iy-benchmark/v1.2-candidate.2",
        "[IYBENCH] PASS_START type=warmup version=iy-benchmark/v1.2-candidate.2",
        "[IYBENCH] PASS_END type=warmup",
        "[IYBENCH] MEASUREMENT_STATUS status=unverified reason=client_commands_require_runtime_confirmation",
        "[IYBENCH] PASS_START type=measured version=iy-benchmark/v1.2-candidate.2",
        "[IYBENCH] CAPTURE_WINDOW pass=measured scene=nuke_outside landmark=yard_landmarks expected_t=9",
        "[IYBENCH] REPORT scene=nuke_outside",
        "[IYBENCH] CAPTURE_WINDOW pass=measured scene=ancient_b landmark=water_reflection expected_t=27",
        "[IYBENCH] CAPTURE_WINDOW pass=measured scene=ancient_b landmark=red_room expected_t=38",
        "[IYBENCH] REPORT scene=ancient_b",
        "[IYBENCH] CAPTURE_WINDOW pass=measured scene=inferno_apps_a landmark=stairs expected_t=48",
        "[IYBENCH] CAPTURE_WINDOW pass=measured scene=inferno_apps_a landmark=apps_details expected_t=53",
        "[IYBENCH] REPORT scene=inferno_apps_a",
        "[IYBENCH] PASS_END type=measured runtime_status=complete measurement_status=unverified",
    ))


def capture(*, run_id: str = "fixture-run-1", frames: int = 384) -> dict[str, object]:
    frame_ms = 64_000 / frames
    return {
        "schema": "iy.cs2_benchmark_capture/v1",
        "run_id": run_id,
        "captured_at_utc": "2026-09-07T16:39:55Z",
        "benchmark": {
            "version": "iy-benchmark/v1.2-candidate.2",
            "map_sha256": MAP_HASH,
            "controller_sha256": CONTROLLER_HASH,
            "pass_seconds": 64,
            "route": ["nuke_outside", "ancient_b", "inferno_apps_a"],
        },
        "graphics_profile": {
            "profile_id": "fixture-profile",
            "label": "Fixture Profile · Not Measured",
            "settings_sha256": SETTINGS_HASH,
        },
        "collector": {
            "collector_id": "fixture-collector",
            "collector_version": "v1",
            "process_name": "cs2.exe",
            "active_confirmation": True,
            "started_at_utc": "2026-09-07T16:39:55Z",
            "ended_at_utc": "2026-09-07T16:40:59Z",
        },
        "policy": {"local_only": True, "external_transfer": False},
        "samples": [
            {"sequence": index + 1, "elapsed_s": 64 * index / (frames - 1), "frametime_ms": frame_ms}
            for index in range(frames)
        ],
    }


def test_valid_external_capture_creates_standalone_metrics() -> None:
    result = build_benchmark_result(capture(), controller_log())
    assert result["schema"] == "iy.cs2_benchmark_result/v1"
    assert result["status"] == "VALID"
    assert result["validity"] == {
        "runtime_status": "complete",
        "collector_status": "VALID",
        "comparable": True,
        "errors": [],
    }
    assert result["metrics"]["sample_count"] == 384
    assert result["metrics"]["duration_s"] == 64
    assert result["metrics"]["average_fps"] == 6
    assert result["metrics"]["one_percent_low_fps"] == 6
    assert [scene["scene"] for scene in result["scenes"]] == ["nuke_outside", "ancient_b", "inferno_apps_a"]
    assert result["policy"] == {
        "local_only": True,
        "network_transfer": False,
        "optimizer_integration": False,
        "user_identity_stored": False,
        "sharing": "USER_INITIATED_SCREENSHOT_ONLY",
    }


def test_controller_marker_failure_is_invalid_and_drops_all_metrics() -> None:
    broken_log = controller_log().replace(
        "[IYBENCH] CAPTURE_WINDOW pass=measured scene=ancient_b landmark=red_room expected_t=38\n",
        "",
    )
    result = build_benchmark_result(capture(), broken_log)
    assert result["status"] == "INVALID"
    assert result["metrics"] is None
    assert result["scenes"] == []
    assert "measured capture windows" in " ".join(result["validity"]["errors"])


def test_inactive_collector_or_remote_policy_cannot_create_a_valid_result() -> None:
    inactive = capture(run_id="inactive")
    inactive["collector"]["active_confirmation"] = False
    result = build_benchmark_result(inactive, controller_log())
    assert result["status"] == "INVALID"
    assert "did not confirm" in " ".join(result["validity"]["errors"])

    remote = capture(run_id="remote")
    remote["policy"] = {"local_only": False, "external_transfer": True}
    result = build_benchmark_result(remote, controller_log())
    assert result["status"] == "INVALID"
    assert "local-only" in " ".join(result["validity"]["errors"])


def test_capture_must_match_the_exact_v12_map_and_controller() -> None:
    wrong_map = capture(run_id="wrong-map")
    wrong_map["benchmark"]["map_sha256"] = "C" * 64
    result = build_benchmark_result(wrong_map, controller_log())
    assert result["status"] == "INVALID"
    assert result["metrics"] is None
    assert "does not identify" in " ".join(result["validity"]["errors"])


def test_samples_must_cover_the_route_and_agree_with_frametime_duration() -> None:
    value = capture(run_id="bad-samples")
    value["samples"] = value["samples"][:100]
    result = build_benchmark_result(value, controller_log())
    assert result["status"] == "INVALID"
    assert result["metrics"] is None
    assert "fewer than 120" in " ".join(result["validity"]["errors"])


def test_collector_timestamps_must_cover_the_measured_pass() -> None:
    value = capture(run_id="short-collector")
    value["collector"]["ended_at_utc"] = "2026-09-07T16:40:05Z"
    result = build_benchmark_result(value, controller_log())
    assert result["status"] == "INVALID"
    assert result["metrics"] is None
    assert "collector timestamps" in " ".join(result["validity"]["errors"])


def test_local_top_ten_is_profile_bound_and_excludes_invalid_runs(tmp_path: Path) -> None:
    store = BenchmarkResultStore(tmp_path)
    slow = build_benchmark_result(capture(run_id="slow", frames=384), controller_log())
    fast_capture = capture(run_id="fast", frames=768)
    fast_capture["captured_at_utc"] = "2026-09-08T16:39:55Z"
    fast = build_benchmark_result(fast_capture, controller_log())
    invalid = build_benchmark_result(capture(run_id="invalid"), "missing controller evidence")
    other_capture = capture(run_id="other-profile")
    other_capture["graphics_profile"] = {
        "profile_id": "other-profile",
        "label": "Other Fixture Profile",
        "settings_sha256": "B" * 64,
    }
    other = build_benchmark_result(other_capture, controller_log())
    for result in (slow, fast, invalid, other):
        store.record(result)
    top = store.top(str(slow["comparison_key"]))
    assert [item["run_id"] for item in top] == ["fast", "slow"]
    assert all(item["status"] == "VALID" for item in top)
    assert store.top(str(other["comparison_key"]))[0]["run_id"] == "other-profile"
    with pytest.raises(ValueError, match="different content"):
        changed = deepcopy(slow)
        changed["captured_at_utc"] = "2026-09-09T00:00:00Z"
        store.record(changed)


def test_store_rejects_a_malformed_valid_result(tmp_path: Path) -> None:
    result = build_benchmark_result(capture(), controller_log())
    result["metrics"]["average_fps"] = None
    with pytest.raises(ValueError, match="positive finite number"):
        BenchmarkResultStore(tmp_path).record(result)


def test_unsafe_invalid_run_id_is_replaced_and_can_be_recorded(tmp_path: Path) -> None:
    value = capture()
    value["run_id"] = "../outside"
    result = build_benchmark_result(value, controller_log())
    destination = BenchmarkResultStore(tmp_path).record(result)
    assert result["status"] == "INVALID"
    assert str(result["run_id"]).startswith("invalid-capture-")
    assert destination.parent == tmp_path / "runs"


def test_record_repairs_a_missing_history_entry_after_interrupted_write(tmp_path: Path) -> None:
    store = BenchmarkResultStore(tmp_path)
    result = build_benchmark_result(capture(), controller_log())
    store.runs.mkdir(parents=True)
    (store.runs / "fixture-run-1.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    store.record(result)
    assert store.top(str(result["comparison_key"]))[0]["run_id"] == "fixture-run-1"


def test_export_writes_only_local_result_history_and_screenshot_page(tmp_path: Path) -> None:
    capture_path = tmp_path / "capture.json"
    log_path = tmp_path / "console.log"
    capture_path.write_text(json.dumps(capture(run_id="exported")), encoding="utf-8")
    log_path.write_text(controller_log(), encoding="utf-8")
    result_path, html_path, result = export_benchmark_result(
        capture_path,
        log_path,
        tmp_path / "benchmark-results",
        tmp_path / "benchmark-results" / "latest.html",
    )
    assert result["status"] == "VALID"
    assert result_path.exists()
    assert html_path.exists()
    page = html_path.read_text(encoding="utf-8")
    assert "PERSÖNLICHE LOKALE TOP 10" in page
    assert "USER_INITIATED_SCREENSHOT_ONLY" not in page
    assert "KEINE OPTIMIZER-VERBINDUNG" in page
    assert "discord" not in page.casefold()
    assert "steam-id" in page.casefold()
    assert "http://" not in page and "https://" not in page


def test_benchmark_module_has_no_optimizer_or_network_dependency() -> None:
    source = (Path(__file__).parents[1] / "src" / "improve_yourself" / "benchmark_results.py").read_text(encoding="utf-8")
    assert "from .optimizer" not in source
    assert "import improve_yourself.optimizer" not in source
    assert "requests" not in source
    assert "socket" not in source
    assert "urllib" not in source


def test_invalid_result_page_shows_no_measurement_values() -> None:
    result = build_benchmark_result(capture(run_id="invalid-page"), "")
    page = render_result_html(result, ())
    assert "NICHT ALS MESSUNG GÜLTIG" in page
    assert '<div class="metric">–</div>' in page
    assert "OPTIMIZER-VERBINDUNG" in page
