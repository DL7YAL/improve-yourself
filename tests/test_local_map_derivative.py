import json
import struct

from improve_yourself.local_map_derivative import BIN_CHUNK, JSON_CHUNK, build_local_derivative, read_glb


def _fixture_glb(path) -> None:
    positions = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
    indices = struct.pack("<3H", 0, 1, 2)
    binary = positions + indices + b"\x00\x00"
    document = {
        "asset": {"version": "2.0"}, "scene": 0,
        "scenes": [{"nodes": [0, 1]}],
        "nodes": [
            {"mesh": 0, "matrix": [2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1], "extras": {"InteractAs": []}},
            {"mesh": 0, "extras": {"InteractAs": ["playerclip"]}},
        ],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(positions)}, {"buffer": 0, "byteOffset": len(positions), "byteLength": 6}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
    }
    encoded = json.dumps(document, separators=(",", ":")).encode()
    encoded += b" " * ((-len(encoded)) % 4)
    total = 12 + 8 + len(encoded) + 8 + len(binary)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<II", len(encoded), JSON_CHUNK) + encoded + struct.pack("<II", len(binary), BIN_CHUNK) + binary)


def test_builds_replay_space_world_only_derivative(tmp_path) -> None:
    source = tmp_path / "source.glb"
    _fixture_glb(source)
    result = build_local_derivative(source, tmp_path / "out")
    assert result["normal_world_nodes"] == 1
    assert result["triangles"] == 1
    assert result["visibility_mesh"].read_bytes() == struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
    document, _ = read_glb(result["render_mesh"])
    assert document["scenes"][0]["nodes"] == [0]
    assert "matrix" not in document["nodes"][0]
