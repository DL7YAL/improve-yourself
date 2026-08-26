from pathlib import Path

import pytest

from improve_yourself.renderer import NullRenderer
from improve_yourself.renderer_session import ReplayRendererSession
from improve_yourself.replay_contract import PlayerState, ReplayFrame, Vec3, to_dict
from improve_yourself.replay_controller import ReplayContext


def _frame(tick):
    return ReplayFrame(
        tick=tick, round_number=1, time_in_round_seconds=None,
        players=(PlayerState("p1", True, True, "CT", Vec3(1, 2, 3), 10, 5, None, 100, 0, None),),
        utilities=(), events=(),
    )


def _context(*, requested=10, resolved=10, player=None, view="tactical_2d"):
    return ReplayContext(
        current_round=1, requested_tick=requested, resolved_tick=resolved,
        frame=to_dict(_frame(resolved)), play_state="paused", playback_speed=1.0,
        selected_player_id=player, selected_scene_id=None, view_mode=view,
        tick_rate=64.0, timing_available=True,
    )


class _Controller:
    def __init__(self):
        self.context = _context()
        self.listeners = []

    def snapshot(self):
        return self.context

    def subscribe(self, listener):
        self.listeners.append(listener)

        def unsubscribe():
            self.listeners.remove(listener)

        return unsubscribe

    def emit(self, context):
        self.context = context
        for listener in tuple(self.listeners):
            listener(context)


def test_session_mirrors_resolved_frame_selection_and_view_without_owning_seek():
    controller = _Controller()
    renderer = NullRenderer()
    renderer.load_map(Path("manifest.json"))
    session = ReplayRendererSession(controller, renderer)
    assert session.state.active is False
    assert renderer.frame.tick == 10
    assert session.render() is False

    controller.emit(_context(requested=14, resolved=12, player="p1", view="first_person"))
    assert (session.state.requested_tick, session.state.resolved_tick) == (14, 12)
    assert renderer.frame.tick == 12
    assert renderer.player_id == "p1"
    assert renderer.view_mode == "first_person"
    assert session.render() is True

    controller.emit(_context(requested=14, resolved=12, player="p1", view="analysis_third_person"))
    assert renderer.view_mode == "third_person"
    assert renderer.frame.tick == 12
    assert (session.state.requested_tick, session.state.resolved_tick) == (14, 12)


def test_session_rejects_controller_tick_mismatch_and_unsubscribes_on_dispose():
    controller = _Controller()
    renderer = NullRenderer()
    session = ReplayRendererSession(controller, renderer)
    mismatch = _context(requested=14, resolved=12)
    mismatch.frame["tick"] = 11
    with pytest.raises(ValueError, match="differs from resolved_tick"):
        controller.emit(mismatch)
    session.dispose()
    assert controller.listeners == []
    assert renderer.disposed is True
    with pytest.raises(RuntimeError, match="disposed"):
        session.render()
