"""Read-only consumer projections from canonical ImproveMatchDataV1."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .analyzer_core import IMPROVE_MATCH_DATA_V1_SCHEMA

ANALYZER_PROJECTION_V1_SCHEMA = "iy.analyzer_projection/v1"
TACTICAL_PROJECTION_V1_SCHEMA = "iy.tactical_projection/v1"
REVIEW_PROJECTION_V1_SCHEMA = "iy.review_projection/v1"
REPORT_PROJECTION_V1_SCHEMA = "iy.report_projection/v1"


class AnalyzerDataHub:
    """Distribute typed projections; it never parses a demo or exposes Awpy data."""

    def __init__(self, match_data: dict[str, Any]) -> None:
        if match_data.get("schema") != IMPROVE_MATCH_DATA_V1_SCHEMA:
            raise ValueError("expected iy.improve_match_data/v1")
        validation = match_data.get("validation", {})
        if validation.get("status") != "PASS":
            raise ValueError("match data did not pass technical validation")
        self._data = deepcopy(match_data)

    def overview(self) -> dict[str, Any]:
        metrics = self._data["metrics"]
        replay = self._data["replay"]
        return {"source": deepcopy(metrics["source"]), "match": deepcopy(metrics["match"]), "players": deepcopy(replay["players"]), "rounds": deepcopy(replay["rounds"]), "validation": deepcopy(self._data["validation"])}

    def events(self) -> dict[str, Any]:
        metrics = self._data["metrics"]
        return {"kills": deepcopy(metrics["kills"]), "available_channels": list(metrics["available_channels"]), "unavailable_channels": list(metrics["unavailable_channels"])}

    def replay_projection(self) -> dict[str, Any]:
        return deepcopy(self._data["replay"])

    def analyzer_projection(self) -> dict[str, Any]:
        """Minimal facts for Analyzer UI/configuration; no parser structures."""
        return {
            "schema": ANALYZER_PROJECTION_V1_SCHEMA,
            **self.overview(),
            "events": self.events(),
        }

    def tactical_projection(self) -> dict[str, Any]:
        """Identity/context plus the explicit canonical replay-v2 reference.

        Player state, position, view angle and utility state remain in the
        hash-bound replay chunks.  This prevents duplicate large state payloads
        while making the required data location unambiguous to Tactical.
        """
        replay = self._data["replay"]
        metrics = self._data["metrics"]
        return {
            "schema": TACTICAL_PROJECTION_V1_SCHEMA,
            "source": deepcopy(metrics["source"]),
            "players": deepcopy(replay["players"]),
            "rounds": deepcopy(replay["rounds"]),
            "replay_reference": deepcopy(metrics.get("replay_reference", {})),
        }

    def review_projection(self) -> dict[str, Any]:
        return {
            "schema": REVIEW_PROJECTION_V1_SCHEMA,
            "source": deepcopy(self._data["metrics"]["source"]),
            "match": deepcopy(self._data["metrics"]["match"]),
            "rounds": deepcopy(self._data["metrics"]["rounds"]),
            "events": self.events(),
            "replay_reference": deepcopy(self._data["metrics"].get("replay_reference", {})),
        }

    def report_projection(self) -> dict[str, Any]:
        metrics = self._data["metrics"]
        return {
            "schema": REPORT_PROJECTION_V1_SCHEMA,
            "source": deepcopy(metrics["source"]),
            "match": deepcopy(metrics["match"]),
            "round_count": len(metrics["rounds"]),
            "event_count": len(metrics["kills"]),
            "channel_availability": deepcopy(metrics["channel_availability"]),
            "validation": deepcopy(self._data["validation"]),
        }

    def for_consumer(self, consumer: str) -> dict[str, Any]:
        projections = {
            "overview": self.overview,
            "analysis": self.events,
            "replay": self.replay_projection,
            "analyzer": self.analyzer_projection,
            "tactical": self.tactical_projection,
            "review": self.review_projection,
            "report": self.report_projection,
        }
        try:
            return projections[consumer]()
        except KeyError as error:
            raise ValueError(f"unknown Analyzer Data Hub projection: {consumer}") from error
