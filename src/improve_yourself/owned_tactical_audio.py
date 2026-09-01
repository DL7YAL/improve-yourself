"""Strict, presentation-only foundation for owned tactical audio cues.

The current Panda viewport intentionally disables audio.  This module therefore
only validates own procedural cue preferences and projects no cue unless a
future, separately authorised canonical event mapping and output capability
exist.  It owns neither replay time nor event truth.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .replay_contract import ReplayFrame


OWNED_TACTICAL_AUDIO_SCHEMA = "iy.improve_tactical_audio/v1"
AudioAvailability = Literal["not_available", "unknown", "disabled"]


class OwnedTacticalAudioError(ValueError):
    """The audio presentation descriptor is missing, malformed, or unsafe."""


@dataclass(frozen=True)
class ProceduralCue:
    cue_id: str
    wave: Literal["sine_decay", "noise_burst"]
    frequency_hz: float | None
    duration_ms: int
    gain: float


@dataclass(frozen=True)
class OwnedTacticalAudio:
    """Validated presentation preferences with no playback/event authority."""

    map_id: str
    output_state: AudioAvailability
    event_mapping_state: AudioAvailability
    cues: tuple[ProceduralCue, ...]
    badge_state: AudioAvailability
    outbox_state: AudioAvailability
    discovery_state: AudioAvailability


_TOP_LEVEL_FIELDS = {
    "schema", "map_id", "purpose", "source_classification", "output_state",
    "event_mapping_state", "user_control", "authenticity_contract", "cues", "future_reservations",
}
_USER_CONTROL_FIELDS = {"default_state"}
_AUTHENTICITY_FIELDS = {"event_truth", "timing", "spatialization", "cue_separation", "playback", "originality"}
_RESERVATION_FIELDS = {"badge", "outbox", "discovery"}
_CUE_FIELDS = {"cue_id", "wave", "frequency_hz", "duration_ms", "gain"}
_AVAILABILITY = {"not_available", "unknown", "disabled"}
_ALLOWED_CUES = {"iy.scene_marker.v1", "iy.analysis_attention.v1", "iy.player_marker.v1"}
_ALLOWED_WAVES = {"sine_decay", "noise_burst"}


def _exact_object(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise OwnedTacticalAudioError(f"{label} must contain exactly {sorted(fields)}")
    return value


def _availability(value: Any, label: str) -> AudioAvailability:
    if value not in _AVAILABILITY:
        raise OwnedTacticalAudioError(f"{label} must be one of {sorted(_AVAILABILITY)}")
    return value


def _finite_number(value: Any, label: str, *, low: float, high: float) -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= float(value) <= high:
        raise OwnedTacticalAudioError(f"{label} must be a finite value within [{low}, {high}]")
    return float(value)


def _cue(value: Any) -> ProceduralCue:
    item = _exact_object(value, _CUE_FIELDS, "cue")
    cue_id = item["cue_id"]
    if cue_id not in _ALLOWED_CUES:
        raise OwnedTacticalAudioError("cue_id is not an approved own tactical cue")
    if item["wave"] not in _ALLOWED_WAVES:
        raise OwnedTacticalAudioError("cue wave is not an approved procedural wave")
    frequency = item["frequency_hz"]
    if item["wave"] == "sine_decay":
        frequency = _finite_number(frequency, "sine_decay.frequency_hz", low=180.0, high=1800.0)
    elif frequency is not None:
        raise OwnedTacticalAudioError("noise_burst frequency_hz must be null")
    duration = _finite_number(item["duration_ms"], "duration_ms", low=20.0, high=250.0)
    if duration != int(duration):
        raise OwnedTacticalAudioError("duration_ms must be integral")
    gain = _finite_number(item["gain"], "gain", low=0.0, high=0.20)
    return ProceduralCue(cue_id, item["wave"], frequency, int(duration), gain)


def load_owned_tactical_audio(path: Path, replay_map_id: str) -> OwnedTacticalAudio:
    """Load a fail-closed own audio descriptor for one canonical replay map."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise OwnedTacticalAudioError(f"owned tactical audio descriptor is missing: {path}") from error
    except json.JSONDecodeError as error:
        raise OwnedTacticalAudioError(f"owned tactical audio descriptor is invalid JSON: {error}") from error

    document = _exact_object(document, _TOP_LEVEL_FIELDS, "audio document")
    if document["schema"] != OWNED_TACTICAL_AUDIO_SCHEMA:
        raise OwnedTacticalAudioError(f"expected schema {OWNED_TACTICAL_AUDIO_SCHEMA}")
    if not isinstance(document["map_id"], str) or document["map_id"] != replay_map_id:
        raise OwnedTacticalAudioError("audio map_id differs from replay map")
    if document["purpose"] != "presentation_only":
        raise OwnedTacticalAudioError("audio purpose must remain presentation_only")
    if document["source_classification"] != "OWNED_PROCEDURAL":
        raise OwnedTacticalAudioError("audio source classification is not approved")

    user_control = _exact_object(document["user_control"], _USER_CONTROL_FIELDS, "user_control")
    if user_control["default_state"] != "disabled":
        raise OwnedTacticalAudioError("audio must remain disabled by default")
    authenticity = _exact_object(document["authenticity_contract"], _AUTHENTICITY_FIELDS, "authenticity_contract")
    expected_authenticity = {
        "event_truth": "canonical_event_only",
        "timing": "canonical_controller_selection_only",
        "spatialization": "canonical_position_only",
        "cue_separation": "gameplay_ui_badge_outbox_discovery_distinct",
        "playback": "optional_local_transparent_removable",
        "originality": "owned_or_separately_licensed_non_valve_non_imitative",
    }
    if authenticity != expected_authenticity:
        raise OwnedTacticalAudioError("audio authenticity_contract must remain exact")
    reservations = _exact_object(document["future_reservations"], _RESERVATION_FIELDS, "future_reservations")
    cue_values = document["cues"]
    if not isinstance(cue_values, list):
        raise OwnedTacticalAudioError("cues must be a list of strict cue objects")
    cues = tuple(_cue(value) for value in cue_values)
    if len({cue.cue_id for cue in cues}) != len(cues):
        raise OwnedTacticalAudioError("cue_id values must be unique")

    return OwnedTacticalAudio(
        map_id=replay_map_id,
        output_state=_availability(document["output_state"], "output_state"),
        event_mapping_state=_availability(document["event_mapping_state"], "event_mapping_state"),
        cues=cues,
        badge_state=_availability(reservations["badge"], "future_reservations.badge"),
        outbox_state=_availability(reservations["outbox"], "future_reservations.outbox"),
        discovery_state=_availability(reservations["discovery"], "future_reservations.discovery"),
    )


def project_owned_audio_cues(audio: OwnedTacticalAudio, frame: ReplayFrame) -> tuple[ProceduralCue, ...]:
    """Return no cue until output and event mapping are separately authorised.

    ``frame`` is accepted solely to make the canonical-boundary explicit.  The
    current foundation intentionally reads no events, owns no deduplication,
    and never advances or interprets replay time.
    """
    del frame
    if audio.output_state != "not_available" or audio.event_mapping_state != "not_available":
        return ()
    return ()
