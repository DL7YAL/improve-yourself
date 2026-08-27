"""Local, read-only user review over the canonical System Check optimizer input."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from .optimizer_input import build_optimizer_input


_KNOWN_CLASSIFICATIONS = {
    "reliably_automatically_checked",
    "reliably_evaluated",
    "recognized_only",
}
_UNAVAILABLE_CLASSIFICATIONS = {
    "not_implemented",
    "technically_investigated_not_reliably_readable",
}
_REQUIRED_REVIEW_POLICY = {
    "local_only": True,
    "read_only": True,
    "changes_applied": False,
    "apply_available": False,
    "restore_available": False,
    "demo_or_replay_data_included": False,
}


def _availability(item: dict[str, object]) -> str:
    classification = item.get("classification")
    if not isinstance(classification, str) or classification not in _KNOWN_CLASSIFICATIONS | _UNAVAILABLE_CLASSIFICATIONS:
        raise ValueError("System Check has an unexpected or missing evidence classification")
    assessment_status = item.get("assessment_status")
    if not isinstance(assessment_status, str) or not assessment_status:
        raise ValueError("System Check evidence requires an assessment status")
    if classification in _UNAVAILABLE_CLASSIFICATIONS:
        return "NOT AVAILABLE"
    if "unbekannt" in assessment_status.lower():
        return "UNKNOWN"
    return "KNOWN"


def _validate_system_check_evidence(system_check: dict[str, object]) -> None:
    """Require the canonical fields needed to make a user-facing evidence claim."""
    checks = system_check.get("checks")
    if not isinstance(checks, list):
        raise ValueError("system check checks must be a list of evidence records")
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("system check checks must be evidence objects")
        classification = check.get("classification")
        if not isinstance(classification, str) or classification not in _KNOWN_CLASSIFICATIONS | _UNAVAILABLE_CLASSIFICATIONS:
            raise ValueError("System Check has an unexpected or missing evidence classification")
        user_view = check.get("user_view")
        if not isinstance(user_view, dict) or not isinstance(user_view.get("status"), str) or not user_view["status"]:
            raise ValueError("System Check evidence requires user_view.status")
        if not isinstance(check.get("evidence"), dict):
            raise ValueError("System Check evidence details must be an object")


def _validate_review_policy(review: dict[str, object]) -> None:
    policy = review.get("policy")
    if not isinstance(policy, dict) or any(policy.get(name) is not value for name, value in _REQUIRED_REVIEW_POLICY.items()):
        raise ValueError("review policy does not prove the local read-only boundary")


def _validate_review_items(items: list[object]) -> list[dict[str, object]]:
    if not all(isinstance(item, dict) for item in items):
        raise ValueError("review items must be evidence objects")
    evidence_items = [item for item in items if isinstance(item, dict)]
    for item in evidence_items:
        if item.get("availability") not in {"KNOWN", "UNKNOWN", "NOT AVAILABLE"}:
            raise ValueError("review item has an invalid availability")
        if not isinstance(item.get("assessment_status"), str) or not item["assessment_status"]:
            raise ValueError("review item requires an assessment status")
        if not isinstance(item.get("evidence"), dict):
            raise ValueError("review item evidence details must be an object")
    return evidence_items


def build_evidence_review(system_check: dict[str, object]) -> dict[str, object]:
    """Project System Check evidence only; never accept demo/replay or action input."""
    if not isinstance(system_check, dict):
        raise ValueError("expected System Check JSON object")
    _validate_system_check_evidence(system_check)
    optimizer_input = build_optimizer_input(system_check)
    policy = optimizer_input["policy"]
    if policy["changes_applied"] or policy["apply_or_restore_available"] or policy["demo_or_replay_data_included"]:
        raise ValueError("optimizer input violates the read-only evidence boundary")
    items = []
    for raw in optimizer_input["planning_items"]:
        item = dict(raw)
        item["availability"] = _availability(item)
        items.append(item)
    return {
        "schema": "iy.optimizer_evidence_review/v1",
        "source": optimizer_input["source"],
        "policy": {"local_only": True, "read_only": True, "changes_applied": False,
                   "apply_available": False, "restore_available": False, "demo_or_replay_data_included": False},
        "items": items,
        "unknown_or_unreadable_items": optimizer_input["optimizer_readiness"]["unknown_or_unreadable_items"],
        "network_mode": "OFFLINE" if system_check.get("policy", {}).get("official_vendor_comparisons") is False else "OFFICIAL COMPARISON",
    }


def render_evidence_review(review: dict[str, object], output: Path) -> Path:
    if review.get("schema") != "iy.optimizer_evidence_review/v1":
        raise ValueError("expected optimizer evidence review")
    _validate_review_policy(review)
    items = review.get("items")
    if not isinstance(items, list):
        raise ValueError("review items must be evidence objects")
    evidence_items = _validate_review_items(items)
    counts = {state: sum(item["availability"] == state for item in evidence_items) for state in ("KNOWN", "UNKNOWN", "NOT AVAILABLE")}
    rows = "".join(
        "<article><h2>{label} <small>{availability}</small></h2><p><b>Observed:</b> {state}</p>"
        "<p><b>Technical status:</b> {status}</p>{source}<p><b>Evidence details:</b> {evidence}</p></article>".format(
            label=html.escape(str(item.get("label", item.get("id", "Unknown")))),
            availability=html.escape(str(item["availability"])), state=html.escape(str(item.get("observed_state", "NOT AVAILABLE"))),
            status=html.escape(str(item.get("assessment_status", "UNKNOWN"))),
            source=("<p><b>Evidence source:</b> {}</p>".format(html.escape(str(item["evidence"].get("source") or item["evidence"].get("official_source"))))
                    if isinstance(item.get("evidence"), dict) and isinstance(item["evidence"].get("source") or item["evidence"].get("official_source"), str) else ""),
            evidence=html.escape(json.dumps(item.get("evidence", {}), ensure_ascii=False)),
        ) for item in evidence_items
    )
    page = """<!doctype html><meta charset='utf-8'><title>Optimizer Evidence Review</title>
