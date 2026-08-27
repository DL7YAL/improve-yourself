"""Translation-only runner for the separate Azure comparison cohort."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .optimizer_foundation import evaluate_recommendations

COHORTS={"realistic","edge_stress","adversarial"}
FIELDS={"system_id","group","hardware","settings","challenge","expected_behavior","boundaries","safety_traps"}
PROJECTION_FIELDS={"goal","limitation","current_state","observation_availability","capability_support","vendor","oem_control_available","comparison_tags","observation_states","capability_states","observed_desired_states"}

def validate_comparison_document(document: dict[str, Any]) -> list[str]:
    cases=document.get("systems"); errors=[]
    if not isinstance(cases,list) or len(cases)!=60: return ["systems must contain exactly 60 cases"]
    ids=set(); counts={x:0 for x in COHORTS}
    for number,case in enumerate(cases,1):
        if not isinstance(case,dict): errors.append(f"case {number} is not an object"); continue
        if FIELDS-case.keys(): errors.append(f"case {number} missing required fields")
        ident=case.get("system_id"); group=case.get("group")
        if not isinstance(ident,str) or ident in ids: errors.append(f"case {number} has invalid/duplicate system_id")
        else: ids.add(ident)
        if group not in COHORTS: errors.append(f"case {ident} has invalid cohort")
        else: counts[group]+=1
        if any(not isinstance(case.get(k),str) for k in FIELDS-{"system_id","group"}): errors.append(f"case {ident} has non-string prose field")
    return errors+[f"{g} must contain 20 cases" for g,n in counts.items() if n!=20]

def _profile(case: dict[str, Any]) -> dict[str, object]:
    raw=case.get("projection", {})
    if not isinstance(raw,dict) or set(raw)-PROJECTION_FIELDS: raise ValueError("invalid structured projection")
    defaults={"goal":"UNKNOWN","limitation":"UNKNOWN","current_state":"UNKNOWN","observation_availability":"UNKNOWN","capability_support":"UNKNOWN","vendor":"UNKNOWN","oem_control_available":"UNKNOWN","comparison_tags":[],"observation_states":{},"capability_states":{},"observed_desired_states":{}}
    p={**defaults,**raw}
    if not isinstance(p["comparison_tags"],list) or any(not isinstance(p[k],dict) for k in ("observation_states","capability_states","observed_desired_states")): raise ValueError("invalid structured projection types")
    return {"schema":"iy.system_profile/v1","profile_id":case["system_id"],"ram":{},"gpu":{"vendor":p["vendor"],"driver_version":None},"motherboard":{},"bios":{},"network":{"adapters":[]},"goal":p["goal"],"limitation":p["limitation"],"comparison_tags":[case["system_id"],case["group"],*p["comparison_tags"]],"challenge_projection":p,"observation_states":p["observation_states"],"capability_states":p["capability_states"],"observed_desired_states":p["observed_desired_states"]}

def run_comparison_matrix(path: Path) -> dict[str, object]:
    document=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(document,dict): raise ValueError("comparison matrix root must be an object")
    errors=validate_comparison_document(document)
    if errors: raise ValueError("; ".join(errors))
    reports=[]
    for case in document["systems"]:
        profile=_profile(case); report=evaluate_recommendations(profile)
        for result in report["results"]:
            result["comparison_tags"]=profile["comparison_tags"]; result["challenge_projection"]=profile["challenge_projection"]
        reports.append({"case_id":case["system_id"],"cohort":case["group"],"expected_pressure":case["expected_behavior"],"actual":report})
    return {"schema":"iy.optimizer_comparison_execution/v1","count":len(reports),"reports":reports}
