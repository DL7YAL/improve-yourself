from __future__ import annotations

import json
import struct
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterator

JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942


def read_glb(path: Path) -> tuple[dict[str, Any], bytes]:
    with path.open("rb") as stream:
        magic, version, length = struct.unpack("<4sII", stream.read(12))
        if magic != b"glTF" or version != 2 or length != path.stat().st_size:
            raise ValueError("expected a complete glTF 2.0 binary")
        chunks: dict[int, bytes] = {}
        while stream.tell() < length:
            size, kind = struct.unpack("<II", stream.read(8))
            chunks[kind] = stream.read(size)
    if JSON_CHUNK not in chunks or BIN_CHUNK not in chunks:
        raise ValueError("GLB requires JSON and BIN chunks")
    return json.loads(chunks[JSON_CHUNK].rstrip(b" \x00")), chunks[BIN_CHUNK]


def normal_world_nodes(document: dict[str, Any]) -> list[int]:
    return [
        index for index, node in enumerate(document.get("nodes", []))
        if node.get("mesh") is not None and node.get("extras", {}).get("InteractAs") == []
    ]


def _accessor_values(document: dict[str, Any], binary: bytes, index: int) -> Iterator[tuple[Any, ...]]:
    accessor = document["accessors"][index]
    view = document["bufferViews"][accessor["bufferView"]]
    component = {5123: "H", 5125: "I", 5126: "f"}.get(accessor["componentType"])
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    if component is None:
        raise ValueError(f"unsupported GLB component type {accessor['componentType']}")
    value_size = struct.calcsize("<" + component * width)
    stride = view.get("byteStride", value_size)
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    for item in range(accessor["count"]):
        yield struct.unpack_from("<" + component * width, binary, offset + item * stride)


def write_visibility_tri(document: dict[str, Any], binary: bytes, nodes: list[int], path: Path) -> int:
    triangle_count = 0
    with path.open("wb") as stream:
        for node_index in nodes:
            mesh = document["meshes"][document["nodes"][node_index]["mesh"]]
            for primitive in mesh["primitives"]:
                if primitive.get("mode", 4) != 4 or "indices" not in primitive:
                    raise ValueError("only indexed triangle primitives are supported")
                positions = list(_accessor_values(document, binary, primitive["attributes"]["POSITION"]))
                indices = [item[0] for item in _accessor_values(document, binary, primitive["indices"])]
                if len(indices) % 3:
                    raise ValueError("triangle index count must be divisible by three")
                for offset in range(0, len(indices), 3):
                    values = positions[indices[offset]] + positions[indices[offset + 1]] + positions[indices[offset + 2]]
                    stream.write(struct.pack("<9f", *values))
                    triangle_count += 1
    return triangle_count


def write_replay_space_glb(document: dict[str, Any], binary: bytes, nodes: list[int], path: Path) -> None:
    output = deepcopy(document)
    output["scenes"] = [{"name": "Improve Yourself local-only Anubis collision mesh", "nodes": nodes}]
    output["scene"] = 0
    for index, node in enumerate(output["nodes"]):
        if index in nodes:
            node.pop("matrix", None)
            node.pop("translation", None)
            node.pop("rotation", None)
            node.pop("scale", None)
    encoded = json.dumps(output, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encoded += b" " * ((-len(encoded)) % 4)
    binary += b"\x00" * ((-len(binary)) % 4)
    total = 12 + 8 + len(encoded) + 8 + len(binary)
    with path.open("wb") as stream:
        stream.write(struct.pack("<4sII", b"glTF", 2, total))
        stream.write(struct.pack("<II", len(encoded), JSON_CHUNK))
        stream.write(encoded)
        stream.write(struct.pack("<II", len(binary), BIN_CHUNK))
        stream.write(binary)


def build_local_derivative(source_glb: Path, output: Path) -> dict[str, Any]:
    document, binary = read_glb(source_glb)
    nodes = normal_world_nodes(document)
    if not nodes:
        raise ValueError("no normal world-physics nodes found")
    output.mkdir(parents=True, exist_ok=True)
    render_path = output / "render_mesh.glb"
    visibility_path = output / "visibility_mesh.tri"
    write_replay_space_glb(document, binary, nodes, render_path)
    triangles = write_visibility_tri(document, binary, nodes, visibility_path)
    return {
        "normal_world_nodes": len(nodes),
        "triangles": triangles,
        "render_mesh": render_path,
        "visibility_mesh": visibility_path,
    }