<style>body{{font:16px system-ui;background:#08111e;color:#eef4fb;max-width:960px;margin:auto;padding:24px}}article{{background:#111f32;border:1px solid #2a3d58;border-radius:10px;padding:14px;margin:12px 0}}small{{color:#8bd5ff}}code{{white-space:pre-wrap}}</style>
<h1>Optimizer Evidence Review</h1><p><b>LOCAL REPORT / READ-ONLY</b> — no recommendation changes the system. No system change was made.</p><p><b>Report mode:</b> LOCAL READ-ONLY · <b>Network mode:</b> {network}</p><p><b>Summary:</b> KNOWN {known} · UNKNOWN {unknown} · NOT AVAILABLE {unavailable}</p><p><b>Legend:</b> KNOWN is supported by current evidence. UNKNOWN means evidence is insufficient or failed safely. NOT AVAILABLE means the current reader cannot reliably provide the value.</p><p>Artifacts remain local and no user evidence is uploaded. In normal mode System Check may query fixed official vendor sources; OFFLINE makes no vendor comparison requests.</p>{rows}""".format(rows=rows, network=html.escape(str(review.get("network_mode", "OFFICIAL COMPARISON"))), known=counts["KNOWN"], unknown=counts["UNKNOWN"], unavailable=counts["NOT AVAILABLE"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a local read-only Optimizer Evidence review from System Check")
    parser.add_argument("system_check", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/optimizer-evidence-review.html"))
    args = parser.parse_args()
    try:
        payload = json.loads(args.system_check.read_text(encoding="utf-8"))
        if not isinstance(payload, dict): raise ValueError("expected System Check JSON object")
        print(render_evidence_review(build_evidence_review(payload), args.output))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    return 0
