"""Validate the fail-honest save record written at measured-pass completion."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


VERSION = "iy-benchmark/v1.2-candidate.2"


def validate_record(record: object) -> list[str]:
    if not isinstance(record, dict):
        return ["save data must be a JSON object"]
    errors = []
    expected = {
        "version": VERSION,
        "runtimeStatus": "complete",
        "measurementStatus": "unverified",
    }
    for key, value in expected.items():
        if record.get(key) != value:
            errors.append(f"{key}: expected {value!r}, got {record.get(key)!r}")
    completed_at = record.get("completedAt")
    if not isinstance(completed_at, (int, float)) or isinstance(completed_at, bool):
        errors.append(f"completedAt must be numeric, got {completed_at!r}")
    elif isinstance(completed_at, float) and not math.isfinite(completed_at):
        errors.append(f"completedAt must be finite, got {completed_at!r}")
    elif completed_at < 134:
        errors.append(f"completedAt is too early for the full run: {completed_at}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate candidate.2 save_local.txt after a measured pass."
    )
    parser.add_argument("save_data", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    raw = args.save_data.read_bytes()
    digest = hashlib.sha256(raw).hexdigest().upper()
    try:
        record = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        record = None
        errors = [f"invalid UTF-8 JSON: {error}"]
    else:
        errors = validate_record(record)

    payload = {
        "schema": "iy.cs2-benchmark-save-validation/v1",
        "benchmark_version": VERSION,
        "status": "PASS" if not errors else "PARTIAL",
        "runtime_status": "complete" if not errors else "unverified",
        "measurement_status": "unverified",
        "completed_at": record.get("completedAt") if isinstance(record, dict) else None,
        "input_sha256": digest,
        "errors": errors,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for key in (
            "status",
            "runtime_status",
            "measurement_status",
            "completed_at",
            "input_sha256",
        ):
            print(f"{key}={payload[key]}")
        for error in errors:
            print(f"ERROR={error}")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
