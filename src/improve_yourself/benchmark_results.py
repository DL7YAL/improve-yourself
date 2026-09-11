"""Standalone, local-only CS2 benchmark result validation and history.

The benchmark is deliberately independent from Analyzer, Replay, System Check
and Optimizer.  It accepts only explicit local artifacts, never discovers or
uploads results, and never turns a measurement into a recommendation.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4


CAPTURE_SCHEMA = "iy.cs2_benchmark_capture/v1"
RESULT_SCHEMA = "iy.cs2_benchmark_result/v1"
HISTORY_SCHEMA = "iy.cs2_benchmark_history/v1"
BENCHMARK_VERSION = "iy-benchmark/v1.2-candidate.2"
EXPECTED_MAP_SHA256 = "DBBE5A05C541D2AB47354449FC16A1495E6934E85734484CE6E09C2AE27D5645"
EXPECTED_CONTROLLER_SHA256 = "0038BAACB132A907654E03FE3B42B27BF198D5D1A23F4F9F0D8C87B5DF16723E"
PASS_SECONDS = 64.0
ROUTE = ("nuke_outside", "ancient_b", "inferno_apps_a")
SCENE_WINDOWS = (
    ("nuke_outside", 0.0, 22.0),
    ("ancient_b", 22.0, 43.0),
    ("inferno_apps_a", 43.0, 64.0),
)
CAPTURE_WINDOWS = (
    ("nuke_outside", "yard_landmarks", 9.0),
    ("ancient_b", "water_reflection", 27.0),
    ("ancient_b", "red_room", 38.0),
    ("inferno_apps_a", "stairs", 48.0),
    ("inferno_apps_a", "apps_details", 53.0),
)

_HASH = re.compile(r"^[0-9a-fA-F]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_RESULT_FIELDS = {
    "schema",
    "run_id",
    "captured_at_utc",
    "status",
    "validity",
    "benchmark",
    "graphics_profile",
    "collector",
    "controller_validation",
    "metrics",
    "scenes",
    "comparison_key",
    "policy",
}
_RESULT_POLICY = {
    "local_only": True,
    "network_transfer": False,
    "optimizer_integration": False,
    "user_identity_stored": False,
    "sharing": "USER_INITIATED_SCREENSHOT_ONLY",
}
_HISTORY_FIELDS = {
    "run_id",
    "captured_at_utc",
    "status",
    "comparison_key",
    "benchmark_version",
    "profile_id",
    "profile_label",
    "average_fps",
    "one_percent_low_fps",
    "mean_frametime_ms",
}


class ResultStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"


def _utc(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"{field} must be a safe identifier")
    return value


def _hash(value: object, field: str) -> str:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise ValueError(f"{field} must be a SHA-256 digest")
    return value.upper()


def _mapping(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _exact_fields(value: dict[str, Any], expected: set[str], field: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{field} must contain exactly: {', '.join(sorted(expected))}")


def _latest_controller_session(log_text: str) -> tuple[list[str], list[str]]:
    markers = [line.split("[IYBENCH]", 1)[1].strip().strip('"') for line in log_text.splitlines() if "[IYBENCH]" in line]
    ready_indexes = [index for index, line in enumerate(markers) if line.startswith("READY version=")]
    if not ready_indexes:
        return [], ["controller log has no READY marker"]
    return markers[ready_indexes[-1]:], []


def _validate_controller_log(log_text: str, benchmark_version: str) -> tuple[dict[str, object], list[str]]:
    session, errors = _latest_controller_session(log_text)
    if errors:
        return {"marker_count": 0}, errors
    expected_ready = f"READY version={benchmark_version}"
    if session[0] != expected_ready:
        errors.append("controller READY version differs from the capture")
    if f"PASS_START type=measured version={benchmark_version}" not in session:
        errors.append("measured pass start is missing")
    final_marker = "PASS_END type=measured runtime_status=complete measurement_status=unverified"
    if final_marker not in session:
        errors.append("measured pass did not end with complete runtime status")
    if any(line.startswith("ERROR ") for line in session):
        errors.append("controller emitted an IYBENCH error")

    actual_windows: list[tuple[str, str, float]] = []
    for line in session:
        match = re.fullmatch(
            r"CAPTURE_WINDOW pass=measured scene=([^ ]+) landmark=([^ ]+) expected_t=([0-9.]+)",
            line,
        )
        if match:
            actual_windows.append((match.group(1), match.group(2), float(match.group(3))))
    if tuple(actual_windows) != CAPTURE_WINDOWS:
        errors.append("measured capture windows are missing, duplicated or out of order")

    reports = tuple(
        match.group(1)
        for line in session
        if (match := re.fullmatch(r"REPORT scene=([^ ]+)", line))
    )
    if reports != ROUTE:
        errors.append("scene reports are missing, duplicated or out of order")
    return {
        "marker_count": len(session),
        "ready": session[0] == expected_ready,
        "runtime_status": "complete" if final_marker in session else "incomplete",
        "controller_measurement_status": "unverified",
        "capture_windows": [
            {"scene": scene, "landmark": landmark, "expected_time_s": expected}
            for scene, landmark, expected in actual_windows
        ],
        "scene_reports": list(reports),
    }, errors


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _metrics(frametimes: list[float]) -> dict[str, object]:
    count = len(frametimes)
    total_ms = sum(frametimes)
    slow_count = max(1, math.ceil(count * 0.01))
    slowest = sorted(frametimes, reverse=True)[:slow_count]
    return {
        "sample_count": count,
        "duration_s": round(total_ms / 1000.0, 3),
        "average_fps": round(1000.0 * count / total_ms, 3),
        "one_percent_low_fps": round(1000.0 / (sum(slowest) / slow_count), 3),
        "frametime_ms": {
            "mean": round(total_ms / count, 3),
            "p95": round(_percentile(frametimes, 0.95), 3),
            "p99": round(_percentile(frametimes, 0.99), 3),
            "maximum": round(max(frametimes), 3),
        },
    }


def _validate_samples(value: object) -> tuple[list[dict[str, float | int]], list[str]]:
    errors: list[str] = []
    if not isinstance(value, list):
        return [], ["samples must be a list"]
    samples: list[dict[str, float | int]] = []
    for index, item in enumerate(value, 1):
        if not isinstance(item, dict) or set(item) != {"sequence", "elapsed_s", "frametime_ms"}:
            errors.append(f"sample {index} has an invalid shape")
            continue
        sequence, elapsed, frametime = item.get("sequence"), item.get("elapsed_s"), item.get("frametime_ms")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence != index:
            errors.append(f"sample {index} has a non-contiguous sequence")
            continue
        if isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)) or not math.isfinite(float(elapsed)):
            errors.append(f"sample {index} has invalid elapsed_s")
            continue
        if isinstance(frametime, bool) or not isinstance(frametime, (int, float)) or not math.isfinite(float(frametime)) or not 0 < float(frametime) <= 60_000:
            errors.append(f"sample {index} has invalid frametime_ms")
            continue
        samples.append({"sequence": sequence, "elapsed_s": float(elapsed), "frametime_ms": float(frametime)})
    if errors:
        return [], errors
    if len(samples) < 120:
        errors.append("capture has fewer than 120 frame samples")
        return [], errors
    elapsed = [float(item["elapsed_s"]) for item in samples]
    if any(current <= previous for previous, current in zip(elapsed, elapsed[1:])):
        errors.append("sample elapsed_s values must be strictly increasing")
    if elapsed[0] > 1.0 or elapsed[-1] < 63.0 or elapsed[-1] > 66.0:
        errors.append("sample timeline does not cover the 64-second measured pass")
    duration = sum(float(item["frametime_ms"]) for item in samples) / 1000.0
    if not 60.0 <= duration <= 68.0:
        errors.append("summed frametimes do not cover the measured pass")
    elapsed_span = elapsed[-1] - elapsed[0]
    if abs(elapsed_span - duration) > 2.0:
        errors.append("sample timestamps and summed frametimes disagree")
    for scene, start, end in SCENE_WINDOWS:
        scene_count = sum(start <= value < end or (scene == ROUTE[-1] and value == end) for value in elapsed)
        if scene_count < 10:
            errors.append(f"scene {scene} has too few samples")
    return samples, errors


def build_benchmark_result(
    capture: dict[str, object],
    controller_log: str,
    *,
    capture_sha256: str | None = None,
) -> dict[str, object]:
    """Validate one explicit local capture and produce a fail-closed result."""
    errors: list[str] = []
    canonical_capture = json.dumps(
        capture,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    try:
        _exact_fields(
            capture,
            {"schema", "run_id", "captured_at_utc", "benchmark", "graphics_profile", "collector", "policy", "samples"},
            "capture",
        )
        if capture.get("schema") != CAPTURE_SCHEMA:
            raise ValueError(f"capture schema must be {CAPTURE_SCHEMA}")
        run_id = _identifier(capture.get("run_id"), "run_id")
        captured_at = _utc(capture.get("captured_at_utc"), "captured_at_utc")

        benchmark = _mapping(capture.get("benchmark"), "benchmark")
        _exact_fields(benchmark, {"version", "map_sha256", "controller_sha256", "pass_seconds", "route"}, "benchmark")
        version = benchmark.get("version")
        if version != BENCHMARK_VERSION:
            raise ValueError(f"benchmark.version must be {BENCHMARK_VERSION}")
        map_hash = _hash(benchmark.get("map_sha256"), "benchmark.map_sha256")
        controller_hash = _hash(benchmark.get("controller_sha256"), "benchmark.controller_sha256")
        if map_hash != EXPECTED_MAP_SHA256:
            raise ValueError("benchmark.map_sha256 does not identify the V1.2 candidate")
        if controller_hash != EXPECTED_CONTROLLER_SHA256:
            raise ValueError("benchmark.controller_sha256 does not identify the V1.2 candidate")
        if benchmark.get("pass_seconds") != 64:
            raise ValueError("benchmark.pass_seconds must be 64")
        if benchmark.get("route") != list(ROUTE):
            raise ValueError("benchmark.route does not match the locked route")

        profile = _mapping(capture.get("graphics_profile"), "graphics_profile")
        _exact_fields(profile, {"profile_id", "label", "settings_sha256"}, "graphics_profile")
        profile_id = _identifier(profile.get("profile_id"), "graphics_profile.profile_id")
        label = profile.get("label")
        if not isinstance(label, str) or not label.strip() or len(label) > 80:
            raise ValueError("graphics_profile.label must be 1-80 characters")
        settings_hash = _hash(profile.get("settings_sha256"), "graphics_profile.settings_sha256")

        collector = _mapping(capture.get("collector"), "collector")
        _exact_fields(
            collector,
            {"collector_id", "collector_version", "process_name", "active_confirmation", "started_at_utc", "ended_at_utc"},
            "collector",
        )
        collector_id = _identifier(collector.get("collector_id"), "collector.collector_id")
        collector_version = _identifier(collector.get("collector_version"), "collector.collector_version")
        if collector.get("process_name") != "cs2.exe":
            raise ValueError("collector.process_name must be cs2.exe")
        if collector.get("active_confirmation") is not True:
            raise ValueError("collector did not confirm an active capture")
        collector_started = _utc(collector.get("started_at_utc"), "collector.started_at_utc")
        collector_ended = _utc(collector.get("ended_at_utc"), "collector.ended_at_utc")
        started_value = datetime.fromisoformat(collector_started.replace("Z", "+00:00"))
        ended_value = datetime.fromisoformat(collector_ended.replace("Z", "+00:00"))
        if ended_value <= started_value:
            raise ValueError("collector end must be after start")
        collector_duration = (ended_value - started_value).total_seconds()
        if not 60.0 <= collector_duration <= 68.0:
            raise ValueError("collector timestamps do not cover the 64-second measured pass")

        policy = _mapping(capture.get("policy"), "policy")
        _exact_fields(policy, {"local_only", "external_transfer"}, "policy")
        if policy != {"local_only": True, "external_transfer": False}:
            raise ValueError("capture policy must be local-only with no external transfer")
    except ValueError as error:
        errors.append(str(error))
        proposed_run_id = capture.get("run_id")
        run_id = (
            proposed_run_id
            if isinstance(proposed_run_id, str) and _IDENTIFIER.fullmatch(proposed_run_id)
            else f"invalid-capture-{hashlib.sha256(canonical_capture).hexdigest()[:12]}"
        )
        captured_at = str(capture.get("captured_at_utc", ""))
        version = str(_mapping(capture.get("benchmark"), "benchmark").get("version", "unknown")) if isinstance(capture.get("benchmark"), dict) else "unknown"
        map_hash = controller_hash = settings_hash = ""
        profile_id = collector_id = collector_version = "unknown"
        label = "Unknown"
        collector_started = collector_ended = ""

    controller_validation, controller_errors = _validate_controller_log(controller_log, version)
    errors.extend(controller_errors)
    samples, sample_errors = _validate_samples(capture.get("samples"))
    errors.extend(sample_errors)

    digest = capture_sha256 or hashlib.sha256(canonical_capture).hexdigest().upper()
    if not _HASH.fullmatch(digest):
        errors.append("capture_sha256 is invalid")
        digest = ""

    status = ResultStatus.INVALID if errors else ResultStatus.VALID
    aggregate: dict[str, object] | None = None
    scenes: list[dict[str, object]] = []
    if status is ResultStatus.VALID:
        aggregate = _metrics([float(item["frametime_ms"]) for item in samples])
        for scene, start, end in SCENE_WINDOWS:
            frame_times = [
                float(item["frametime_ms"])
                for item in samples
                if start <= float(item["elapsed_s"]) < end or (scene == ROUTE[-1] and float(item["elapsed_s"]) == end)
            ]
            scenes.append({"scene": scene, "start_s": start, "end_s": end, "metrics": _metrics(frame_times)})

    comparison_key = ":".join((version, map_hash, controller_hash, profile_id, settings_hash)) if status is ResultStatus.VALID else None
    return {
        "schema": RESULT_SCHEMA,
        "run_id": run_id,
        "captured_at_utc": captured_at,
        "status": status.value,
        "validity": {
            "runtime_status": controller_validation.get("runtime_status", "unknown"),
            "collector_status": "VALID" if status is ResultStatus.VALID else "INVALID",
            "comparable": status is ResultStatus.VALID,
            "errors": errors,
        },
        "benchmark": {
            "version": version,
            "map_sha256": map_hash or None,
            "controller_sha256": controller_hash or None,
            "pass_seconds": PASS_SECONDS,
            "route": list(ROUTE),
        },
        "graphics_profile": {"profile_id": profile_id, "label": label, "settings_sha256": settings_hash or None},
        "collector": {
            "collector_id": collector_id,
            "collector_version": collector_version,
            "process_name": "cs2.exe",
            "started_at_utc": collector_started,
            "ended_at_utc": collector_ended,
            "capture_sha256": digest or None,
        },
        "controller_validation": controller_validation,
        "metrics": aggregate,
        "scenes": scenes,
        "comparison_key": comparison_key,
        "policy": dict(_RESULT_POLICY),
    }


def _atomic_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _positive_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a positive finite number")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field} must be a positive finite number")
    return number


def _validate_metric_summary(value: object, field: str) -> dict[str, object]:
    metrics = _mapping(value, field)
    _exact_fields(
        metrics,
        {"sample_count", "duration_s", "average_fps", "one_percent_low_fps", "frametime_ms"},
        field,
    )
    sample_count = metrics.get("sample_count")
    if isinstance(sample_count, bool) or not isinstance(sample_count, int) or sample_count < 1:
        raise ValueError(f"{field}.sample_count must be a positive integer")
    for name in ("duration_s", "average_fps", "one_percent_low_fps"):
        _positive_number(metrics.get(name), f"{field}.{name}")
    frametime = _mapping(metrics.get("frametime_ms"), f"{field}.frametime_ms")
    _exact_fields(frametime, {"mean", "p95", "p99", "maximum"}, f"{field}.frametime_ms")
    for name in ("mean", "p95", "p99", "maximum"):
        _positive_number(frametime.get(name), f"{field}.frametime_ms.{name}")
    return metrics


def _validate_result_for_store(result: dict[str, object]) -> str:
    _exact_fields(result, _RESULT_FIELDS, "result")
    if result.get("schema") != RESULT_SCHEMA:
        raise ValueError(f"result schema must be {RESULT_SCHEMA}")
    run_id = _identifier(result.get("run_id"), "result.run_id")
    if result.get("policy") != _RESULT_POLICY:
        raise ValueError("result policy must remain local-only, identity-free and screenshot-only")

    status = result.get("status")
    if status not in {ResultStatus.VALID, ResultStatus.INVALID}:
        raise ValueError("result.status must be VALID or INVALID")
    validity = _mapping(result.get("validity"), "result.validity")
    _exact_fields(validity, {"runtime_status", "collector_status", "comparable", "errors"}, "result.validity")
    errors = validity.get("errors")
    if not isinstance(errors, list) or not all(isinstance(item, str) and item for item in errors):
        raise ValueError("result.validity.errors must be a list of non-empty strings")

    scenes = result.get("scenes")
    if not isinstance(scenes, list):
        raise ValueError("result.scenes must be a list")
    if status == ResultStatus.INVALID:
        if result.get("metrics") is not None or scenes or result.get("comparison_key") is not None:
            raise ValueError("invalid results must not contain metrics, scenes or a comparison key")
        if validity.get("comparable") is not False or not errors:
            raise ValueError("invalid results must be non-comparable and explain why")
        return run_id

    _utc(result.get("captured_at_utc"), "result.captured_at_utc")
    if validity != {
        "runtime_status": "complete",
        "collector_status": "VALID",
        "comparable": True,
        "errors": [],
    }:
        raise ValueError("valid result validity state is inconsistent")
    _validate_metric_summary(result.get("metrics"), "result.metrics")
    if len(scenes) != len(SCENE_WINDOWS):
        raise ValueError("valid result must contain all benchmark scenes")
    for item, (expected_scene, expected_start, expected_end) in zip(scenes, SCENE_WINDOWS):
        scene = _mapping(item, "result.scene")
        _exact_fields(scene, {"scene", "start_s", "end_s", "metrics"}, "result.scene")
        if (scene.get("scene"), scene.get("start_s"), scene.get("end_s")) != (
            expected_scene,
            expected_start,
            expected_end,
        ):
            raise ValueError("result scenes do not match the locked route windows")
        _validate_metric_summary(scene.get("metrics"), f"result.scene.{expected_scene}.metrics")

    benchmark = _mapping(result.get("benchmark"), "result.benchmark")
    profile = _mapping(result.get("graphics_profile"), "result.graphics_profile")
    _exact_fields(
        benchmark,
        {"version", "map_sha256", "controller_sha256", "pass_seconds", "route"},
        "result.benchmark",
    )
    if (
        benchmark.get("version") != BENCHMARK_VERSION
        or _hash(benchmark.get("map_sha256"), "result.benchmark.map_sha256") != EXPECTED_MAP_SHA256
        or _hash(benchmark.get("controller_sha256"), "result.benchmark.controller_sha256") != EXPECTED_CONTROLLER_SHA256
        or benchmark.get("pass_seconds") != PASS_SECONDS
        or benchmark.get("route") != list(ROUTE)
    ):
        raise ValueError("valid result benchmark identity is inconsistent")
    _exact_fields(profile, {"profile_id", "label", "settings_sha256"}, "result.graphics_profile")
    _identifier(profile.get("profile_id"), "result.graphics_profile.profile_id")
    _hash(profile.get("settings_sha256"), "result.graphics_profile.settings_sha256")
    label = profile.get("label")
    if not isinstance(label, str) or not label.strip() or len(label) > 80:
        raise ValueError("result.graphics_profile.label must be 1-80 characters")
    expected_key = ":".join(
        str(value)
        for value in (
            benchmark.get("version"),
            benchmark.get("map_sha256"),
            benchmark.get("controller_sha256"),
            profile.get("profile_id"),
            profile.get("settings_sha256"),
        )
    )
    if result.get("comparison_key") != expected_key:
        raise ValueError("result comparison key is inconsistent")
    return run_id


def _history_entry(result: dict[str, object], run_id: str) -> dict[str, object]:
    metrics = _mapping(result.get("metrics"), "result.metrics") if result.get("metrics") is not None else {}
    return {
        "run_id": run_id,
        "captured_at_utc": result.get("captured_at_utc"),
        "status": result.get("status"),
        "comparison_key": result.get("comparison_key"),
        "benchmark_version": _mapping(result.get("benchmark"), "result.benchmark").get("version"),
        "profile_id": _mapping(result.get("graphics_profile"), "result.graphics_profile").get("profile_id"),
        "profile_label": _mapping(result.get("graphics_profile"), "result.graphics_profile").get("label"),
        "average_fps": metrics.get("average_fps"),
        "one_percent_low_fps": metrics.get("one_percent_low_fps"),
        "mean_frametime_ms": _mapping(metrics.get("frametime_ms"), "metrics.frametime_ms").get("mean") if metrics else None,
    }


class BenchmarkResultStore:
    """Local result/history persistence with no discovery or network access."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.runs = root / "runs"
        self.history_path = root / "history.json"

    def _history(self) -> dict[str, object]:
        if not self.history_path.exists():
            return {"schema": HISTORY_SCHEMA, "policy": {"local_only": True, "network_transfer": False}, "runs": []}
        value = json.loads(self.history_path.read_text(encoding="utf-8"))
        if (
            not isinstance(value, dict)
            or set(value) != {"schema", "policy", "runs"}
            or value.get("schema") != HISTORY_SCHEMA
            or value.get("policy") != {"local_only": True, "network_transfer": False}
            or not isinstance(value.get("runs"), list)
        ):
            raise ValueError("local benchmark history is invalid")
        for item in value["runs"]:
            if not isinstance(item, dict) or set(item) != _HISTORY_FIELDS:
                raise ValueError("local benchmark history contains an invalid run entry")
        return value

    def record(self, result: dict[str, object]) -> Path:
        run_id = _validate_result_for_store(result)
        destination = self.runs / f"{run_id}.json"
        if destination.exists():
            existing = json.loads(destination.read_text(encoding="utf-8"))
            if existing != result:
                raise ValueError(f"run_id already exists with different content: {run_id}")
        history = self._history()
        entry = _history_entry(result, run_id)
        existing_entries = [item for item in history["runs"] if item.get("run_id") == run_id]
        if any(item != entry for item in existing_entries) or len(existing_entries) > 1:
            raise ValueError(f"run_id already exists with different history content: {run_id}")
        if not existing_entries:
            history["runs"].append(entry)
        _atomic_json(destination, result)
        _atomic_json(self.history_path, history)
        return destination

    def top(self, comparison_key: str, *, limit: int = 10) -> tuple[dict[str, object], ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        runs = [
            item for item in self._history()["runs"]
            if isinstance(item, dict) and item.get("status") == ResultStatus.VALID and item.get("comparison_key") == comparison_key
        ]
        runs.sort(
            key=lambda item: (
                -float(item.get("average_fps", 0)),
                -float(item.get("one_percent_low_fps", 0)),
                str(item.get("captured_at_utc", "")),
                str(item.get("run_id", "")),
            )
        )
        return tuple(runs[:limit])


def render_result_html(result: dict[str, object], top_results: tuple[dict[str, object], ...]) -> str:
    """Render a self-contained local page intended for a user-made screenshot."""
    metrics = result.get("metrics") if isinstance(result.get("metrics"), dict) else {}
    frame = metrics.get("frametime_ms") if isinstance(metrics.get("frametime_ms"), dict) else {}
    valid = result.get("status") == ResultStatus.VALID
    value = lambda item, suffix="": f"{item:.2f}{suffix}" if isinstance(item, (int, float)) else "–"
    rows = "".join(
        "<tr>"
        f"<td>{rank}</td><td>{html.escape(str(item.get('captured_at_utc', ''))[:10])}</td>"
        f"<td>{value(item.get('average_fps'))}</td><td>{value(item.get('one_percent_low_fps'))}</td>"
        f"<td>{value(item.get('mean_frametime_ms'), ' ms')}</td>"
        "</tr>"
        for rank, item in enumerate(top_results, 1)
    ) or '<tr><td colspan="5">Noch kein vergleichbarer gültiger Lauf.</td></tr>'
    status = "GÜLTIGER LOKALER LAUF" if valid else "NICHT ALS MESSUNG GÜLTIG"
    profile = _mapping(result.get("graphics_profile"), "result.graphics_profile")
    benchmark = _mapping(result.get("benchmark"), "result.benchmark")
    errors = _mapping(result.get("validity"), "result.validity").get("errors", [])
    error_text = "" if valid else " · ".join(html.escape(str(item)) for item in errors)
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Improve Benchmark · lokales Ergebnis</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#030b12;color:#eef8ff;font:15px Inter,Segoe UI,sans-serif}}
.page{{max-width:1180px;margin:0 auto;padding:36px}} .brand{{letter-spacing:.22em;color:#7fd8ff;font-weight:800}}
h1{{font-size:36px;margin:10px 0 6px}} .sub,.note{{color:#88a9ba}} .status{{display:inline-block;margin:18px 0;padding:8px 13px;border:1px solid {'#20d09a' if valid else '#dba84b'};border-radius:999px;color:{'#72f2c5' if valid else '#ffd47a'};font-weight:800}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:20px 0}} .card{{background:#0a1823;border:1px solid #17384a;border-radius:14px;padding:20px}}
.label{{color:#7ba0b3;font-size:12px;letter-spacing:.12em}} .metric{{font-size:34px;font-weight:800;margin-top:8px}}
table{{width:100%;border-collapse:collapse;margin-top:10px}} th,td{{text-align:left;padding:12px;border-bottom:1px solid #17384a}} th{{color:#75cdec;font-size:12px;letter-spacing:.08em}}
.footer{{margin-top:22px;padding-top:18px;border-top:1px solid #17384a;color:#7192a3;font-size:12px}}
</style></head><body><main class="page">
<div class="brand">IMPROVE YOURSELF · BENCHMARK</div><h1>Dein lokales Ergebnis</h1>
<div class="sub">{html.escape(str(benchmark.get('version', '')))} · {html.escape(str(profile.get('label', '')))} · {html.escape(str(result.get('captured_at_utc', '')))}</div>
<div class="status">{status}</div><div class="note">{error_text}</div>
<section class="grid"><div class="card"><div class="label">Ø FPS</div><div class="metric">{value(metrics.get('average_fps'))}</div></div>
<div class="card"><div class="label">1% LOW</div><div class="metric">{value(metrics.get('one_percent_low_fps'))}</div></div>
<div class="card"><div class="label">FRAMETIME Ø</div><div class="metric">{value(frame.get('mean'), ' ms')}</div></div></section>
<section class="card"><div class="label">PERSÖNLICHE LOKALE TOP 10 · IDENTISCHES PROFIL</div>
<table><thead><tr><th>#</th><th>DATUM</th><th>Ø FPS</th><th>1% LOW</th><th>FRAMETIME</th></tr></thead><tbody>{rows}</tbody></table></section>
<div class="footer">LOCAL ONLY · KEIN UPLOAD · KEINE STEAM-ID · KEINE OPTIMIZER-VERBINDUNG · Teilen nur durch einen vom Nutzer selbst erstellten Screenshot.</div>
</main></body></html>"""


def export_benchmark_result(capture_path: Path, controller_log_path: Path, root: Path, html_path: Path) -> tuple[Path, Path, dict[str, object]]:
    capture_bytes = capture_path.read_bytes()
    capture = json.loads(capture_bytes.decode("utf-8"))
    if not isinstance(capture, dict):
        raise ValueError("capture root must be an object")
    result = build_benchmark_result(
        capture,
        controller_log_path.read_text(encoding="utf-8", errors="replace"),
        capture_sha256=hashlib.sha256(capture_bytes).hexdigest().upper(),
    )
    store = BenchmarkResultStore(root)
    result_path = store.record(result)
    top = store.top(str(result.get("comparison_key"))) if result.get("comparison_key") else ()
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(render_result_html(result, top), encoding="utf-8")
    return result_path, html_path, result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and store one standalone local CS2 benchmark result")
    parser.add_argument("capture", type=Path, help="Explicit local iy.cs2_benchmark_capture/v1 JSON")
    parser.add_argument("controller_log", type=Path, help="Explicit local CS2 console log")
    parser.add_argument("--root", type=Path, default=Path("results/benchmark"))
    parser.add_argument("--html", type=Path, default=Path("results/benchmark/latest.html"))
    args = parser.parse_args()
    try:
        result_path, html_path, result = export_benchmark_result(args.capture, args.controller_log, args.root, args.html)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(result_path)
    print(html_path)
    print(f"status={result['status']}")
    return 0 if result["status"] == ResultStatus.VALID else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
