"""Read-only boundary between System Check evidence and a future Optimizer planner.

This module deliberately contains no recommendation application, restore action,
registry write, driver operation, or BIOS/UEFI interaction.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .system_check import SYSTEM_CHECK_SCHEMA

OPTIMIZER_INPUT_SCHEMA = "iy.optimizer_input/v1"


def build_optimizer_input(system_check: dict[str, Any]) -> dict[str, Any]:
    """Validate and project explicit System Check evidence for optimizer planning.

    The caller must run the System Check separately. Only its documented,
    read-only output becomes an input artifact; no demo/replay data is accepted
    or inferred here.
    """
    if system_check.get("schema") != SYSTEM_CHECK_SCHEMA:
        raise ValueError(f"expected {SYSTEM_CHECK_SCHEMA}")
    policy = system_check.get("policy")
    if not isinstance(policy, dict) or policy.get("read_only") is not True or policy.get("changes_applied") is not False:
        raise ValueError("system check is not documented as read-only evidence")
    checks = system_check.get("checks")
    if not isinstance(checks, list):
        raise ValueError("system check checks must be a list")
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
        "checks": checks,
        "policy": {
            "planning_input_only": True,
            "changes_applied": False,
            "apply_or_restore_available": False,
            "demo_or_replay_data_included": False,
        },
    }


def export_optimizer_input(system_path: Path, output_path: Path) -> Path:
    value = json.loads(system_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected System Check JSON object")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(build_optimizer_input(value), ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a read-only Optimizer planning input from an explicit System Check")
    parser.add_argument("system_check", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/optimizer-input.json"))
    args = parser.parse_args()
    try:
        print(export_optimizer_input(args.system_check, args.output))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
