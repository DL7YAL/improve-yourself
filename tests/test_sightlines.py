from improve_yourself.replay_contract import PlayerState, ReplayFrame, Vec3
from improve_yourself.sightlines import UnknownSmokeEvidence, evaluate_sightline
from improve_yourself.visibility_mesh import SegmentObstruction


class _Geometry:
    def __init__(self, state):
        self.result = SegmentObstruction(state, 0.5 if state == "blocked" else None, "fixture")

    def segment_obstruction(self, start, end):
        return self.result


class _Smoke:
    def __init__(self, state):
        self.result = SegmentObstruction(state, 0.5 if state == "blocked" else None, "fixture")

    def segment_obstruction(self, frame, start, end):
        return self.result


def _frame(*, target_position=Vec3(100, 0, 0), target_active=True):
    return ReplayFrame(
        tick=777,
        round_number=3,
        time_in_round_seconds=12.0,
        players=(
            PlayerState("observer", True, True, "CT", Vec3(0, 0, 0), 0, 0, None, 100, 0, None),
            PlayerState("target", target_active, True, "T", target_position, 180, 0, None, 100, 0, None),
        ),
        utilities=(),
        events=(),
    )


def test_clear_geometry_and_evidenced_clear_smoke_is_visible_at_exact_tick():
    result = evaluate_sightline(_frame(), "observer", "target", _Geometry("clear"), smoke_evidence=_Smoke("clear"))
    assert (result.tick, result.geometry_state, result.smoke_state, result.result) == (777, "clear", "clear", "visible")
    assert result.observer_player_id == "observer"
    assert result.target_player_id == "target"
    assert "canonical_tick:777" in result.evidence


def test_verified_geometry_or_evidenced_smoke_block_is_occluded():
    geometry_block = evaluate_sightline(_frame(), "observer", "target", _Geometry("blocked"))
    smoke_block = evaluate_sightline(
        _frame(), "observer", "target", _Geometry("clear"), smoke_evidence=_Smoke("blocked")
    )
    assert geometry_block.result == "occluded"
    assert geometry_block.smoke_state == "unknown"
    assert smoke_block.result == "occluded"


def test_clear_geometry_without_smoke_coverage_remains_unknown_never_visible():
    result = evaluate_sightline(_frame(), "observer", "target", _Geometry("clear"))
    assert result.geometry_state == "clear"
    assert result.smoke_state == "unknown"
    assert result.result == "unknown"


def test_unknown_geometry_dominates_even_when_smoke_is_clear():
    result = evaluate_sightline(
        _frame(), "observer", "target", _Geometry("unknown"), smoke_evidence=_Smoke("clear")
    )
    assert result.result == "unknown"


def test_missing_inactive_or_same_player_state_is_unknown_without_querying_fallback():
    missing = evaluate_sightline(_frame(target_position=None), "observer", "target", _Geometry("clear"))
    inactive = evaluate_sightline(_frame(target_active=False), "observer", "target", _Geometry("clear"))
    same = evaluate_sightline(_frame(), "observer", "observer", _Geometry("clear"))
    assert missing.result == inactive.result == same.result == "unknown"
    assert missing.geometry_state == inactive.geometry_state == same.geometry_state == "unknown"
