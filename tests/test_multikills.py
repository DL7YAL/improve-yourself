from improve_yourself.domain import round_multikills
from improve_yourself.model import Kill


def kill(round_number: int, tick: int, attacker: str = "Player") -> Kill:
    return Kill(round_number, tick, attacker, f"Victim-{tick}")


def test_three_kills_across_entire_round_are_one_multikill() -> None:
    result = round_multikills([kill(4, 100), kill(4, 2_000), kill(4, 9_000)])
    assert len(result) == 1
    assert result[0].kill_count == 3
    assert result[0].first_tick == 100
    assert result[0].last_tick == 9_000


def test_two_kills_are_not_a_multikill() -> None:
    assert round_multikills([kill(4, 100), kill(4, 200)]) == []


def test_kills_are_not_combined_across_rounds() -> None:
    assert round_multikills([kill(1, 100), kill(1, 200), kill(2, 300)]) == []


def test_only_one_marker_is_created_for_four_kills() -> None:
    result = round_multikills([kill(1, tick) for tick in (1, 2, 3, 4)])
    assert len(result) == 1
    assert result[0].kill_count == 4
