from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from improve_yourself.owned_tactical_audio import (
    OWNED_TACTICAL_AUDIO_SCHEMA,
    OwnedTacticalAudioError,
    load_owned_tactical_audio,
    project_owned_audio_cues,
)
from improve_yourself.replay_contract import ReplayEvent, ReplayFrame


ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR = ROOT / "resources" / "3d_pov" / "de_anubis" / "owned_tactical_audio.json"


def _document() -> dict:
    return json.loads(DESCRIPTOR.read_text(encoding="utf-8"))


def _write(tmp_path: Path, document: dict) -> Path:
    path = tmp_path / "audio.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def _frame_with_canonical_event() -> ReplayFrame:
    return ReplayFrame(
        tick=6401,
        round_number=1,
        time_in_round_seconds=None,
        players=(),
        utilities=(),
        events=(ReplayEvent("canonical-event", "kill", 6401, ("p1", "p2"), "parser_event", {}),),
    )


def test_audio_descriptor_is_owned_procedural_disabled_and_has_no_gameplay_authority() -> None:
    document = _document()
    assert document["schema"] == OWNED_TACTICAL_AUDIO_SCHEMA
    assert set(document) == {
        "schema", "map_id", "purpose", "source_classification", "output_state",
        "event_mapping_state", "user_control", "authenticity_contract", "cues", "future_reservations",
    }
    assert document["purpose"] == "presentation_only"
    assert document["source_classification"] == "OWNED_PROCEDURAL"
    assert document["output_state"] == document["event_mapping_state"] == "not_available"
    assert document["user_control"] == {"default_state": "disabled"}
    assert document["authenticity_contract"] == {
        "event_truth": "canonical_event_only",
        "timing": "canonical_controller_selection_only",
        "spatialization": "canonical_position_only",
        "cue_separation": "gameplay_ui_badge_outbox_discovery_distinct",
        "playback": "optional_local_transparent_removable",
        "originality": "owned_or_separately_licensed_non_valve_non_imitative",
    }
    assert document["future_reservations"] == {
        "badge": "not_available", "outbox": "not_available", "discovery": "not_available",
    }
    assert [cue["cue_id"] for cue in document["cues"]] == [
        "iy.scene_marker.v1", "iy.analysis_attention.v1", "iy.player_marker.v1",
    ]
    prohibited_tokens = {
        "tick", "position", "yaw", "pitch", "collision", "visibility", "route", "callout",
        "weapon", "kill", "footstep", "bomb", "flash", "smoke", "valve", "cs2", "vpk",
        "path", "url", "reward", "unlock", "progress", "profile",
    }
    serialized = json.dumps(document, sort_keys=True).lower()
    assert not any(f'"{token}"' in serialized for token in prohibited_tokens)


def test_audio_descriptor_loads_only_for_exact_map_and_never_projects_a_cue_yet() -> None:
    audio = load_owned_tactical_audio(DESCRIPTOR, "de_anubis")
    assert [cue.cue_id for cue in audio.cues] == [
        "iy.scene_marker.v1", "iy.analysis_attention.v1", "iy.player_marker.v1",
    ]
    frame = _frame_with_canonical_event()
    assert project_owned_audio_cues(audio, frame) == ()
    assert frame.events[0].event_id == "canonical-event"
    with pytest.raises(OwnedTacticalAudioError, match="differs from replay map"):
        load_owned_tactical_audio(DESCRIPTOR, "de_mirage")


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda d: d.update({"unknown": True}), "audio document"),
        (lambda d: d.update({"purpose": "replay_event_audio"}), "presentation_only"),
        (lambda d: d.update({"source_classification": "CS2_EXTRACTED"}), "not approved"),
        (lambda d: d["user_control"].update({"default_state": "enabled"}), "disabled by default"),
        (lambda d: d["authenticity_contract"].update({"originality": "valve_sample"}), "authenticity_contract"),
        (lambda d: d.update({"output_state": "available"}), "output_state"),
        (lambda d: d.update({"event_mapping_state": "available"}), "event_mapping_state"),
        (lambda d: d["future_reservations"].update({"badge": "available"}), "future_reservations.badge"),
        (lambda d: d["cues"].append(deepcopy(d["cues"][0])), "unique"),
        (lambda d: d["cues"][0].update({"cue_id": "cs2_footstep"}), "not an approved"),
        (lambda d: d["cues"][0].update({"wave": "recorded_sample"}), "not an approved"),
        (lambda d: d["cues"][0].update({"frequency_hz": "https://example.invalid/sound"}), "finite"),
        (lambda d: d["cues"][0].update({"gain": 0.5}), "within"),
        (lambda d: d.update({"cues": "C:/Users/private/Valve.wav"}), "cues must be a list"),
    ],
)
def test_unsafe_audio_claims_fail_closed(tmp_path: Path, mutate, message: str) -> None:
    document = deepcopy(_document())
    mutate(document)
    with pytest.raises(OwnedTacticalAudioError, match=message):
        load_owned_tactical_audio(_write(tmp_path, document), "de_anubis")


def test_audio_foundation_has_no_playback_loader_or_second_time_event_path() -> None:
    source = (ROOT / "src" / "improve_yourself" / "owned_tactical_audio.py").read_text(encoding="utf-8")
    renderer = (ROOT / "src" / "improve_yourself" / "panda_renderer.py").read_text(encoding="utf-8")
    assert "loadSfx" not in source and "AudioSound" not in source and ".play(" not in source
    assert "ReplayStore(" not in source and "ReplayController(" not in source
    assert "import time" not in source and "time.monotonic(" not in source and "subscribe(" not in source
    assert "audio-library-name null" in renderer
