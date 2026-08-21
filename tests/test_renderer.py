from pathlib import Path

import pytest

from improve_yourself.renderer import (
    CameraUnavailable,
    NullRenderer,
    ReplayRenderer,
    first_person_camera,
    third_person_camera,
)
from improve_yourself.replay_contract import PlayerState, ReplayFrame, Vec3


def _frame(*, active=True, alive=True, position=Vec3(100.0, 200.0, 10.0), yaw=90.0, pitch=0.0):
    return ReplayFrame(
        tick=123,
        round_number=2,
        time_in_round_seconds=10.0,
        players=(PlayerState("p1", active, alive, "CT", position, yaw, pitch, None, 100, 0, None),),
        utilities=(),
        events=(),
    )


def test_first_person_camera_uses_observed_transform_deterministically():
    pose = first_person_camera(_frame(), "p1")
    assert pose.origin == Vec3(100.0, 200.0, 74.0)
    assert pose.target.x == pytest.approx(100.0)
    assert pose.target.y == pytest.approx(520.0)
    assert pose.target.z == pytest.approx(74.0)
    assert (pose.yaw_deg, pose.pitch_deg, pose.roll_deg) == (90.0, 0.0, 0.0)
    assert pose.camera_adjusted is False


def test_fixed_third_person_camera_matches_v1_formula():
    pose = third_person_camera(_frame(), "p1")
    assert pose.origin.x == pytest.approx(100.0)
    assert pose.origin.y == pytest.approx(40.0)
    assert pose.origin.z == pytest.approx(146.0)
    assert pose.target.x == pytest.approx(100.0)
    assert pose.target.y == pytest.approx(520.0)
    assert pose.target.z == pytest.approx(74.0)


@pytest.mark.parametrize(
    "frame",
    [
        _frame(active=False),
        _frame(alive=False),
        _frame(position=None),
        _frame(yaw=None),
        _frame(pitch=None),
    ],
)
def test_camera_never_invents_unavailable_player_state(frame):
    with pytest.raises(CameraUnavailable):
        first_person_camera(frame, "p1")


def test_null_renderer_proves_protocol_lifecycle_and_guards_dispose():
    renderer = NullRenderer()
    assert isinstance(renderer, ReplayRenderer)
    renderer.load_map(Path("manifest.json"))
    renderer.set_frame(_frame())
    renderer.set_camera_player("p1")
    renderer.set_view_mode("third_person")
    renderer.resize(1280, 720)
    renderer.render()
    assert renderer.size == (1280, 720)
    assert renderer.render_count == 1
    renderer.dispose()
    with pytest.raises(RuntimeError, match="disposed"):
        renderer.render()
