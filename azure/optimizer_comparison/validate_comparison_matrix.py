#!/usr/bin/env python3
"""Validate the independent read-only Optimizer comparison cohort.

This validator checks dataset integrity only. It does not import Optimizer
code, evaluate recommendations, access a machine, call Azure, or create any
performance claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

GROUPS = {"realistic", "edge_stress", "adversarial"}
REQUIRED = {
    "system_id", "group", "hardware", "settings", "challenge",
    "expected_behavior", "boundaries", "safety_traps",
}
FORBIDDEN_FIELDS = {"recommendation", "recommendations", "action", "apply_plan"}
FORBIDDEN_CLAIMS = ("apply automatically", "install driver", "real performance result")


def validate(document: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if document.get("schema") != "iy.optimizer_independent_comparison_matrix/v1":
        errors.append("unexpected schema")
    policy = document.get("policy")
    if not isinstance(policy, dict):
        errors.append("missing policy")
    else:
        for key, expected in {
            "read_only": True, "real_evidence_allowed": False,
            "apply_authority": False, "performance_claims_allowed": False,
            "canonical_matrix_replacement": False,
        }.items():
            if policy.get(key) is not expected:
                errors.append(f"policy.{key} must be {expected!r}")
    systems = document.get("systems")
    if not isinstance(systems, list) or len(systems) != 60:
        return errors + ["systems must contain exactly 60 records"]
    ids: set[str] = set()
    counts = {group: 0 for group in GROUPS}
    for index, system in enumerate(systems, start=1):
        if not isinstance(system, dict):
            errors.append(f"system {index} is not an object")
            continue
        missing = REQUIRED - system.keys()
        if missing:
            errors.append(f"system {index} missing: {', '.join(sorted(missing))}")
        unexpected = FORBIDDEN_FIELDS & system.keys()
        if unexpected:
            errors.append(f"system {index} contains engine-owned field(s): {', '.join(sorted(unexpected))}")
        system_id = system.get("system_id")
        if not isinstance(system_id, str) or not system_id.startswith("cmp-"):
            errors.append(f"system {index} has invalid system_id")
        elif system_id in ids:
            errors.append(f"duplicate system_id: {system_id}")
        else:
            ids.add(system_id)
        group = system.get("group")
        if group not in GROUPS:
            errors.append(f"system {system_id} has invalid group")
        else:
            counts[str(group)] += 1
        combined = " ".join(str(system.get(key, "")) for key in REQUIRED).lower()
        for forbidden in FORBIDDEN_CLAIMS:
            if forbidden in combined:
                errors.append(f"system {system_id} contains forbidden claim: {forbidden}")
    for group, count in counts.items():
        if count != 20:
            errors.append(f"{group} must contain exactly 20 systems, found {count}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    args = parser.parse_args()
    try:
        document = json.loads(args.matrix.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read matrix: {exc}")
        return 2
    if not isinstance(document, dict):
        print("ERROR: matrix root must be an object")
        return 2
    errors = validate(document)
    if errors:
        print("Comparison matrix validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Independent 60-system Optimizer comparison matrix validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
