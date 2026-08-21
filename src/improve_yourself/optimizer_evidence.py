"""Local, declarative optimizer evidence selection with no apply authority.

The module is deliberately separate from Windows collection and UI.  Rules
describe candidates for a later read/snapshot/apply/verify/restore workflow;
this slice only matches profiles, records exclusions and validates synthetic
decision coverage.  Synthetic profiles never carry measured FPS evidence.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Iterable


EVIDENCE_SCHEMA = "iy.optimizer_evidence_matrix/v1"
SYNTHETIC_MATRIX_SCHEMA = "iy.optimizer_synthetic_matrix/v1"
RUNNER_SCHEMA = "iy.optimizer_runner_report/v1"


class EvidenceClass(StrEnum):
    VERIFIED_STABLE = "VERIFIED_STABLE"
    CONDITIONAL = "CONDITIONAL"
    EXPERIMENTAL = "EXPERIMENTAL"


class GoalProfile(StrEnum):
    PERFORMANCE = "PERFORMANCE"
    QUALITY = "QUALITY"


@dataclass(frozen=True)
class OptimizerRule:
    rule_id: str
    name: str
    category: str
    description: str
    current_state_path: str
    target_state: str
    supported_conditions: tuple[tuple[str, str, object], ...]
    exclusion_conditions: tuple[tuple[str, str, object], ...]
    expected_effect: str
    possible_side_effects: tuple[str, ...]
    reversible: bool
    backup_restore_requirement: str
    evidence_class: EvidenceClass
    confidence: str
    source_rationale: str
    measurement_metrics: tuple[str, ...]
    validation_status: str
    conflicts_with: tuple[str, ...] = ()
    priority: int = 0

    def as_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["evidence_class"] = self.evidence_class.value
        return result


@dataclass(frozen=True)
class BenchmarkABPlan:
    schema: str = "iy.optimizer_ab_validation/v1"
    sequence: tuple[str, ...] = ("A_BASELINE", "B_OPTIMIZED", "A_REPEAT", "B_REPEAT")
    metrics: tuple[str, ...] = (
        "average_fps", "one_percent_low", "frametime_percentiles",
        "frametime_stability", "stutter_spikes", "cpu_gpu_limitation",
        "reproducible_delta", "latency_if_measurable",
    )
    required_fields: tuple[str, ...] = (
        "system_profile", "source_state", "target_state", "scenario", "runs",
        "aggregated_metrics", "delta", "variance", "software_driver_state", "result",
    )

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def evidence_matrix() -> tuple[OptimizerRule, ...]:
    """Small initial matrix; every item is a candidate, never an apply action."""
    return (
        OptimizerRule(
            "refresh-rate-alignment", "CS2 Refresh-Rate-Abgleich", "CS2 configuration",
            "Prüft nur, ob eine bekannte CS2-Rate hinter der bestätigten Anzeige liegt.",
            "cs2.refresh_hz", "CS2-Rate an bestätigte aktive Anzeige anpassen",
            (("monitor.refresh_hz", "gte", 120), ("cs2.refresh_hz", "lt_path", "monitor.refresh_hz")), (),
            "Vermeidet eine bekannte Unterausnutzung der bestätigten Anzeige.",
            ("Falsche Zuordnung mehrerer Displays möglich, daher Snapshot und Verifikation erforderlich."),
            True, "READ → Snapshot der CS2-Konfiguration → spätere Änderung → Verify → Restore",
            EvidenceClass.VERIFIED_STABLE, "HIGH",
            "Technische Konsistenzprüfung; reale Wirkung erst über identische Benchmarkstrecke validieren.",
            ("frametime_percentiles", "frametime_stability", "reproducible_delta"), "READY_FOR_REAL_AB",
            priority=90,
        ),
        OptimizerRule(
            "amd-driver-option-review", "AMD-Treiberoption prüfen", "GPU driver",
            "Bedingter Kandidat nur für bekannte AMD-GPU- und Treiberkonstellationen.",
            "gpu_options.latency_mode", "bekannte AMD-Treiberoption mit Snapshot prüfen",
            (("gpu.vendor", "equals", "AMD"), ("gpu.driver_version", "present", True), ("goal", "equals", "PERFORMANCE")), (),
            "Kandidatenprüfung für kompetitive Latenz-/Frametime-Validierung.",
            ("Treiberstand und Spielszenario können Wirkung umkehren oder neutralisieren."),
            True, "READ → Treiberprofil-Snapshot → spätere Änderung → Verify → Restore",
            EvidenceClass.CONDITIONAL, "MEDIUM",
            "Hersteller- und Treiberversion sind zwingende Eingabedaten; keine generische AMD-Vorgabe.",
            ("frametime_stability", "stutter_spikes", "latency_if_measurable"), "SYNTHETIC_MATCH_ONLY",
            priority=60,
        ),
        OptimizerRule(
            "nvidia-reflex-review", "NVIDIA Reflex-Kompatibilität prüfen", "GPU driver",
            "Bedingter Kandidat nur für bekannte NVIDIA-GPU- und CS2-Konstellationen.",
            "cs2.reflex", "bekannten CS2-/NVIDIA-Zustand mit Snapshot prüfen",
            (("gpu.vendor", "equals", "NVIDIA"), ("gpu.driver_version", "present", True), ("cs2.reflex", "present", True)), (),
            "Kandidatenprüfung für Latenz und stabile Frametimes.",
            ("GPU-Limit, Treiber und Szenario beeinflussen die Wirkung."),
            True, "READ → CS2-/Treiberprofil-Snapshot → spätere Änderung → Verify → Restore",
            EvidenceClass.CONDITIONAL, "MEDIUM",
            "Nur Kompatibilitätsprüfung, keine behauptete universelle Leistungssteigerung.",
            ("frametime_percentiles", "latency_if_measurable", "cpu_gpu_limitation"), "SYNTHETIC_MATCH_ONLY",
            priority=60,
        ),
        OptimizerRule(
            "performance-frame-pacing-candidate", "Performance-Frame-Pacing-Kandidat", "Frame pacing",
            "Experimenteller Kandidat für CPU-limitierte Performance-Ziele.",
            "cs2.frame_pacing", "leistungsorientierten Frame-Pacing-Zustand nur A/B-validieren",
            (("goal", "equals", "PERFORMANCE"), ("limitation", "equals", "CPU"), ("cs2.frame_pacing", "present", True)),
            (("ram.capacity_gb", "lt", 16),),
            "Hypothese für stabilere Lows; keine Leistungsbehauptung ohne Messung.",
            ("Kann Bildqualität oder Frame-Cap-Verhalten beeinflussen."),
            True, "READ → Konfigurations-Snapshot → experimenteller A/B-Test → Restore bei Varianz oder Nachteil",
            EvidenceClass.EXPERIMENTAL, "LOW",
            "Synthetische Matrix prüft nur Auswahlweg; echte Wirkung ist NOT_MEASURED.",
            ("one_percent_low", "frametime_stability", "stutter_spikes"), "EXPERIMENTAL_NOT_MEASURED",
            conflicts_with=("quality-frame-pacing-candidate",), priority=30,
        ),
        OptimizerRule(
            "quality-frame-pacing-candidate", "Quality-Frame-Pacing-Kandidat", "Frame pacing",
            "Experimenteller Kandidat für Quality-Ziele bei GPU-Limitierung.",
            "cs2.frame_pacing", "qualitätsorientierten Frame-Pacing-Zustand nur A/B-validieren",
            (("goal", "equals", "QUALITY"), ("limitation", "equals", "GPU"), ("cs2.frame_pacing", "present", True)),
            (("ram.capacity_gb", "lt", 16),),
            "Hypothese für bessere Frametime-Stabilität ohne unnötigen Qualitätsverlust.",
            ("Kann Durchschnittsleistung reduzieren oder keine Wirkung zeigen."),
            True, "READ → Konfigurations-Snapshot → experimenteller A/B-Test → Restore bei Nachteil",
            EvidenceClass.EXPERIMENTAL, "LOW",
            "Synthetische Matrix prüft nur Auswahlweg; echte Wirkung ist NOT_MEASURED.",
            ("frametime_percentiles", "frametime_stability", "reproducible_delta"), "EXPERIMENTAL_NOT_MEASURED",
            conflicts_with=("performance-frame-pacing-candidate",), priority=30,
        ),
    )


def evidence_matrix_document() -> dict[str, object]:
    """Return the complete, machine-readable V1 contract without an apply path."""
    return {
        "schema": EVIDENCE_SCHEMA,
        "safety_protocol": "READ → SNAPSHOT → APPLY → VERIFY → RESTORE",
        "selection_order": ("safety", "compatibility", "evidence", "stability", "performance"),
        "rules": [rule.as_dict() for rule in evidence_matrix()],
        "ab_validation_model": BenchmarkABPlan().as_dict(),
    }


def _read_path(profile: dict[str, object], path: str) -> object | None:
    value: object = profile
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _condition(profile: dict[str, object], condition: tuple[str, str, object]) -> tuple[bool, str | None]:
    path, operator, expected = condition
    actual = _read_path(profile, path)
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
    if operator == "lt_path":
        other = _read_path(profile, str(expected))
        if other is None:
            return False, str(expected)
        return isinstance(actual, (int, float)) and isinstance(other, (int, float)) and actual < other, None
    raise ValueError(f"unsupported condition operator: {operator}")


def evaluate_profile(profile: dict[str, object], rules: Iterable[OptimizerRule] | None = None) -> dict[str, object]:
    """Evaluate one declared profile deterministically; no writes and no benchmarks."""
    active_rules = tuple(rules or evidence_matrix())
    selected: list[OptimizerRule] = []
    excluded: list[dict[str, object]] = []
    missing: set[str] = set()
    for rule in active_rules:
        unmet: list[str] = []
        for condition in rule.supported_conditions:
            matched, absent = _condition(profile, condition)
            if absent:
                missing.add(absent)
            if not matched:
                unmet.append(condition[0])
        for condition in rule.exclusion_conditions:
            matched, absent = _condition(profile, condition)
            if absent:
                missing.add(absent)
            if matched:
                unmet.append(f"excluded:{condition[0]}")
        if unmet:
            excluded.append({"rule_id": rule.rule_id, "reason": ", ".join(sorted(unmet))})
        else:
            selected.append(rule)

    accepted: list[OptimizerRule] = []
    conflicts: list[dict[str, str]] = []
    for rule in sorted(selected, key=lambda item: (-item.priority, item.rule_id)):
        conflict = next((winner for winner in accepted if winner.rule_id in rule.conflicts_with or rule.rule_id in winner.conflicts_with), None)
        if conflict is None:
            accepted.append(rule)
        else:
            conflicts.append({"excluded_rule_id": rule.rule_id, "winning_rule_id": conflict.rule_id, "reason": "deterministic priority"})
            excluded.append({"rule_id": rule.rule_id, "reason": f"conflict:{conflict.rule_id}"})

    def bucket(evidence: EvidenceClass) -> list[dict[str, object]]:
        return [rule.as_dict() for rule in accepted if rule.evidence_class is evidence]

    backups = sorted({rule.backup_restore_requirement for rule in accepted})
    return {
        "schema": RUNNER_SCHEMA,
        "system_id": str(profile.get("system_id") or "local-profile"),
        "profile_source": profile.get("profile_source", "UNKNOWN"),
        "performance_evidence": profile.get("performance_evidence", "NOT_MEASURED"),
        "stable_recommendations": bucket(EvidenceClass.VERIFIED_STABLE),
        "conditional_recommendations": bucket(EvidenceClass.CONDITIONAL),
        "experimental_candidates": bucket(EvidenceClass.EXPERIMENTAL),
        "excluded_rules": sorted(excluded, key=lambda item: str(item["rule_id"])),
        "conflicts": conflicts,
        "missing_input_data": sorted(missing),
        "backup_restore_requirements": backups,
        "ab_validation_plan": BenchmarkABPlan().as_dict(),
    }


def profile_from_system_check(payload: dict[str, object], *, goal: GoalProfile = GoalProfile.PERFORMANCE) -> dict[str, object] | None:
    """Project known system-check evidence without manufacturing unavailable settings."""
    if payload.get("schema") != "iy.system_check/v1" or not isinstance(payload.get("checks"), list):
        return None
    checks = {item.get("id"): item for item in payload["checks"] if isinstance(item, dict) and isinstance(item.get("id"), str)}
    gpu = ((checks.get("gpu") or {}).get("evidence") or {}).get("adapters") or []
    adapter = gpu[0] if isinstance(gpu, list) and gpu and isinstance(gpu[0], dict) else {}
    gpu_name = str(adapter.get("name") or "")
    vendor = "AMD" if "AMD" in gpu_name.upper() or "RADEON" in gpu_name.upper() else ("NVIDIA" if "NVIDIA" in gpu_name.upper() or "GEFORCE" in gpu_name.upper() else None)
    refresh = ((checks.get("display") or {}).get("evidence") or {}).get("refresh_rates_hz") or []
    return {
        "system_id": "local-system-check", "profile_source": "READ_ONLY_SYSTEM_CHECK",
        "performance_evidence": "NOT_MEASURED", "goal": goal.value,
        "cpu": {"name": ((checks.get("cpu") or {}).get("evidence") or {}).get("name")},
        "gpu": {"name": gpu_name or None, "vendor": vendor, "driver_version": adapter.get("driver_version")},
        "ram": {"capacity_gb": ((checks.get("memory") or {}).get("evidence") or {}).get("total_gb")},
        "windows": ((checks.get("windows") or {}).get("evidence") or {}),
        "monitor": {"refresh_hz": max(refresh) if refresh else None},
        "security": {"secure_boot": ((checks.get("secure_boot") or {}).get("evidence") or {}).get("enabled"), "tpm": ((checks.get("tpm") or {}).get("evidence") or {}).get("enabled")},
        # Gaming, driver-option and CS2 keys are deliberately absent until safe readers exist.
    }


def synthetic_system_matrix() -> dict[str, object]:
    """Return exactly 150 deterministic, explicitly non-measured test systems."""
    cpus = (("AMD", "Ryzen 7 7800X3D", True), ("AMD", "Ryzen 5 7600", False), ("AMD", "Ryzen 5 3600", False), ("Intel", "Core i5-14600K", False), ("Intel", "Core i7-9700K", False))
    gpus = (("AMD", "Radeon RX 7900 XTX"), ("AMD", "Radeon RX 6700 XT"), ("NVIDIA", "GeForce RTX 4080"), ("NVIDIA", "GeForce RTX 3060"), ("NVIDIA", "GeForce GTX 1660"))
    refreshes = (60, 120, 144, 165, 240, 360)
    systems: list[dict[str, object]] = []
    for index in range(150):
        cpu_vendor, cpu_name, x3d = cpus[index % len(cpus)]
        gpu_vendor, gpu_name = gpus[(index // len(cpus)) % len(gpus)]
        refresh = refreshes[index % len(refreshes)]
        goal = GoalProfile.PERFORMANCE.value if index % 2 == 0 else GoalProfile.QUALITY.value
        limitation = "CPU" if index % 3 == 0 else "GPU"
        systems.append({
            "schema": "iy.system_profile/v1", "system_id": f"synthetic-{index + 1:03d}", "profile_id": f"synthetic-{index + 1:03d}", "profile_source": "SYNTHETIC_VALIDATION", "performance_evidence": "NOT_MEASURED",
            "synthetic_label": "SYNTHETIC / EXPECTED / NOT MEASURED", "goal": goal, "limitation": limitation,
            "cpu": {"vendor": cpu_vendor, "name": cpu_name, "family": "X3D" if x3d else "NON_X3D", "generation": 3 + (index % 12)},
            "gpu": {"vendor": gpu_vendor, "name": gpu_name, "tier": ("HIGH" if index % 5 == 0 else "MID" if index % 5 < 3 else "LOW"), "driver_version": None if index % 31 == 0 else f"{24 + index % 3}.{10 + index % 12}.1"},
            "ram": {"capacity_gb": (8, 16, 32, 64)[index % 4], "speed_mt_s": (2666, 3200, 5600, 6000)[index % 4]},
            "windows": {"build": (19045, 22631, 26100, 26200)[index % 4]},
            "monitor": {"refresh_hz": refresh},
            "windows_gaming": {"game_mode": bool(index % 2), "hags": bool((index // 2) % 2)},
            "gpu_options": {"latency_mode": "KNOWN" if index % 4 else "UNKNOWN"},
            "cs2": {"refresh_hz": refresh if index % 4 else max(60, refresh // 2), "reflex": "ON" if gpu_vendor == "NVIDIA" else None, "frame_pacing": "DEFAULT"},
            "motherboard": {} if index % 23 == 0 else {"manufacturer": ("AMD Board Vendor" if cpu_vendor == "AMD" else "Intel Board Vendor"), "product": f"Board-{index % 9}", "version": f"R{1 + index % 3}"},
            "bios": {} if index % 23 == 0 else {"version": f"B{100 + index % 17}", "date": f"202{index % 5}-0{1 + index % 9}-01"},
            "network": {"adapters": [] if index % 29 == 0 else [{"name": ("Realtek 2.5GbE" if index % 2 else "Intel Ethernet"), "driver_version": f"{1 + index % 4}.0", "link_speed_mbps": (100 if index % 7 == 0 else 1000 if index % 3 else 2500), "mtu": 1500 if index % 5 else None, "rss": bool(index % 2), "eee": "UNKNOWN" if index % 4 else "NOT_RELIABLY_DETECTABLE"}]},
            "field_observation": {"ram_speed": "DETECTED" if index % 4 else "NOT_RELIABLY_DETECTABLE", "network_mtu": "DETECTED" if index % 5 else "NOT_AVAILABLE", "gpu.driver_options": "NOT_RELIABLY_DETECTABLE" if index % 4 == 0 else "DETECTED"},
            "current_recommendations": {"fixture-system-memory": True} if index % 19 == 0 else {},
            "synthetic_case": {"case_id": f"matrix-{index + 1:03d}", "expected_validation": "DETERMINISTIC_DECISION_ONLY", "real_evidence_allowed": False},
        })
    return {"schema": SYNTHETIC_MATRIX_SCHEMA, "performance_evidence": "SYNTHETIC / EXPECTED / NOT MEASURED", "systems": systems}


def run_synthetic_matrix(matrix: dict[str, object] | None = None) -> dict[str, object]:
    source = matrix or synthetic_system_matrix()
    systems = source.get("systems") if isinstance(source, dict) else None
    if source.get("schema") != SYNTHETIC_MATRIX_SCHEMA or not isinstance(systems, list):
        raise ValueError("expected iy.optimizer_synthetic_matrix/v1")
    reports = [evaluate_profile(system) for system in systems if isinstance(system, dict)]
    counts = {"stable": 0, "conditional": 0, "experimental": 0, "excluded": 0, "conflicts": 0, "without_recommendation": 0, "missing_data": 0}
    for report in reports:
        counts["stable"] += len(report["stable_recommendations"])
        counts["conditional"] += len(report["conditional_recommendations"])
        counts["experimental"] += len(report["experimental_candidates"])
        counts["excluded"] += len(report["excluded_rules"])
        counts["conflicts"] += len(report["conflicts"])
        counts["without_recommendation"] += not any(report[key] for key in ("stable_recommendations", "conditional_recommendations", "experimental_candidates"))
        counts["missing_data"] += bool(report["missing_input_data"])
    return {
        "schema": RUNNER_SCHEMA,
        "input_schema": SYNTHETIC_MATRIX_SCHEMA,
        "performance_evidence": "SYNTHETIC / EXPECTED / NOT MEASURED",
        "evidence_matrix": evidence_matrix_document(),
        "system_count": len(reports),
        "summary": counts,
        "reports": reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the synthetic Improve Yourself optimizer evidence matrix")
    parser.add_argument("--output", type=Path, default=Path("results/optimizer-synthetic-report.json"))
    args = parser.parse_args()
    report = run_synthetic_matrix()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
