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
