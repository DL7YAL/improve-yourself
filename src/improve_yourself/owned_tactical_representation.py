"""Strict, presentation-only contract for owned tactical 3D accents.

This module deliberately has no map, replay, collision, or progression
authority.  It translates an already canonical ``ReplayFrame`` into optional
own procedural marker instructions; no model, texture, or map asset is loaded.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .replay_contract import ReplayFrame, Vec3


OWNED_TACTICAL_REPRESENTATION_SCHEMA = "iy.improve_tactical_representation/v1"
PresentationAvailability = Literal["not_available", "unknown"]


class OwnedTacticalRepresentationError(ValueError):
    """The presentation-only descriptor is absent, malformed, or unsafe."""


@dataclass(frozen=True)
class TeamMarkerStyle:
    color: tuple[float, float, float, float]


@dataclass(frozen=True)
class OwnedTacticalRepresentation:
    """Validated visual preferences with no gameplay/map authority."""

    map_id: str
    team_styles: dict[str, TeamMarkerStyle]
    badge_anchor_state: PresentationAvailability
    outbox_state: PresentationAvailability
    discovery_state: PresentationAvailability


@dataclass(frozen=True)
class PlayerMarkerInstruction:
    """One own visual marker derived from an already canonical player state."""

    player_id: str
    position: Vec3
    color: tuple[float, float, float, float]
    forward_xy: tuple[float, float] | None
    badge_anchor_state: PresentationAvailability


_TOP_LEVEL_FIELDS = {
    "schema",
    "map_id",
    "purpose",
    "source_classification",
    "player_markers",
    "outbox",
    "discovery",
}
_PLAYER_MARKER_FIELDS = {"mode", "team_colors", "badge_anchor"}
_OUTBOX_FIELDS = {"state"}
_DISCOVERY_FIELDS = {"state", "slots"}
_TEAM_IDS = {"CT", "T", "unknown"}
_SAFE_PRESENTATION_STATES = {"not_available", "unknown"}


def _require_exact_fields(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise OwnedTacticalRepresentationError(f"{label} must contain exactly {sorted(fields)}")
    return value


def _color(value: Any, team: str) -> tuple[float, float, float, float]:
    if not isinstance(value, list) or len(value) != 4 or not all(isinstance(item, (int, float)) for item in value):
        raise OwnedTacticalRepresentationError(f"team_colors.{team} must be four finite numeric channels")
    result = tuple(float(item) for item in value)
    if not all(math.isfinite(item) and 0.0 <= item <= 1.0 for item in result):
        raise OwnedTacticalRepresentationError(f"team_colors.{team} must be within [0, 1]")
    return result  # type: ignore[return-value]


def _presentation_state(value: Any, label: str) -> PresentationAvailability:
    if value not in _SAFE_PRESENTATION_STATES:
        raise OwnedTacticalRepresentationError(f"{label} must be one of {sorted(_SAFE_PRESENTATION_STATES)}")
    return value


def load_owned_tactical_representation(path: Path, replay_map_id: str) -> OwnedTacticalRepresentation:
    """Load an owned, fail-closed presentation descriptor for one replay map."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise OwnedTacticalRepresentationError(f"owned tactical representation is missing: {path}") from error
    except json.JSONDecodeError as error:
        raise OwnedTacticalRepresentationError(f"owned tactical representation is invalid JSON: {error}") from error

    document = _require_exact_fields(document, _TOP_LEVEL_FIELDS, "representation document")
    if document["schema"] != OWNED_TACTICAL_REPRESENTATION_SCHEMA:
        raise OwnedTacticalRepresentationError(f"expected schema {OWNED_TACTICAL_REPRESENTATION_SCHEMA}")
    if not isinstance(document["map_id"], str) or document["map_id"] != replay_map_id:
        raise OwnedTacticalRepresentationError("representation map_id differs from replay map")
    if document["purpose"] != "presentation_only":
        raise OwnedTacticalRepresentationError("representation purpose must remain presentation_only")
    if document["source_classification"] != "OWNED_IMPROVE_PROCEDURAL":
        raise OwnedTacticalRepresentationError("representation source classification is not approved")

    player_markers = _require_exact_fields(document["player_markers"], _PLAYER_MARKER_FIELDS, "player_markers")
    if player_markers["mode"] != "procedural_marker":
        raise OwnedTacticalRepresentationError("player_markers mode must remain procedural_marker")
    team_colors = _require_exact_fields(player_markers["team_colors"], _TEAM_IDS, "player_markers.team_colors")
    badge_anchor_state = _presentation_state(player_markers["badge_anchor"], "player_markers.badge_anchor")

    outbox = _require_exact_fields(document["outbox"], _OUTBOX_FIELDS, "outbox")
    discovery = _require_exact_fields(document["discovery"], _DISCOVERY_FIELDS, "discovery")
    if discovery["slots"] != []:
        raise OwnedTacticalRepresentationError("discovery slots must remain empty until separately authorised")

    return OwnedTacticalRepresentation(
        map_id=replay_map_id,
        team_styles={team: TeamMarkerStyle(_color(team_colors[team], team)) for team in _TEAM_IDS},
        badge_anchor_state=badge_anchor_state,
        outbox_state=_presentation_state(outbox["state"], "outbox.state"),
        discovery_state=_presentation_state(discovery["state"], "discovery.state"),
    )


def player_marker_instructions(
    representation: OwnedTacticalRepresentation,
    frame: ReplayFrame,
    *,
    selected_player_id: str | None,
    view_mode: str,
) -> tuple[PlayerMarkerInstruction, ...]:
    """Project canonical players into own marker instructions without mutation.

    Active players without a canonical position are omitted; their position is
    never guessed.  An optional direction is shown only when canonical yaw is
    present.  The selected first-person player's marker is hidden solely to
    avoid placing an own marker around the active camera.
    """
    instructions: list[PlayerMarkerInstruction] = []
    for player in frame.players:
        if not player.active or player.position is None:
            continue
        if view_mode == "first_person" and player.player_id == selected_player_id:
            continue
        style = representation.team_styles.get(player.team, representation.team_styles["unknown"])
        forward_xy: tuple[float, float] | None = None
        if player.view_yaw_deg is not None:
            yaw = math.radians(player.view_yaw_deg)
            forward_xy = (math.cos(yaw), math.sin(yaw))
        instructions.append(PlayerMarkerInstruction(
            player_id=player.player_id,
            position=player.position,
            color=style.color,
            forward_xy=forward_xy,
            badge_anchor_state=representation.badge_anchor_state,
        ))
    return tuple(instructions)
