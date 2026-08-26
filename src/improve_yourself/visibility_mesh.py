from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

import numpy as np

from .map_assets import assess_map_asset
from .replay_contract import Vec3

ObstructionState = Literal["clear", "blocked", "unknown"]


@dataclass(frozen=True)
class SegmentObstruction:
    state: ObstructionState
    last_hit_fraction: float | None = None
    reason: str = ""


class VisibilityGeometry(Protocol):
    def segment_obstruction(self, start: Vec3, end: Vec3) -> SegmentObstruction: ...


class UnknownVisibilityGeometry:
    def __init__(self, reason: str = "verified visibility geometry is unavailable") -> None:
        self.reason = reason

    def segment_obstruction(self, start: Vec3, end: Vec3) -> SegmentObstruction:
        return SegmentObstruction("unknown", reason=self.reason)


class TriVisibilityMesh:
    """Read-only segment queries over the verified local `.tri` derivative."""

    def __init__(self, triangles: np.ndarray, *, chunk_size: int = 65_536) -> None:
        values = np.asarray(triangles, dtype=np.float32)
        if values.ndim != 3 or values.shape[1:] != (3, 3):
            raise ValueError("visibility triangles must have shape (n, 3, 3)")
        if len(values) == 0:
            raise ValueError("visibility mesh must contain triangles")
        self._triangles = values
        self._chunk_size = chunk_size

    @classmethod
    def from_verified_manifest(cls, manifest_path: Path, replay_map_id: str) -> "TriVisibilityMesh":
        assessment = assess_map_asset(manifest_path, replay_map_id)
        if assessment.availability != "available" or assessment.manifest is None:
            raise ValueError(f"visibility asset unavailable: {assessment.availability}: {assessment.reason}")
        descriptor = assessment.manifest["visibility_mesh"]
        path = manifest_path.resolve().parent / descriptor["path"]
        if path.stat().st_size % 36:
            raise ValueError("visibility mesh byte length is not a whole triangle")
        triangles = np.memmap(path, dtype="<f4", mode="r").reshape((-1, 3, 3))
        return cls(triangles)

    def segment_obstruction(self, start: Vec3, end: Vec3) -> SegmentObstruction:
        origin = np.array((start.x, start.y, start.z), dtype=np.float64)
        direction = np.array((end.x - start.x, end.y - start.y, end.z - start.z), dtype=np.float64)
        if not np.isfinite(origin).all() or not np.isfinite(direction).all():
            return SegmentObstruction("unknown", reason="segment contains non-finite coordinates")
        if float(np.dot(direction, direction)) <= 1e-12:
            return SegmentObstruction("unknown", reason="segment has zero length")

        last_hit: float | None = None
        epsilon = 1e-7
        for offset in range(0, len(self._triangles), self._chunk_size):
            triangle = np.asarray(self._triangles[offset : offset + self._chunk_size], dtype=np.float64)
            edge1 = triangle[:, 1] - triangle[:, 0]
            edge2 = triangle[:, 2] - triangle[:, 0]
            pvec = np.cross(direction, edge2)
            determinant = np.einsum("ij,ij->i", edge1, pvec)
            valid = np.abs(determinant) > epsilon
            inverse = np.zeros_like(determinant)
            inverse[valid] = 1.0 / determinant[valid]
            tvec = origin - triangle[:, 0]
            u = np.einsum("ij,ij->i", tvec, pvec) * inverse
            valid &= (u >= -epsilon) & (u <= 1.0 + epsilon)
            qvec = np.cross(tvec, edge1)
            v = np.einsum("j,ij->i", direction, qvec) * inverse
            valid &= (v >= -epsilon) & ((u + v) <= 1.0 + epsilon)
            fraction = np.einsum("ij,ij->i", edge2, qvec) * inverse
            valid &= (fraction > epsilon) & (fraction < 1.0 - epsilon)
            if np.any(valid):
                chunk_last = float(np.max(fraction[valid]))
                last_hit = chunk_last if last_hit is None else max(last_hit, chunk_last)
        if last_hit is None:
            return SegmentObstruction("clear", reason="verified mesh has no segment intersection")
        return SegmentObstruction("blocked", last_hit, "verified mesh intersects the segment")
