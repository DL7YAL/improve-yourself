from __future__ import annotations

from improve_yourself.optimizer_evidence import synthetic_system_matrix
from improve_yourself.optimizer_foundation import fixture_rules, validate_synthetic_rule_pack


def test_matrix_has_150_diverse_canonical_profiles_without_real_evidence() -> None:
    matrix = synthetic_system_matrix()
    profiles = matrix["systems"]
    assert len(profiles) == 150
    assert all(profile["schema"] == "iy.system_profile/v1" for profile in profiles)
    assert {profile["cpu"]["vendor"] for profile in profiles} == {"AMD", "Intel"}
    assert {profile["gpu"]["vendor"] for profile in profiles} == {"AMD", "NVIDIA"}
    assert {profile["monitor"]["refresh_hz"] for profile in profiles} == {60, 120, 144, 165, 240, 360}
    assert {profile["network"]["adapters"][0]["link_speed_mbps"] for profile in profiles if profile["network"]["adapters"]} == {100, 1000, 2500}
    assert all(profile["performance_evidence"] == "NOT_MEASURED" for profile in profiles)
    assert all(profile["synthetic_case"]["real_evidence_allowed"] is False for profile in profiles)


def test_rule_pack_validation_is_deterministic_and_never_claims_real_validation() -> None:
    first = validate_synthetic_rule_pack(fixture_rules())
    second = validate_synthetic_rule_pack(fixture_rules())
    assert first == second
    assert first["system_count"] == 150
    assert first["validation_kind"] == "SYNTHETIC_RULE_PACK_VALIDATION"
    assert first["real_validation_result_created"] is False
    assert first["confidence_changed"] is False
    assert first["state_counts"]["RECOMMENDED"] > 0
    assert first["state_counts"]["ALREADY_RECOMMENDED"] > 0
    assert first["state_counts"]["INSUFFICIENT_EVIDENCE"] > 0


def test_matrix_reports_exclusions_unknowns_and_all_domain_paths_for_future_packs() -> None:
    report = validate_synthetic_rule_pack(fixture_rules())
    domains = {result["domain"] for profile in report["reports"] for result in profile["results"]}
    assert domains == {"SYSTEM_OPTIMIZER", "GRAPHICS_OPTIMIZER", "NETWORK_OPTIMIZER", "BIOS_OPTIMIZER"}
    assert any(result["missing_evidence"] for profile in report["reports"] for result in profile["results"])
    assert any(trace["exclusions"] and trace["exclusions"][0]["matched"] for profile in report["reports"] for result in profile["results"] for trace in [result["compatibility_trace"]])
