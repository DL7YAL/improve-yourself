import numpy as np
import pytest

from improve_yourself.replay_contract import Vec3
from improve_yourself.visibility_mesh import TriVisibilityMesh, UnknownVisibilityGeometry


def _wall(x):
    return [[x, -10, -10], [x, 10, -10], [x, 0, 10]]


def test_verified_triangle_mesh_reports_clear_and_blocked_with_last_hit():
    mesh = TriVisibilityMesh(np.array([_wall(2), _wall(7)], dtype=np.float32), chunk_size=1)
    blocked = mesh.segment_obstruction(Vec3(0, 0, 0), Vec3(10, 0, 0))
    assert blocked.state == "blocked"
    assert blocked.last_hit_fraction == pytest.approx(0.7)
    assert mesh.segment_obstruction(Vec3(0, 20, 0), Vec3(10, 20, 0)).state == "clear"


def test_unknown_geometry_and_invalid_segments_remain_unknown():
    assert UnknownVisibilityGeometry("missing").segment_obstruction(Vec3(0, 0, 0), Vec3(1, 0, 0)).state == "unknown"
    mesh = TriVisibilityMesh(np.array([_wall(2)], dtype=np.float32))
    result = mesh.segment_obstruction(Vec3(0, 0, 0), Vec3(0, 0, 0))
    assert result.state == "unknown"
    assert "zero length" in result.reason
