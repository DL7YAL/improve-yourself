"""Translation-only runner for the separate Azure comparison cohort."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .optimizer_foundation import evaluate_recommendations

def _profile(case: dict[str, Any]) -> dict[str, object]:
    text = " ".join(str(case.get(k, "")) for k in ("hardware", "settings", "boundaries", "challenge")).upper()
    vendor = "NVIDIA" if "NVIDIA" in text or "RTX" in text else "AMD" if "RADEON" in text else "UNKNOWN"
    known = "UNKNOWN" not in text and "NOT AVAILABLE" not in text
    profile: dict[str, object] = {"schema":"iy.system_profile/v1","profile_id":case["system_id"],"ram":{"capacity_gb":32 if "32GB" in text or "64GB" in text else 8 if "8GB" in text else 16},"gpu":{"vendor":vendor,"driver_version":"declared" if known else None},"motherboard":{"product":"declared" if known else None},"bios":{"version":"declared" if known else None},"network":{"adapters":[{"name":"declared"}] if known else []},"comparison_tags":[case["group"],case.get("challenge","")],"field_observation":{"comparison":"KNOWN" if known else "UNKNOWN"}}
    if "KNOWN OPTIMAL" in text:
        profile["observed_desired_states"]={"fixture-system-memory":True}
    return profile

def run_comparison_matrix(path: Path) -> dict[str, object]:
    document=json.loads(path.read_text(encoding="utf-8-sig"))
    cases=document.get("systems")
    if not isinstance(cases,list) or len(cases)!=60: raise ValueError("comparison matrix must contain 60 cases")
    reports=[]
    for case in cases:
        if not isinstance(case,dict): raise ValueError("comparison case must be an object")
        report=evaluate_recommendations(_profile(case))
        for result in report["results"]:
            result["comparison_tags"]=[case["system_id"],case["group"],str(case.get("expected_behavior",""))]
        reports.append({"case_id":case["system_id"],"cohort":case["group"],"expected_pressure":case["expected_behavior"],"actual":report})
    return {"schema":"iy.optimizer_comparison_execution/v1","count":len(reports),"reports":reports}
