"""Fail-closed, data-driven import gate for future curated Improve Rule Packs."""

from __future__ import annotations

from dataclasses import asdict
from enum import StrEnum
from typing import Any

from .optimizer_foundation import (
    EvidenceRecord, OptimizationRule, OptimizerDomain, RiskClass, RuleCompatibility,
    RuleMaturity, RuleType, fixture_rules, validate_synthetic_rule_pack,
)


RULE_PACK_SCHEMA = "iy.improve_rule_pack/v1"


class RulePackClass(StrEnum):
    RELEASE_CANDIDATE = "RELEASE_CANDIDATE"
    CONDITIONAL = "CONDITIONAL"
    EXPERIMENTAL = "EXPERIMENTAL"
    NO_CHANGE = "NO_CHANGE"
    SECURITY_PERFORMANCE_TRADEOFF = "SECURITY_PERFORMANCE_TRADEOFF"
    REJECTED = "REJECTED"


class RulePackValidationError(ValueError):
    pass


def fixture_rule_pack_document() -> dict[str, object]:
    """A fixture-only pack proving the exact external data format; not activatable."""
    items: list[dict[str, object]] = []
    for rule in fixture_rules():
        record = rule.as_dict()
        record.update({"description": rule.explanation, "pack_class": RulePackClass.SECURITY_PERFORMANCE_TRADEOFF.value if rule.rule_type is RuleType.SECURITY_PERFORMANCE_TRADEOFF else RulePackClass.CONDITIONAL.value, "current_state_path": rule.setting, "candidate_state": "FIXTURE_ONLY", "version": "fixture-1", "provenance": "TEST_ONLY; not a real Improve rule", "read_capable": rule.readable, "apply_capable": False, "restore_capable": rule.restore_capable})
        items.append(record)
    return {"schema": RULE_PACK_SCHEMA, "pack_id": "fixture-rule-pack", "pack_version": "fixture-1", "provenance": "SYNTHETIC / TEST ONLY", "rules": items}


def _conditions(value: object, field: str) -> tuple[tuple[str, str, object], ...]:
    if not isinstance(value, (list, tuple)):
        raise RulePackValidationError(f"{field} must be a list")
    conditions: list[tuple[str, str, object]] = []
    allowed = {"equals", "present", "gte", "lt"}
    for condition in value:
        if not isinstance(condition, (list, tuple)) or len(condition) != 3 or not isinstance(condition[0], str) or condition[1] not in allowed:
            raise RulePackValidationError(f"invalid {field} condition")
        conditions.append((condition[0], condition[1], condition[2]))
    return tuple(conditions)


def import_rule_pack(document: dict[str, object]) -> tuple[OptimizationRule, ...]:
    if document.get("schema") != RULE_PACK_SCHEMA or not isinstance(document.get("rules"), list):
        raise RulePackValidationError("invalid rule-pack schema")
    seen: set[str] = set()
    imported: list[OptimizationRule] = []
    for raw in document["rules"]:
        if not isinstance(raw, dict):
            raise RulePackValidationError("rule must be an object")
        rule_id = raw.get("rule_id")
        if not isinstance(rule_id, str) or not rule_id or rule_id in seen:
            raise RulePackValidationError("rule_id must be stable and unique")
        seen.add(rule_id)
        try:
            domain = OptimizerDomain(str(raw["domain"]))
            risk = RiskClass(str(raw["risk_class"]))
            pack_class = RulePackClass(str(raw["pack_class"]))
        except (KeyError, ValueError) as error:
            raise RulePackValidationError("invalid domain, risk_class or pack_class") from error
        required_text = ("title", "setting", "description", "current_state_path", "candidate_state", "version", "provenance", "explanation")
        if not all(isinstance(raw.get(key), str) and raw[key] for key in required_text):
            raise RulePackValidationError("required explanation/state/provenance metadata missing")
        required = _conditions((raw.get("compatibility") or {}).get("required") if isinstance(raw.get("compatibility"), dict) else None, "compatibility.required")
        excluded = _conditions((raw.get("compatibility") or {}).get("excluded", []) if isinstance(raw.get("compatibility"), dict) else None, "compatibility.excluded")
        if set(required) & set(excluded):
            raise RulePackValidationError("contradictory required and exclusion condition")
        evidence_raw = raw.get("evidence")
        if not isinstance(evidence_raw, (list, tuple)) or not evidence_raw:
            raise RulePackValidationError("at least one evidence record is required")
        evidence: list[EvidenceRecord] = []
        for item in evidence_raw:
            if not isinstance(item, dict) or not all(isinstance(item.get(key), str) and item[key] for key in ("evidence_id", "source_type", "source", "affected_system_class", "result", "quality", "provenance")):
                raise RulePackValidationError("invalid evidence record")
            evidence.append(EvidenceRecord(str(item["evidence_id"]), rule_id, str(item["source_type"]), str(item["source"]), str(item["affected_system_class"]), str(item["result"]), str(item["quality"]), str(item["provenance"]), item.get("evidence_version") if isinstance(item.get("evidence_version"), str) else None, item.get("observed_at_utc") if isinstance(item.get("observed_at_utc"), str) else None))
        maturity = RuleMaturity.EXPERIMENTAL if pack_class is RulePackClass.EXPERIMENTAL else (RuleMaturity.REJECTED_NO_BENEFIT if pack_class in {RulePackClass.REJECTED, RulePackClass.NO_CHANGE} else RuleMaturity.CONDITIONAL_VERIFIED)
        rule_type = RuleType.SECURITY_PERFORMANCE_TRADEOFF if pack_class is RulePackClass.SECURITY_PERFORMANCE_TRADEOFF else RuleType.STANDARD
        compatibility = raw["compatibility"] if isinstance(raw.get("compatibility"), dict) else {}
        imported.append(OptimizationRule(
            rule_id, domain, str(raw["title"]), str(raw["setting"]),
            tuple(str(x) for x in raw.get("possible_states", ("UNKNOWN",))),
            str(raw.get("goal") or "Curated rule-pack evaluation"),
            bool(raw.get("read_capable")), bool(raw.get("apply_capable")),
            bool(raw.get("restore_capable")), bool(raw.get("restart_required")),
            risk, maturity,
            RuleCompatibility(f"compat-{rule_id}", required, excluded,
                              tuple(str(x) for x in raw.get("conflicts_with", ())),
                              str(compatibility.get("rationale") or "")),
            tuple(evidence), str(raw["explanation"]),
            bool(raw.get("manual_action_required")), bool(raw.get("guidance_available")),
            bool(raw.get("screenshot_verification_later")), rule_type,
            bool(raw.get("fixture_only", False)),
        ))
    return tuple(imported)


def validate_rule_pack(document: dict[str, object]) -> dict[str, object]:
    rules = import_rule_pack(document)
    return {"schema": RULE_PACK_SCHEMA, "pack_id": document["pack_id"], "pack_version": document["pack_version"], "valid": True, "rules": [rule.as_dict() for rule in rules], "synthetic_regression": validate_synthetic_rule_pack(rules)}
