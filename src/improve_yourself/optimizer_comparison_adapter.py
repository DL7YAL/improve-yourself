"""Translation-only execution of the separate Azure comparison cohort.

The prose matrix supplies identity, cohort, and pressure text only. Reviewed
semantic facts are exclusively supplied by the versioned projection contract.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .optimizer_foundation import evaluate_recommendations

COHORTS = {"realistic", "edge_stress", "adversarial"}
CASE_FIELDS = {"system_id", "group", "hardware", "settings", "challenge", "expected_behavior", "boundaries", "safety_traps"}
PROJECTION_SCHEMA = "iy.optimizer_comparison_projection/v1"
PROJECTION_FIELDS = {"system_id", "goal", "limitation", "current_state", "vendor", "oem_control_available", "comparison_tags", "observation_states", "capability_states", "observed_desired_states"}
DEFAULT_PROJECTION_PATH = Path(__file__).resolve().parents[2] / "resources" / "optimizer_comparison" / "comparison_projection_v1.json"


def validate_comparison_document(document: dict[str, Any]) -> list[str]:
    cases, errors = document.get("systems"), []
    if not isinstance(cases, list) or len(cases) != 60:
        return ["systems must contain exactly 60 cases"]
    ids: set[str] = set(); counts = {group: 0 for group in COHORTS}
    for number, case in enumerate(cases, 1):
        if not isinstance(case, dict): errors.append(f"case {number} is not an object"); continue
        if set(case) != CASE_FIELDS: errors.append(f"case {number} must contain exactly the matrix fields")
        ident, group = case.get("system_id"), case.get("group")
        if not isinstance(ident, str) or not ident or ident in ids: errors.append(f"case {number} has invalid/duplicate system_id")
        else: ids.add(ident)
        if group not in COHORTS: errors.append(f"case {ident} has invalid cohort")
        else: counts[group] += 1
        if any(not isinstance(case.get(field), str) for field in CASE_FIELDS): errors.append(f"case {ident} has non-string matrix field")
    return errors + [f"{group} must contain 20 cases" for group, count in counts.items() if count != 20]


def validate_projection_document(document: dict[str, Any], case_ids: set[str]) -> list[str]:
    projections, errors = document.get("projections"), []
    if document.get("schema") != PROJECTION_SCHEMA: errors.append(f"schema must be {PROJECTION_SCHEMA}")
    if not isinstance(projections, list) or len(projections) != 60: return errors + ["projections must contain exactly 60 entries"]
    ids: set[str] = set()
    for number, projection in enumerate(projections, 1):
        if not isinstance(projection, dict): errors.append(f"projection {number} is not an object"); continue
        if set(projection) - PROJECTION_FIELDS or "system_id" not in projection: errors.append(f"projection {number} has invalid shape")
        ident = projection.get("system_id")
        if not isinstance(ident, str) or not ident or ident in ids: errors.append(f"projection {number} has invalid/duplicate system_id")
        else: ids.add(ident)
        if "comparison_tags" in projection and (not isinstance(projection["comparison_tags"], list) or not all(isinstance(tag, str) for tag in projection["comparison_tags"])): errors.append(f"projection {ident} has invalid comparison_tags")
        for field in ("observation_states", "capability_states", "observed_desired_states"):
            if field in projection and not isinstance(projection[field], dict): errors.append(f"projection {ident} has invalid {field}")
        for field in ("goal", "limitation", "current_state", "vendor", "oem_control_available"):
            if field in projection and not isinstance(projection[field], str): errors.append(f"projection {ident} has invalid {field}")
    if ids != case_ids: errors.append("projection system_id coverage must exactly equal matrix system_id coverage")
    return errors


def _profile(case: dict[str, Any], projection: dict[str, Any]) -> dict[str, object]:
    defaults: dict[str, Any] = {"goal":"UNKNOWN", "limitation":"UNKNOWN", "current_state":"UNKNOWN", "vendor":"UNKNOWN", "oem_control_available":"UNKNOWN", "comparison_tags":[], "observation_states":{}, "capability_states":{}, "observed_desired_states":{}}
    facts = {**defaults, **projection}
    return {"schema":"iy.system_profile/v1", "profile_id":case["system_id"], "ram":{}, "gpu":{"vendor":facts["vendor"], "driver_version":None}, "motherboard":{}, "bios":{}, "network":{"adapters":[]}, "goal":facts["goal"], "limitation":facts["limitation"], "comparison_tags":[case["system_id"], case["group"], *facts["comparison_tags"]], "challenge_projection":facts, "observation_states":facts["observation_states"], "capability_states":facts["capability_states"], "observed_desired_states":facts["observed_desired_states"]}


def run_comparison_matrix(path: Path, projection_path: Path | None = None) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(document, dict): raise ValueError("comparison matrix root must be an object")
    errors = validate_comparison_document(document)
    if errors: raise ValueError("; ".join(errors))
    contract_path = projection_path or DEFAULT_PROJECTION_PATH
    projection_document = json.loads(contract_path.read_text(encoding="utf-8"))
    if not isinstance(projection_document, dict): raise ValueError("projection contract root must be an object")
    ids = {case["system_id"] for case in document["systems"]}
    errors = validate_projection_document(projection_document, ids)
    if errors: raise ValueError("; ".join(errors))
    projections = {projection["system_id"]: projection for projection in projection_document["projections"]}
    reports = []
    for case in document["systems"]:
        profile = _profile(case, projections[case["system_id"]]); report = evaluate_recommendations(profile)
        for result in report["results"]:
            result["comparison_tags"] = profile["comparison_tags"]; result["challenge_projection"] = profile["challenge_projection"]
        reports.append({"case_id":case["system_id"], "cohort":case["group"], "expected_pressure":case["expected_behavior"], "actual":report})
    return {"schema":"iy.optimizer_comparison_execution/v1", "count":len(reports), "reports":reports}
