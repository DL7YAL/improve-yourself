"""Versioned, consumer-neutral foundation for the Improve Analyzer.

Only this module coordinates an :class:`AwpyAdapter` parse for an Analyzer
request.  It deliberately exposes normalized Improve data, never an Awpy
object, to the rest of the product.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
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
# Metrics V1 is an availability contract.  It names the exact location of
# every product datum rather than advertising parser possibilities as inline
# fields.  Large tick/state data deliberately remains one canonical replay-v2
# store and is referenced after replay validation.
METRICS_V1_FIELDS = {
    "inline_match": {"schema": "iy.metrics.match/v1", "fields": ("source", "map_id", "tick_rate")},
    "inline_rounds": {"schema": "iy.metrics.rounds/v1", "fields": ("round_number", "start_tick", "end_tick")},
    "inline_events": {"schema": "iy.metrics.events/v1", "fields": ("kills", "channel_availability")},
    "replay_reference": {
        "schema": "iy.replay/v2",
        "fields": ("players", "rounds", "ticks", "time_in_round", "player_states", "positions", "view_angles", "weapons", "utility", "smokes", "infernos", "bomb", "footsteps"),
        "representation": "validated_reference",
    },
}
OPTIONAL_CHANNELS_V1 = ("damages", "shots", "bomb", "smokes", "infernos", "grenades", "footsteps")
REPLAY_METRIC_KEYS_V1 = ("players", "teams", "ticks", "time_in_round", "player_states", "positions", "view_angles", "weapons", "utility", "grenades", "smokes", "infernos", "bomb", "footsteps", "economy")


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
    capabilities: dict[str, str] = field(default_factory=dict)
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
        parser_rounds = _records(getattr(parsed_demo, "rounds", None))
        critical: list[str] = []
        if not isinstance(header, dict):
            critical.append("parser header is unreadable")
        normalized_rounds: list[dict[str, int | None]] = []
        unknown_round_records = 0
        for index, row in enumerate(parser_rounds, start=1):
            try:
                number = int(row.get("round_num", index))
            except (AttributeError, TypeError, ValueError):
                unknown_round_records += 1
                continue
            if number <= 0:
                unknown_round_records += 1
                continue
            start = row.get("start", row.get("start_tick"))
            end = row.get("end", row.get("official_end", row.get("end_tick")))
            try:
                start_tick = int(start) if start is not None else None
                end_tick = int(end) if end is not None else None
            except (TypeError, ValueError):
                unknown_round_records += 1
                continue
            if start_tick is not None and end_tick is not None and end_tick < start_tick:
                critical.append(f"round {number} end tick precedes start tick")
                continue
            normalized_rounds.append({"round_number": number, "start_tick": start_tick, "end_tick": end_tick})
        if not normalized_rounds:
            critical.append("no referencable rounds")
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
        # product-referencable and are dropped rather than guessed.  A match
        # with no usable kills is still a technically valid match dataset.
        if unknown_records:
            quality.warnings.append("Nicht referenzierbare Ereignisse wurden ohne Interpretation verworfen.")
        available = set(available_channels)
        unavailable = set(quality.missing_channels)
        channel_availability = {
            "kills": "available" if valid_kills else "unavailable",
            **{name: "available" if name in available else "unavailable" if name in unavailable else "unknown" for name in OPTIONAL_CHANNELS_V1},
        }
        capabilities = {
            "match": "available" if isinstance(header, dict) else "unavailable",
            "rounds": "available" if normalized_rounds else "unavailable",
            **channel_availability,
            **{name: "via_replay_v2" for name in REPLAY_METRIC_KEYS_V1},
        }
        report = ValidationReportV1(
            demo_valid=not critical,
            players_processed=0,
            rounds_processed=len(normalized_rounds),
            events_processed=len(valid_kills),
            warnings=tuple(quality.warnings),
            unknown_records=unknown_records + unknown_round_records,
            duplicates_dropped=duplicates,
            critical_errors=tuple(critical),
            capabilities=capabilities,
        )
        if not report.demo_valid:
            raise ValueError("core validation failed: " + "; ".join(report.critical_errors))
        metrics = {
            "schema": METRICS_V1_SCHEMA,
            "profile": METRICS_V1_PROFILE,
            "contract": METRICS_V1_FIELDS,
            "source": {"name": source_name, "sha256": source_sha256},
            "match": {"map_id": str(header.get("map_name", "")), "tick_rate": tickrate},
            "channel_availability": channel_availability,
            "available_channels": sorted(name for name, state in channel_availability.items() if state == "available"),
            "unavailable_channels": sorted(name for name, state in channel_availability.items() if state == "unavailable"),
            "kills": [asdict(kill) for kill in valid_kills],
            "rounds": normalized_rounds,
        }
        return CoreParseResult(request, parsed_demo, metrics, report, (header, valid_kills, available_channels, quality))

    def finalize_match_data(self, prepared: CoreParseResult, replay_manifest: dict[str, Any]) -> dict[str, Any]:
        """Attach the canonical replay projection without exposing parser rows."""
        source = replay_manifest.get("source", {})
        if source.get("sha256") != prepared.normalized_metrics["source"]["sha256"]:
            raise ValueError("replay source differs from normalized core data")
        capabilities = dict(prepared.validation_report.capabilities)
        replay_capabilities = replay_manifest.get("capabilities", {})
        for name in REPLAY_METRIC_KEYS_V1:
            # The canonical replay describes available state precisely.  Do
            # not turn an absent capability into a positive claim here.
            value = replay_capabilities.get(name)
            capabilities[name] = str(value) if value is not None else capabilities.get(name, "unknown")
        report = ValidationReportV1(
            demo_valid=True,
            players_processed=len(replay_manifest.get("players", [])),
            rounds_processed=len(replay_manifest.get("rounds", [])),
            events_processed=prepared.validation_report.events_processed,
            warnings=prepared.validation_report.warnings,
            unknown_records=prepared.validation_report.unknown_records,
            duplicates_dropped=prepared.validation_report.duplicates_dropped,
            capabilities=capabilities,
        )
        metrics = {**prepared.normalized_metrics}
        metrics["replay_reference"] = {
            "schema": replay_manifest.get("schema"),
            "source_sha256": source.get("sha256"),
            "reference": "replay",
            "capabilities": replay_capabilities,
        }
        return {
            "schema": IMPROVE_MATCH_DATA_V1_SCHEMA,
            "request": prepared.request.to_dict(),
            "metrics": metrics,
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
