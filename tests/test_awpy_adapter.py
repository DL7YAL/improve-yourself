from improve_yourself.awpy_adapter import _read_optional_channel, _round_for_kill, _round_for_tick


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
