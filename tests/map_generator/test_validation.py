import struct
import pytest
from tools.map_generator.validate import is_horizontal_surface_candidate, iter_triangles

def test_validation_rejects_partial_triangle_and_classifies_vertical_surface(tmp_path):
    bad=tmp_path/'bad.tri'; bad.write_bytes(b'bad')
    with pytest.raises(ValueError,match='complete'): list(iter_triangles(bad))
    vertical=((0.,0.,0.),(0.,0.,1.),(0.,1.,0.))
    assert not is_horizontal_surface_candidate(vertical)
