"""Versioned, consumer-neutral foundation for the Improve Analyzer.

Only this module coordinates an :class:`AwpyAdapter` parse for an Analyzer
request.  It deliberately exposes normalized Improve data, never an Awpy
object, to the rest of the product.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from .awpy_adapter import AwpyAdapter
from .model import DataQuality, Kill

ANALYSIS_REQUEST_V1_SCHEMA = "iy.analysis_request/v1"
METRICS_V1_SCHEMA = "iy.metrics/v1"
IMPROVE_MATCH_DATA_V1_SCHEMA = "iy.improve_match_data/v1"
VALIDATION_REPORT_V1_SCHEMA = "iy.validation_report/v1"
METRICS_V1_PROFILE = "METRICS_V1"

# This is an explicit product contract, not a promise that every demo exposes
# every channel.  Absent and unsupported information remains unavailable.
METRICS_V1_FIELDS = {
    "match": ("source", "map", "tick_rate", "teams", "players", "rounds"),
    "time_and_state": ("ticks", "time_in_round", "player_states", "positions", "view_angles"),
    "events": ("kills", "deaths", "assists", "damage", "shots", "weapons", "utility", "grenades", "smokes", "infernos", "bomb", "footsteps"),
    "economy": ("economy",),
}


@dataclass(frozen=True)
class AnalysisRequestV1:
    demo_path: Path
    request_id: str
    requested_profile: str = METRICS_V1_PROFILE

    @classmethod
    def create(cls, demo_path: Path, *, request_id: str | None = None, requested_profile: str = METRICS_V1_PROFILE) -> "AnalysisRequestV1":
        return cls(demo_path=demo_path.resolve(), request_id=request_id or str(uuid4()), requested_profile=requested_profile)

    def to_dict(self) -> dict[str, str]:
        # The source path is intentionally local process input, never written
        # into a portable match-data artifact.
        return {"schema": ANALYSIS_REQUEST_V1_SCHEMA, "request_id": self.request_id, "requested_profile": self.requested_profile}


@dataclass(frozen=True)
class ValidationReportV1:
    demo_valid: bool
    players_processed: int
    rounds_processed: int
    events_processed: int
    warnings: tuple[str, ...] = ()
    unknown_records: int = 0
    duplicates_dropped: int = 0
    critical_errors: tuple[str, ...] = ()
    schema: str = VALIDATION_REPORT_V1_SCHEMA

    @property
    def status(self) -> str:
        return "PASS" if self.demo_valid and not self.critical_errors else "FAIL"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status
        return payload


@dataclass(frozen=True)
class CoreParseResult:
    """Internal core result; parsed_demo is opaque and never a consumer API."""

    request: AnalysisRequestV1
    parsed_demo: Any
    normalized_metrics: dict[str, Any]
    validation_report: ValidationReportV1
    analysis_input: tuple[dict[str, Any], list[Kill], list[str], DataQuality]


def _records(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    converter = getattr(value, "to_dicts", None)
    return converter() if converter else list(value) if isinstance(value, list) else []


class ImproveMatchNormalizer:
    """Validate technical parser output and map it into Metrics V1 names."""

    def normalize(
        self,
        request: AnalysisRequestV1,
        parsed_demo: Any,
        adapter: AwpyAdapter,
        *,
        source_sha256: str,
        source_name: str,
    ) -> CoreParseResult:
        if request.requested_profile != METRICS_V1_PROFILE:
            raise ValueError(f"unsupported analysis profile: {request.requested_profile}")
        header, kills, available_channels, quality = adapter.adapt(parsed_demo)
        rounds = _records(getattr(parsed_demo, "rounds", None))
        critical: list[str] = []
        if not isinstance(header, dict):
            critical.append("parser header is unreadable")
        if not rounds:
            critical.append("no referencable rounds")
        if not kills:
            critical.append("no referencable kill events")
        tickrate = header.get("tick_rate", header.get("tickrate")) if isinstance(header, dict) else None
        try:
            tickrate = float(tickrate) if tickrate is not None else None
        except (TypeError, ValueError):
            tickrate = None
        if tickrate is not None and tickrate <= 0:
            critical.append("invalid tick rate")

        unique_kills: list[Kill] = []
        seen_kills: set[tuple[int, int, str, str, str, bool]] = set()
        duplicates = 0
        for kill in kills:
            key = (kill.round_number, kill.tick, kill.attacker, kill.victim, kill.weapon, kill.headshot)
            if key in seen_kills:
                duplicates += 1
                continue
            seen_kills.add(key)
            unique_kills.append(kill)
        valid_kills = [kill for kill in unique_kills if kill.round_number > 0 and kill.tick >= 0]
        unknown_records = len(unique_kills) - len(valid_kills)
        # Awpy may surface warm-up or unassigned parser events.  They are not
        # product-referencable and are dropped rather than guessed.  Only a
        # complete lack of usable events blocks this Metrics V1 request.
        if unknown_records:
            quality.warnings.append("Nicht referenzierbare Ereignisse wurden ohne Interpretation verworfen.")
        if not valid_kills:
            critical.append("no referencable kill events after normalization")
        report = ValidationReportV1(
            demo_valid=not critical,
            players_processed=0,
            rounds_processed=len(rounds),
            events_processed=len(valid_kills),
            warnings=tuple(quality.warnings),
            unknown_records=unknown_records,
            duplicates_dropped=duplicates,
            critical_errors=tuple(critical),
        )
        if not report.demo_valid:
            raise ValueError("core validation failed: " + "; ".join(report.critical_errors))
        metrics = {
            "schema": METRICS_V1_SCHEMA,
            "profile": METRICS_V1_PROFILE,
            "contract": METRICS_V1_FIELDS,
            "source": {"name": source_name, "sha256": source_sha256},
            "match": {"map_id": str(header.get("map_name", "")), "tick_rate": tickrate},
            "available_channels": sorted(available_channels),
            "unavailable_channels": sorted(quality.missing_channels),
            "kills": [asdict(kill) for kill in valid_kills],
            "rounds": [{"round_number": int(row.get("round_num", index)), "start_tick": row.get("start"), "end_tick": row.get("end", row.get("official_end"))} for index, row in enumerate(rounds, start=1)],
        }
        return CoreParseResult(request, parsed_demo, metrics, report, (header, valid_kills, available_channels, quality))

    def finalize_match_data(self, prepared: CoreParseResult, replay_manifest: dict[str, Any]) -> dict[str, Any]:
        """Attach the canonical replay projection without exposing parser rows."""
        source = replay_manifest.get("source", {})
        if source.get("sha256") != prepared.normalized_metrics["source"]["sha256"]:
            raise ValueError("replay source differs from normalized core data")
        report = ValidationReportV1(
            demo_valid=True,
            players_processed=len(replay_manifest.get("players", [])),
            rounds_processed=len(replay_manifest.get("rounds", [])),
            events_processed=prepared.validation_report.events_processed,
            warnings=prepared.validation_report.warnings,
            unknown_records=prepared.validation_report.unknown_records,
            duplicates_dropped=prepared.validation_report.duplicates_dropped,
        )
        return {
            "schema": IMPROVE_MATCH_DATA_V1_SCHEMA,
            "request": prepared.request.to_dict(),
            "metrics": prepared.normalized_metrics,
            "validation": report.to_dict(),
            "replay": {
                "schema": replay_manifest.get("schema"),
                "source": source,
                "players": replay_manifest.get("players", []),
                "rounds": replay_manifest.get("rounds", []),
                "capabilities": replay_manifest.get("capabilities", {}),
                "data_quality": replay_manifest.get("data_quality", {}),
            },
        }


class AnalyzerCore:
    """The sole Analyze-to-Awpy boundary for an AnalysisRequestV1."""

    def __init__(self, adapter: AwpyAdapter | None = None, normalizer: ImproveMatchNormalizer | None = None) -> None:
        self._adapter = adapter or AwpyAdapter()
        self._normalizer = normalizer or ImproveMatchNormalizer()

    def prepare(self, request: AnalysisRequestV1, *, parser_path: Path, source_sha256: str, source_name: str) -> CoreParseResult:
        parsed_demo = self._adapter.parse_demo(str(parser_path))
        return self._normalizer.normalize(request, parsed_demo, self._adapter, source_sha256=source_sha256, source_name=source_name)

    def finalize(self, prepared: CoreParseResult, replay_manifest: dict[str, Any]) -> dict[str, Any]:
        return self._normalizer.finalize_match_data(prepared, replay_manifest)
