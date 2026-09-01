"""Strict, presentation-only readiness contract for an owned 3D POV scene.

The descriptor deliberately has no map, collision, replay, camera, asset-gate,
or gameplay authority. It records only whether an own visual presentation layer
exists; it never turns diagnostic physics geometry into product map art.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


OWNED_SCENE_PRESENTATION_SCHEMA = "iy.improve_3d_scene_presentation/v1"
SceneAvailability = Literal["not_available", "unknown", "technical_only"]


class OwnedScenePresentationError(ValueError):
    """The owned 3D scene descriptor is missing, malformed, or unsafe."""


@dataclass(frozen=True)
class OwnedScenePresentation:
    """Validated visual-readiness facts with no map or replay authority."""

    map_id: str
    output_state: SceneAvailability
    player_marker_layer: str
    view_direction_layer: str
    neutral_spatial_reference_state: SceneAvailability
    badge_state: SceneAvailability
    outbox_state: SceneAvailability
    discovery_state: SceneAvailability


_TOP_LEVEL_FIELDS = {
    "schema", "map_id", "purpose", "source_classification", "output_state",
    "visual_layers", "future_reservations", "non_authority",
}
_VISUAL_LAYER_FIELDS = {"player_markers", "view_directions", "neutral_spatial_reference"}
_RESERVATION_FIELDS = {"badge", "outbox", "discovery"}
_NON_AUTHORITY = [
    "map_geometry", "collision_authority", "navmesh", "callout_source",
    "route_source", "event_source", "replay_source", "camera_source",
    "asset_gate_replacement", "proprietary_asset_manifest",
]
_AVAILABILITY = {"not_available", "unknown", "technical_only"}
_CANONICAL_REPLAY_LAYER = "canonical_replay"


def _exact_object(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise OwnedScenePresentationError(f"{label} must contain exactly {sorted(fields)}")
    return value


def _availability(value: Any, label: str) -> SceneAvailability:
    if value not in _AVAILABILITY:
        raise OwnedScenePresentationError(f"{label} must be one of {sorted(_AVAILABILITY)}")
    return value


def load_owned_scene_presentation(path: Path, replay_map_id: str) -> OwnedScenePresentation:
    """Load a fail-closed own visual-readiness descriptor for one replay map."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise OwnedScenePresentationError(f"owned scene presentation is missing: {path}") from error
    except json.JSONDecodeError as error:
        raise OwnedScenePresentationError(f"owned scene presentation is invalid JSON: {error}") from error

    document = _exact_object(document, _TOP_LEVEL_FIELDS, "scene document")
    if document["schema"] != OWNED_SCENE_PRESENTATION_SCHEMA:
        raise OwnedScenePresentationError(f"expected schema {OWNED_SCENE_PRESENTATION_SCHEMA}")
    if not isinstance(document["map_id"], str) or document["map_id"] != replay_map_id:
        raise OwnedScenePresentationError("scene map_id differs from replay map")
    if document["purpose"] != "presentation_only":
        raise OwnedScenePresentationError("scene purpose must remain presentation_only")
    if document["source_classification"] != "OWNED_IMPROVE_PROCEDURAL":
        raise OwnedScenePresentationError("scene source classification is not approved")
    if document["non_authority"] != _NON_AUTHORITY:
        raise OwnedScenePresentationError("scene non_authority declaration must remain exact")

    layers = _exact_object(document["visual_layers"], _VISUAL_LAYER_FIELDS, "visual_layers")
    if layers["player_markers"] != _CANONICAL_REPLAY_LAYER:
        raise OwnedScenePresentationError("player_markers must remain canonical_replay")
    if layers["view_directions"] != _CANONICAL_REPLAY_LAYER:
        raise OwnedScenePresentationError("view_directions must remain canonical_replay")
    reservations = _exact_object(document["future_reservations"], _RESERVATION_FIELDS, "future_reservations")

    return OwnedScenePresentation(
        map_id=replay_map_id,
        output_state=_availability(document["output_state"], "output_state"),
        player_marker_layer=layers["player_markers"],
        view_direction_layer=layers["view_directions"],
        neutral_spatial_reference_state=_availability(
            layers["neutral_spatial_reference"], "visual_layers.neutral_spatial_reference"
        ),
        badge_state=_availability(reservations["badge"], "future_reservations.badge"),
        outbox_state=_availability(reservations["outbox"], "future_reservations.outbox"),
        discovery_state=_availability(reservations["discovery"], "future_reservations.discovery"),
    )
