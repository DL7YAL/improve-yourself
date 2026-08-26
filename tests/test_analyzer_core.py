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
    assert prepared.normalized_metrics["contract"]["replay_reference"]["schema"] == "iy.replay/v2"

    match_data = AnalyzerCore(adapter=adapter).finalize(prepared, _replay("a" * 64))
    assert match_data["schema"] == IMPROVE_MATCH_DATA_V1_SCHEMA
    assert match_data["validation"]["players_processed"] == 1
    hub = AnalyzerDataHub(match_data)
    assert hub.overview()["match"]["map_id"] == "de_ancient"
    assert hub.events()["unavailable_channels"] == ["footsteps"]
    assert hub.replay_projection()["players"][0]["display_name"] == "Alpha"
    assert hub.for_consumer("analyzer")["schema"] == "iy.analyzer_projection/v1"
    assert hub.for_consumer("tactical")["schema"] == "iy.tactical_projection/v1"
    assert hub.for_consumer("tactical")["replay_reference"]["schema"] == "iy.replay/v2"
    assert hub.for_consumer("review")["schema"] == "iy.review_projection/v1"
    assert hub.for_consumer("report")["schema"] == "iy.report_projection/v1"
    isolated = hub.for_consumer("analyzer")
    isolated["players"][0]["display_name"] = "Mutated consumer copy"
    assert hub.for_consumer("analyzer")["players"][0]["display_name"] == "Alpha"
    with pytest.raises(ValueError, match="unknown Analyzer Data Hub"):
        hub.for_consumer("awpy")


def test_missing_optional_kills_stays_a_valid_match_dataset(tmp_path: Path) -> None:
    class NoKillAdapter(_Adapter):
        def adapt(self, _demo: _Demo):
            return _Demo.header, [], ["rounds"], DataQuality("limited", ["kills", "footsteps"])

    prepared = AnalyzerCore(adapter=NoKillAdapter()).prepare(
            AnalysisRequestV1.create(tmp_path / "no-kills.dem"),
            parser_path=tmp_path / "no-kills.dem",
            source_sha256="b" * 64,
            source_name="no-kills.dem",
    )
    assert prepared.validation_report.status == "PASS"
    assert prepared.validation_report.capabilities["kills"] == "unavailable"
    assert prepared.normalized_metrics["kills"] == []


def test_core_fails_closed_for_structurally_unusable_round_data(tmp_path: Path) -> None:
    class NoRoundsDemo(_Demo):
        rounds = _Frame([])

    class InvalidAdapter(_Adapter):
        def parse_demo(self, path: str) -> NoRoundsDemo:
            self.paths.append(path)
            return NoRoundsDemo()

    with pytest.raises(ValueError, match="no referencable rounds"):
        AnalyzerCore(adapter=InvalidAdapter()).prepare(
            AnalysisRequestV1.create(tmp_path / "invalid.dem"), parser_path=tmp_path / "invalid.dem",
            source_sha256="c" * 64, source_name="invalid.dem",
        )


def test_data_hub_refuses_unvalidated_or_wrong_schema_data() -> None:
    with pytest.raises(ValueError, match="expected"):
        AnalyzerDataHub({})
    with pytest.raises(ValueError, match="did not pass"):
        AnalyzerDataHub({"schema": IMPROVE_MATCH_DATA_V1_SCHEMA, "validation": {"status": "FAIL"}})


def test_only_awpy_adapter_imports_awpy_in_product_source() -> None:
    source_root = Path(__file__).parents[1] / "src" / "improve_yourself"
    direct = [
        path.name for path in source_root.glob("*.py")
        if "from awpy " in path.read_text(encoding="utf-8") or "import awpy" in path.read_text(encoding="utf-8")
    ]
    assert direct == ["awpy_adapter.py"]
