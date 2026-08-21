from dataclasses import replace

import pytest

from improve_yourself.replay_contract import PlayerState, ReplayFrame, Vec3
from improve_yourself.sightlines import SIGHTLINE_COLORS, UnknownSmokeEvidence, evaluate_sightline, present_sightline
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


def test_presentation_uses_same_tick_players_and_fixed_result_color_without_reevaluation():
    frame = _frame()
    result = evaluate_sightline(frame, "observer", "target", _Geometry("blocked"))
    segment = present_sightline(frame, result)
    assert segment is not None
    assert (segment.tick, segment.observer_player_id, segment.target_player_id) == (777, "observer", "target")
    assert segment.start == Vec3(0, 0, 64)
    assert segment.end == Vec3(100, 0, 64)
    assert segment.color == SIGHTLINE_COLORS["occluded"]


def test_presentation_rejects_cross_tick_result_and_skips_missing_endpoints():
    frame = _frame()
    other_tick = replace(frame, tick=778)
    result = evaluate_sightline(frame, "observer", "target", _Geometry("clear"))
    with pytest.raises(ValueError, match="tick differs"):
        present_sightline(other_tick, result)
    missing = evaluate_sightline(_frame(target_position=None), "observer", "target", _Geometry("clear"))
    assert present_sightline(_frame(target_position=None), missing) is None


def test_v1_sightline_palette_is_fixed_and_distinct():
    assert SIGHTLINE_COLORS == {
        "visible": (0.20, 0.85, 0.42, 1.0),
        "occluded": (0.95, 0.30, 0.22, 1.0),
        "unknown": (0.62, 0.66, 0.72, 1.0),
    }
    assert len(set(SIGHTLINE_COLORS.values())) == 3
