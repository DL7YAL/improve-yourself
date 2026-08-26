from improve_yourself.awpy_adapter import AwpyAdapter, _read_optional_channel, _regular_kills, _round_for_kill, _round_for_tick
from improve_yourself.domain import round_multikills


class DemoWithoutPlayerSound:
    @property
    def footsteps(self):
        raise KeyError("player_sound fehlt")


def test_missing_lazy_awpy_event_is_treated_as_optional() -> None:
    value, warning = _read_optional_channel(DemoWithoutPlayerSound(), "footsteps")
    assert value is None
    assert warning is not None
    assert "KeyError" in warning


def test_late_official_round_event_uses_explicit_source_round_number() -> None:
    rounds = [{"round_num": 25, "start": 159_427, "end": 165_442, "official_end": 165_890}]
    late_kill = {"tick": 165_532, "round_num": 25}

    assert _round_for_tick(165_532, rounds) == 25
    assert _round_for_kill(late_kill, 165_532, rounds) == 25


def test_missing_explicit_round_number_falls_back_to_official_round_boundary() -> None:
    rounds = [{"round_num": 25, "start": 159_427, "end": 165_442, "official_end": 165_890}]

    assert _round_for_kill({"tick": 165_532}, 165_532, rounds) == 25


def test_warmup_events_are_excluded_before_regular_match_metrics_and_scenes() -> None:
    rounds = [{"round_num": 1, "start": 100, "official_end": 500, "winner": "t", "reason": "ct_killed"}]
    rows = [
        {"tick": 10, "round_num": 0, "attacker_name": "Warmup", "victim_name": "Victim"},
        {"tick": 150, "round_num": 1, "attacker_name": "Match", "victim_name": "Victim-1"},
        {"tick": 200, "round_num": 1, "attacker_name": "Match", "victim_name": "Victim-2"},
        {"tick": 250, "round_num": 1, "attacker_name": "Match", "victim_name": "Victim-3"},
    ]

    kills, excluded = _regular_kills(rows, rounds)

    assert excluded == 1
    assert [kill.round_number for kill in kills] == [1, 1, 1]
    assert [kill.attacker for kill in kills] == ["Match", "Match", "Match"]
    assert round_multikills(kills)[0].round_number == 1


class _Frame:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def to_dicts(self) -> list[dict]:
        return self.rows


class _DemoWithWarmup:
    header = {"map_name": "de_ancient"}
    rounds = _Frame([{"round_num": 1, "start": 100, "official_end": 500, "winner": "t", "reason": "ct_killed"}])
    kills = _Frame([
        {"tick": 10, "round_num": 0, "attacker_name": "Warmup", "victim_name": "Victim"},
        {"tick": 150, "round_num": 1, "attacker_name": "Match", "victim_name": "Victim-1"},
    ])


def test_adapter_reports_excluded_non_match_events_without_emitting_them_as_kills() -> None:
    _header, kills, _available, quality = AwpyAdapter().adapt(_DemoWithWarmup())

    assert [(kill.round_number, kill.attacker) for kill in kills] == [(1, "Match")]
    assert any("außerhalb regulärer Matchrunden" in warning for warning in quality.warnings)
