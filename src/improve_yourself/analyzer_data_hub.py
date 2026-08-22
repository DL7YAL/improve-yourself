"""Read-only consumer projections from canonical ImproveMatchDataV1."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .analyzer_core import IMPROVE_MATCH_DATA_V1_SCHEMA


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

    def for_consumer(self, consumer: str) -> dict[str, Any]:
        projections = {"overview": self.overview, "analysis": self.events, "replay": self.replay_projection}
        try:
            return projections[consumer]()
        except KeyError as error:
            raise ValueError(f"unknown Analyzer Data Hub projection: {consumer}") from error
