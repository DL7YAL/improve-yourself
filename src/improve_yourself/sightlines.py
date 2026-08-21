from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal, Protocol

from .replay_contract import PlayerState, ReplayFrame, Vec3
from .visibility_mesh import ObstructionState, SegmentObstruction, VisibilityGeometry

SightlineOutcome = Literal["visible", "occluded", "unknown"]
SightlineColor = tuple[float, float, float, float]
SIGHTLINE_COLORS: dict[SightlineOutcome, SightlineColor] = {
    "visible": (0.20, 0.85, 0.42, 1.0),
    "occluded": (0.95, 0.30, 0.22, 1.0),
    "unknown": (0.62, 0.66, 0.72, 1.0),
}


@dataclass(frozen=True)
class SightlineResult:
    observer_player_id: str
    target_player_id: str
    tick: int
    geometry_state: ObstructionState
    smoke_state: ObstructionState
    result: SightlineOutcome
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class SightlineSegment:
    observer_player_id: str
    target_player_id: str
    tick: int
    start: Vec3
    end: Vec3
    result: SightlineOutcome
    color: SightlineColor


class SmokeEvidence(Protocol):
    """Evidence-qualified smoke intersection boundary, deliberately separate from geometry."""

    def segment_obstruction(self, frame: ReplayFrame, start: Vec3, end: Vec3) -> SegmentObstruction: ...


class UnknownSmokeEvidence:
    def __init__(self, reason: str = "canonical smoke coverage or V1 volume evidence is unavailable") -> None:
        self.reason = reason

    def segment_obstruction(self, frame: ReplayFrame, start: Vec3, end: Vec3) -> SegmentObstruction:
        return SegmentObstruction("unknown", reason=self.reason)


V1_SMOKE_SPHERE_RADIUS = 144.0


class CanonicalSmokeEvidence:
    """Conservative V1 sphere approximation gated by complete canonical coverage."""

    def __init__(self, utility_lifetimes: Literal["full", "partial", "unavailable"], *, radius: float = V1_SMOKE_SPHERE_RADIUS) -> None:
        if radius <= 0.0 or not math.isfinite(radius):
            raise ValueError("smoke approximation radius must be finite and positive")
        self.utility_lifetimes = utility_lifetimes
        self.radius = radius

    @staticmethod
    def _segment_distance_squared(start: Vec3, end: Vec3, point: Vec3) -> float:
        dx, dy, dz = end.x - start.x, end.y - start.y, end.z - start.z
        length_squared = dx * dx + dy * dy + dz * dz
        if length_squared <= 1e-12:
            return math.inf
        fraction = ((point.x - start.x) * dx + (point.y - start.y) * dy + (point.z - start.z) * dz) / length_squared
        fraction = min(1.0, max(0.0, fraction))
        nearest = Vec3(start.x + dx * fraction, start.y + dy * fraction, start.z + dz * fraction)
        return (point.x - nearest.x) ** 2 + (point.y - nearest.y) ** 2 + (point.z - nearest.z) ** 2

    def segment_obstruction(self, frame: ReplayFrame, start: Vec3, end: Vec3) -> SegmentObstruction:
        disclosure = f"V1 disclosed sphere approximation radius={self.radius:g} source_units"
        if self.utility_lifetimes != "full":
            return SegmentObstruction(
                "unknown", reason=f"utility lifetime/position coverage is {self.utility_lifetimes}; {disclosure} not applied"
            )
        active_smokes = tuple(item for item in frame.utilities if item.utility_type == "smoke" and item.active)
        for smoke in active_smokes:
            if (
                smoke.position is None
                or smoke.end_tick is None
                or smoke.evidence != "lifetime"
                or not smoke.start_tick <= frame.tick <= smoke.end_tick
            ):
                return SegmentObstruction("unknown", reason=f"active smoke evidence is incomplete; {disclosure}")
        for smoke in active_smokes:
            assert smoke.position is not None
            if self._segment_distance_squared(start, end, smoke.position) <= self.radius * self.radius:
                return SegmentObstruction("blocked", reason=f"active smoke intersects; {disclosure}")
        return SegmentObstruction("clear", reason=f"no active smoke intersects; {disclosure}")


def _player(frame: ReplayFrame, player_id: str) -> PlayerState | None:
    return next((player for player in frame.players if player.player_id == player_id), None)


def _eye(player: PlayerState | None, eye_height: float) -> Vec3 | None:
    if player is None or not player.active or player.alive is False or player.position is None:
        return None
    return Vec3(player.position.x, player.position.y, player.position.z + eye_height)


def evaluate_sightline(
    frame: ReplayFrame,
    observer_player_id: str,
    target_player_id: str,
    visibility_geometry: VisibilityGeometry,
    *,
    smoke_evidence: SmokeEvidence | None = None,
    eye_height: float = 64.0,
) -> SightlineResult:
    """Evaluate one canonical-tick sightline without inferring missing evidence."""
    evidence = [f"canonical_tick:{frame.tick}"]
    if observer_player_id == target_player_id:
        evidence.append("invalid:same_observer_and_target")
        return SightlineResult(
            observer_player_id, target_player_id, frame.tick, "unknown", "unknown", "unknown", tuple(evidence)
        )

    start = _eye(_player(frame, observer_player_id), eye_height)
    end = _eye(_player(frame, target_player_id), eye_height)
    if start is None or end is None:
        evidence.append("player_state:missing_or_inactive")
        return SightlineResult(
            observer_player_id, target_player_id, frame.tick, "unknown", "unknown", "unknown", tuple(evidence)
        )

    geometry = visibility_geometry.segment_obstruction(start, end)
    evidence.append(f"geometry:{geometry.state}:{geometry.reason or 'no_reason'}")
    smoke_provider = smoke_evidence or UnknownSmokeEvidence()
    smoke = smoke_provider.segment_obstruction(frame, start, end)
    evidence.append(f"smoke:{smoke.state}:{smoke.reason or 'no_reason'}")

    if geometry.state == "blocked":
        outcome: SightlineOutcome = "occluded"
    elif geometry.state == "unknown":
        outcome = "unknown"
    elif smoke.state == "blocked":
        outcome = "occluded"
    elif smoke.state == "clear":
        outcome = "visible"
    else:
        outcome = "unknown"
    evidence.append(f"result:{outcome}")
    return SightlineResult(
        observer_player_id,
        target_player_id,
        frame.tick,
        geometry.state,
        smoke.state,
        outcome,
        tuple(evidence),
    )


def present_sightline(
    frame: ReplayFrame, result: SightlineResult, *, eye_height: float = 64.0
) -> SightlineSegment | None:
    """Create renderer-ready coordinates without re-evaluating geometry or smoke."""
    if result.tick != frame.tick:
        raise ValueError("sightline result tick differs from the canonical frame")
    start = _eye(_player(frame, result.observer_player_id), eye_height)
    end = _eye(_player(frame, result.target_player_id), eye_height)
    if start is None or end is None:
        return None
    return SightlineSegment(
        observer_player_id=result.observer_player_id,
        target_player_id=result.target_player_id,
        tick=result.tick,
        start=start,
        end=end,
        result=result.result,
        color=SIGHTLINE_COLORS[result.result],
    )
