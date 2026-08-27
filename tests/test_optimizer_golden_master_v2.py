import json
from pathlib import Path

from improve_yourself.optimizer_comparison_adapter import run_comparison_matrix
from improve_yourself.optimizer_evidence import synthetic_system_matrix
from improve_yourself.optimizer_foundation import RecommendationState, evaluate_recommendations


def _profile() -> dict[str, object]:
    return {"schema":"iy.system_profile/v1","profile_id":"golden","ram":{"capacity_gb":32},"gpu":{"vendor":"NVIDIA","driver_version":"x"},"motherboard":{"product":"x"},"bios":{"version":"x"},"network":{"adapters":[{}]}}


def test_v2_result_dimensions_and_observed_already_optimal_are_independent() -> None:
    profile=_profile(); profile["observed_desired_states"]={"fixture-system-memory":True}; profile["current_recommendations"]={"fixture-graphics-driver":True}
    results={x["rule_id"]:x for x in evaluate_recommendations(profile)["results"]}
    assert results["fixture-system-memory"]["state"] == RecommendationState.ALREADY_OPTIMAL
    assert results["fixture-graphics-driver"]["state"] == RecommendationState.ALREADY_RECOMMENDED
    assert {"observation_state","evidence_status","capability_status","recommendation_state","action_classification","restart_requirement","restore_theory","rationale","comparison_tags"} <= results["fixture-system-memory"].keys()
    assert results["fixture-bios-guidance"]["action_classification"] == "MANUAL_ONLY"


def test_missing_evidence_never_claims_known_or_applyable() -> None:
    profile=_profile(); profile["motherboard"]={}; profile["bios"]={}
    result={x["rule_id"]:x for x in evaluate_recommendations(profile)["results"]}["fixture-bios-guidance"]
    assert result["state"] == RecommendationState.INSUFFICIENT_EVIDENCE
    assert result["observation_state"] == "UNKNOWN"
    assert result["action_classification"] == "NOT_APPLYABLE"


def test_explicit_not_available_and_capability_states_are_never_inferred() -> None:
    missing=_profile(); missing["motherboard"]={}; missing["bios"]={}
    absent=_profile(); absent["motherboard"]={}; absent["bios"]={}; absent["observation_states"]={"motherboard.product":"NOT_AVAILABLE","bios.version":"NOT_AVAILABLE"}
    unsupported=_profile(); unsupported["capability_states"]={"GRAPHICS_OPTIMIZER":"UNSUPPORTED"}
    unknown=_profile(); unknown["capability_states"]={"GRAPHICS_OPTIMIZER":"UNKNOWN"}
    get=lambda p, rule: {x["rule_id"]:x for x in evaluate_recommendations(p)["results"]}[rule]
    assert get(missing,"fixture-bios-guidance")["observation_state"] == "UNKNOWN"
    assert get(absent,"fixture-bios-guidance")["state"] == RecommendationState.NOT_AVAILABLE
    assert get(absent,"fixture-bios-guidance")["observation_state"] == "NOT_AVAILABLE"
    assert get(unsupported,"fixture-graphics-driver")["state"] == RecommendationState.UNSUPPORTED
    assert get(unsupported,"fixture-graphics-driver")["capability_status"] == "UNSUPPORTED"
    assert get(unknown,"fixture-graphics-driver")["capability_status"] == "UNKNOWN"


def test_150_matrix_is_deterministic_with_stable_case_ids() -> None:
    first=synthetic_system_matrix(); second=synthetic_system_matrix()
    assert first == second and len(first["systems"]) == 150
    assert len({x["synthetic_case"]["case_id"] for x in first["systems"]}) == 150


def test_challenge_adapter_executes_60_without_recommendation_fields(tmp_path: Path) -> None:
    case={"system_id":"cmp-x","group":"realistic","hardware":"RTX 4060 | 32GB","settings":"known","challenge":"x","expected_behavior":"no policy","boundaries":"none","safety_traps":"none"}
    document={"systems":[{**case,"system_id":f"cmp-{i}"} for i in range(60)]}
    path=tmp_path/'matrix.json'; path.write_text(json.dumps(document),encoding='utf-8')
    output=run_comparison_matrix(path)
    assert output["count"] == 60
    assert all("recommendation" not in item for item in document["systems"])


def test_challenge_projection_preserves_pairs_without_policy(tmp_path: Path) -> None:
    base={"group":"adversarial","hardware":"RTX 4060 | 32GB","challenge":"pair","expected_behavior":"semantic only","boundaries":"","safety_traps":"none"}
    cases=[{**base,"system_id":"cmp-0","settings":"competitive CPU known optimal supported"},{**base,"system_id":"cmp-1","settings":"quality GPU mismatch unknown OEM lock unsupported"}]
    document={"systems":[{**cases[i%2],"system_id":f"cmp-{i}"} for i in range(60)]}
    path=tmp_path/'pairs.json'; path.write_text(json.dumps(document),encoding='utf-8')
    reports=run_comparison_matrix(path)["reports"]
    first,second=reports[0]["actual"]["results"][0],reports[1]["actual"]["results"][0]
    assert first["comparison_tags"][0] == "cmp-0" and second["comparison_tags"][0] == "cmp-1"
    assert first["challenge_projection"] != second["challenge_projection"]
    assert first["challenge_projection"]["goal"] == "PERFORMANCE"
    assert second["challenge_projection"]["observation_availability"] == "UNKNOWN"
