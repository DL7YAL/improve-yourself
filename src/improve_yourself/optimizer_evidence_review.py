"""Local, read-only user review over the canonical System Check optimizer input."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from .optimizer_input import build_optimizer_input


def _availability(item: dict[str, object]) -> str:
    classification = str(item.get("classification", ""))
    if classification in {"not_implemented", "technically_investigated_not_reliably_readable"}:
        return "NOT AVAILABLE"
    if str(item.get("assessment_status", "")).lower().find("unbekannt") >= 0:
        return "UNKNOWN"
    return "KNOWN"


def build_evidence_review(system_check: dict[str, object]) -> dict[str, object]:
    """Project System Check evidence only; never accept demo/replay or action input."""
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
    }


def render_evidence_review(review: dict[str, object], output: Path) -> Path:
    if review.get("schema") != "iy.optimizer_evidence_review/v1":
        raise ValueError("expected optimizer evidence review")
    rows = "".join(
        "<article><h2>{label} <small>{availability}</small></h2><p><b>Observed:</b> {state}</p>"
        "<p><b>Technical status:</b> {status}</p><p><b>Provenance:</b> {evidence}</p></article>".format(
            label=html.escape(str(item.get("label", item.get("id", "Unknown")))),
            availability=html.escape(str(item["availability"])), state=html.escape(str(item.get("observed_state", "NOT AVAILABLE"))),
            status=html.escape(str(item.get("assessment_status", "UNKNOWN"))),
            evidence=html.escape(json.dumps(item.get("evidence", {}), ensure_ascii=False)),
        ) for item in review.get("items", []) if isinstance(item, dict)
    )
    page = """<!doctype html><meta charset='utf-8'><title>Optimizer Evidence Review</title>
<style>body{{font:16px system-ui;background:#08111e;color:#eef4fb;max-width:960px;margin:auto;padding:24px}}article{{background:#111f32;border:1px solid #2a3d58;border-radius:10px;padding:14px;margin:12px 0}}small{{color:#8bd5ff}}code{{white-space:pre-wrap}}</style>
<h1>Optimizer Evidence Review</h1><p><b>READ-ONLY / LOCAL-ONLY</b> — no recommendation is an Apply instruction. No system change was made.</p><p>Unknown evidence remains UNKNOWN; unavailable readers remain NOT AVAILABLE.</p>{rows}""".format(rows=rows)
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
