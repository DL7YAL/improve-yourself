from __future__ import annotations

from improve_yourself.network_quality import NetworkTarget, ProbeResult, TargetClass, collect_network_quality, network_quality_evidence
from improve_yourself.optimizer_foundation import (
    RecommendationState,
    integration_proof,
    system_profile_from_facts,
)


def _profile() -> dict[str, object]:
    return system_profile_from_facts({
        "windows": {"build": 26100}, "cpu": {"name": "CPU"}, "memory": {"total_gb": 32},
        "motherboard": {"product": "Board", "version": "1"}, "bios": {"version": "F1"},
        "gpus": [{"name": "GPU", "vendor": "NVIDIA", "driver_version": "1"}],
        "network_adapters": [{"name": "NIC", "mtu": 1500, "rss": True}],
    })


def test_full_read_only_pipeline_proves_four_domains_evidence_and_ui_contract() -> None:
    measurement = collect_network_quality(NetworkTarget("fixture-network", TargetClass.LOCAL_GATEWAY, "gateway.fixture", "recorded fixture"), sample_count=3, interval_ms=0, measurement_session_id="network-proof", probe=lambda _h, _t, sequence: ProbeResult(sequence, 10 + sequence, "success"))
    proof = integration_proof(_profile(), (network_quality_evidence(measurement),))
    assert proof["pipeline"] == ("COLLECT", "SYSTEM_PROFILE", "RULE_COMPATIBILITY", "EVIDENCE", "RECOMMENDATION_RESULT", "UI_VIEWMODEL")
    assert proof["read_only"] is True
    domains = {item["domain"] for item in proof["report"]["results"]}
    assert domains == {"SYSTEM_OPTIMIZER", "GRAPHICS_OPTIMIZER", "NETWORK_OPTIMIZER", "BIOS_OPTIMIZER"}
    assert proof["report"]["evidence_path"]["configuration_evidence"] == []
    assert proof["report"]["evidence_path"]["observed_network_quality"][0]["source_type"] == "OBSERVED_NETWORK_QUALITY"
    for result, view in zip(proof["report"]["results"], proof["view_models"]):
        assert result["compatibility_trace"]
        assert "evidence_records" in result
        assert view["apply_available"] is False
        assert view["improve_recommendation"].startswith("FIXTURE_ONLY")


def test_all_recommendation_outcomes_missing_and_exclusion_are_explainable() -> None:
    base = _profile()
    base["current_recommendations"] = {"fixture-system-memory": True}
    results = {item["rule_id"]: item for item in integration_proof(base, ()) ["report"]["results"]}
    assert results["fixture-system-memory"]["state"] == RecommendationState.ALREADY_RECOMMENDED
    assert results["fixture-security-performance-tradeoff"]["state"] == RecommendationState.NO_CHANGE
    conditional = _profile()
    conditional["gpu"] = {"vendor": "AMD", "driver_version": "1"}
    conditional_result = {item["rule_id"]: item for item in integration_proof(conditional, ()) ["report"]["results"]}
    assert conditional_result["fixture-graphics-driver"]["state"] == RecommendationState.CONDITIONAL
    excluded = _profile()
    excluded["ram"] = {"capacity_gb": 8}
    excluded_result = {item["rule_id"]: item for item in integration_proof(excluded, ()) ["report"]["results"]}
    assert excluded_result["fixture-conditional-exclusion"]["state"] == RecommendationState.NO_CHANGE
    assert excluded_result["fixture-conditional-exclusion"]["compatibility_trace"]["exclusions"][0]["matched"] is True
    missing = _profile()
    missing["bios"] = {}
    missing_result = {item["rule_id"]: item for item in integration_proof(missing, ()) ["report"]["results"]}
    assert missing_result["fixture-bios-guidance"]["state"] == RecommendationState.INSUFFICIENT_EVIDENCE
    assert "bios.version" in missing_result["fixture-bios-guidance"]["missing_evidence"]
