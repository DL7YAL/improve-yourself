from improve_yourself.awpy_adapter import _read_optional_channel


class DemoWithoutPlayerSound:
    @property
    def footsteps(self):
        raise KeyError("player_sound fehlt")


def test_missing_lazy_awpy_event_is_treated_as_optional() -> None:
    value, warning = _read_optional_channel(DemoWithoutPlayerSound(), "footsteps")
    assert value is None
    assert warning is not None
    assert "KeyError" in warning
