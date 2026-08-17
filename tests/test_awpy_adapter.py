from improve_yourself.awpy_adapter import _read_optional_channel, _regular_kills, _round_for_kill, _round_for_tick
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


def test_pre_match_kills_without_regular_round_state_are_excluded_from_match_stats() -> None:
    rounds = [{"round_num": 1, "start": 100, "official_end": 500, "winner": "t", "reason": "ct_killed"}]
    rows = [
        {"tick": 10, "round_num": 0, "attacker_name": "Knife", "victim_name": "Victim"},
        {"tick": 150, "round_num": 1, "attacker_name": "Match", "victim_name": "Victim-1"},
        {"tick": 200, "round_num": 1, "attacker_name": "Match", "victim_name": "Victim-2"},
        {"tick": 250, "round_num": 1, "attacker_name": "Match", "victim_name": "Victim-3"},
    ]

    kills, excluded = _regular_kills(rows, rounds)

    assert excluded == 1
    assert [kill.round_number for kill in kills] == [1, 1, 1]
    assert [kill.attacker for kill in kills] == ["Match", "Match", "Match"]
    assert round_multikills(kills)[0].round_number == 1


def test_regular_match_without_pre_match_phase_keeps_all_kills_and_never_emits_round_zero() -> None:
    rounds = [{"round_num": 1, "start": 100, "official_end": 500, "winner": "t", "reason": "ct_killed"}]
    rows = [{"tick": 150, "round_num": 1, "attacker_name": "Match", "victim_name": "Victim"}]

    kills, excluded = _regular_kills(rows, rounds)

    assert excluded == 0
    assert len(kills) == 1
    assert kills[0].round_number == 1
