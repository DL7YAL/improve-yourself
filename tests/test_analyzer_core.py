from __future__ import annotations

from pathlib import Path

import pytest

from improve_yourself.analyzer_core import (
    ANALYSIS_REQUEST_V1_SCHEMA,
    IMPROVE_MATCH_DATA_V1_SCHEMA,
    METRICS_V1_SCHEMA,
    AnalysisRequestV1,
    AnalyzerCore,
)
from improve_yourself.analyzer_data_hub import AnalyzerDataHub
from improve_yourself.model import DataQuality, Kill


class _Frame:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def to_dicts(self) -> list[dict]:
        return self._rows


class _Demo:
    header = {"map_name": "de_ancient", "tick_rate": 64}
    rounds = _Frame([{"round_num": 1, "start": 10, "end": 100}])


class _Adapter:
    def __init__(self) -> None:
        self.paths: list[str] = []

    def parse_demo(self, path: str) -> _Demo:
        self.paths.append(path)
        return _Demo()

    def adapt(self, _demo: _Demo):
        return (
            _Demo.header,
            [Kill(1, 20, "Alpha", "Bravo", "ak47", True)],
            ["rounds", "kills", "shots"],
            DataQuality("ok", ["footsteps"], ["Footsteps unavailable"]),
        )


def _replay(source_hash: str) -> dict:
    return {
        "schema": "iy.replay/v2",
        "source": {"sha256": source_hash, "map_id": "de_ancient"},
        "players": [{"player_id": "steam:1", "display_name": "Alpha"}],
        "rounds": [{"round_number": 1, "chunk": "rounds/round-001.json.gz"}],
        "capabilities": {"positions": "full"},
        "data_quality": {},
    }


def test_core_turns_one_request_into_versioned_match_data_and_hub_projections(tmp_path: Path) -> None:
    adapter = _Adapter()
    request = AnalysisRequestV1.create(tmp_path / "real.dem", request_id="request-1")
    assert request.to_dict() == {
        "schema": ANALYSIS_REQUEST_V1_SCHEMA,
        "request_id": "request-1",
        "requested_profile": "METRICS_V1",
    }
    prepared = AnalyzerCore(adapter=adapter).prepare(
        request, parser_path=tmp_path / "parser.dem", source_sha256="a" * 64, source_name="real.dem"
    )
    assert adapter.paths == [str(tmp_path / "parser.dem")]
    assert prepared.normalized_metrics["schema"] == METRICS_V1_SCHEMA
    assert prepared.normalized_metrics["kills"][0]["attacker"] == "Alpha"
    assert prepared.validation_report.status == "PASS"

    match_data = AnalyzerCore(adapter=adapter).finalize(prepared, _replay("a" * 64))
    assert match_data["schema"] == IMPROVE_MATCH_DATA_V1_SCHEMA
    assert match_data["validation"]["players_processed"] == 1
    hub = AnalyzerDataHub(match_data)
    assert hub.overview()["match"]["map_id"] == "de_ancient"
    assert hub.events()["unavailable_channels"] == ["footsteps"]
    assert hub.replay_projection()["players"][0]["display_name"] == "Alpha"
    with pytest.raises(ValueError, match="unknown Analyzer Data Hub"):
        hub.for_consumer("awpy")


def test_core_fails_closed_when_event_round_or_tick_is_not_referencable(tmp_path: Path) -> None:
    class InvalidAdapter(_Adapter):
        def adapt(self, _demo: _Demo):
            return _Demo.header, [Kill(0, -1, "", "", "", False)], ["rounds", "kills"], DataQuality()

    with pytest.raises(ValueError, match="core validation failed"):
        AnalyzerCore(adapter=InvalidAdapter()).prepare(
            AnalysisRequestV1.create(tmp_path / "invalid.dem"),
            parser_path=tmp_path / "invalid.dem",
            source_sha256="b" * 64,
            source_name="invalid.dem",
        )


def test_data_hub_refuses_unvalidated_or_wrong_schema_data() -> None:
    with pytest.raises(ValueError, match="expected"):
        AnalyzerDataHub({})
    with pytest.raises(ValueError, match="did not pass"):
        AnalyzerDataHub({"schema": IMPROVE_MATCH_DATA_V1_SCHEMA, "validation": {"status": "FAIL"}})
