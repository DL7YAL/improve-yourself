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
from improve_yourself.visibility_mesh import SegmentObstruction, UnknownVisibilityGeometry
from improve_yourself.sightlines import SightlineSegment


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
    assert pose.obstruction_state == "unknown"


class _Geometry:
    def __init__(self, result):
        self.result = result

    def segment_obstruction(self, start, end):
        return self.result


def test_third_person_camera_moves_past_last_obstruction_only_along_fixed_segment():
    pose = third_person_camera(
        _frame(), "p1", visibility_geometry=_Geometry(SegmentObstruction("blocked", 0.5)), safety_margin=8.0
    )
    # Base camera (100, 40, 146) moves toward anchor (100, 200, 74), never sideways.
    assert pose.origin.x == pytest.approx(100.0)
    segment_length = (160.0**2 + 72.0**2) ** 0.5
    fraction = 0.5 + 8.0 / segment_length
    assert pose.origin.y == pytest.approx(40.0 + 160.0 * fraction)
    assert pose.origin.z == pytest.approx(146.0 - 72.0 * fraction)
    assert pose.camera_adjusted is True
    assert pose.obstruction_state == "blocked"


def test_third_person_camera_preserves_fixed_pose_for_clear_or_unknown_geometry():
    clear = third_person_camera(_frame(), "p1", visibility_geometry=_Geometry(SegmentObstruction("clear")))
    unknown = third_person_camera(_frame(), "p1", visibility_geometry=UnknownVisibilityGeometry())
    assert clear.origin == unknown.origin == third_person_camera(_frame(), "p1").origin
    assert clear.obstruction_state == "clear"
    assert unknown.obstruction_state == "unknown"
    assert clear.camera_adjusted is unknown.camera_adjusted is False


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
    sightline = SightlineSegment("p1", "p2", 123, Vec3(0, 0, 0), Vec3(1, 1, 1), "unknown", (0.62, 0.66, 0.72, 1.0))
    renderer.set_sightlines((sightline,))
    renderer.resize(1280, 720)
    renderer.render()
    assert renderer.size == (1280, 720)
    assert renderer.render_count == 1
    renderer.set_view_mode("first_person")
    assert renderer.sightlines == (sightline,)
    renderer.set_view_mode("third_person")
    assert renderer.sightlines == (sightline,)
    renderer.dispose()
    with pytest.raises(RuntimeError, match="disposed"):
        renderer.render()
