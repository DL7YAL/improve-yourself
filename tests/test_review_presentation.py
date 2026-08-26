from __future__ import annotations

import pytest

from improve_yourself.review_presentation import REVIEW_PRESENTATION_V1_SCHEMA, build_review_presentation


def _review_projection() -> dict[str, object]:
    return {
        "schema": "iy.review_projection/v1",
        "match": {"map_id": "de_ancient"},
        "rounds": [{"round_number": 1}],
        "events": {"kills": [{"tick": 100}], "unavailable_channels": ["footsteps"]},
        "replay_reference": {"schema": "iy.replay/v2"},
    }


def test_review_presentation_separates_facts_hints_limits_and_next_steps() -> None:
    result = build_review_presentation(_review_projection())

    assert result["schema"] == REVIEW_PRESENTATION_V1_SCHEMA
    assert result["analysis"]["facts"] == ("Map: de_ancient", "Runden: 1", "Belegte Kill-Ereignisse: 1")
    assert result["analysis"]["hints"] == ("Szenen sind Prüfhinweise und kein Cheat-Nachweis.",)
    assert result["analysis"]["limits"] == ("footsteps: UNKNOWN / NOT AVAILABLE",)
    assert result["analysis"]["next_steps"] == ("Eine Szene auswählen und den belegten Tick im lokalen Review prüfen.",)


def test_system_check_is_a_separate_read_only_source_and_never_leaks_into_analysis() -> None:
    system = {
        "schema": "iy.system_check/v1",
        "policy": {"read_only": True, "changes_applied": False},
        "checks": [{"label": "CPU", "status": "OK", "summary": "Erkannt.", "evidence": {"name": "CPU"}}],
        "optimizer": {"must_not_flow": True},
        "demo": {"must_not_flow": True},
        "replay": {"must_not_flow": True},
    }

    result = build_review_presentation(_review_projection(), system)

    assert result["system_check"]["availability"] == "AVAILABLE / READ-ONLY"
    assert result["system_check"]["results"] == ({"label": "CPU", "status": "OK", "summary": "Erkannt.", "next_step": "Keine automatische Änderung wurde vorgenommen."},)
    assert set(result) == {"schema", "analysis", "system_check"}
    assert "optimizer" not in result["analysis"]
    assert "demo" not in result["analysis"]
    assert "replay" not in result["analysis"]


def test_untrusted_system_check_stays_unknown_and_invalid_review_projection_is_rejected() -> None:
    result = build_review_presentation(_review_projection(), {"schema": "iy.system_check/v1", "policy": {}, "checks": []})
    assert result["system_check"]["availability"] == "UNKNOWN / NOT AVAILABLE"
    assert result["system_check"]["limits"] == ("System-Check-Evidenz ist nicht als read-only bestätigt.",)
    with pytest.raises(ValueError, match="iy.review_projection/v1"):
        build_review_presentation({})
