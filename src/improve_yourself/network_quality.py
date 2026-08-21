"""Local, declared-target network quality collection with no recommendation authority."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Callable
from uuid import uuid4

from .optimizer_foundation import EvidenceRecord


NETWORK_QUALITY_SCHEMA = "iy.network_quality_measurement/v1"


class TargetClass(StrEnum):
    LOCAL_GATEWAY = "LOCAL_GATEWAY"
    CONTROLLED_PUBLIC_TARGET = "CONTROLLED_PUBLIC_TARGET"
    GAME_RELEVANT_TARGET = "GAME_RELEVANT_TARGET"


class MeasurementStatus(StrEnum):
    VALID = "VALID"
    TOO_FEW_SAMPLES = "TOO_FEW_SAMPLES"
    TARGET_UNREACHABLE = "TARGET_UNREACHABLE"
    TIMEOUT = "TIMEOUT"
    BLOCKED_OR_FILTERED = "BLOCKED_OR_FILTERED"
    ADAPTER_UNAVAILABLE = "ADAPTER_UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class NetworkTarget:
    target_id: str
    target_class: TargetClass
    host: str
    purpose: str
    version: str = "v1"


@dataclass(frozen=True)
class ProbeResult:
    sequence: int
    rtt_ms: float | None
    outcome: str
    detail: str = ""


def summarize_probes(probes: list[ProbeResult], *, requested: int) -> dict[str, object]:
    successful = [probe.rtt_ms for probe in probes if probe.rtt_ms is not None]
    failed = requested - len(successful)
    if not successful:
        outcomes = {probe.outcome for probe in probes}
        status = MeasurementStatus.BLOCKED_OR_FILTERED if "blocked" in outcomes else (MeasurementStatus.TIMEOUT if "timeout" in outcomes else MeasurementStatus.TARGET_UNREACHABLE)
        return {"status": status.value, "successful_samples": 0, "failed_samples": failed, "rtt_ms": None, "jitter_ms": None, "packet_loss_percent": None, "note": "A non-responsive target is not interpreted as subscriber packet loss."}
    rtts = [float(value) for value in successful]
    jitter = sum(abs(current - previous) for previous, current in zip(rtts, rtts[1:])) / max(len(rtts) - 1, 1)
    status = MeasurementStatus.VALID if len(rtts) >= 3 else MeasurementStatus.TOO_FEW_SAMPLES
    return {"status": status.value, "successful_samples": len(rtts), "failed_samples": failed, "rtt_ms": {"min": min(rtts), "max": max(rtts), "mean": sum(rtts) / len(rtts), "samples": rtts}, "jitter_ms": jitter if len(rtts) >= 2 else None, "packet_loss_percent": (failed / requested) * 100, "note": "Packet loss is reported only when the declared target returned at least one response."}


_RTT = re.compile(r"(?:time[=<])\s*(\d+(?:\.\d+)?)\s*ms", re.IGNORECASE)


def windows_ping_probe(host: str, timeout_ms: int, sequence: int) -> ProbeResult:
    completed = subprocess.run(["ping.exe", "-n", "1", "-w", str(timeout_ms), host], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    output = f"{completed.stdout}\n{completed.stderr}"
    match = _RTT.search(output)
    if match:
        return ProbeResult(sequence, float(match.group(1)), "success")
    lowered = output.lower()
    if "timed out" in lowered or "zeitüberschreitung" in lowered:
        return ProbeResult(sequence, None, "timeout")
    if "unreachable" in lowered or "nicht erreichbar" in lowered:
        return ProbeResult(sequence, None, "unreachable")
    return ProbeResult(sequence, None, "blocked", "ping returned no RTT")


def collect_network_quality(target: NetworkTarget, *, sample_count: int = 8, interval_ms: int = 250, timeout_ms: int = 1000, measurement_session_id: str | None = None, adapter_context: dict[str, object] | None = None, probe: Callable[[str, int, int], ProbeResult] = windows_ping_probe, sleep: Callable[[float], None] = time.sleep) -> dict[str, object]:
    if sample_count < 1 or interval_ms < 0 or timeout_ms < 1:
        raise ValueError("sample_count, interval_ms and timeout_ms must be positive")
    started = datetime.now(UTC)
    probes: list[ProbeResult] = []
    for sequence in range(1, sample_count + 1):
        try:
            probes.append(probe(target.host, timeout_ms, sequence))
        except OSError as error:
            probes.append(ProbeResult(sequence, None, "error", str(error)))
        if sequence < sample_count and interval_ms:
            sleep(interval_ms / 1000)
    summary = summarize_probes(probes, requested=sample_count)
    sanitized_adapter = {key: value for key, value in (adapter_context or {}).items() if key in {"name", "manufacturer", "driver_version", "interface_index", "link_speed_mbps", "mtu", "connection_state", "rss"}}
    return {"schema": NETWORK_QUALITY_SCHEMA, "measurement_session_id": measurement_session_id or str(uuid4()), "measured_at_utc": started.isoformat(), "policy": {"read_only": True, "external_transfer": False, "public_ip_persisted": False}, "target": asdict(target) | {"target_class": target.target_class.value}, "method": {"protocol": "ICMP_ECHO", "sample_count": sample_count, "interval_ms": interval_ms, "timeout_ms": timeout_ms, "jitter_definition": "mean absolute difference of consecutive successful RTT samples", "packet_loss_definition": "failed requested samples / requested samples; unavailable when no sample succeeds"}, "adapter_context": sanitized_adapter or {"status": "ADAPTER_UNAVAILABLE"}, "probes": [asdict(item) for item in probes], "summary": summary}


def network_quality_evidence(measurement: dict[str, object]) -> EvidenceRecord:
    target = measurement.get("target") if isinstance(measurement.get("target"), dict) else {}
    summary = measurement.get("summary") if isinstance(measurement.get("summary"), dict) else {}
    return EvidenceRecord("network-quality-" + str(measurement.get("measurement_session_id", "unknown")), "network-quality-observation", "OBSERVED_NETWORK_QUALITY", str(target.get("target_id", "declared-target")), str(target.get("target_class", "UNKNOWN")), str(summary.get("status", "ERROR")), "LOCAL_MEASUREMENT", "Declared target; correlation is not configuration causation.", NETWORK_QUALITY_SCHEMA, str(measurement.get("measured_at_utc", "")))


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Improve Yourself network quality collector")
    parser.add_argument("--target-id", required=True)
    parser.add_argument("--target-class", choices=[item.value for item in TargetClass], required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--output", type=Path, default=Path("results/network-quality.json"))
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--interval-ms", type=int, default=250)
    parser.add_argument("--timeout-ms", type=int, default=1000)
    args = parser.parse_args()
    target = NetworkTarget(args.target_id, TargetClass(args.target_class), args.host, args.purpose)
    measurement = collect_network_quality(target, sample_count=args.samples, interval_ms=args.interval_ms, timeout_ms=args.timeout_ms)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(measurement, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
