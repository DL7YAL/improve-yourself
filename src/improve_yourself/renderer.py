from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from .replay_contract import PlayerState, ReplayFrame, Vec3
from .sightlines import SightlineSegment
from .visibility_mesh import ObstructionState, VisibilityGeometry

ViewMode = Literal["first_person", "third_person"]


@dataclass(frozen=True)
class CameraPose:
    origin: Vec3
    target: Vec3
    yaw_deg: float
    pitch_deg: float
    roll_deg: float = 0.0
    camera_adjusted: bool = False
    obstruction_state: ObstructionState = "unknown"


class CameraUnavailable(ValueError):
    """The canonical frame cannot support the requested camera."""


@runtime_checkable
class ReplayRenderer(Protocol):
    """Backend-neutral V1 renderer boundary; replay interpretation stays upstream."""

    def load_map(self, manifest_path: Path) -> None: ...

    def set_frame(self, frame: ReplayFrame) -> None: ...

    def set_camera_player(self, player_id: str) -> None: ...

    def set_view_mode(self, mode: ViewMode) -> None: ...

    def set_sightlines(self, sightlines: tuple[SightlineSegment, ...]) -> None: ...

    def render(self) -> None: ...

    def resize(self, width: int, height: int) -> None: ...

    def dispose(self) -> None: ...


def _selected_player(frame: ReplayFrame, player_id: str) -> PlayerState:
    player = next((item for item in frame.players if item.player_id == player_id), None)
    if player is None:
        raise CameraUnavailable("selected player is absent from the canonical frame")
    if not player.active or player.alive is False:
        raise CameraUnavailable("Spieler zu diesem Zeitpunkt nicht aktiv.")
    if player.position is None or player.view_yaw_deg is None or player.view_pitch_deg is None:
        raise CameraUnavailable("selected player has no complete position/yaw/pitch evidence")
    return player


def _forward(yaw_deg: float, pitch_deg: float) -> Vec3:
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    horizontal = math.cos(pitch)
    # Source view pitch is positive while looking down, hence negative world Z.
    return Vec3(horizontal * math.cos(yaw), horizontal * math.sin(yaw), -math.sin(pitch))


def _offset(origin: Vec3, direction: Vec3, distance: float) -> Vec3:
    return Vec3(
        origin.x + direction.x * distance,
        origin.y + direction.y * distance,
        origin.z + direction.z * distance,
    )


def first_person_camera(frame: ReplayFrame, player_id: str, *, eye_height: float = 64.0) -> CameraPose:
    player = _selected_player(frame, player_id)
    assert player.position is not None and player.view_yaw_deg is not None and player.view_pitch_deg is not None
    eye = Vec3(player.position.x, player.position.y, player.position.z + eye_height)
    forward = _forward(player.view_yaw_deg, player.view_pitch_deg)
    return CameraPose(
        origin=eye,
        target=_offset(eye, forward, 320.0),
        yaw_deg=player.view_yaw_deg,
        pitch_deg=player.view_pitch_deg,
    )


def third_person_camera(
    frame: ReplayFrame,
    player_id: str,
    *,
    eye_height: float = 64.0,
    follow_distance: float = 160.0,
    vertical_offset: float = 72.0,
    visibility_geometry: VisibilityGeometry | None = None,
    safety_margin: float = 8.0,
) -> CameraPose:
    first_person = first_person_camera(frame, player_id, eye_height=eye_height)
    forward = _forward(first_person.yaw_deg, first_person.pitch_deg)
    anchor = first_person.origin
    origin = _offset(anchor, forward, -follow_distance)
    origin = Vec3(origin.x, origin.y, origin.z + vertical_offset)
    obstruction_state: ObstructionState = "unknown"
    camera_adjusted = False
    if visibility_geometry is not None:
        obstruction = visibility_geometry.segment_obstruction(origin, anchor)
        obstruction_state = obstruction.state
        if obstruction.state == "blocked":
            if obstruction.last_hit_fraction is None:
                raise ValueError("blocked visibility result requires a hit fraction")
            if not 0.0 < obstruction.last_hit_fraction < 1.0:
                raise ValueError("visibility hit fraction must be inside the camera segment")
            if safety_margin < 0.0:
                raise ValueError("camera safety margin cannot be negative")
            segment = Vec3(anchor.x - origin.x, anchor.y - origin.y, anchor.z - origin.z)
            segment_length = math.sqrt(segment.x * segment.x + segment.y * segment.y + segment.z * segment.z)
            fraction = min(1.0, obstruction.last_hit_fraction + safety_margin / segment_length)
            origin = _offset(origin, segment, fraction)
            camera_adjusted = True
    return CameraPose(
        origin=origin,
        target=_offset(anchor, forward, 320.0),
        yaw_deg=first_person.yaw_deg,
        pitch_deg=first_person.pitch_deg,
        camera_adjusted=camera_adjusted,
        obstruction_state=obstruction_state,
    )


class NullRenderer:
    """Lifecycle-checkable backend for controller integration and headless tests."""

    def __init__(self) -> None:
        self.manifest_path: Path | None = None
        self.frame: ReplayFrame | None = None
        self.player_id: str | None = None
        self.view_mode: ViewMode = "first_person"
        self.size = (0, 0)
        self.sightlines: tuple[SightlineSegment, ...] = ()
        self.render_count = 0
        self.disposed = False

    def _require_live(self) -> None:
        if self.disposed:
            raise RuntimeError("renderer is disposed")

    def load_map(self, manifest_path: Path) -> None:
        self._require_live()
        self.manifest_path = Path(manifest_path)

    def set_frame(self, frame: ReplayFrame) -> None:
        self._require_live()
        self.frame = frame

    def set_camera_player(self, player_id: str) -> None:
        self._require_live()
        self.player_id = player_id

    def set_view_mode(self, mode: ViewMode) -> None:
        self._require_live()
        if mode not in ("first_person", "third_person"):
            raise ValueError(f"unsupported V1 view mode: {mode}")
        self.view_mode = mode

    def set_sightlines(self, sightlines: tuple[SightlineSegment, ...]) -> None:
        self._require_live()
        self.sightlines = tuple(sightlines)

    def render(self) -> None:
        self._require_live()
        if self.manifest_path is None or self.frame is None or self.player_id is None:
            raise RuntimeError("map, canonical frame and camera player are required before render")
        self.render_count += 1

    def resize(self, width: int, height: int) -> None:
        self._require_live()
        if width <= 0 or height <= 0:
            raise ValueError("renderer dimensions must be positive")
        self.size = (width, height)

    def dispose(self) -> None:
        self.disposed = True
