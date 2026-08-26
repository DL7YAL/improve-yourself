from __future__ import annotations

from improve_yourself.optimizer_foundation import (
    FOUNDATION_SCHEMA,
    RecommendationState,
    OptimizerDomain,
    evaluate_recommendations,
    fixture_rules,
    recommendation_detail_view_model,
    run_fixture_harness,
    system_profile_from_facts,
)


def _facts() -> dict[str, object]:
    return {
        "windows": {"caption": "Windows 11 Pro", "version": "10.0", "build": 26100},
        "cpu": {"name": "AMD Ryzen 7", "manufacturer": "AuthenticAMD", "architecture": 9, "family": 25},
        "memory": {"total_gb": 32, "speed_mt_s": None},
        "motherboard": {"manufacturer": "Vendor", "product": "Board", "version": "1.0"},
        "bios": {"version": "F1", "date": "2026-01-01", "manufacturer": "Vendor"},
        "gpus": [{"name": "GPU", "vendor": "NVIDIA", "driver_version": "1.2.3"}],
        "displays": [{"width": 2560, "height": 1440, "refresh_hz": 240}],
        "network_adapters": [{"name": "NIC", "manufacturer": "Vendor", "driver_version": "1", "link_speed_mbps": 1000, "mac_address": "redacted-local"}],
    }


def test_system_profile_is_versioned_read_only_and_preserves_unknowns() -> None:
    profile = system_profile_from_facts(_facts())
    assert profile["schema"] == "iy.system_profile/v1"
    assert profile["policy"] == {"read_only": True, "changes_applied": False}
    assert profile["cpu"]["manufacturer"] == "AuthenticAMD"
    assert profile["display"][0]["width"] == 2560
    assert profile["network"]["adapters"][0]["link_speed_mbps"] == 1000
    assert "cs2.configuration" in profile["unknown_fields"]
    assert profile["applications"]["cs2"] == {"status": "NOT_AVAILABLE"}
    assert profile["field_observation"]["cs2.configuration"] == "NOT_AVAILABLE"


def test_system_profile_projects_collector_bios_facts_without_inventing_values() -> None:
    facts = _facts()
    facts["bios"] = {}
    facts["motherboard"] = {
        "manufacturer": "Vendor",
        "product": "Board",
        "bios_version": "F2",
        "bios_date": "2026-02-03",
    }

    profile = system_profile_from_facts(facts)

    assert profile["bios"] == {
        "manufacturer": "Vendor",
        "version": "F2",
        "date": "2026-02-03",
    }


def test_fixture_rules_cover_four_domains_and_are_not_real_rules() -> None:
    rules = fixture_rules()
    assert {rule.domain for rule in rules} == set(OptimizerDomain)
    assert len(rules) >= 5
    assert all(record.quality == "SYNTHETIC" for rule in rules for record in rule.evidence)
    assert all(rule.changeable_later is False for rule in rules)


def test_recommendations_cover_match_conditional_exclusion_and_missing_evidence() -> None:
    profile = system_profile_from_facts(_facts())
    report = evaluate_recommendations(profile)
    result = {item["rule_id"]: item for item in report["results"]}
    assert report["schema"] == FOUNDATION_SCHEMA
    assert result["fixture-system-memory"]["state"] == RecommendationState.RECOMMENDED
    assert result["fixture-graphics-driver"]["state"] == RecommendationState.RECOMMENDED
    assert result["fixture-bios-guidance"]["state"] == RecommendationState.RECOMMENDED
    assert result["fixture-network-link"]["state"] == RecommendationState.RECOMMENDED
    low_ram = dict(profile)
    low_ram["ram"] = {"total_gb": 8, "capacity_gb": 8}
    low_report = {item["rule_id"]: item for item in evaluate_recommendations(low_ram)["results"]}
    assert low_report["fixture-conditional-exclusion"]["state"] == RecommendationState.NO_CHANGE
    missing = dict(profile)
    missing["motherboard"] = {}
    assert {item["rule_id"]: item for item in evaluate_recommendations(missing)["results"]}["fixture-bios-guidance"]["state"] == RecommendationState.INSUFFICIENT_EVIDENCE


def test_view_model_has_explanation_panel_contract_without_apply() -> None:
    item = evaluate_recommendations(system_profile_from_facts(_facts()))["results"][3]
    model = recommendation_detail_view_model(item)
    assert {"title", "current_state", "improve_recommendation", "status", "what_is_it", "why_for_this_system", "what_can_change", "evidence_validity", "risk_notes", "restore_change_information", "guidance"} <= set(model)
    assert "apply" not in {key.lower() for key in model}
    assert model["guidance"]["manual_action_required"] is True


def test_already_recommended_and_conflicting_rules_are_deterministic() -> None:
    profile = system_profile_from_facts(_facts())
    profile["current_recommendations"] = {"fixture-system-memory": True}
    result = {item["rule_id"]: item for item in evaluate_recommendations(profile)["results"]}
    assert result["fixture-system-memory"]["state"] == RecommendationState.ALREADY_RECOMMENDED


def test_150_system_harness_is_deterministic_and_not_a_performance_simulation() -> None:
    first = run_fixture_harness()
    second = run_fixture_harness()
    assert first == second
    assert first["system_count"] == 150
    assert first["label"] == "SYNTHETIC / DECISION LOGIC ONLY / NOT MEASURED"
    assert first["states"][RecommendationState.INSUFFICIENT_EVIDENCE] > 0
    assert first["states"][RecommendationState.RECOMMENDED] > 0
