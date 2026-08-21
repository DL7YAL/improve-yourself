from __future__ import annotations

from dataclasses import replace

from improve_yourself.optimizer_evidence import (
    BenchmarkABPlan,
    EvidenceClass,
    GoalProfile,
    OptimizerRule,
    evaluate_profile,
    evidence_matrix,
    evidence_matrix_document,
    profile_from_system_check,
    run_synthetic_matrix,
    synthetic_system_matrix,
)


def test_matrix_is_machine_readable_and_covers_every_evidence_class() -> None:
    document = evidence_matrix_document()
    rules = document["rules"]
    assert document["schema"] == "iy.optimizer_evidence_matrix/v1"
    assert document["safety_protocol"] == "READ → SNAPSHOT → APPLY → VERIFY → RESTORE"
    assert document["selection_order"] == ("safety", "compatibility", "evidence", "stability", "performance")
    assert {rule["evidence_class"] for rule in rules} == {item.value for item in EvidenceClass}
    required = {"rule_id", "name", "category", "description", "current_state_path", "target_state", "supported_conditions", "exclusion_conditions", "expected_effect", "possible_side_effects", "reversible", "backup_restore_requirement", "evidence_class", "confidence", "source_rationale", "measurement_metrics", "validation_status"}
    assert all(required <= set(rule) for rule in rules)
    assert all(rule["reversible"] for rule in rules)


def test_system_check_projection_does_not_invent_cs2_or_driver_option_state() -> None:
    payload = {
        "schema": "iy.system_check/v1",
        "checks": [
            {"id": "cpu", "evidence": {"name": "AMD Ryzen 7 7800X3D"}},
            {"id": "gpu", "evidence": {"adapters": [{"name": "AMD Radeon RX 7900 XTX", "driver_version": "24.10.1"}]}},
            {"id": "memory", "evidence": {"total_gb": 32}},
            {"id": "display", "evidence": {"refresh_rates_hz": [240]}},
            {"id": "windows", "evidence": {"build": 26100}},
        ],
    }
    profile = profile_from_system_check(payload, goal=GoalProfile.PERFORMANCE)
    assert profile is not None
    assert profile["profile_source"] == "READ_ONLY_SYSTEM_CHECK"
    assert profile["performance_evidence"] == "NOT_MEASURED"
    assert "cs2" not in profile and "gpu_options" not in profile
    report = evaluate_profile(profile)
    assert "cs2.refresh_hz" in report["missing_input_data"]
    assert "cs2.frame_pacing" in report["missing_input_data"]


def test_synthetic_matrix_has_exactly_150_non_measured_diverse_profiles() -> None:
    matrix = synthetic_system_matrix()
    systems = matrix["systems"]
    assert matrix["schema"] == "iy.optimizer_synthetic_matrix/v1"
    assert len(systems) == 150
    assert {system["gpu"]["vendor"] for system in systems} == {"AMD", "NVIDIA"}
    assert {system["ram"]["capacity_gb"] for system in systems} == {8, 16, 32, 64}
    assert {system["monitor"]["refresh_hz"] for system in systems} == {60, 120, 144, 165, 240, 360}
    assert all(system["performance_evidence"] == "NOT_MEASURED" for system in systems)
    assert all(system["synthetic_label"] == "SYNTHETIC / EXPECTED / NOT MEASURED" for system in systems)


def test_synthetic_runner_is_deterministic_and_reports_matrix_contract() -> None:
    first = run_synthetic_matrix()
    second = run_synthetic_matrix()
    assert first == second
    assert first["system_count"] == 150
    assert first["performance_evidence"] == "SYNTHETIC / EXPECTED / NOT MEASURED"
    assert first["evidence_matrix"]["schema"] == "iy.optimizer_evidence_matrix/v1"
    assert first["summary"]["stable"] > 0
    assert first["summary"]["conditional"] > 0
    assert first["summary"]["experimental"] > 0
    assert all(report["performance_evidence"] == "NOT_MEASURED" for report in first["reports"])


def test_low_memory_profile_is_excluded_from_experimental_frame_pacing() -> None:
    profile = next(system for system in synthetic_system_matrix()["systems"] if system["ram"]["capacity_gb"] == 8 and system["goal"] == "PERFORMANCE" and system["limitation"] == "CPU")
    report = evaluate_profile(profile)
    excluded = {item["rule_id"]: item["reason"] for item in report["excluded_rules"]}
    assert "performance-frame-pacing-candidate" in excluded
    assert "excluded:ram.capacity_gb" in excluded["performance-frame-pacing-candidate"]


def test_conflicts_use_declared_priority_and_do_not_choose_maximum_fps() -> None:
    source = next(rule for rule in evidence_matrix() if rule.rule_id == "amd-driver-option-review")
    safer = replace(source, rule_id="safer", name="Safer", priority=99, conflicts_with=("faster",))
    faster = replace(source, rule_id="faster", name="Faster", priority=1, conflicts_with=("safer",))
    report = evaluate_profile({"goal": "PERFORMANCE", "gpu": {"vendor": "AMD", "driver_version": "24.10.1"}}, (safer, faster))
    assert [item["rule_id"] for item in report["conditional_recommendations"]] == ["safer"]
    assert report["conflicts"] == [{"excluded_rule_id": "faster", "winning_rule_id": "safer", "reason": "deterministic priority"}]


def test_ab_plan_exposes_abab_and_required_result_context() -> None:
    plan = BenchmarkABPlan().as_dict()
    assert plan["sequence"] == ("A_BASELINE", "B_OPTIMIZED", "A_REPEAT", "B_REPEAT")
    assert {"average_fps", "one_percent_low", "frametime_percentiles", "frametime_stability", "stutter_spikes", "cpu_gpu_limitation", "reproducible_delta"} <= set(plan["metrics"])
    assert {"system_profile", "source_state", "target_state", "scenario", "runs", "delta", "variance", "result"} <= set(plan["required_fields"])
