"""Canonical, read-only optimizer evidence and recommendation foundation.

This is the single shared infrastructure for System, Graphics, Network and
BIOS domains.  It selects transparent recommendations only; it has no apply,
registry, driver, BIOS or network write path.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

from .optimizer_evidence import synthetic_system_matrix
from .system_check import collect_windows_facts


FOUNDATION_SCHEMA = "iy.optimizer_foundation/v1"
SYSTEM_PROFILE_SCHEMA = "iy.system_profile/v1"
VALIDATION_SCHEMA = "iy.optimizer_validation_result/v1"


class OptimizerDomain(StrEnum):
    SYSTEM = "SYSTEM_OPTIMIZER"
    GRAPHICS = "GRAPHICS_OPTIMIZER"
    NETWORK = "NETWORK_OPTIMIZER"
    BIOS = "BIOS_OPTIMIZER"


class RecommendationState(StrEnum):
    RECOMMENDED = "RECOMMENDED"
    ALREADY_RECOMMENDED = "ALREADY_RECOMMENDED"
    CONDITIONAL = "CONDITIONAL"
    NO_CHANGE = "NO_CHANGE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class RuleMaturity(StrEnum):
    RELEASE_VERIFIED = "RELEASE_VERIFIED"
    CONDITIONAL_VERIFIED = "CONDITIONAL_VERIFIED"
    EXPERIMENTAL = "EXPERIMENTAL"
    REJECTED_NO_BENEFIT = "REJECTED_NO_BENEFIT"


class RiskClass(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class RuleCompatibility:
    compatibility_id: str
    required: tuple[tuple[str, str, object], ...] = ()
    excluded: tuple[tuple[str, str, object], ...] = ()
    conflicts_with: tuple[str, ...] = ()
    rationale: str = ""


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    rule_id: str
    source_type: str
    source: str
    affected_system_class: str
    result: str
    quality: str
    provenance: str
    evidence_version: str | None = None
    observed_at_utc: str | None = None


@dataclass(frozen=True)
class OptimizationRule:
    rule_id: str
    domain: OptimizerDomain
    title: str
    setting: str
    possible_states: tuple[str, ...]
    goal: str
    readable: bool
    changeable_later: bool
    restore_capable: bool
    restart_required: bool
    risk_class: RiskClass
    maturity: RuleMaturity
    compatibility: RuleCompatibility
    evidence: tuple[EvidenceRecord, ...]
    explanation: str
    manual_action_required: bool = False
    guidance_available: bool = False
    screenshot_verification_later: bool = False

    def as_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["domain"] = self.domain.value
        result["risk_class"] = self.risk_class.value
        result["maturity"] = self.maturity.value
        return result


@dataclass(frozen=True)
class ValidationResult:
    validation_id: str
    rule_id: str
    profile_id: str
    source: str
    result: str
    measured: bool = False
    metrics: dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {"schema": VALIDATION_SCHEMA, **asdict(self)}


def _path(profile: dict[str, object], dotted: str) -> object | None:
    value: object = profile
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _matches(profile: dict[str, object], condition: tuple[str, str, object]) -> tuple[bool, str | None]:
    path, operator, expected = condition
    actual = _path(profile, path)
    if actual is None:
        return False, path
    if operator == "equals":
        return actual == expected, None
    if operator == "present":
        return (actual is not None) is bool(expected), None
    if operator == "gte":
        return isinstance(actual, (int, float)) and actual >= expected, None
    if operator == "lt":
        return isinstance(actual, (int, float)) and actual < expected, None
    raise ValueError(f"Unsupported compatibility operator: {operator}")


def fixture_rules() -> tuple[OptimizationRule, ...]:
    """Five explicitly fixture-only rules; none assert a performance outcome."""
    def record(rule_id: str, domain: OptimizerDomain) -> EvidenceRecord:
        return EvidenceRecord(f"fixture-evidence-{rule_id}", rule_id, "FIXTURE", "optimizer_foundation fixture", domain.value, "TEST_ONLY", "SYNTHETIC", "No real system or performance claim.")
    return (
        OptimizationRule("fixture-system-memory", OptimizerDomain.SYSTEM, "Fixture System Memory", "memory.capacity_gb", ("KNOWN",), "Schema matching", True, False, True, False, RiskClass.LOW, RuleMaturity.RELEASE_VERIFIED, RuleCompatibility("compat-fixture-system", (("ram.capacity_gb", "gte", 16),), (), (), "Fixture requires known 16 GB RAM."), (record("fixture-system-memory", OptimizerDomain.SYSTEM),), "Fixture-only System rule."),
        OptimizationRule("fixture-graphics-driver", OptimizerDomain.GRAPHICS, "Fixture Graphics Driver", "gpu.driver_version", ("KNOWN",), "Conditional matching", True, False, True, False, RiskClass.LOW, RuleMaturity.CONDITIONAL_VERIFIED, RuleCompatibility("compat-fixture-graphics", (("gpu.vendor", "equals", "NVIDIA"), ("gpu.driver_version", "present", True)), (), (), "Fixture requires NVIDIA driver evidence."), (record("fixture-graphics-driver", OptimizerDomain.GRAPHICS),), "Fixture-only Graphics rule."),
        OptimizationRule("fixture-network-link", OptimizerDomain.NETWORK, "Fixture Network Link", "network.adapters.0.link_speed_mbps", ("KNOWN",), "Unknown handling", True, False, True, False, RiskClass.LOW, RuleMaturity.CONDITIONAL_VERIFIED, RuleCompatibility("compat-fixture-network", (("network.adapters", "present", True),), (), (), "Fixture requires an observed adapter."), (record("fixture-network-link", OptimizerDomain.NETWORK),), "Fixture-only Network rule."),
        OptimizationRule("fixture-bios-guidance", OptimizerDomain.BIOS, "Fixture BIOS Guidance", "bios.version", ("KNOWN",), "Manual guidance metadata", True, False, True, True, RiskClass.HIGH, RuleMaturity.CONDITIONAL_VERIFIED, RuleCompatibility("compat-fixture-bios", (("motherboard.product", "present", True), ("bios.version", "present", True)), (), (), "Fixture requires board and BIOS evidence."), (record("fixture-bios-guidance", OptimizerDomain.BIOS),), "Fixture-only BIOS rule; never automatically changeable.", True, True, True),
        OptimizationRule("fixture-conditional-exclusion", OptimizerDomain.SYSTEM, "Fixture Conditional Exclusion", "windows.build", ("KNOWN",), "Exclusion behavior", True, False, True, False, RiskClass.LOW, RuleMaturity.CONDITIONAL_VERIFIED, RuleCompatibility("compat-fixture-exclusion", (("windows.build", "gte", 22000),), (("ram.capacity_gb", "lt", 16),), (), "Fixture excludes low-memory systems."), (record("fixture-conditional-exclusion", OptimizerDomain.SYSTEM),), "Fixture-only conditional/exclusion rule."),
    )


def evaluate_recommendations(profile: dict[str, object], rules: Iterable[OptimizationRule] | None = None) -> dict[str, object]:
    results: list[dict[str, object]] = []
    accepted: set[str] = set()
    for rule in rules or fixture_rules():
        missing: set[str] = set()
        unmet: list[str] = []
        excluded = False
        for condition in rule.compatibility.required:
            matched, absent = _matches(profile, condition)
            if absent: missing.add(absent)
            elif not matched: unmet.append(condition[0])
        for condition in rule.compatibility.excluded:
            matched, absent = _matches(profile, condition)
            if absent: missing.add(absent)
            if matched: excluded = True
        if any(conflict in accepted for conflict in rule.compatibility.conflicts_with):
            state, rationale = RecommendationState.NO_CHANGE, "Conflicts with an already selected compatible rule."
        elif missing:
            state, rationale = RecommendationState.INSUFFICIENT_EVIDENCE, "Missing evidence: " + ", ".join(sorted(missing))
        elif excluded:
            state, rationale = RecommendationState.NO_CHANGE, "Explicit compatibility exclusion."
        elif unmet:
            state, rationale = RecommendationState.CONDITIONAL, "Conditions not currently met: " + ", ".join(sorted(unmet))
        elif rule.maturity in {RuleMaturity.EXPERIMENTAL, RuleMaturity.REJECTED_NO_BENEFIT}:
            state, rationale = RecommendationState.NO_CHANGE, f"Rule maturity {rule.maturity.value} is not eligible for Improve recommendations."
        elif isinstance(profile.get("current_recommendations"), dict) and profile["current_recommendations"].get(rule.rule_id) is True:
            state, rationale = RecommendationState.ALREADY_RECOMMENDED, "The read-only profile records the recommended state already present."
        else:
            state, rationale = RecommendationState.RECOMMENDED, "Fixture compatibility conditions are met."
        if state in {RecommendationState.RECOMMENDED, RecommendationState.ALREADY_RECOMMENDED}:
            accepted.add(rule.rule_id)
        results.append({"rule_id": rule.rule_id, "domain": rule.domain.value, "state": state.value, "rationale": rationale, "missing_evidence": sorted(missing), "rule": rule.as_dict()})
    return {"schema": FOUNDATION_SCHEMA, "profile_schema": profile.get("schema", "unknown"), "profile_id": profile.get("profile_id", profile.get("system_id", "unknown")), "read_only": True, "results": results}


def recommendation_detail_view_model(result: dict[str, object]) -> dict[str, object]:
    """Stable no-apply panel contract for later desktop UI work."""
    rule = result["rule"]
    assert isinstance(rule, dict)
    return {"title": rule["title"], "current_state": "unknown/not_available", "improve_recommendation": result["state"], "status": result["state"], "what_is_it": rule["setting"], "why_for_this_system": result["rationale"], "what_can_change": rule["goal"], "evidence_validity": rule["evidence"], "risk_notes": rule["risk_class"], "restore_change_information": {"restore_capable": rule["restore_capable"], "changeable_later": rule["changeable_later"]}, "guidance": {"manual_action_required": rule["manual_action_required"], "guidance_available": rule["guidance_available"], "screenshot_verification_later": rule["screenshot_verification_later"]}}


def system_profile_from_facts(facts: dict[str, Any]) -> dict[str, object]:
    """Canonical persistable profile, preserving unavailable values as None."""
    gpus = facts.get("gpus") if isinstance(facts.get("gpus"), list) else []
    displays = facts.get("displays") if isinstance(facts.get("displays"), list) else []
    memory = dict(facts.get("memory") or {})
    memory.setdefault("capacity_gb", memory.get("total_gb"))
    return {"schema": SYSTEM_PROFILE_SCHEMA, "profile_id": "local-read-only-system", "profile_source": "READ_ONLY_COLLECTOR", "policy": {"read_only": True, "changes_applied": False}, "cpu": facts.get("cpu") or {}, "gpu": gpus[0] if gpus else {"name": None, "vendor": None, "driver_version": None}, "ram": memory, "motherboard": facts.get("motherboard") or {}, "bios": facts.get("bios") or {}, "windows": facts.get("windows") or {}, "display": displays, "network": {"adapters": facts.get("network_adapters") or []}, "applications": {"cs2": facts.get("cs2") if isinstance(facts.get("cs2"), dict) else {"status": "NOT_AVAILABLE"}}, "field_observation": {"cpu": "DETECTED", "gpu": "DETECTED" if gpus else "NOT_AVAILABLE", "ram_speed": "NOT_RELIABLY_DETECTABLE" if memory.get("speed_mt_s") is None else "DETECTED", "network_mtu": "DETECTED" if any(item.get("mtu") is not None for item in facts.get("network_adapters") or [] if isinstance(item, dict)) else "NOT_AVAILABLE", "cs2.configuration": "NOT_AVAILABLE", "gpu.driver_options": "NOT_RELIABLY_DETECTABLE", "current_cpu_gpu_limitation": "NOT_RELIABLY_DETECTABLE"}, "unknown_fields": ("cs2.configuration", "gpu.driver_options", "current_cpu_gpu_limitation")}


def collect_system_profile() -> dict[str, object]:
    return system_profile_from_facts(collect_windows_facts())


def run_fixture_harness() -> dict[str, object]:
    matrix = synthetic_system_matrix()["systems"]
    reports = [evaluate_recommendations(profile) for profile in matrix if isinstance(profile, dict)]
    states = {state.value: 0 for state in RecommendationState}
    for report in reports:
        for result in report["results"]:
            states[str(result["state"])] += 1
    return {"schema": FOUNDATION_SCHEMA, "label": "SYNTHETIC / DECISION LOGIC ONLY / NOT MEASURED", "system_count": len(reports), "states": states, "reports": reports}


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Improve Yourself system profile collector")
    parser.add_argument("--output", default="results/system-profile.json")
    parser.add_argument("--fixture-harness", action="store_true")
    args = parser.parse_args()
    payload = run_fixture_harness() if args.fixture_harness else collect_system_profile()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output:
        json.dump(payload, output, ensure_ascii=False, indent=2)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
