from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

REPLAY_V2_SCHEMA = "iy.replay/v2"
ROUND_CHUNK_SCHEMA = "iy.replay_round/v2"

CapabilityLevel = Literal["full", "partial", "unavailable"]
Team = Literal["T", "CT", "unknown"]


@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class PlayerIdentity:
    player_id: str
    steam_id: str | None
    entity_id: int | None
    display_name: str
    identity_quality: Literal["steam", "entity", "scoped_slot", "unresolved"]


@dataclass(frozen=True)
class PlayerState:
    player_id: str
    active: bool
    alive: bool | None
    team: Team
    position: Vec3 | None
    view_yaw_deg: float | None
    view_pitch_deg: float | None
    velocity: Vec3 | None
    health: int | None
    armor: int | None
    weapon: str | None
    availability: tuple[str, ...] = ()


@dataclass(frozen=True)
class UtilityState:
    utility_id: str
    utility_type: str
    owner_player_id: str | None
    start_tick: int
    end_tick: int | None
    position: Vec3 | None
    trajectory: tuple[dict[str, Any], ...] | None
    active: bool
    evidence: Literal["trajectory", "lifetime", "detonation_only"]


@dataclass(frozen=True)
class ReplayEvent:
    event_id: str
    type: str
    tick: int
    player_ids: tuple[str, ...] = ()
    position: Vec3 | None = None
    evidence: str = "parser_event"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReplayFrame:
    tick: int
    round_number: int
    time_in_round_seconds: float | None
    players: tuple[PlayerState, ...]
    utilities: tuple[UtilityState, ...]
    events: tuple[ReplayEvent, ...]


@dataclass(frozen=True)
class ReplayCapabilities:
    positions: CapabilityLevel
    view_yaw: CapabilityLevel
    view_pitch: CapabilityLevel
    alive_state: CapabilityLevel
    weapon_state: CapabilityLevel
    velocity: CapabilityLevel
    utility_lifetimes: CapabilityLevel
    utility_trajectories: CapabilityLevel
    flash_effect: CapabilityLevel
    sound: CapabilityLevel
    map_geometry: Literal["verified", "mismatch", "unavailable"] = "unavailable"


def to_dict(value: Any) -> Any:
    """Convert immutable contract values into plain JSON-compatible data."""
    if hasattr(value, "__dataclass_fields__"):
        return {key: to_dict(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [to_dict(item) for item in value]
    if isinstance(value, list):
        return [to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    return value


def replay_frame_from_dict(value: dict[str, Any]) -> ReplayFrame:
    """Restore one validated canonical frame for typed renderer/evaluator consumers."""
    def vec3(item: dict[str, Any] | None) -> Vec3 | None:
        return None if item is None else Vec3(float(item["x"]), float(item["y"]), float(item["z"]))

    players = tuple(
        PlayerState(
            player_id=item["player_id"], active=item["active"], alive=item.get("alive"), team=item["team"],
            position=vec3(item.get("position")), view_yaw_deg=item.get("view_yaw_deg"),
            view_pitch_deg=item.get("view_pitch_deg"), velocity=vec3(item.get("velocity")), health=item.get("health"),
            armor=item.get("armor"), weapon=item.get("weapon"), availability=tuple(item.get("availability", ())),
        ) for item in value.get("players", ())
    )
    utilities = tuple(
        UtilityState(
            utility_id=item["utility_id"], utility_type=item["utility_type"], owner_player_id=item.get("owner_player_id"),
            start_tick=item["start_tick"], end_tick=item.get("end_tick"), position=vec3(item.get("position")),
            trajectory=None if item.get("trajectory") is None else tuple(item["trajectory"]),
            active=item["active"], evidence=item["evidence"],
        ) for item in value.get("utilities", ())
    )
    events = tuple(
        ReplayEvent(
            event_id=item["event_id"], type=item["type"], tick=item["tick"],
            player_ids=tuple(item.get("player_ids", ())), position=vec3(item.get("position")),
            evidence=item.get("evidence", "parser_event"), details=dict(item.get("details", {})),
        ) for item in value.get("events", ())
    )
    return ReplayFrame(
        tick=value["tick"], round_number=value["round_number"],
        time_in_round_seconds=value.get("time_in_round_seconds"), players=players, utilities=utilities, events=events,
    )
