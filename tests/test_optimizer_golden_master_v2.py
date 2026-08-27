import json
from pathlib import Path

from improve_yourself.optimizer_comparison_adapter import (
    DEFAULT_PROJECTION_PATH,
    run_comparison_matrix,
    validate_comparison_document,
    validate_projection_document,
)
from improve_yourself.optimizer_evidence import synthetic_system_matrix
from improve_yourself.optimizer_foundation import RecommendationState, evaluate_recommendations


def _profile() -> dict[str, object]:
    return {"schema":"iy.system_profile/v1","profile_id":"golden","ram":{"capacity_gb":32},"gpu":{"vendor":"NVIDIA","driver_version":"x"},"motherboard":{"product":"x"},"bios":{"version":"x"},"network":{"adapters":[{}]}}


def _projection(path: Path, cases: list[dict[str, object]], projections: list[dict[str, object]] | None = None) -> Path:
    target = path / "projection.json"
    target.write_text(json.dumps({"schema":"iy.optimizer_comparison_projection/v1", "projections": projections or [{"system_id": case["system_id"]} for case in cases]}), encoding="utf-8")
    return target


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


def test_mixed_missing_observations_have_deterministic_not_available_precedence() -> None:
    first=_profile(); first["motherboard"]={}; first["bios"]={}; first["observation_states"]={"bios.version":"NOT_AVAILABLE","motherboard.product":"UNKNOWN"}
    second=_profile(); second["motherboard"]={}; second["bios"]={}; second["observation_states"]={"motherboard.product":"UNKNOWN","bios.version":"NOT_AVAILABLE"}
    get=lambda profile: {item["rule_id"]:item for item in evaluate_recommendations(profile)["results"]}["fixture-bios-guidance"]
    assert get(first)["state"] == get(second)["state"] == RecommendationState.NOT_AVAILABLE
    assert get(first)["missing_evidence"] == get(second)["missing_evidence"] == ["bios.version", "motherboard.product"]


def test_150_matrix_is_deterministic_with_stable_case_ids() -> None:
    first=synthetic_system_matrix(); second=synthetic_system_matrix()
    assert first == second and len(first["systems"]) == 150
    assert len({x["synthetic_case"]["case_id"] for x in first["systems"]}) == 150


def test_challenge_adapter_executes_60_without_recommendation_fields(tmp_path: Path) -> None:
    case={"system_id":"cmp-x","group":"realistic","hardware":"RTX 4060 | 32GB","settings":"known","challenge":"x","expected_behavior":"no policy","boundaries":"none","safety_traps":"none"}
    document={"systems":[{**case,"system_id":f"cmp-{i}","group":("realistic" if i<20 else "edge_stress" if i<40 else "adversarial")} for i in range(60)]}
    path=tmp_path/'matrix.json'; path.write_text(json.dumps(document),encoding='utf-8')
    output=run_comparison_matrix(path, _projection(tmp_path, document["systems"]))
    assert output["count"] == 60
    assert all("recommendation" not in item for item in document["systems"])


def test_challenge_projection_preserves_pairs_without_policy(tmp_path: Path) -> None:
    base={"group":"adversarial","hardware":"RTX 4060 | 32GB","challenge":"pair","expected_behavior":"semantic only","boundaries":"","safety_traps":"none"}
    cases=[{**base,"system_id":"cmp-0","settings":"prose is ignored"},{**base,"system_id":"cmp-1","settings":"prose is ignored"}]
    document={"systems":[{**cases[i%2],"system_id":f"cmp-{i}","group":("realistic" if i<20 else "edge_stress" if i<40 else "adversarial")} for i in range(60)]}
    path=tmp_path/'pairs.json'; path.write_text(json.dumps(document),encoding='utf-8')
    projections=[{"system_id":f"cmp-{i}", **({"goal":"PERFORMANCE","limitation":"CPU","current_state":"OPTIMAL","vendor":"AMD","comparison_tags":["pair"],"capability_states":{"nvidia_feature":"SUPPORTED"}} if i % 2 == 0 else {"goal":"QUALITY","limitation":"GPU","current_state":"MISMATCH","vendor":"AMD","oem_control_available":"NOT_AVAILABLE","capability_states":{"nvidia_feature":"UNSUPPORTED"}})} for i in range(60)]
    reports=run_comparison_matrix(path, _projection(tmp_path, document["systems"], projections))["reports"]
    first,second=reports[0]["actual"]["results"][0],reports[1]["actual"]["results"][0]
    assert first["comparison_tags"][0] == "cmp-0" and second["comparison_tags"][0] == "cmp-1"
    assert first["challenge_projection"] != second["challenge_projection"]
    assert first["challenge_projection"]["goal"] == "PERFORMANCE"
    assert second["challenge_projection"]["oem_control_available"] == "NOT_AVAILABLE"


def test_actual_challenge_contract_requires_60_unique_20_20_20_typed_cases() -> None:
    cases=[{"system_id":f"cmp-{i}","group":("realistic" if i<20 else "edge_stress" if i<40 else "adversarial"),"hardware":"x","settings":"x","challenge":"x","expected_behavior":"x","boundaries":"x","safety_traps":"x"} for i in range(60)]
    assert validate_comparison_document({"systems":cases}) == []
    cases[0]["group"]="wrong"
    assert validate_comparison_document({"systems":cases})


def test_committed_projection_is_exact_60_case_contract_and_encodes_tuv_hazards() -> None:
    contract = json.loads(DEFAULT_PROJECTION_PATH.read_text(encoding="utf-8"))
    ids = {f"cmp-{prefix}{number:02d}" for prefix in ("r", "e", "a") for number in range(1, 21)}
    assert validate_projection_document(contract, ids) == []
    projections = {item["system_id"]: item for item in contract["projections"]}
    assert projections["cmp-r02"]["vendor"] == "AMD"
    assert projections["cmp-r02"]["capability_states"]["nvidia_feature"] == "UNSUPPORTED"
    assert projections["cmp-a03"]["goal"] == "PERFORMANCE"
    assert projections["cmp-a04"]["goal"] == "QUALITY"
    assert projections["cmp-a09"]["limitation"] == "CPU"
    assert projections["cmp-a10"]["limitation"] == "GPU"
    assert projections["cmp-a17"]["oem_control_available"] == "NOT_AVAILABLE"
    assert projections["cmp-a18"]["oem_control_available"] == "SUPPORTED"
    assert projections["cmp-a01"].get("observed_desired_states") == {}


def test_projection_coverage_fails_closed_for_missing_or_extra_case_ids() -> None:
    ids = {f"cmp-{i}" for i in range(60)}
    document = {"schema":"iy.optimizer_comparison_projection/v1", "projections":[{"system_id":f"cmp-{i}"} for i in range(60)]}
    assert validate_projection_document(document, ids) == []
    document["projections"][-1]["system_id"] = "extra"
    assert validate_projection_document(document, ids)
