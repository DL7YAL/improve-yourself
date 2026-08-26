"""Read-only System Check export view over the canonical Optimizer Evidence boundary."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .optimizer_evidence import GoalProfile, profile_from_system_check
from .system_check import SYSTEM_CHECK_SCHEMA


OPTIMIZER_INPUT_SCHEMA = "iy.optimizer_input/v1"


def _validated_system_check(payload: dict[str, object]) -> list[dict[str, object]]:
    if payload.get("schema") != SYSTEM_CHECK_SCHEMA:
        raise ValueError(f"expected {SYSTEM_CHECK_SCHEMA}")
    policy = payload.get("policy")
    if not isinstance(policy, dict) or policy.get("read_only") is not True or policy.get("changes_applied") is not False:
        raise ValueError("system check is not documented as read-only evidence")
    checks = payload.get("checks")
    if not isinstance(checks, list) or not all(isinstance(check, dict) for check in checks):
        raise ValueError("system check checks must be a list of evidence records")
    return checks


def _planning_item(check: dict[str, object]) -> dict[str, object]:
    user_view = check.get("user_view") if isinstance(check.get("user_view"), dict) else {}
    return {
        "id": check.get("id"),
        "label": check.get("label"),
        "observed_state": check.get("summary"),
        "technical_status": check.get("status"),
        "classification": check.get("classification", "not_implemented"),
        "assessment_status": user_view.get("status", "Nicht prüfbar / unbekannt"),
        "priority": user_view.get("priority", "informativ"),
        "recommendation": user_view.get("action", "Keine automatische Änderung wurde vorgenommen."),
        "relevance": user_view.get("relevance", "Keine zusätzliche Bewertung verfügbar."),
        "evidence": check.get("evidence", {}),
    }


def build_optimizer_input(system_check: dict[str, object], *, goal: GoalProfile = GoalProfile.PERFORMANCE) -> dict[str, object]:
    """Expose only documented System Check evidence for read-only optimizer planning.

    This is an export view, not a second optimizer: the canonical profile is
    produced by ``profile_from_system_check`` and no demo, replay or apply
    input is accepted or copied.
    """
    checks = _validated_system_check(system_check)
    profile = profile_from_system_check(system_check, goal=goal)
    if profile is None:  # Defensive parity with the shared boundary contract.
        raise ValueError("system check cannot be projected as read-only optimizer evidence")
    planning_items = [_planning_item(check) for check in checks]
    unknown = [
        item["id"]
        for item in planning_items
        if item["classification"] in {"technically_investigated_not_reliably_readable", "not_implemented"}
    ]
    return {
        "schema": OPTIMIZER_INPUT_SCHEMA,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source": {
            "schema": SYSTEM_CHECK_SCHEMA,
            "generated_at_utc": system_check.get("generated_at_utc"),
            "read_only": True,
            "changes_applied": False,
        },
        "system_summary": system_check.get("user_summary", {}),
        "planning_items": planning_items,
        "foundation_profile": profile,
        "optimizer_readiness": {
            "input_complete": True,
            "unknown_or_unreadable_items": unknown,
            "automatic_apply_authorized": False,
        },
        "policy": {
            "planning_input_only": True,
            "changes_applied": False,
            "apply_or_restore_available": False,
            "demo_or_replay_data_included": False,
        },
    }
